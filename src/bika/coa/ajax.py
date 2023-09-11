# -*- coding: utf-8 -*-

import StringIO
import csv
from bika.coa import logger
from bika.lims import api
from DateTime import DateTime
from senaite.app.supermodel.interfaces import ISuperModel
from senaite.impress.interfaces import IPdfReportStorage
from senaite.impress.interfaces import ITemplateFinder
from senaite.impress.ajax import AjaxPublishView as AP
from zope.component import getMultiAdapter
from zope.component import getAdapter
from zope.component import getUtility


class AjaxPublishView(AP):
    def ajax_save_reports(self):
        """Render all reports as PDFs and store them as AR Reports
        """
        # Data sent via async ajax call as JSON data from the frontend
        data = self.get_json()

        # This is the html after it was rendered by the client browser and
        # eventually extended by JavaScript, e.g. Barcodes or Graphs added etc.
        # NOTE: It might also contain multiple reports!
        html = data.get("html")

        # get the triggered action (Save|Email)
        action = data.get("action", "save")

        # get the selected template
        template = data.get("template")

        # get the selected paperformat
        paperformat = data.get("format")

        # get the selected orientation
        orientation = data.get("orientation", "portrait")

        # Generate the print CSS with the set format/orientation
        css = self.get_print_css(
            paperformat=paperformat, orientation=orientation)
        logger.info(u"Print CSS: {}".format(css))

        # get the publisher instance
        publisher = self.publisher
        # add the generated CSS to the publisher
        publisher.add_inline_css(css)

        # get COA number
        parser = publisher.get_parser(html)
        coa_num = parser.find_all(attrs={'name': 'coa_num'})
        coa_num = coa_num.pop()
        coa_num = coa_num.text.strip()

        # split the html per report
        # NOTE: each report is an instance of <bs4.Tag>
        html_reports = publisher.parse_reports(html)

        # generate a PDF for each HTML report
        pdf_reports = map(publisher.write_pdf, html_reports)

        # extract the UIDs of each HTML report
        # NOTE: UIDs are injected in `.analysisrequest.reportview.render`
        report_uids = map(
            lambda report: report.get("uids", "").split(","), html_reports)

        # generate a CSV for each report_uids
        samples = []
        for sample in data['items']:
            sample = getAdapter(sample, ISuperModel)
            samples.append(sample)

        csv_reports = []
        is_multi_template = self.is_multi_template(template)
        if template == "bika.coa:GeoangolBatchMulti.pt":
            csv_report = self.create_geochemistry_csv_report(samples,coa_num)
            csv_reports = [csv_report for i in range(len(pdf_reports))]
        elif template == "bika.coa:AWTCBatchMulti.pt":
            csv_report= self.create_batch_csv_reports(samples,coa_num)
            csv_reports = [csv_report for i in range(len(pdf_reports))]
        elif template == "bika.coa:ZimlabsTransposedMulti.pt":
            csv_report = self.create_zlabs_csv_report(samples,coa_num)
            csv_reports = [csv_report for i in range(len(pdf_reports))]
        elif is_multi_template:
            csv_report = self.create_csv_reports(samples)
            csv_reports = [csv_report for i in range(len(pdf_reports))]
        else:
            for sample_csv in samples:
                csv_report = self.create_csv_report(sample_csv)
                csv_reports.append(csv_report)

        # prepare some metadata
        metadata = {
            "template": template,
            "paperformat": paperformat,
            "orientation": orientation,
            "timestamp": DateTime().ISO8601(),
        }

        # Create PDFs and HTML
        # get the storage multi-adapter to save the generated PDFs
        storage = getMultiAdapter(
            (self.context, self.request), IPdfReportStorage)

        report_groups = []
        for pdf, html, csv_text, uids in zip(pdf_reports, html_reports, csv_reports, report_uids):
            # ensure we have valid UIDs here
            uids = filter(api.is_uid, uids)
            # convert the bs4.Tag back to pure HTML
            html = publisher.to_html(html)
            # BBB: inject contained UIDs into metadata
            metadata["contained_requests"] = uids
            # store the report(s)
            objs = storage.store(pdf, html, uids, metadata=metadata, csv_text=csv_text, coa_num=coa_num)
            # append the generated reports to the list
            report_groups.append(objs)

        # Fixed LIMS-3288 - send one email with multiple attache
        report_groups = [[a[0] for a in report_groups]]

        # NOTE: The reports might be stored in multiple places (clients),
        #       which makes it difficult to redirect to a single exit URL
        #       based on the action the users clicked (save/email)
        exit_urls = map(lambda reports: self.get_exit_url_for(
            reports, action=action), report_groups)

        if not exit_urls:
            return api.get_url(self.context)

        return exit_urls[0]

    def create_batch_csv_reports(self,samples,coa_num):
        analyses = []
        output = StringIO.StringIO()
        top_headers= ["Unique COA ID","Project Title","Batch ID","Client","Date Sampled","Date Reported"]
        group_cats = {}
        writer = csv.writer(output)

        # The key is the is the analysis service followed space to enter the results of the analysis service
        # for the sample in question
        field_analyses = {}
        lab_analyses = {}
        analysis_services = api.get_setup().bika_analysisservices.values()

        for AS in analysis_services:
            if not AS.getHidden():
                if AS.getPointOfCapture()=="field":
                    if AS.Title() not in field_analyses.keys():
                        full_columns = [""]*len(samples)
                        full_columns.append(AS.getSortKey())
                        field_analyses[AS.Title()] = full_columns
                else:
                    if AS.Title() not in lab_analyses.keys():
                        full_columns = [""]*len(samples)
                        full_columns.append(AS.getSortKey())
                        lab_analyses[AS.Title()] = full_columns

        for sample in samples:
            date_received = sample.DateReceived
            date_sampled = sample.DateSampled
            date_reported = DateTime().Date()
            coa_id =coa_num
            batch_title = ""
            if date_sampled:
                date_sampled = date_sampled.strftime('%m-%d-%y')
            if date_received:
                date_received = date_received.strftime('%m-%d-%y')
            date_verified = sample.getDateVerified()
            if date_verified:
                date_verified = date_verified.strftime('%m-%d-%y')
            if sample.Batch:
                batch_title = sample.Batch.title

            headers_line= [
                coa_id,
                batch_title,
                sample.BatchID,
                sample.Client.title,
                date_sampled,
                date_reported
            ]

            analyses = sample.getAnalyses(full_objects=True)
            for analysis in analyses:
                analysis_info = {'sampleID':sample.id,
                                 'samplePoint':sample.SamplePointTitle,
                                 'sampleType':sample.SampleTypeTitle,
                                 'title': analysis.Title(),
                                 'result': analysis.getFormattedResult(html=False),
                                 'unit': analysis.getService().getUnit(),
                                 'obj':analysis,
                                 'order':analysis.getSortKey()}
                if analysis.getPointOfCapture() not in group_cats.keys():
                    group_cats[analysis.getPointOfCapture()] = []
                group_cats[analysis.getPointOfCapture()].append(analysis_info)

            if len(headers_line) != len(top_headers):
                for i in top_headers[len(headers_line):]:
                    headers_line.append('')

        sample_data = self.get_sample_header_data(samples)
        sample_ids = sample_data[0]
        penultimate_field_analyses = self.create_field_sample_rows(
                    group_cats, field_analyses, sample_ids)
        penultimate_lab_analyses = self.create_lab_sample_rows(
                    group_cats, lab_analyses, sample_ids)

        header_rows = self.merge_header_and_values(top_headers, headers_line)
        final_field_analyses = self.sort_analyses_to_list(
                penultimate_field_analyses)
        final_lab_analyses = self.sort_analyses_to_list(
                penultimate_lab_analyses)
        
        for row in header_rows:
            writer.writerow(row)

        for new_row in sample_data:
            writer.writerow(new_row)

        writer.writerow(["Field Analyses"])
        for field_analyses_row in final_field_analyses:
            results_row = field_analyses_row[1]
            if not all('' == s or s is None for s in results_row):
                results_row.insert(0,field_analyses_row[0])
                results_row.pop()
                writer.writerow(results_row)

        writer.writerow(["Lab Analyses"])
        for lab_analyses_row in final_lab_analyses:
            lab_results_row = lab_analyses_row[1]
            if not all('' == s or s is None for s in lab_results_row):
                lab_results_row.insert(0,lab_analyses_row[0])
                lab_results_row.pop()
                writer.writerow(lab_results_row)
        return output.getvalue()

    def create_geochemistry_csv_report(self,samples,coa_num):
        output = StringIO.StringIO()
        writer = csv.writer(output)
        headers = self.get_geochemistry_headers(samples,coa_num)
        analysis_services,body = self.get_geochemistry_body(samples)
        sample_data = self.get_geochemistry_analysis_request(analysis_services,samples)
        if sample_data:
            removal_keys = self.get_index_of_columns_to_be_removed(sample_data)
        body,sample_data = self.remove_empty_services(body,sample_data,removal_keys)

        #write headers
        for header in headers:
            writer.writerow(header)
        #write body
        for row in body:
            writer.writerow(row)
        #write sample data
        for data in sample_data:
            writer.writerow(data)

        return output.getvalue()

    def get_index_of_columns_to_be_removed(self,sample_data):
        removal_keys = []
        for indx in range(len(sample_data[0])):
            column = [i[indx] for i in sample_data if len(i) > 1]
            if all('' == s or s is None for s in column):
                removal_keys.append(indx)
        return removal_keys

    def get_geochemistry_analysis_request(self,analysis_services,samples):
        sorted_samples = sorted(samples, key=lambda x:x.ClientSampleID)
        sample_data = []
        sample_analyses,sample_analyses_ids = self.get_sample_analyses(sorted_samples) #The first entry is the sample and the rest are the analyses of those samples
        for indx,sample in enumerate(sample_analyses):
            sample_results = [sample[0].ClientSampleID]
            for analysis_service in analysis_services:
                if analysis_service.getKeyword() in sample_analyses_ids[indx]:
                    sample_results.append(sample[sample_analyses_ids[indx].index(analysis_service.getKeyword())].getFormattedResult(html=False))
                else:
                    sample_results.append("")
            sample_data.append(sample_results)
            sample_data.append(["\n"])
        sample_data.pop()
        return sample_data

    def get_sample_analyses(self,samples):
        all_samples_with_analyses = []
        all_sample_ids = []
        for sample in samples:
            sample_analyses = sample.Analyses
            sample_analyses.insert(0,sample)
            all_samples_with_analyses.append(sample_analyses)
            all_sample_ids.append([i.get("id") for i in sample_analyses])
        return all_samples_with_analyses,all_sample_ids


    def get_geochemistry_body(self,samples):
        analysis_services_full_list = api.get_setup().bika_analysisservices.values()
        eligible_analysis_services = sorted([item for item in analysis_services_full_list if item.getSortKey()], key=lambda x:x.getSortKey())
        methods_list = ["Method"]
        analysis_Ids_list = ["Element"]
        unit_list = ["Unit"]
        ldl_list = ["LDL"]
        udl_list = ["UDL"]
        tolerance_list = ["TOLERANCE"]
        digestion_list = ["DIGESTION"]
        temperature_list = ["TEMPERATURE"]
        time_list = ["TIME"]
        final_body_rows = []

        for analysis_service in eligible_analysis_services:
            if analysis_service.getMethod():
                methods_list.append(analysis_service.getMethod().getMethodID())
            else:
                methods_list.append("")
            analysis_Ids_list.append(analysis_service.getProtocolID())
            unit_list.append(analysis_service.getUnit())
            ldl_list.append(analysis_service.getLowerDetectionLimit())
            udl_list.append(analysis_service.getUpperDetectionLimit())
            if analysis_service.getKeyword() == "Au":
                tolerance_list.append("0.05")
                digestion_list.append("FA-FUS02")
                temperature_list.append("1050°C")
                time_list.append("60 mins.")
            else:
                tolerance_list.append("NA")
                digestion_list.append("NA")
                temperature_list.append("NA")
                time_list.append("NA")
        
        final_body_rows = [
            methods_list,["\n"],analysis_Ids_list,["\n"],unit_list,["\n"],
            ldl_list,["\n"],udl_list,["\n"],tolerance_list,["\n"],digestion_list,["\n"],
            temperature_list,["\n"],time_list,["\n"]]

        return eligible_analysis_services,final_body_rows


    def get_geochemistry_headers(self,samples,coa_num):
        sample = samples[0]
        current_user = api.get_current_user()
        user = api.get_user_contact(current_user)
        lab_obj = self.context.bika_setup.laboratory
        if not user:
            user = '{}'.format(current_user.id)
        headers = []
        headers.append(['Lab Certificate Number',coa_num])
        headers.append(["\n"])
        headers.append(["Client Name",sample.Client.title])
        headers.append(["\n"])
        headers.append(["Client Reference Number", sample.getBatchID()])
        headers.append(["\n"])
        headers.append(["Lab Name and Location",lab_obj.getName(),lab_obj.getPhysicalAddress().get('city')])
        headers.append(["\n"])
        headers.append(["Country of Sample Origin",sample.Client.PostalAddress.get('country')])
        headers.append(["\n"])
        batch_title = ''
        if sample.Batch:
            batch_title = sample.Batch.title
        headers.append(["Project Name",batch_title])
        headers.append(["\n"])

        date_received = ""
        if sample.DateReceived:
            date_received = sample.DateReceived.strftime('20%y/%m/%d')
        headers.append(["Date Sample Received at Lab",date_received])
        headers.append(["\n"])
        date_verified = ""
        if sample.getDateVerified():
            date_verified = sample.getDateVerified().strftime('20%y/%m/%d')
        headers.append(["Date of Analysis Finalization",date_verified])
        headers.append(["\n"])
        date_published = ""
        if sample.DatePublished:
            date_published = sample.DatePublished.strftime('20%y/%m/%d')

        headers.append(["Date Assay Report Delivered",date_published])
        headers.append(["\n"])
        headers.append(["Total Number of Samples Submitted to Lab",len(samples)])
        headers.append(["\n"])
        headers.append(["Sample Type",sample.SampleTypeTitle])
        headers.append(["\n"])
        coa_remarks = ''
        if sample.Batch:
            coa_remarks = sample.Batch.COARemarks
        headers.append(["Certificate Comments",coa_remarks])
        headers.append(["\n"])
        headers.append(["Final Approval",user])
        headers.append(["\n"])
        profiles_titles = ""
        if sample.Profiles:
            profiles_titles = [i.title for i in sample.Profiles]
        if len(profiles_titles) == 1:
            profiles_titles = profiles_titles[0]
        headers.append(["Analysis",profiles_titles])
        headers.append(["\n"])
        return headers

    def remove_empty_services(self,body,analyses,removal_keys):
        sorted_removal_keys = sorted(removal_keys,reverse=True)
        for indx,item in enumerate(analyses):
            if len(item) > 1:
                for rem_key in sorted_removal_keys:
                    analyses[indx].pop(rem_key)
        for indx2,item2 in enumerate(body):
            if len(item2) > 1:
                for rem_key in sorted_removal_keys:
                    body[indx2].pop(rem_key)
        return body, analyses

    def sort_analyses_to_list(self,analyses):
        title_sort = sorted(analyses.items(), key=lambda x:x[0])
        key_sort = sorted(title_sort, key=lambda x:(x[1][-1] is None,x[1][-1]))
        return key_sort

    def create_field_sample_rows(
                self, grouped_analyses, field_analyses, sample_ids):

        if grouped_analyses.get("field"):
            for field_AS in grouped_analyses.get("field"):
                position_at_top = sample_ids.index(
                                            field_AS.get("sampleID")) - 1
                title = field_AS.get('title')
                field_analyses[title][position_at_top] = field_AS.get(
                                                                "result")
        return field_analyses

    def create_lab_sample_rows(
                self, grouped_analyses, lab_analyses, sample_ids):

        if grouped_analyses.get("lab"):
            for lab_AS in grouped_analyses.get("lab"):
                position_at_top = sample_ids.index(
                                            lab_AS.get("sampleID")) - 1
                title = lab_AS.get('title')
                if lab_analyses.get(title):
                    lab_analyses.get(title)[position_at_top] = lab_AS.get(
                                                                "result")
        return lab_analyses

    def get_sample_header_data(self, samples):
        sample_ids = ["Sample ID"]
        sample_points = ["Sample Points"]
        sample_types = ["Sample Types"]
        for sample in samples:
            sample_ids.append(sample.Title())
            sample_points.append(sample.getSamplePointTitle())
            sample_types.append(sample.getSampleTypeTitle())
        return [sample_ids, sample_points, sample_types]

    def merge_header_and_values(self,headers,values):
        """Merge the headers and their values to make writing to CSV easier"""
        row1 = []
        row2 = []
        for num in range(len(headers)):
            if num < len(headers)//2:
                row1.append(headers[num])
                row1.append(values[num])
            else:
                row2.append(headers[num])
                row2.append(values[num])
        return [row1,row2]

#ZimLabs CSV begin

    def create_zlabs_csv_report(self,samples,coa_num):
        output = StringIO.StringIO()
        writer = csv.writer(output)
        headers = self.get_zlabs_headers(samples,coa_num)
        analysis_services,body = self.get_zlabs_body()
        extra_column = True
        sample_data = self.get_zlabs_analysis_request(samples,analysis_services,extra_column)
        if sample_data:
            removal_keys = self.get_index_of_columns_to_be_removed(sample_data)
        body,sample_data = self.remove_empty_services(body,sample_data,removal_keys)

        #write headers
        for header in headers:
            writer.writerow(header)
        #write body
        for row in body:
            writer.writerow(row)
        #write sample data
        for data in sample_data:
            writer.writerow(data)

        return output.getvalue()

    def get_zlabs_headers(self,samples,coa_num):
        sample = samples[0]
        current_user = api.get_current_user()
        user = api.get_user_contact(current_user)
        if not user:
            user = '{}'.format(current_user.id)
        headers = []
        headers.append(['COA',coa_num])
        headers.append(["Client Name",sample.Client.title,"Client Contact",sample.Contact.title,"Client Contact Email Address",sample.Contact.EmailAddress])
        headers.append(["Project", sample.getBatchID(),"Sample Type",sample.SampleTypeTitle,"No of Samples",len(samples)])

        date_received = ""
        if sample.DateReceived:
            date_received = sample.DateReceived.strftime('%d/%m/20%y')
        headers.append(["Date Received",date_received])

        analyzed_from,analyzed_to = self.get_analyzed_dates(samples)
        headers.append(["Date Analyzed",analyzed_from,"to",analyzed_to])

        verified_from,verified_to = self.get_verified_dates(samples)
        headers.append(["Date Verified",verified_from,"to",verified_to])

        date_published = ""
        if sample.DatePublished:
            date_published = sample.DatePublished.strftime('%d/%m/20%y')
        headers.append(["Date Published",date_published])

        headers.append(["Soft Copy Number","To be Confirmed"])
        return headers
    
    def get_verified_dates(self,samples):
        verified_from = ""
        verified_to = ""
        all_dates = []
        for sample in samples:
            date_verified = sample.getDateVerified()
            if date_verified:
                all_dates.append(date_verified)
        all_dates.sort()
        if len(all_dates) > 1:
            verified_from = all_dates[0].strftime('%d/%m/20%y')
            verified_to = all_dates[-1].strftime('%d/%m/20%y')
        if len(all_dates) == 1:
            verified_from = all_dates[0].strftime('%d/%m/20%y')
            verified_to = all_dates[0].strftime('%d/%m/20%y')
        return verified_from,verified_to

    def get_analyzed_dates(self,samples):
        analyzed_from = ""
        analyzed_to = ""
        all_dates = []
        for sample in samples:
            for analysis in sample.Analyses:
                date_analyzed = analysis.ResultCaptureDate
                if date_analyzed:
                    all_dates.append(date_analyzed)
        all_dates.sort()
        if len(all_dates) > 1:
            analyzed_from = all_dates[0].strftime('%d/%m/20%y')
            analyzed_to = all_dates[-1].strftime('%d/%m/20%y')
        if len(all_dates) == 1:
            analyzed_from = all_dates[0].strftime('%d/%m/20%y')
            analyzed_to = all_dates[0].strftime('%d/%m/20%y')
        return analyzed_from,analyzed_to

    def get_zlabs_body(self):
        analysis_services_full_list = api.get_setup().bika_analysisservices.values()
        eligible_analysis_services = sorted([item for item in analysis_services_full_list if item.getSortKey()], key=lambda x:x.getSortKey())
        analysis_Ids_list = ["Analysis",""]
        methods_list = ["Method",""]
        unit_list = ["Unit",""]
        final_body_rows = []

        for analysis_service in eligible_analysis_services:
            if analysis_service.getMethod():
                methods_list.append(analysis_service.getMethod().Title())
            else:
                methods_list.append("")
            analysis_Ids_list.append(analysis_service.Title())
            unit_list.append(analysis_service.getUnit())
        
        final_body_rows = [
            analysis_Ids_list,methods_list,unit_list,]
        return eligible_analysis_services,final_body_rows
    
    def get_zlabs_analysis_request(self,samples,analysis_services,extra_column):
        sorted_samples = sorted(samples, key=lambda x:x.ClientSampleID)
        sample_data = []
        sample_analyses,sample_analyses_ids = self.get_sample_analyses(sorted_samples) #The first entry is the sample and the rest are the analyses of those samples
        for indx,sample in enumerate(sample_analyses):
            sample_results = [sample[0].ClientSampleID]
            if extra_column:
                sample_results.append(sample[0].id)
            for analysis_service in analysis_services:
                if analysis_service.getKeyword() in sample_analyses_ids[indx]:
                    sample_results.append(sample[sample_analyses_ids[indx].index(analysis_service.getKeyword())].getFormattedResult(html=False))
                else:
                    sample_results.append("")
            sample_data.append(sample_results)
        return sample_data

#ZimLabs CSV end

    def create_csv_report(self, sample):
        analyses = []
        output = StringIO.StringIO()
        date_sampled = sample.DateSampled
        if date_sampled:
            date_sampled = date_sampled.strftime('%m-%d-%y')
        date_received = sample.DateReceived
        if date_received:
            date_received = date_received.strftime('%m-%d-%y')
        date_verified = sample.getDateVerified()
        if date_verified:
            date_verified = date_verified.strftime('%m-%d-%y')
        writer = csv.writer(output)
        writer.writerow(["Sample ID", sample.id])
        writer.writerow(["Client Sample ID", sample.ClientSampleID])
        writer.writerow(["Sample Type", sample.SampleTypeTitle])
        writer.writerow(["Sample Point", sample.SamplePointTitle])
        writer.writerow(["Date Sampled", date_sampled])
        writer.writerow(["Date Received", date_received])
        writer.writerow(["Date Verified", date_verified])
        writer.writerow([])
        analyses = sample.getAnalyses(full_objects=True)
        group_cats = {}
        for analysis in analyses:
            analysis_info = {'title': analysis.Title(),
                             'result': analysis.getFormattedResult(html=False),
                             'unit': analysis.getService().getUnit()}
            if analysis.getCategoryTitle() not in group_cats.keys():
                group_cats[analysis.getCategoryTitle()] = []
            group_cats[analysis.getCategoryTitle()].append(analysis_info)

        for g_cat in sorted(group_cats.keys()):
            writer.writerow([g_cat])
            writer.writerow(["Analysis", "Result", "Unit"])
            for a_info in group_cats[g_cat]:
                writer.writerow([a_info['title'], a_info['result'], a_info['unit']])

        return output.getvalue()

    def create_csv_reports(self, samples):
        analyses = []
        output = StringIO.StringIO()
        headers = ["Sample ID", "Client Sample ID",
                   "Sample Type", "Sample Point",
                   "Date Sampled", "Date Received", "Date Verified"]
        body = []
        for sample in samples:
            date_received = sample.DateReceived
            date_sampled = sample.DateSampled
            if date_sampled:
                date_sampled = date_sampled.strftime('%m-%d-%y')
            if date_received:
                date_received = date_received.strftime('%m-%d-%y')
            date_verified = sample.getDateVerified()
            if date_verified:
                date_verified = date_verified.strftime('%m-%d-%y')
            writer = csv.writer(output)
            line = [
                sample.id,
                sample.ClientSampleID,
                sample.SampleTypeTitle,
                sample.SamplePointTitle,
                date_sampled,
                date_received,
                date_verified
            ]

            analyses = sample.getAnalyses(full_objects=True)
            group_cats = {}
            for analysis in analyses:
                analysis_info = {'title': analysis.Title(),
                                 'result': analysis.getFormattedResult(html=False),
                                 'unit': analysis.getService().getUnit()}
                if analysis.getCategoryTitle() not in group_cats.keys():
                    group_cats[analysis.getCategoryTitle()] = []
                group_cats[analysis.getCategoryTitle()].append(analysis_info)

            for g_cat in sorted(group_cats.keys()):
                for a_info in group_cats[g_cat]:
                    title = a_info['title']
                    result = a_info['result']
                    unit = a_info['unit']
                    title_unit = title
                    if unit:
                        title_unit = '{} ({})'.format(title, unit)
                    if len(line) != len(headers):
                        for i in headers[len(line):]:
                            line.append('')

                    if title_unit not in headers:
                        headers.append(title_unit)
                        line.append(result)
                    else:
                        line[headers.index(title_unit)] = result

            body.append(line)

        writer.writerow(headers)
        for rec in body:
            writer.writerow(rec)

        return output.getvalue()

    def ajax_templates(self):
        """Returns the available templates
        """
        templates = api.get_registry_record("senaite.impress.templates")
        return sorted([item for item in templates if 'bika' in item or 'testit' in item])

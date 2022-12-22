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
        if template == "bika.coa:MultiBatch.pt":
            csv_report= self.create_batch_csv_reports(samples,coa_num)
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

        # The key is the is the analysis service followed space to enter the results of the analysis service
        # for the sample in question
        field_analyses = {}
        lab_analyses = {}
        analysis_services = api.get_setup().bika_analysisservices.values()
        for AS in analysis_services:
            if AS.getPointOfCapture()=="field":
                if AS.Title() not in field_analyses.keys():
                    field_analyses[AS.Title()] = [""]*len(samples)
            else:
                if AS.Title() not in lab_analyses.keys():
                    lab_analyses[AS.Title()] = [""]*len(samples)

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

            writer = csv.writer(output)

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

        sample_data, final_field_analyses, final_lab_analyses = self.create_sample_rows(group_cats,field_analyses,lab_analyses)
        header_rows = self.merge_header_and_values(top_headers,headers_line)

        for row in header_rows:
            writer.writerow(row)

        for new_row in sample_data:
            writer.writerow(new_row)
        writer.writerow(["Field Analyses"])
        for analyses_row in final_field_analyses.items():
            results_row = analyses_row[1]
            results_row.insert(0,analyses_row[0])
            writer.writerow(results_row)

        writer.writerow(["Lab Analyses"])
        for lab_analyses_row in final_lab_analyses.items():
            lab_results_row = lab_analyses_row[1]
            lab_results_row.insert(0,lab_analyses_row[0])
            writer.writerow(lab_results_row)

        return output.getvalue()

    def create_sample_rows(self,grouped_analyses,field_analyses,lab_analyses):
        sample_ids = ["Sample ID"]
        sample_Points = ["Sample Points"]
        sample_Types = ["Sample Types"]

        for Analysis_service in grouped_analyses.get("field"):
            if Analysis_service.get("sampleID") not in sample_ids:
                sample_ids.append(Analysis_service.get("sampleID"))
                sample_Points.append(Analysis_service.get("samplePoint"))
                sample_Types.append(Analysis_service.get("sampleType"))
            position_at_top = sample_ids.index(Analysis_service.get("sampleID")) - 1
            title = Analysis_service.get('title')
            field_analyses[title][position_at_top] = Analysis_service.get("result")
        
        for lab_Analysis_service in grouped_analyses.get("lab"):
            if lab_Analysis_service.get("sampleID") not in sample_ids:
                sample_ids.append(lab_Analysis_service.get("sampleID"))
                sample_Points.append(lab_Analysis_service.get("samplePoint"))
                sample_Types.append(lab_Analysis_service.get("sampleType"))
            position_at_top = sample_ids.index(lab_Analysis_service.get("sampleID")) - 1
            title = lab_Analysis_service.get('title')
            if lab_analyses.get(title):
                lab_analyses.get(title)[position_at_top] = lab_Analysis_service.get("result")
        sample_headers = [sample_ids,sample_Points,sample_Types]
        return sample_headers,field_analyses,lab_analyses

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
        finder = getUtility(ITemplateFinder)
        templates = finder.get_templates(extensions=[".pt", ".html"])
        return sorted([item[0] for item in templates if 'bika' in item[0]])

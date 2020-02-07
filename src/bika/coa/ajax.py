import StringIO
import csv
from bika.coa import logger
from bika.lims import api
from DateTime import DateTime
from senaite.core.supermodel.interfaces import ISuperModel
from senaite.impress.interfaces import IPdfReportStorage
from senaite.impress.ajax import AjaxPublishView as AP
from zope.component import getMultiAdapter
from zope.component import getAdapter


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
        ars = []
        for ar in data['items']:
            ar = getAdapter(ar, ISuperModel)
            ars.append(ar)
        csv_reports = []
        for ar_csv in ars:
            csv_report = self.create_csv_report(ar_csv)
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
            objs = storage.store(pdf, html, uids, metadata=metadata, csv_text=csv_text)
            # append the generated reports to the list
            report_groups.append(objs)

        # NOTE: The reports might be stored in multiple places (clients),
        #       which makes it difficult to redirect to a single exit URL
        #       based on the action the users clicked (save/email)
        exit_urls = map(lambda reports: self.get_exit_url_for(
            reports, action=action), report_groups)

        if not exit_urls:
            return api.get_url(self.context)

        return exit_urls[0]

    def create_csv_report(self, ar):
        analyses = []
        output = StringIO.StringIO()
        # sample = ar.getSample()
        date_rec = ar.getDateReceived()
        if date_rec:
            date_rec = date_rec.strftime('%m-%d-%y')
        sampling_date = ar.getSamplingDate()
        if sampling_date:
            sampling_date = sampling_date.strftime('%m-%d-%y')
        writer = csv.writer(output)
        writer.writerow(["Sample Type", ''])
        writer.writerow(["Client's Ref", ar.getClientReference()])
        writer.writerow(["Client's Sample ID", ])
        writer.writerow(["Lab Sample ID", ])
        writer.writerow(["Date Received", date_rec])
        writer.writerow(["Sampling Date", sampling_date])
        writer.writerow([])
        writer.writerow(["Helllo", "sss"])
        # analyses = ar.getAnalyses(full_objects=True)
        # group_cats = {}
        # for analysis in analyses:
        #     analysis_info = {'title': analysis.Title(),
        #                      'result': analysis.getFormattedResult(html=False),
        #                      'unit': analysis.getService().getUnit()}
        #     if analysis.getCategoryTitle() not in group_cats.keys():
        #         group_cats[analysis.getCategoryTitle()] = []
        #     group_cats[analysis.getCategoryTitle()].append(analysis_info)

        # for g_cat in sorted(group_cats.keys()):
        #     writer.writerow([g_cat])
        #     writer.writerow(["Analysis", "Result", "Unit"])
        #     for a_info in group_cats[g_cat]:
        #         writer.writerow([a_info['title'], a_info['result'], a_info['unit']])

        return output.getvalue()

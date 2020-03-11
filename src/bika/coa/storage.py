# -*- coding: utf-8 -*-

import transaction
from bika.lims import api
from senaite.impress import logger
from senaite.impress.decorators import synchronized
from senaite.impress.storage import PdfReportStorageAdapter as PRSA


class PdfReportStorageAdapter(PRSA):
    """Storage adapter for PDF reports
    """

    def store(self, pdf, html, uids, metadata=None, csv_text=None):
        """Store the PDF

        :param pdf: generated PDF report (binary)
        :param html: report HTML (string)
        :param csv: report CSV (string)
        :param uids: UIDs of the objects contained in the PDF
        :param metadata: dict of metadata to store
        """

        if metadata is None:
            metadata = {}

        # get the contained objects
        objs = map(api.get_object_by_uid, uids)

        # handle primary object storage
        if not self.store_multireports_individually():
            # reduce the list to the primary object only
            objs = [self.get_primary_report(objs)]

        # generate the reports
        reports = []
        for obj in objs:
            report = self.create_report(
                obj, pdf, html, uids, metadata, csv_text=csv_text)
            reports.append(report)

        return reports

    @synchronized(max_connections=1)
    def create_report(self, parent, pdf, html, uids, metadata, csv_text=None):
        """Create a new report object

        NOTE: We limit the creation of reports to 1 to avoid conflict errors on
              simultaneous publication.

        :param parent: parent object where to create the report inside
        :returns: ARReport
        """

        parent_id = api.get_id(parent)
        logger.info("Create Report for {} ...".format(parent_id))

        # Manually update the view on the database to avoid conflict errors
        parent._p_jar.sync()

        # Create the report object
        report = api.create(
            parent,
            "ARReport",
            AnalysisRequest=api.get_uid(parent),
            Pdf=pdf,
            Html=html,
            CSV=csv_text,
            ContainedAnalysisRequests=uids,
            Metadata=metadata)
        fld = report.getField('Pdf')
        fld.get(report).setFilename(parent_id + ".pdf")
        fld.get(report).setContentType('application/pdf')
        fld = report.getField('CSV')
        fld.get(report).setFilename(parent_id + ".csv")
        fld.get(report).setContentType('text/csv')

        # Commit the changes
        transaction.commit()

        logger.info("Create Report for {} [DONE]".format(parent_id))

        return report

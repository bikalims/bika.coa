# -*- coding: utf-8 -*-

from plone.namedfile.file import NamedBlobFile

from bika.lims import api
from bika.lims.idserver import generateUniqueId
from senaite.impress import logger
from senaite.impress.decorators import synchronized
from senaite.impress.storage import PdfReportStorageAdapter as PRSA


class PdfReportStorageAdapter(PRSA):
    """Storage adapter for PDF reports
    """

    def store(self, pdf, html, uids, metadata=None, csv_text=None, coa_num=""):
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
            items = sorted(objs, key=lambda item: item.ClientSampleID, reverse=True)
            objs = [items[0]]

        # generate the reports
        reports = []
        for obj in objs:
            report = self.create_report(
                obj, pdf, html, uids, metadata,
                csv_text=csv_text, coa_num=coa_num)
            reports.append(report)

        return reports

    @synchronized(max_connections=1)
    def create_report(self, parent, pdf, html, uids, metadata,
                      csv_text=None, coa_num=""):
        """Create a new report object

        NOTE: We limit the creation of reports to 1 to avoid conflict errors on
              simultaneous publication. The transaction is committed once for
              all reports in the store() method using savepoints for rollback
              capability.

        :param parent: parent object where to create the report inside
        :returns: ResultsReport
        """

        parent_id = api.get_id(parent)
        logger.info("Create Report for {} ...".format(parent_id))

        # Manually update the view on the database to avoid conflict errors
        parent._p_jar.sync()

        if not coa_num:
            coa_num = self.get_coa_number()

        # Convert PDF binary data to NamedBlobFile
        pdf_filename = "{}.pdf".format(coa_num)
        pdf_blob = NamedBlobFile(
            data=pdf,
            filename=api.safe_unicode(pdf_filename),
            contentType="application/pdf"
        )
        # Convert CSV binary data to NamedBlobFile
        csv_filename = "{}.csv".format(coa_num)
        csv_blob = NamedBlobFile(
            data=csv_text,
            filename=api.safe_unicode(csv_filename),
            contentType="text/csv"
        )

        # Create the report object
        # Field setters are called automatically by api.create(), including
        # UIDReferenceField.set() which creates backreferences via event
        # handler
        report = api.create(
            parent,
            "ResultsReport",
            sample=api.get_uid(parent),
            contained_samples=uids if uids else [],
            pdf=pdf_blob,
            csv=csv_blob,
            metadata=metadata if metadata else {})

        logger.info("Create Report for {} [DONE]".format(parent_id))

        return report

    def get_coa_number(self):
        kwargs = {"portal_type": "ResultsReport", "dry_run": True}
        coa_num = generateUniqueId(self.context, **kwargs)
        increment = 0 if int(coa_num.split("-")[-1]) == 1 else 1
        items = self.get_items()
        if items:
            increment += items.index(self.model.uid)
        num = "{:05d}".format(int(coa_num.split("-")[-1]) + increment)
        dry_run = coa_num.replace(coa_num.split("-")[-1], num)
        return dry_run

# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.CORE.
#
# SENAITE.CORE is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2018-2020 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.coa import logger
from bika.lims import api
from bika.lims.api import mail as mailapi
from bika.lims.browser.publish.emailview import EmailView as EV
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse


class EmailView(EV):
    """Overrride Email Attachments View
    """

    implements(IPublishTraverse)
    template = ViewPageTemplateFile("templates/email.pt")

    def __init__(self, context, request):
        super(EmailView, self).__init__(context, request)

    def email_csv_report_enabled(self):
        """ Check registry to see if csv email enabled
        """
        # check first if a registry record exists
        enabled = api.get_registry_record("bika.coa.email_csv_report_enabled")
        logger.info("email_csv_report_enabled: is {}".format(enabled))
        return enabled

    @property
    def get_batch(self):
        reports = self.reports
        batch_id = None
        for num, report in enumerate(reports):
            samples = report.getContainedAnalysisRequests()
            if all([getattr(i.getBatch(), "id", '') for i in samples]):
                batch_id = samples[0].getBatch().id
            break
        return batch_id

    @property
    def email_body(self):
        """Email body text to be used in the template
        """
        # request parameter has precedence
        body = self.request.get("body", None)
        if body is not None:
            return body
        setup = api.get_setup()
        body = setup.getEmailBodySamplePublication()
        template_context = {
            "client_name": self.client_name,
            "lab_name": self.lab_name,
            "lab_address": self.lab_address,
            "batch_id": self.get_batch,
        }
        rendered_body = self.render_email_template(
            body, template_context=template_context)
        return rendered_body

    @property
    def email_attachments(self):
        logger.info("email_attachments bika.coa: entered")
        attachments = []

        csv_found = False
        # Convert report PDFs -> email attachments
        for report in self.reports:
            pdf = self.get_pdf(report)
            if pdf is not None:
                filename = pdf.filename
                filedata = pdf.data
                attachments.append(mailapi.to_email_attachment(filedata, filename))
                # We don't send CSVs when it is single reports
                if "Single" in report["Metadata"]["template"]:
                    continue
                # also send 1 csv only
                if csv_found is True:
                    continue

                if self.email_csv_report_enabled and report.CSV:
                    filename = report.CSV.filename
                    f = report.CSV.getBlob().open()
                    filedata = f.read()
                    f.close()
                    attachments.append(
                        mailapi.to_email_attachment(
                            filedata, filename, mime_type="text/csv"
                        )
                    )
                    csv_found = True

        # Convert additional attachments
        for attachment in self.attachments:
            af = attachment.getAttachmentFile()
            filedata = af.data
            filename = af.filename
            attachments.append(mailapi.to_email_attachment(filedata, filename))

        logger.info("email_attachments bika.coa exit with {}".format(len(attachments)))
        return attachments

    def get_report_data(self, report):
        """Report data to be used in the template
        """
        primary_sample = report.getAnalysisRequest()
        samples = report.getContainedAnalysisRequests() or [primary_sample]
        attachments_data = []

        for sample in samples:
            for attachment in self.get_all_sample_attachments(sample):
                attachment_data = self.get_attachment_data(sample, attachment)
                attachments_data.append(attachment_data)

        pdf = self.get_pdf(report)
        filesize = "{} Kb".format(self.get_filesize(pdf))
        filename = self.get_report_filename(report)

        return {
            "sample": primary_sample,
            "attachments": attachments_data,
            "pdf": pdf,
            "obj": report,
            "uid": api.get_uid(report),
            "filesize": filesize,
            "filename": filename,
        }

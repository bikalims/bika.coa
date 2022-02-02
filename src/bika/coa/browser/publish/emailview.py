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
        sample = report.getAnalysisRequest()
        # sample attachments only
        attachments = sample.getAttachment()
        attachments_data = map(self.get_attachment_data, attachments)
        pdf = self.get_pdf(report)
        filesize = "{} Kb".format(self.get_filesize(pdf))

        return {
            "sample": sample,
            "attachments": attachments_data,
            "pdf": pdf,
            "obj": report,
            "uid": api.get_uid(report),
            "filesize": filesize,
            "filename": pdf.filename,
        }

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


class EmailView(EV):
    """Overrride Email Attachments View
    """

    template = ViewPageTemplateFile("templates/email.pt")

    def email_csv_report_enabled(self):
        """ Check registry to see if csv email enabled
        """
        # check first if a registry record exists
        enabled = api.get_registry_record("bika.coa.email_csv_report_enabled")
        logger.info('email_csv_report_enabled: is {}'.format(enabled))
        return enabled

    @property
    def email_attachments(self):
        attachments = []

        # Convert report PDFs -> email attachments
        import pdb; pdb.set_trace()
        for report in self.reports:
            pdf = self.get_pdf(report)
            if pdf is not None:
                sample = report.getAnalysisRequest()
                filename = "{}.pdf".format(api.get_id(sample))
                filedata = pdf.data
                attachments.append(
                    mailapi.to_email_attachment(filedata, filename))
                if self.email_csv_report_enabled and report.CSV:
                    filename = "{}.csv".format(api.get_id(sample))
                    filedata = report.CSV
                    attachments.append(
                        mailapi.to_email_attachment(filedata, filename))

        # Convert additional attachments
        for attachment in self.attachments:
            af = attachment.getAttachmentFile()
            filedata = af.data
            filename = af.filename
            attachments.append(
                mailapi.to_email_attachment(filedata, filename))

        return attachments

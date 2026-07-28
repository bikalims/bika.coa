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

import six
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from collections import OrderedDict
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse

from bika.lims import api
from bika.lims.api import mail as mailapi
from bika.lims.browser.publish.emailview import EmailView as EV
from bika.coa import logger


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
    def reports(self):
        """Return the objects from the UIDs given in the request
        """
        # Create a mapping of source ARs for copy
        uids = self.request.form.get("uids", [])
        # handle 'uids' GET parameter coming from a redirect
        if isinstance(uids, six.string_types):
            uids = uids.split(",")
        uids = filter(api.is_uid, uids)
        unique_uids = OrderedDict().fromkeys(uids).keys()
        return filter(None, map(self.get_object_by_uid, unique_uids))

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
                filename = self.get_report_filename(report)
                filedata = pdf.data
                attachments.append(mailapi.to_email_attachment(filedata, filename))
                # We don't send CSVs when it is single reports
                if "Single" in report.metadata["template"]:
                    continue
                # also send 1 csv only
                if csv_found is True:
                    continue

                if self.email_csv_report_enabled and report.csv:
                    filename = report.csv.filename
                    filedata = report.csv.data
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

    @property
    def generated_attachments(self):
        """Return the generated PDF and CSV files attached to the email."""
        files = []
        csv_found = False

        for report in self.reports:
            pdf = self.get_pdf(report)
            if pdf is None:
                continue
            files.append(pdf)

            if "Single" in report.metadata["template"] or csv_found:
                continue

            csv_report = getattr(report, "csv", None)
            # Keep this in sync with ``email_attachments``: this method is
            # intentionally used as a boolean attribute by the existing view.
            if self.email_csv_report_enabled and csv_report:
                files.append(csv_report)
                csv_found = True

        return files

    @property
    def attachment_count(self):
        """Return the number of files that will be attached to the email."""
        return len(self.generated_attachments) + len(self.attachments)

    @property
    def total_size(self):
        """Return the total size of generated and additional attachments."""
        return self.get_total_size(self.generated_attachments, self.attachments)

    def get_filesize(self, file_data):
        """Return a file size in KB for both AT and Dexterity blob files."""
        if file_data is None:
            return 0.0

        for accessor in ("get_size", "getSize"):
            get_size = getattr(file_data, accessor, None)
            if get_size is not None:
                try:
                    return float("%.2f" % (float(get_size()) / 1024))
                except (TypeError, ValueError):
                    pass

        data = getattr(file_data, "data", None)
        if data is None:
            return 0.0
        return float("%.2f" % (float(len(data)) / 1024))

    def ajax_recalculate_size(self):
        """Recalculate count and size after selecting extra attachments."""
        total_size = self.total_size
        return {
            "files": self.attachment_count,
            "size": "%.2f" % total_size,
            "limit": self.max_email_size,
            "limit_exceeded": total_size > self.max_email_size,
        }

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

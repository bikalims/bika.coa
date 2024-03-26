# -*- coding: utf-8 -*-

import collections
from ZODB.POSException import POSKeyError
from zope.component import adapts
from zope.interface import implements

from bika.lims import api
from bika.lims.utils import get_link
from bika.coa import is_installed
from bika.coa import _
from senaite.app.listing.interfaces import IListingView
from senaite.app.listing.interfaces import IListingViewAdapter


class ReportsListingViewAdapter(object):
    adapts(IListingView)
    implements(IListingViewAdapter)

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    def before_render(self):
        if not is_installed():
            return
        self.listing.columns = collections.OrderedDict((
            ("Info", {
                "title": "",
                "toggle": True},),
            ("COA", {
                "title": _("COA"),
                "index": "sortable_title"},),
            ("Batch", {
                "title": _("Batch")},),
            ("State", {
                "title": _("Review State")},),
            ("PDF", {
                "title": _("Download PDF")},),
            ("FileSize", {
                "title": _("Filesize")},),
            ("CSV", {
                "title": _("Download CSV")},),
            ("Date", {
                "title": _("Published Date")},),
            ("PublishedBy", {
                "title": _("Published By")},),
            ("Sent", {
                "title": _("Email sent")},),
            ("Recipients", {
                "title": _("Recipients")},),
        ))
        for i in range(len(self.listing.review_states)):
            self.listing.review_states[i]["columns"].append("COA")
            self.listing.review_states[i]["columns"].append("CSV")

    def folder_item(self, obj, item, index):
        if not is_installed():
            return item
        obj = api.get_object(obj)
        csv = self.get_csv(obj)
        filesize_csv = self.listing.get_filesize(csv)
        if filesize_csv > 0:
            url = "{}/at_download/CSV".format(obj.absolute_url())
            item["replace"]["CSV"] = get_link(
                url, value="CSV", target="_blank")

        pdf = self.listing.get_pdf(obj)
        filesize_pdf = self.listing.get_filesize(pdf)
        if filesize_pdf > 0:
            url = "{}/at_download/Pdf".format(obj.absolute_url())
            item["replace"]["PDF"] = get_link(
                url, value="PDF", target="_blank")

        pdf_filename = pdf.filename
        pdf_filename_value = 'Unknown'
        if pdf_filename:
            pdf_filename_value = pdf_filename.split('.')[0]
        ar = obj.getAnalysisRequest()
        item["replace"]["COA"] = get_link(
            ar.absolute_url(), value=pdf_filename_value
        )

        return item

    def get_csv(self, obj):
        """Get the report csv
        """
        try:
            return obj.CSV
        except (POSKeyError, TypeError):
            return None

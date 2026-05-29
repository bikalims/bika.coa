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
from senaite.core.catalog import REPORT_CATALOG


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
        """Augment folder listing item
        """
        if not is_installed():
            return item

        obj = api.get_object(obj)
        sample = obj.getSample()
        pdf = self.listing.get_pdf(obj)
        item["replace"]["COA"] = get_link(
            sample.absolute_url(), value=pdf.filename.split('.')[0]
        )

        csv = self.get_csv(obj)
        if not csv:
            return item

        filesize = self.listing.get_filesize(csv)
        if filesize > 0:
            url = "{}/download/csv".format(obj.absolute_url())
            item["replace"]["CSV"] = get_link(
                url, value="CSV", target="_blank")

        return item

    def get_csv(self, obj):
        """Get the report csv
        """
        try:
            return obj.csv
        except (POSKeyError, TypeError, AttributeError):
            return None

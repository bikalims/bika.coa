# -*- coding: utf-8 -*-

from zope.component import adapts
from zope.interface import implements

from bika.coa import is_installed
from bika.coa.browser.listingview.report_listing import \
    ReportsListingViewAdapter as RLVA
from bika.lims import api
from senaite.app.listing.interfaces import IListingView
from senaite.app.listing.interfaces import IListingViewAdapter


class AnalysisRequestPublishedResults(RLVA):
    adapts(IListingView)
    implements(IListingViewAdapter)

    def before_render(self):
        if not is_installed():
            return
        # get the client for the catalog query
        client = self.context.getClient()
        client_path = api.get_path(client)

        # get the UID of the current context (sample)
        sample_uid = api.get_uid(self.context)

        self.contentFilter = {
            "portal_type": "ARReport",
            "path": {
                "query": client_path,
                "depth": 2,
            },
            # search all reports, where the current sample UID is included
            "sample_uid": [sample_uid],
            "sort_on": "created",
            "sort_order": "descending",
        }

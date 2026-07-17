from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from plone.app.layout.viewlets import ViewletBase


class COARemarksTemplateSelector(ViewletBase):

    def available(self):
        view_name = self.request.get("URL", "").rstrip("/").split("/")[-1]
        return view_name in ("edit", "base_edit")

    def get_interpretation_templates(self):
        query = {
            "portal_type": "InterpretationTemplate",
            "review_state": "active",
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }
        return ({
            "uid": api.get_uid(brain),
            "title": api.get_title(brain),
        } for brain in api.search(query, SETUP_CATALOG))

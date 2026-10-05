# -*- coding: utf-8 -*-
from bika.coa.setuphandlers import add_method_supplier_behavior
from bika.lims import api
from senaite.core.catalog import SETUP_CATALOG


def upgrade(tool):
    portal = tool.aq_inner.aq_parent
    add_method_supplier_behavior(portal)
    # Recover legacy UIDs retained on methods by the AT-to-DX migration.
    for brain in api.search({"portal_type": "Method"}, SETUP_CATALOG):
        method = api.get_object(brain)
        if not api.is_dexterity_content(method):
            continue
        legacy_uid = method.__dict__.get("Supplier")
        field = api.get_fields(method).get("supplier")
        if field is not None and legacy_uid and not field.get_raw(method):
            field.set(method, legacy_uid)
            method.reindexObject()

# -*- coding: utf-8 -*-
"""Dexterity supplier reference for subcontracted methods."""

from bika.coa import _
from bika.lims import api
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from plone.supermodel import model
from senaite.core.catalog import SETUP_CATALOG
from senaite.core.schema import UIDReferenceField
from senaite.core.z3cform.widgets.uidreference import UIDReferenceWidgetFactory
from zope.interface import Interface, implementer, provider


class IMethodSupplierMarker(Interface):
    """Methods with a subcontractor reference."""


@provider(IFormFieldProvider)
class IMethodSupplier(model.Schema):
    supplier = UIDReferenceField(
        title=_(u"Subcontracted to"),
        allowed_types=("Supplier",),
        multi_valued=False,
        required=False,
    )

    directives.widget(
        "supplier", UIDReferenceWidgetFactory,
        catalog=SETUP_CATALOG,
        query={"portal_type": "Supplier", "is_active": True,
               "sort_on": "sortable_title", "sort_order": "ascending"},
        display_template="<a href='${url}'>${title}</a>",
        columns=[{"name": "title", "align": "left", "label": _(u"Title")}],
        limit=15,
    )


@implementer(IBehavior, IMethodSupplier)
class MethodSupplier(object):
    def __init__(self, context):
        self.context = context

    def getSupplier(self):
        return IMethodSupplier["supplier"].get(self.context)

    def getRawSupplier(self):
        return IMethodSupplier["supplier"].get_raw(self.context)

    def setSupplier(self, value):
        IMethodSupplier["supplier"].set(self.context, value)

    supplier = property(getSupplier, setSupplier)


def get_method_supplier(method):
    """Resolve the reference for both DX and legacy AT report methods."""
    if not method:
        return None
    method = api.get_object(method)
    if api.is_dexterity_content(method):
        behavior = IMethodSupplier(method, None)
        return behavior.supplier if behavior is not None else None
    accessor = getattr(method, "getSupplier", None)
    return accessor() if accessor else None

from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from .fields import ExtReferenceField
from bika.lims.interfaces import IMethod
from zope.component import adapts
from zope.interface import implements
from bika.lims.browser.widgets import ReferenceWidget as BikaReferenceWidget


class MethodSchemaExtender(object):
    adapts(IMethod)
    implements(IOrderableSchemaExtender)

    fields = [
        ExtReferenceField(
            'Supplier',
            allowed_types=['Supplier'],
            relationship='MethodSupplier',
            widget=BikaReferenceWidget(
                label=_("Subcontracted to"),
                size=20,
                catalog_name='portal_catalog',
                showOn=True,
                search_fields=('Title'),
                colModel=[
                    {'columnName': 'Title',
                     'width': '25', 'label': _('Title'),
                     'align': 'left'},
                    # UID is required in colModel
                    {'columnName': 'UID', 'hidden': True},
                ],
            ),
        ),
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        default = schematas['default']
        default.append('Supplier')
        return schematas

    def getFields(self):
        return self.fields


class MethodSchemaModifier(object):
    adapts(IMethod)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        """
        """
        return schema

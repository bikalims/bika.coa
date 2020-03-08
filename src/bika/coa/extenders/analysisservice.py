from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from bika.lims.fields import ExtReferenceField
from bika.lims.interfaces import IAnalysisService
from zope.component import adapts
from zope.interface import implements
from bika.lims.browser.widgets import ReferenceWidget as BikaReferenceWidget


class AnalysisServiceSchemaExtender(object):
    adapts(IAnalysisService)
    implements(IOrderableSchemaExtender)

    fields = [
        ExtReferenceField(
            'Supplier',
            schemata='Method',
            allowed_types=['Supplier'],
            relationship='AnalysisServiceSupplier',
            widget=BikaReferenceWidget(
                label=_("Subcontracted to"),
                size=20,
                # catalog_name='bika_setup_catalog',
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
        ExtReferenceField(
            'AnalysisService',
            schemata='Method',
            multiValued=1,
            allowed_types=['AnalysisService'],
            relationship='AnalysisServiceAnalysisService',
            widget=BikaReferenceWidget(
                label=_("Associated analysisservices"),
                size=20,
                showOn=True,
                search_fields=('Title'),
                colModel=[
                    {'columnName': 'Title',
                     'width': '25', 'label': _('Title'),
                     'align': 'left'},
                    {'columnName': 'Keyword',
                     'width': '25', 'label': _('Keyword'),
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
        default = schematas['Analysis']
        default.append('Supplier')
        return schematas

    def getFields(self):
        return self.fields


class AnalysisServiceSchemaModifier(object):
    adapts(IAnalysisService)
    implements(ISchemaModifier)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        """
        """
        schema.moveField("AnalysisService", after="Methods")
        schema.moveField("Supplier", before="ManualEntryOfResults")
        return schema

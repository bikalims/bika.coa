from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims import bikaMessageFactory as _
from Products.Archetypes.atapi import DisplayList, PicklistWidget
from Products.Archetypes.interfaces.vocabulary import IVocabulary
from bika.lims.fields import ExtReferenceField
from bika.lims.interfaces import IAnalysisService
from zope.component import adapts
from zope.interface import implements
from bika.lims.browser.widgets import ReferenceWidget as BikaReferenceWidget
from plone import api
from Products.CMFCore.utils import getToolByName


class Vocabulary_AnalysisService(object):
    implements(IVocabulary)

    def getDisplayList(self, context):
        portal = api.portal.get()
        bsc = getToolByName(portal, 'bika_setup_catalog')
        analysisservices = bsc(portal_type='AnalysisService', sort_on='sortable_title')
        items = [['', ''], ]
        current_analysisservice = context.Title()
        for analysisservice in analysisservices:
            if current_analysisservice == analysisservice.Title:
                continue
            items.append([analysisservice.UID, analysisservice.Title])

        return DisplayList(items)


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
            allowed_types=['AnalysisService'],
            relationship='AnalysisServiceAnalysisService',
            widget=PicklistWidget(
                size=10,
                label=_("Associated Analyses"),
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
        schema['AnalysisService'].vocabulary = Vocabulary_AnalysisService()
        schema.moveField("AnalysisService", after="Methods")
        schema.moveField("Supplier", before="ManualEntryOfResults")
        return schema

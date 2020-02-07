from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from bika.lims.fields import ExtensionField
from bika.lims.content.arreport import ARReport
from plone.app.blob.field import BlobField
from zope.component import adapts
from zope.interface import implements


class ExtBlobField(ExtensionField, BlobField):

    "Field extender"


class CSVField(ExtBlobField):
    """
    """


class ARReportSchemaExtender(object):
    adapts(ARReport)
    implements(IOrderableSchemaExtender)

    fields = [
        CSVField('CSV')
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        return schematas

    def getFields(self):
        return self.fields

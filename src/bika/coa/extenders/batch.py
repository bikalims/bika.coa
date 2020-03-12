from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from Products.Archetypes.atapi import TextField, TextAreaWidget
from bika.lims import bikaMessageFactory as _
from bika.lims.interfaces import IBatch
from bika.lims.fields import ExtTextField
from zope.component import adapts
from zope.interface import implements


class BatchSchemaExtender(object):
    adapts(IBatch)
    implements(IOrderableSchemaExtender)

    fields = [
        ExtTextField(
            'COARemarks',
            default_content_type='text/plain',
            allowed_content_types=('text/plain', ),
            default_output_type="text/plain",
            widget=TextAreaWidget(
                label=_('COA Remarks')
            ),
        ),
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        default = schematas['default']
        default.append('COARemarks')
        return schematas

    def getFields(self):
        return self.fields

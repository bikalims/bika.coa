from Products.Archetypes.Widget import RichWidget
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from zope.component import adapts
from zope.interface import implements

from bika.coa import _
from bika.coa import is_installed
from bika.coa.interfaces import IBikaCOALayer
from bika.lims.interfaces import IBatch
from .fields import ExtTextField

coa_remarks_field = ExtTextField(
        'COARemarks',
        default_content_type='text/html',
        default_output_type='text/x-html-safe',
        widget=RichWidget(
            label=_('COA Remarks'),
            allow_file_upload=False,
            default_mime_type='text/x-rst',
            output_mime_type='text/x-html',
        ),
)


class BatchSchemaExtender(object):
    adapts(IBatch)
    implements(IOrderableSchemaExtender)
    layer = IBikaCOALayer

    fields = [
        coa_remarks_field,
    ]

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        default = schematas['default']
        default.append('COARemarks')
        return schematas

    def getFields(self):
        return self.fields


class BatchSchemaModifier(object):
    adapts(IBatch)
    implements(ISchemaModifier)
    layer = IBikaCOALayer

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        """
        """
        if is_installed():
            schema["Remarks"].widget.visible = {"edit": "invisible",
                                                "view": "invisible"}

        return schema

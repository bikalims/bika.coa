from AccessControl import ClassSecurityInfo
from Products.CMFCore import permissions
from Products.CMFPlone.utils import safe_hasattr
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile.field import NamedBlobFile as NamedBlobFileField
from plone.namedfile.file import NamedBlobFile
from plone.supermodel import model
from zope.interface import Interface
from zope.interface import implementer
from zope.component import adapter
from zope.interface import provider


from bika.lims import api
from bika.coa import _


class IExtendedResultsReportMarker(Interface):
    pass


@provider(IFormFieldProvider)
class IExtendedResultsReport(model.Schema):
    """
    Extended Page content type schema with an extra field
    """
    model.fieldset(
        "default",
        label=_(u"Results Report"),
        fields=[
            "csv",
        ]
    )

    csv = NamedBlobFileField(
        title=_(u"CSV"),
        description=_(u"CSV file of the report"),
        required=False,
        default=None,
    )


@implementer(IExtendedResultsReport)
@adapter(IExtendedResultsReportMarker)
class ExtendedResultsReport(object):
    security = ClassSecurityInfo()

    def __init__(self, context):
        self.context = context

    @property
    def csv(self):
        if safe_hasattr(self.context, 'csv'):
            return self.context.csv
        return None

    @security.protected(permissions.View)
    def getRawCSV(self):
        accessor = self.accessor("csv", raw=True)
        return accessor(self)

    @security.protected(permissions.View)
    def getCSV(self):
        accessor = self.accessor("csv")
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setCSV(self, value):
        """Set PDF content

        Accepts:
        - NamedBlobFile instance (used as-is)
        - Raw binary data (auto-converts to NamedBlobFile with default name)
        - Dict with 'data', 'filename', 'contentType' keys
        """
        mutator = self.mutator("csv")

        if value is None:
            mutator(self, None)
            return

        # If already a NamedBlobFile, use as-is
        if isinstance(value, NamedBlobFile):
            mutator(self, value)
            return

        # If it's a dict, extract components
        if isinstance(value, dict):
            data = value.get("data")
            filename = value.get("filename", u"report.csv")
            content_type = value.get("contentType", "text/csv")
        # If it's raw bytes/string, use defaults
        elif isinstance(value, (bytes, str)):
            data = value
            filename = u"report.csv"
            content_type = "text/csv"
        else:
            raise ValueError(
                "CSV value must be NamedBlobFile, bytes, or dict")

        # Create NamedBlobFile instance
        csv_blob = NamedBlobFile(
            data=data,
            filename=api.safe_unicode(filename),
            contentType=content_type
        )

        mutator(self, csv_blob)

    # BBB: AT schema field property
    CSV = property(getCSV, setCSV)

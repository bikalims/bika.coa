from bika.lims.interfaces import IBikaLIMS
from senaite.impress.interfaces import ILayer as ISenaiteIMPRESS
from senaite.lims.interfaces import ISenaiteLIMS


class IBikaCOALayer(IBikaLIMS, ISenaiteLIMS, ISenaiteIMPRESS):
    """Marker interface that defines a Zope 3 browser layer.
    """

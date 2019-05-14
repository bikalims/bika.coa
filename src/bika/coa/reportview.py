from bika.coa import logger
from senaite.impress.analysisrequest.reportview import MultiReportView as ReportView


class MultiReportView(ReportView):
    """View for Bika COA Multi Reports
    """

    def __init__(self, collection, request):
        import pdb; pdb.set_trace()
        logger.info("MultiReportView::__init__:collection={}"
                    .format(collection))
        super(MultiReportView, self).__init__(collection, request)
        self.collection = collection
        self.request = request

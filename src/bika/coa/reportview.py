from bika.coa import logger
from senaite.impress.analysisrequest.reportview import MultiReportView as ReportView


class MultiReportView(ReportView):
    """View for Bika COA Multi Reports
    """

    def __init__(self, collection, request):
        logger.info("MultiReportView::__init__:collection={}"
                    .format(collection))
        super(MultiReportView, self).__init__(collection, request)
        self.collection = collection
        self.request = request

    def get_common_row_data(self, collection, poc, category):
        model = collection[0]
        analyses = self.get_analyses_by(collection, poc=poc, category=category)
        common_data = []
        for analysis in analyses:
            datum = [analysis.Title(), '-', model.get_formatted_unit(analysis)]
            if analysis.Method:
                datum[1] = analysis.Method.Title()
            common_data.append(datum)
        unique_data = self.uniquify_items(common_data)
        return unique_data

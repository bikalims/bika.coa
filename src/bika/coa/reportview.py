from bika.coa import logger
from bika.lims.workflow import getTransitionUsers
from bika.lims import api
from plone import api as ploneapi
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

    def get_extra_data(self, collection=None, poc=None, category=None):
        analyses = self.get_analyses(collection)
        analyses = self.sort_items_by('DateSampled', analyses)
        sampled_from = analyses[0].DateSampled
        to = analyses[-1].DateSampled
        analysis_title = analyses[-1].Title()
        datum = {"methods": [], 'from': sampled_from, 'to': to,
                 "analysis_title": analysis_title}
        for analysis in analyses:
            if analysis.Method:
                method = '{} {}'.format(analysis.Method.Title(), analysis.Method.Description())
                datum['methods'].append(method)
        datum['methods'] = self.uniquify_items(datum['methods'])
        return datum

    def get_verifier(self, collection):
        analyses = self.get_analyses_by(collection)
        # TODO: Get transitioned user
        actor = getTransitionUsers(analyses[0], 'verify')
        user_name = actor[0] if actor else ''
        user = api.get_user(user_name)
        roles = ploneapi.user.get_roles(username=user_name)
        return {"fullname": user.fullname, 'role': roles[0]}

    def get_analyst(self, collection):
        analyses = self.get_analyses_by(collection)
        actor = getTransitionUsers(analyses[0], 'submit')
        user = actor[0] if actor else ''
        user = api.get_user(user)
        return user.fullname

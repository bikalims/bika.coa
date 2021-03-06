from bika.coa import logger
from bika.lims import api
from bika.lims.workflow import getTransitionUsers
from plone import api as ploneapi
from bika.lims.utils.analysis import format_uncertainty
from senaite.impress.analysisrequest.reportview import MultiReportView as MRV
from senaite.impress.analysisrequest.reportview import SingleReportView as SRV


class SingleReportView(SRV):
    """View for Bika COA Single Reports
    """

    def get_coa_number(self, model):
        obj = model.instance
        query = {'portal_type': 'ARReport',
                 'path': {
                     'query': api.get_path(obj),
                     'depth': 1}
                 }
        brains = api.search(query, 'portal_catalog')
        obj_id = api.get_id(obj)
        coa_num = '{}-COA-{}'.format(obj_id, len(brains) + 1)
        return coa_num

    def get_sampler_fullname(self, model):
        obj = model.instance
        return obj.getSamplerFullName()

    def get_formatted_date(self, analysis):
        result = analysis.ResultCaptureDate
        return result.strftime('%Y-%m-%d')

    def get_formatted_uncertainty(self, analysis):
        setup = api.get_setup()
        sciformat = int(setup.getScientificNotationReport())
        decimalmark = setup.getDecimalMark()
        uncertainty = format_uncertainty(
            analysis.instance,
            analysis.getResult(),
            decimalmark=decimalmark,
            sciformat=sciformat)
        return "&plusmn; {}".format(uncertainty)


class MultiReportView(MRV):
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
        analyses = self.get_analyses_by(collection)
        analyses = self.sort_items_by('DateSampled', analyses)
        sampled_from = analyses[0].DateSampled
        to = analyses[-1].DateSampled

        model = analyses[0].getParentNode()
        query = {'portal_type': 'ARReport',
                 'path': {
                     'query': api.get_path(model),
                     'depth': 1}
                 }
        brains = api.search(query, 'portal_catalog')
        coa_num = '{}-COA-{}'.format(model.id, len(brains) + 1)

        analysis_title = ''
        for an in analyses:
            if an.Method:
                analysis_title = an.Title()
                break
        accredited_symbol = "{}//++resource++bika.coa.images/star.png".format(
            self.portal_url)
        subcontracted_method = "{}//++resource++bika.coa.images/outsourced.png".format(
            self.portal_url)
        outofrange_symbol = "{}//++resource++bika.coa.images/outofrange.png".format(
            self.portal_url)
        datum = {'methods': [], 'from': sampled_from, 'to': to,
                 'analysis_title': analysis_title, 'coa_num': coa_num,
                 'accredited_symbol': accredited_symbol,
                 'subcontracted_method': subcontracted_method,
                 'outofrange_symbol': outofrange_symbol}

        for analysis in analyses:
            methods = analysis.getAnalysisService().getAvailableMethods()
            for method in methods:
                if analysis.Method.Title() == method.Title():
                    continue
                title = method.Title()
                description = method.Description()
                accredited = method.Accredited
                # TODO:
                # supplier = analysis.Method.getSupplier()
                try:
                    supplier = True if method['Supplier'] else False
                except AttributeError:
                    supplier = False
                rec = {'title': title, 'description': description,
                       'accredited': accredited, 'supplier': supplier,
                       }

                if rec in datum['methods']:
                    continue
                datum['methods'].append(rec)
        return datum

    def get_verifier(self, collection):
        model = collection[0]
        analyses = self.get_analyses_by([model])
        actor = getTransitionUsers(analyses[0], 'verify')
        user_name = actor[0] if actor else ''
        user = api.get_user(user_name)
        roles = ploneapi.user.get_roles(username=user_name)
        date_verified = self.to_localized_time(model.getDateVerified())
        return {"fullname": user.fullname, 'role': roles[0], 'date_verified': date_verified}

    def get_analyst(self, collection):
        model = collection[0]
        analyses = self.get_analyses_by([model])
        actor = getTransitionUsers(analyses[0], 'submit')
        user = actor[0] if actor else ''
        user = api.get_user(user)
        return user.fullname

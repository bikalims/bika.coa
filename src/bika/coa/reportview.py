from bika.coa import logger
from bika.lims import api
from bika.lims.workflow import getTransitionUsers
from bika.lims.utils.analysis import format_uncertainty
from plone import api as ploneapi
from Products.CMFPlone.utils import safe_unicode
from senaite.impress.analysisrequest.reportview import MultiReportView as MRV
from senaite.impress.analysisrequest.reportview import MULTI_TEMPLATE
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

    def get_report_images(self):
        outofrange_symbol_url = "{}/++resource++bika.coa.images/outofrange.png".format(
            self.portal_url)
        datum = {'outofrange_symbol_url': outofrange_symbol_url}
        return datum


class MultiReportView(MRV):
    """View for Bika COA Multi Reports
    """

    def __init__(self, collection, request):
        logger.info("MultiReportView::__init__:collection={}"
                    .format(collection))
        super(MultiReportView, self).__init__(collection, request)
        self.collection = collection
        self.request = request

    def get_max_pdf_samples(self):
        """ get max num of allowed samples in a PDF
        """
        num = api.get_registry_record("bika.coa.max_pdf_samples")
        logger.info('get_max_pdf_samples: is {}'.format(num))
        return num

    def is_pdfs_disabled(self):
        """ Check registry to see if PDF are disabled
        """
        disabled = api.get_registry_record("bika.coa.disable_pdfs")
        logger.info('pdfs disabled: is {}'.format(disabled))
        return disabled

    def render(self, template, **kw):
        """Wrap the template and render
        """
        if self.is_pdfs_disabled():
            template = safe_unicode("<div><p>Note: PDFs are disabled.</p></div>")
            return MULTI_TEMPLATE.safe_substitute(self.context, template=template)

        max_pdf_samples = self.get_max_pdf_samples()
        if max_pdf_samples > 0 and len(self.collection) > max_pdf_samples:
            template = safe_unicode("<div><p>ERROR: Only {} samples allowed in a PDF, {} submitted.</p></div>".format(max_pdf_samples, len(self.collection)))
            return MULTI_TEMPLATE.safe_substitute(self.context, template=template)
        return super(MultiReportView, self).render(template, **kw)

    def get_pages(self, options):
        if options.get('orientation', '') == 'portrait':
            num_per_page = 5
        elif options.get('orientation', '') == 'landscape':
            num_per_page = 8
        else:
            logger.error('get_pages: orientation unknown')
            num_per_page = 5
        logger.info('get_pages: col len = {}; num_per_page = {}'.format(len(self.collection), num_per_page))
        pages = []
        new_page = []
        for idx, col in enumerate(self.collection):
            if idx % num_per_page == 0:
                if len(new_page):
                    pages.append(new_page)
                    logger.info('New page len = {}'.format(len(new_page)))
                new_page = [col]
                continue
            new_page.append(col)

        if len(new_page) > 0:
            pages.append(new_page)
            logger.info('Last page len = {}'.format(len(new_page)))
        return pages

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

    def get_report_images(self):
        outofrange_symbol_url = "{}/++resource++bika.coa.images/outofrange.png".format(
            self.portal_url)
        datum = {'outofrange_symbol_url': outofrange_symbol_url}
        return datum

    def to_localized_date(self, date):
        return self.to_localized_time(date)[:10]

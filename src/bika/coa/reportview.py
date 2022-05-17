from bika.coa import logger
from bika.lims import api
from bika.lims.workflow import getTransitionUsers
from DateTime import DateTime
from plone import api as ploneapi
from plone.registry.interfaces import IRegistry
from bika.lims.utils.analysis import format_uncertainty
from bika.lims.catalog import SETUP_CATALOG
from senaite.app.supermodel import SuperModel
from senaite.impress.analysisrequest.reportview import MultiReportView as MRV
from senaite.impress.analysisrequest.reportview import SingleReportView as SRV
from zope.component import getUtility

LOGO = "/++plone++bika.coa.static/images/bikalimslogo.png"


class SingleReportView(SRV):
    """View for Bika COA Single Reports
    """

    def get_coa_number(self, model):
        instance = model.instance
        client = instance.aq_parent
        today = DateTime()
        query = {
            "portal_type": "ARReport",
            "path": {"query": api.get_path(client)},
            "created": {"query": today.Date(), "range": "min"},
            "sort_on": "created",
            "sort_order": "descending",
        }
        brains = api.search(query, "portal_catalog")
        num = 1
        if len(brains):
            coa = brains[0]
            num = coa.Title.split("-")[-1]
            num = int(num)
            num += 1
        coa_num = "{}-COA{}-{:02d}".format(
            client.getClientID(), today.strftime("%y%m%d"), num
        )
        return coa_num

    def get_sampler_fullname(self, model):
        obj = model.instance
        return obj.getSamplerFullName()

    def get_formatted_date(self, analysis):
        result = analysis.ResultCaptureDate
        return result.strftime("%Y-%m-%d")

    def get_formatted_uncertainty(self, analysis):
        setup = api.get_setup()
        sciformat = int(setup.getScientificNotationReport())
        decimalmark = setup.getDecimalMark()
        uncertainty = format_uncertainty(
            analysis.instance,
            analysis.getResult(),
            decimalmark=decimalmark,
            sciformat=sciformat,
        )
        return "&plusmn; {}".format(uncertainty)

    def get_report_images(self):
        outofrange_symbol_url = "{}/++resource++bika.coa.images/outofrange.png".format(
            self.portal_url
        )
        datum = {"outofrange_symbol_url": outofrange_symbol_url}
        return datum

    def get_toolbar_logo(self):
        registry = getUtility(IRegistry)
        portal_url = self.portal_url
        try:
            logo = registry["senaite.toolbar_logo"]
        except (AttributeError, KeyError):
            logo = LOGO
        if not logo:
            logo = LOGO
        return portal_url + logo

    def get_coa_styles(self):
        registry = getUtility(IRegistry)
        styles = {}
        try:
            ac_style = registry["senaite.coa_logo_accredition_styles"]
        except (AttributeError, KeyError):
            styles["ac_styles"] = "max-height:68px;"
        css = map(lambda ac_style: "{}:{};".format(*ac_style), ac_style.items())
        css.append("max-width:200px;")
        styles["ac_styles"] = " ".join(css)

        try:
            logo_style = registry["senaite.coa_logo_styles"]
        except (AttributeError, KeyError):
            styles["logo_styles"] = "height:15px;"
        css = map(lambda logo_style: "{}:{};".format(*logo_style), logo_style.items())
        styles["logo_styles"] = " ".join(css)
        return styles


class MultiReportView(MRV):
    """View for Bika COA Multi Reports
    """

    def __init__(self, collection, request):
        logger.info("MultiReportView::__init__:collection={}".format(collection))
        super(MultiReportView, self).__init__(collection, request)
        self.collection = collection
        self.request = request

    def get_pages(self, options):
        if options.get("orientation", "") == "portrait":
            num_per_page = 5
        elif options.get("orientation", "") == "landscape":
            num_per_page = 8
        else:
            logger.error("get_pages: orientation unknown")
            num_per_page = 5
        logger.info(
            "get_pages: col len = {}; num_per_page = {}".format(
                len(self.collection), num_per_page
            )
        )
        pages = []
        new_page = []
        for idx, col in enumerate(self.collection):
            if idx % num_per_page == 0:
                if len(new_page):
                    pages.append(new_page)
                    logger.info("New page len = {}".format(len(new_page)))
                new_page = [col]
                continue
            new_page.append(col)

        if len(new_page) > 0:
            pages.append(new_page)
            logger.info("Last page len = {}".format(len(new_page)))
        return pages

    def get_common_row_data(self, collection, poc, category):
        model = collection[0]
        analyses = self.get_analyses_by(collection, poc=poc, category=category)
        common_data = []
        for analysis in analyses:
            datum = [analysis.Title(), "-", model.get_formatted_unit(analysis), "-"]
            if analysis.Method:
                datum[1] = analysis.Method.Title()
            instruments = analysis.getAnalysisService().getInstruments()
            # TODO: Use getInstruments
            instr_list = []
            if instruments:
                for i, instrument in enumerate(instruments):
                    title = instrument.Title()
                    if title in instr_list:
                        continue
                    instr_list.append(title)
                datum[3] = " ".join(instr_list)
            common_data.append(datum)
        unique_data = self.uniquify_items(common_data)
        return unique_data

    def get_analyses_parameters(self, collection=None, poc=None, category=None):
        analyses = self.get_analyses_by(collection, poc=poc, category=category)
        analyses_parameters = []
        for c, analysis in enumerate(analyses):
            methods = analysis.getAnalysisService().getAvailableMethods()
            for m, method in enumerate(methods):
                if analysis.Method.Title() == method.Title():
                    continue
                title = method.Title()
                description = method.Description()
                accredited = method.Accredited
                # TODO:
                # supplier = analysis.Method.getSupplier()
                try:
                    supplier = True if method["Supplier"] else False
                except AttributeError:
                    supplier = False
                rec = {
                    "title": title,
                    "description": description,
                    "accredited": accredited,
                    "supplier": supplier,
                }

                if rec in analyses_parameters:
                    continue
                analyses_parameters.append(rec)
        return analyses_parameters

    def get_analyses_instruments(self, collection=None, poc=None, category=None):
        analyses = self.get_analyses_by(collection, poc=poc, category=category)
        analyses_parameters = []
        for c, analysis in enumerate(analyses):
            instruments = analysis.getAnalysisService().getInstruments()
            for i, instrument in enumerate(instruments):
                title = instrument.Title()
                description = instrument.Description()
                rec = {"description": '{}. {}'.format(title, description)}
                if rec in analyses_parameters:
                    continue
                analyses_parameters.append(rec)
        return analyses_parameters

    def get_analyses_preparations(self, collection=None, poc=None, category=None):
        query = {"portal_type": "AnalysisCategory", "title": "Preparation"}
        super_cat = False
        analyses = []
        for brain in api.search(query, SETUP_CATALOG):
            super_cat = SuperModel(brain.UID)

        if not super_cat:
            return []
        analyses = self.get_analyses_by(collection, category=super_cat)

        analyses_parameters = []
        for c, analysis in enumerate(analyses):
            an_service = analysis.getAnalysisService()
            title = an_service.Title()
            description = an_service.Description()
            sort_key = an_service.getSortKey()
            an_parameter = "{}. {}".format(title, description)
            rec = {"title": title, "sortKey": sort_key, "an_parameter": an_parameter}
            if rec in analyses_parameters:
                continue
            analyses_parameters.append(rec)
        items = sorted(
            analyses_parameters, key=lambda item: item["sortKey"], reverse=True
        )
        return items

    def get_batch(self, collection=None):
        if all([getattr(i.Batch , "id", '') for i in collection]):
            return collection[0].Batch.id
        return None

    def is_analysis_method_subcontracted(self, analysis):
        if analysis.Method:
            if analysis.Method.Supplier:
                return True
        return False

    def is_analysis_method_accreditted(self, analysis):
        if analysis.Method:
            if analysis.Method.Accredited:
                return True
        return False


    def get_extra_data(self, collection=None, poc=None, category=None):
        analyses = self.get_analyses_by(collection)
        analyses = self.sort_items_by("DateSampled", analyses)
        sampled_from = analyses[0].DateSampled
        to = analyses[-1].DateSampled

        analysis_title = ""
        for an in analyses:
            if an.Method:
                analysis_title = an.Title()
                break
        accredited_symbol = "{}//++resource++bika.coa.images/star.png".format(
            self.portal_url
        )
        subcontracted_method = "{}//++resource++bika.coa.images/outsourced.png".format(
            self.portal_url
        )
        outofrange_symbol = "{}//++resource++bika.coa.images/outofrange.png".format(
            self.portal_url
        )
        datum = {
            "methods": [],
            "from": sampled_from,
            "to": to,
            "analysis_title": analysis_title,
            "accredited_symbol": accredited_symbol,
            "subcontracted_method": subcontracted_method,
            "outofrange_symbol": outofrange_symbol,
        }

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
                    supplier = True if method["Supplier"] else False
                except AttributeError:
                    supplier = False
                rec = {
                    "title": title,
                    "description": description,
                    "accredited": accredited,
                    "supplier": supplier,
                }

                if rec in datum["methods"]:
                    continue
                datum["methods"].append(rec)
        return datum

    def get_verifier(self, collection):
        model = collection[0]
        analyses = self.get_analyses_by([model])
        actor = getTransitionUsers(analyses[0], "verify")
        user_name = actor[0] if actor else ""
        user = api.get_user(user_name)
        roles = ploneapi.user.get_roles(username=user_name)
        date_verified = self.to_localized_time(model.getDateVerified())
        return {
            "fullname": user.fullname,
            "role": roles[0],
            "date_verified": date_verified,
        }

    def get_analyst(self, collection):
        model = collection[0]
        analyses = self.get_analyses_by([model])
        actor = getTransitionUsers(analyses[0], "submit")
        user = actor[0] if actor else ""
        user = api.get_user(user)
        return user.fullname

    def get_report_images(self):
        outofrange_symbol_url = "{}/++resource++bika.coa.images/outofrange.png".format(
            self.portal_url
        )
        subcontracted_symbol_url = "{}/++resource++bika.coa.images/subcontracted.png".format(
            self.portal_url
        )
        datum = {"outofrange_symbol_url": outofrange_symbol_url,
                "subcontracted_symbol_url": subcontracted_symbol_url}
        return datum

    def get_toolbar_logo(self):
        registry = getUtility(IRegistry)
        portal_url = self.portal_url
        try:
            logo = registry["senaite.toolbar_logo"]
        except (AttributeError, KeyError):
            logo = LOGO
        if not logo:
            logo = LOGO
        return portal_url + logo

    def to_localized_date(self, date):
        return self.to_localized_time(date)[:10]

    def get_coa_number(self):
        instance = self.collection[0].instance
        client = instance.aq_parent
        today = DateTime()
        query = {
            "portal_type": "ARReport",
            "path": {"query": api.get_path(client)},
            "created": {"query": today.Date(), "range": "min"},
            "sort_on": "created",
            "sort_order": "descending",
        }
        brains = api.search(query, "portal_catalog")
        num = 1
        if len(brains):
            coa = brains[0]
            num = coa.Title.split("-")[-1]
            num = int(num)
            num += 1
        coa_num = "{}-COA{}-{:02d}".format(
            client.getClientID(), today.strftime("%y%m%d"), num
        )
        return coa_num

    def get_coa_styles(self):
        registry = getUtility(IRegistry)
        styles = {}
        try:
            ac_style = registry["senaite.coa_logo_accredition_styles"]
        except (AttributeError, KeyError):
            styles["ac_styles"] = "max-height:68px;"
        css = map(lambda ac_style: "{}:{};".format(*ac_style), ac_style.items())
        css.append("max-width:200px;")
        styles["ac_styles"] = " ".join(css)

        try:
            logo_style = registry["senaite.coa_logo_styles"]
        except (AttributeError, KeyError):
            styles["logo_styles"] = "height:15px;"
        css = map(lambda logo_style: "{}:{};".format(*logo_style), logo_style.items())
        styles["logo_styles"] = " ".join(css)
        return styles

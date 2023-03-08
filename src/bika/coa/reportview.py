from DateTime import DateTime
from plone import api as ploneapi
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component._api import getAdapters

from bika.coa import logger
from bika.lims import api
from bika.lims.api import _marker
from bika.lims.interfaces import IAnalysis, IReferenceAnalysis, \
    IResultOutOfRange
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.content.analysisspec import ResultsRangeDict
from bika.lims.interfaces import IDuplicateAnalysis
from bika.lims.utils.analysis import format_uncertainty
from bika.lims.workflow import getTransitionUsers
from senaite.app.supermodel import SuperModel
from senaite.impress.analysisrequest.reportview import MultiReportView as MRV
from senaite.impress.analysisrequest.reportview import SingleReportView as SRV

LOGO = "/++plone++bika.coa.static/images/bikalimslogo.png"


def is_out_of_range(brain_or_object, result=_marker, spec_type="Specification"):
    """
    Taken from bika.lims.api.analysis is_out_of_range and inculded the 
    spec_type.
    :param spec_type: Specification type to be returned, it could the
    Specficification or PublicationSpecification type result_range
    """
    analysis = api.get_object(brain_or_object)
    if not IAnalysis.providedBy(analysis) and \
            not IReferenceAnalysis.providedBy(analysis):
        api.fail("{} is not supported. Needs to be IAnalysis or "
                 "IReferenceAnalysis".format(repr(analysis)))

    if result is _marker:
        result = api.safe_getattr(analysis, "getResult", None)

    if result in [None, '']:
        # Empty result
        return False, False

    if IDuplicateAnalysis.providedBy(analysis):
        # Result range for duplicate analyses is calculated from the original
        # result, applying a variation % in shoulders. If the analysis has
        # result options enabled or string results enabled, system returns an
        # empty result range for the duplicate: result must match %100 with the
        # original result
        original = analysis.getAnalysis()
        original_result = original.getResult()

        # Does original analysis have a valid result?
        if original_result in [None, '']:
            return False, False

        # Does original result type matches with duplicate result type?
        if api.is_floatable(result) != api.is_floatable(original_result):
            return True, True

        # Does analysis has result options enabled or non-floatable?
        if analysis.getResultOptions() or not api.is_floatable(original_result):
            # Let's always assume the result is 'out from shoulders', cause we
            # consider the shoulders are precisely the duplicate variation %
            out_of_range = original_result != result
            return out_of_range, out_of_range

    elif not api.is_floatable(result):
        # A non-duplicate with non-floatable result. There is no chance to know
        # if the result is out-of-range
        return False, False

    # Convert result to a float
    result = api.to_float(result)

    # Note that routine analyses, duplicates and reference analyses all them
    # implement the function getResultRange:
    # - For routine analyses, the function returns the valid range based on the
    #   specs assigned during the creation process.
    # - For duplicates, the valid range is the result of the analysis the
    #   the duplicate was generated from +/- the duplicate variation.
    # - For reference analyses, getResultRange returns the valid range as
    #   indicated in the Reference Sample from which the analysis was created.
    result_range = None
    if spec_type == "Specification":
        result_range = api.safe_getattr(analysis, "getResultsRange", None)
    if spec_type == "PublicationSpecification":
        sample = analysis.getRequest()
        pub_spec = sample.getPublicationSpecification()
        result_ranges = api.safe_getattr(pub_spec, "getResultsRange", None)
        keyword = analysis.getKeyword()
        for index, i in enumerate(result_ranges):
            if i["keyword"] == keyword:
                result_range = i
                break

    if not result_range:
        # No result range defined or the passed in object does not suit
        return False, False

    # Maybe there is a custom adapter
    adapters = getAdapters((analysis,), IResultOutOfRange)
    for name, adapter in adapters:
        ret = adapter(result=result, specification=result_range)
        if not ret or not ret.get('out_of_range', False):
            continue
        if not ret.get('acceptable', True):
            # Out of range + out of shoulders
            return True, True
        # Out of range, but in shoulders
        return True, False

    result_range = ResultsRangeDict(result_range)

    # The assignment of result as default fallback for min and max guarantees
    # the result will be in range also if no min/max values are defined
    specs_min = api.to_float(result_range.min, result)
    specs_max = api.to_float(result_range.max, result)

    in_range = False
    min_operator = result_range.min_operator
    if min_operator == "geq":
        in_range = result >= specs_min
    else:
        in_range = result > specs_min

    max_operator = result_range.max_operator
    if in_range:
        if max_operator == "leq":
            in_range = result <= specs_max
        else:
            in_range = result < specs_max

    # If in range, no need to check shoulders
    if in_range:
        return False, False

    # Out of range, check shoulders. If no explicit warn_min or warn_max have
    # been defined, no shoulders must be considered for this analysis. Thus, use
    # specs' min and max as default fallback values
    warn_min = api.to_float(result_range.warn_min, specs_min)
    warn_max = api.to_float(result_range.warn_max, specs_max)
    in_shoulder = warn_min <= result <= warn_max
    return True, not in_shoulder


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
        coa_num = "COA{}-{:02d}".format(today.strftime("%y%m%d"), num)
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

    def get_common_row_data_by_poc(self, collection, poc):
        model = collection[0]
        all_analyses = self.get_analyses_by_poc(collection)
        analyses = all_analyses.get(poc)
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
            if analysis.getCategory().Title() == "Preparation":
                continue
            methods = analysis.getAnalysisService().getAvailableMethods()
            for m, method in enumerate(methods):
                title = method.Title()
                description = method.Description()
                method_id = method.getId()
                rec = {
                    "title": title,
                    "description": description,
                    "method_id": method_id,
                }

                if rec in analyses_parameters:
                    continue
                analyses_parameters.append(rec)
        items = sorted(
            analyses_parameters, key=lambda item: item["method_id"])
        return items

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
        items = sorted(
            analyses_parameters, key=lambda item: item["description"])
        return items

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

    def is_batch_unique(self, collection=None):
        return len(set([getattr(i.Batch , "id", '') for i in collection])) == 1

    def get_order_number(self, collection=None):
        if all([getattr(i, "ClientOrderNumber", '') for i in collection]):
            return collection[0].ClientOrderNumber
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

    def is_out_of_range(self, analysis, spec_type="Specification"):
        return is_out_of_range(analysis.instance, spec_type=spec_type)[0]

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
        actor = getTransitionUsers(analyses[0].getObject(), "verify")
        if not actor:
            return {"verifier": 'admin', "email": ""}
            
        user_name = actor[0] if actor else ""
        user_obj = api.get_user(user_name)
        roles = ploneapi.user.get_roles(username=user_name)
        date_verified = self.to_localized_time(model.getDateVerified())
        contact = api.get_user_contact(user_obj)
        verifier = {"fullname": "", "role": "", "email": "", "verifier": ""}
        if not contact:
            return verifier

        verifier["fullname"] =  contact.getFullname()
        verifier["role"] =  roles[0]
        verifier["date_verified"] =  date_verified
        verifier["email"] =  contact.getEmailAddress()

        if contact.getSalutation():
            verifier["verifier"] = "{}. {}".format(contact.getSalutation(), contact.getFullname())
        else:
            verifier["verifier"] = "{}".format(contact.getFullname())

        return verifier

    def get_publisher(self):
        publisher = {
                "today":"{}".format(DateTime().strftime("%Y-%m-%d")),
                "email": "",}
        current_user = api.get_current_user()
        user = api.get_user_contact(current_user)
        if not user:
            publisher["publisher"] = '{}'.format(current_user.id)
            return publisher

        publisher["email"] = '{}'.format(user.getEmailAddress())
        if user.getSalutation():
            publisher["publisher"] = '{}. {}'.format(user.getSalutation(), user.getFullname())
        else:
            publisher["publisher"] = '{}'.format(user.fullname)

        return publisher

    def has_results_intepretation(self, collection):
        has_additional_info = False
        for model in collection:
            if model.get_resultsinterpretation():
                has_additional_info = True
                break
        return has_additional_info

    def has_remarks(self, collection):
        has_additional_info = False
        for model in collection:
            if model.getRemarks():
                has_additional_info = True
                break
        return has_additional_info

    def has_additional_info(self, collection):
        has_additional_info = False
        if self.has_results_intepretation(collection) or self.has_remarks(collection):
            has_additional_info = True
        return has_additional_info


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
        accredited_symbol_url = "{}/++resource++bika.coa.images/star.png".format(
            self.portal_url
        )
        datum = {"outofrange_symbol_url": outofrange_symbol_url,
                "subcontracted_symbol_url": subcontracted_symbol_url,
                "accredited_symbol_url": accredited_symbol_url,}
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
        coa_num = "COA{}-{:02d}".format(today.strftime("%y%m%d"), num)
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

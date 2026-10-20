# -*- coding: utf-8 -*-
"""Preview COA numbers using the ResultsReport ID Server configuration."""
from bika.lims import api
from senaite.core.idserver import idserver
from senaite.core.interfaces import INumberGenerator
from zope.component import getUtility


def get_coa_number(context, offset=0):
    """Format the next report number without advancing the sequence."""
    kw = {"portal_type": "ResultsReport"}
    config = idserver.get_config(context, **kw)
    variables = idserver.get_variables(context, **kw)
    form = config["form"]
    sequence_type = config.get("sequence_type", "generated")
    number = 0
    if sequence_type == "generated":
        prefix = idserver.slice(form, separator="-",
                                end=config.get("split_length", 1))
        prefix = api.normalize_filename(prefix.format(**variables))
        key = idserver.make_storage_key("ResultsReport", prefix)
        number = getUtility(INumberGenerator).get(key, 0) + 1
    elif sequence_type == "counter":
        number = idserver.get_counted_number(context, config, variables, **kw)
    number += offset
    variables["seq"] = number
    variables["alpha"] = idserver.Alphanumber(number)
    return api.safe_unicode(form).format(**variables)

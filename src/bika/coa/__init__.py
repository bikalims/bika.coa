# -*- coding: utf-8 -*-
#
# This file is part of BIKA.COA
#
# Copyright 2019 by it's authors.

import logging

logger = logging.getLogger("bika.coa")


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    logger.info("*** Initializing BIKA.COA ***")

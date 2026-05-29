# -*- coding: utf-8 -*-

from bika.coa import PRODUCT_NAME
from bika.coa import PROFILE_ID
from bika.coa import logger

from senaite.core.upgrade import upgradestep
from senaite.core.upgrade.utils import UpgradeUtils

version = "2.7.0"


@upgradestep(PRODUCT_NAME, version)
def upgrade(tool):
    portal = tool.aq_inner.aq_parent
    setup = portal.portal_setup
    ut = UpgradeUtils(portal)
    ver_from = ut.getInstalledVersion(PRODUCT_NAME)

    if ut.isOlderVersion(PRODUCT_NAME, version):
        logger.info(
            "Skipping upgrade of {0}: {1} > {2}".format(
                PRODUCT_NAME, ver_from, version)
        )
        return True

    logger.info("Upgrading {0}: {1} -> {2}".format(
        PRODUCT_NAME, ver_from, version))

    # -------- ADD YOUR STUFF BELOW --------

    setup.runImportStepFromProfile(PROFILE_ID, "typeinfo")

    logger.info("{0} upgraded to version {1}".format(PRODUCT_NAME, version))
    return True

from bika.coa import PRODUCT_NAME
from bika.coa import PROFILE_ID
from bika.coa import logger
from Products.CMFCore.utils import getToolByName


def pre_install(portal_setup):
    """Runs before the first import step of the *default* profile
    This handler is registered as a *pre_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} pre-install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)
    portal = context.getSite()  # noqa

    # # Only install senaite.lims once!
    # qi = portal.portal_quickinstaller
    # if not qi.isProductInstalled("senaite.lims"):
    #     portal_setup.runAllImportStepsFromProfile("profile-senaite.lims:default")

    logger.info("{} pre-install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_install(portal_setup):
    """Runs after the last import step of the *default* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} post-install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)
    portal = context.getSite()  # noqa

    # update senaite_setup_catalog
    pc = getToolByName(portal, 'portal_catalog')
    if 'getSupplier' not in pc.indexes():
        logger.info("{} post-install handler: add getSupplier to portal catalog".format(PRODUCT_NAME.upper()))
        pc.addIndex('getSupplier', 'FieldIndex')
        pc.addColumn('getSupplier')
        pc.manage_reindexIndex('getSupplier')

    logger.info("{} post-install handler [DONE]".format(PRODUCT_NAME.upper()))

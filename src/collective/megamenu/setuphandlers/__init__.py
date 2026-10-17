from Acquisition import aq_parent
from plone.base.interfaces.installable import INonInstallable
from zope.interface import implementer


BEHAVIOR = "collective.megamenu.menu"


def add_behavior_to_lrf(tool):
    """Profile post_handler: enable the menu behavior on LRF when PAM is present.

    The declarative ``profiles/default/types/LRF.xml`` already covers PAM
    installed before this addon. This handler is the profile-level fallback
    and keeps the assignment idempotent. It deliberately does not react to
    PAM being installed later; reapply the addon profile in that case.
    """
    portal = aq_parent(tool)
    portal_types = getattr(portal, "portal_types", None)
    if portal_types is None:
        return

    fti = portal_types.get("LRF")
    if fti is None or not hasattr(fti, "behaviors"):
        return

    behaviors = list(fti.behaviors)
    if BEHAVIOR not in behaviors:
        behaviors.append(BEHAVIOR)
        fti._updateProperty("behaviors", tuple(behaviors))


@implementer(INonInstallable)
class HiddenProfiles:
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "collective.megamenu:uninstall",
        ]

    def getNonInstallableProducts(self):
        """Hide the upgrades package from site-creation and quickinstaller."""
        return [
            "collective.megamenu.upgrades",
        ]

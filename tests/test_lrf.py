from collective.megamenu.setuphandlers import add_behavior_to_lrf
from plone.app.testing import applyProfile


PAM_PROFILE = "plone.app.multilingual:default"
OWN_PROFILE = "collective.megamenu:default"
BEHAVIOR = "collective.megamenu.menu"


def test_no_lrf_without_pam(portal):
    assert portal.portal_types.get("LRF") is None


def test_pam_installed_before_addon_adds_behavior(portal, installer):
    applyProfile(portal, PAM_PROFILE)
    installer.uninstall_product("collective.megamenu")
    installer.install_product("collective.megamenu")

    fti = portal.portal_types.get("LRF")

    assert BEHAVIOR in fti.behaviors


def test_pam_installed_after_addon_requires_reapply(portal):
    applyProfile(portal, PAM_PROFILE)

    fti = portal.portal_types.get("LRF")

    assert fti is not None
    assert BEHAVIOR not in fti.behaviors

    applyProfile(portal, OWN_PROFILE)

    assert BEHAVIOR in fti.behaviors


def test_reapplying_profile_is_idempotent(portal):
    applyProfile(portal, PAM_PROFILE)
    applyProfile(portal, OWN_PROFILE)
    applyProfile(portal, OWN_PROFILE)

    fti = portal.portal_types.get("LRF")

    assert fti.behaviors.count(BEHAVIOR) == 1


def test_post_handler_adds_behavior_idempotently(portal):
    applyProfile(portal, PAM_PROFILE)
    fti = portal.portal_types.get("LRF")
    fti._updateProperty(
        "behaviors",
        tuple(behavior for behavior in fti.behaviors if behavior != BEHAVIOR),
    )

    add_behavior_to_lrf(portal.portal_setup)
    add_behavior_to_lrf(portal.portal_setup)

    assert fti.behaviors.count(BEHAVIOR) == 1


def test_uninstall_removes_only_our_behavior(portal, installer):
    applyProfile(portal, PAM_PROFILE)
    installer.uninstall_product("collective.megamenu")

    fti = portal.portal_types.get("LRF")

    assert BEHAVIOR not in fti.behaviors
    assert "plone.dublincore" in fti.behaviors

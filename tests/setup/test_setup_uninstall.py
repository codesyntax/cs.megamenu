from cs.megamenu import PACKAGE_NAME

import pytest


class TestSetupUninstall:
    @pytest.fixture(autouse=True)
    def uninstalled(self, installer):
        installer.uninstall_product(PACKAGE_NAME)

    def test_addon_uninstalled(self, installer):
        """Test if cs.megamenu is uninstalled."""
        assert installer.is_product_installed(PACKAGE_NAME) is False

    def test_browserlayer_not_registered(self, browser_layers):
        """Test that IBrowserLayer is not registered."""
        from cs.megamenu.interfaces import IBrowserLayer

        assert IBrowserLayer not in browser_layers

    def test_behavior_removed(self, portal):
        """Test that the editable menu behavior is removed."""
        from cs.megamenu.behaviors.menu import IEditableMenu
        from plone.behavior.interfaces import IBehaviorAssignable

        assert not IBehaviorAssignable(portal).supports(IEditableMenu)

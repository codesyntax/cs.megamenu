from collective.megamenu.browser.widgets import MegaMenuWidget
from collective.megamenu.interfaces import IEditableMenu
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.base.interfaces import IBundleRegistry
from plone.registry.interfaces import IRegistry
from z3c.form.interfaces import IFieldWidget
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import setSite
from zope.globalrequest import setRequest
from zope.interface import alsoProvides

import json


VALID_MENU = {
    "version": 1,
    "items": [
        {
            "id": "11111111-1111-4111-8111-111111111111",
            "type": "folder",
            "title": "Products",
            "css_class": "nav-products",
            "icon": "box",
            "children": [],
        }
    ],
}


def test_widget_is_registered(portal, http_request):
    alsoProvides(http_request, IPloneFormLayer)
    field = IEditableMenu["menu"]

    widget = getMultiAdapter((field, http_request), IFieldWidget)

    assert isinstance(widget, MegaMenuWidget)


def test_widget_renders_tree_container_and_textarea(portal, http_request):
    setSite(portal)
    setRequest(http_request)
    alsoProvides(http_request, IPloneFormLayer)
    widget = MegaMenuWidget(http_request)
    widget.context = portal
    widget.field = IEditableMenu["menu"]
    widget.name = "form.widgets.menu"
    widget.value = json.dumps(VALID_MENU)

    html = widget.render()

    assert 'name="form.widgets.menu"' in html
    assert 'class="megamenu-json"' in html
    assert 'class="megamenu-options"' in html
    assert 'class="megamenu-translations"' in html
    assert 'class="pat-megamenu"' in html
    assert "Products" in html
    assert "Menu tree" in html


def test_widget_contentbrowser_options(portal, http_request):
    setSite(portal)
    setRequest(http_request)
    widget = MegaMenuWidget(http_request)
    widget.context = portal
    widget.field = IEditableMenu["menu"]

    options = json.loads(widget.contentbrowser_options_json())

    assert options["maximumSelectionSize"] == 1
    assert options["mode"] == "browse"
    assert options["basePath"] == "/".join(portal.getPhysicalPath())
    assert "getVocabulary" in options["vocabularyUrl"]


def test_widget_translations(portal, http_request):
    setSite(portal)
    setRequest(http_request)
    widget = MegaMenuWidget(http_request)
    widget.context = portal
    widget.field = IEditableMenu["menu"]

    translations = json.loads(widget.translations_json())

    assert translations["menuTree"] == "Menu tree"
    assert translations["addFolder"] == "Add folder"
    assert translations["titleRequired"] == "Title is required."


def test_bundle_registered(portal):
    registry = getUtility(IRegistry)
    bundle = registry.forInterface(
        IBundleRegistry,
        prefix="plone.bundles/collective.megamenu",
    )

    assert bundle.enabled is True
    assert bundle.jscompilation.endswith("collective.megamenu-remote.min.js")
    assert bundle.depends == "plone"

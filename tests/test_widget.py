from cs.megamenu.behaviors.menu import IEditableMenu
from cs.megamenu.widgets.menu import MegaMenuFieldWidget
from cs.megamenu.widgets.menu import MegaMenuWidget
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.autoform.interfaces import WIDGETS_KEY
from plone.autoform.widgets import ParameterizedWidget
from plone.base.interfaces import IBundleRegistry
from plone.registry.interfaces import IRegistry
from plone.schema import JSONField
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


def test_menu_field_uses_megamenu_widget():
    widget = IEditableMenu.getTaggedValue(WIDGETS_KEY)["menu"]

    assert isinstance(widget, ParameterizedWidget)
    assert widget.widget_factory is MegaMenuFieldWidget


def test_other_json_fields_use_the_default_widget(portal, http_request):
    alsoProvides(http_request, IPloneFormLayer)
    field = JSONField(title="Other")
    field.__name__ = "other"

    widget = getMultiAdapter((field, http_request), IFieldWidget)

    assert widget is not None
    assert not isinstance(widget, MegaMenuWidget)


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
        prefix="plone.bundles/cs.megamenu",
    )

    assert bundle.enabled is True
    assert bundle.jscompilation.endswith("cs.megamenu-remote.min.js")
    assert bundle.depends == "plone"

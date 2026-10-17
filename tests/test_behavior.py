from collective.megamenu.behaviors.menu import IEditableMenu
from plone import api
from plone.app.testing import login
from plone.behavior.interfaces import IBehaviorAssignable
from plone.supermodel.interfaces import FIELDSETS_KEY
from zope.schema.interfaces import WrongContainedType

import copy
import pytest


VALID_MENU = {
    "version": 1,
    "items": [
        {
            "id": "11111111-1111-4111-8111-111111111111",
            "type": "folder",
            "title": "Products",
            "css_class": "nav-products",
            "icon": "box",
            "children": [
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "type": "link",
                    "title": "Product A",
                    "css_class": "",
                    "icon": "file-earmark",
                    "internal_uid": "product-a-uid",
                    "external_url": "",
                    "open_in_new_tab": False,
                }
            ],
        }
    ],
}


def test_folder_has_editable_menu(portal):
    login(portal.aq_parent, "admin")
    folder = api.content.create(
        container=portal,
        type="Folder",
        id="menu-folder",
        title="Menu folder",
    )

    assert IBehaviorAssignable(folder).supports(IEditableMenu)
    assert folder.menu is None


def test_plone_site_has_editable_menu(portal):
    assert IBehaviorAssignable(portal).supports(IEditableMenu)
    assert portal.menu is None


def test_menu_field_has_its_own_fieldset():
    fieldsets = IEditableMenu.queryTaggedValue(FIELDSETS_KEY)

    assert [fieldset.__name__ for fieldset in fieldsets] == ["megamenu"]
    assert fieldsets[0].fields == ["menu"]
    assert str(fieldsets[0].label) == "Mega menu"


def test_valid_menu_passes_schema_validation():
    field = IEditableMenu["menu"]

    field.validate(copy.deepcopy(VALID_MENU))


def test_link_with_both_targets_is_rejected():
    field = IEditableMenu["menu"]
    invalid = copy.deepcopy(VALID_MENU)
    invalid["items"][0]["children"][0]["external_url"] = "https://example.com"

    with pytest.raises(WrongContainedType):
        field.validate(invalid)


def test_folder_with_target_is_rejected():
    field = IEditableMenu["menu"]
    invalid = copy.deepcopy(VALID_MENU)
    invalid["items"][0]["internal_uid"] = "product-a-uid"

    with pytest.raises(WrongContainedType):
        field.validate(invalid)


def test_unknown_top_level_property_is_rejected():
    field = IEditableMenu["menu"]
    invalid = copy.deepcopy(VALID_MENU)
    invalid["unexpected"] = True

    with pytest.raises(WrongContainedType):
        field.validate(invalid)

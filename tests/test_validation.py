from cs.megamenu.behaviors.menu import IEditableMenu
from cs.megamenu.validators.menu import MenuValidator
from cs.megamenu.validators.validation import validate_menu
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from z3c.form.interfaces import IValidator
from zope.component import getMultiAdapter
from zope.component.hooks import setSite
from zope.interface import Invalid

import pytest


UUID_1 = "11111111-1111-4111-8111-111111111111"
UUID_2 = "22222222-2222-4222-8222-222222222222"
UUID_3 = "33333333-3333-4333-8333-333333333333"


def external_link(item_id=UUID_1, title="External", url="https://example.com"):
    return {
        "id": item_id,
        "type": "link",
        "title": title,
        "css_class": "",
        "icon": "link-45deg",
        "internal_uid": "",
        "external_url": url,
        "open_in_new_tab": False,
    }


def internal_link(item_id=UUID_2, title="Internal", uid="target-uid"):
    return {
        "id": item_id,
        "type": "link",
        "title": title,
        "css_class": "",
        "icon": "link-45deg",
        "internal_uid": uid,
        "external_url": "",
        "open_in_new_tab": False,
    }


def folder(item_id=UUID_3, title="Folder", children=None):
    return {
        "id": item_id,
        "type": "folder",
        "title": title,
        "css_class": "",
        "icon": "folder",
        "children": children or [],
    }


def menu(*items):
    return {"version": 1, "items": list(items)}


def test_none_is_valid():
    assert validate_menu(None) == []


def test_empty_menu_is_valid():
    assert validate_menu(menu()) == []


def test_valid_external_menu():
    assert validate_menu(menu(external_link())) == []


def test_empty_folder_is_valid():
    assert validate_menu(menu(folder(children=[]))) == []


def test_version_must_be_one():
    assert validate_menu({"version": 2, "items": []}) == [
        "Unsupported menu version. Expected version 1."
    ]


def test_unknown_top_level_field():
    value = menu(external_link())
    value["unexpected"] = True

    assert validate_menu(value) == ["Unknown field: `unexpected`."]


def test_duplicate_ids():
    value = menu(
        external_link(item_id=UUID_1, title="One"),
        external_link(item_id=UUID_1, title="Two"),
    )

    assert validate_menu(value) == [
        "Two: Menu item IDs must be unique and valid UUIDs."
    ]


def test_invalid_uuid():
    value = menu(external_link(item_id="not-a-uuid"))

    assert validate_menu(value) == [
        "External: Menu item IDs must be unique and valid UUIDs."
    ]


def test_title_required():
    value = menu(external_link(title="   "))

    assert validate_menu(value) == ["Untitled item #1: Title is required."]


def test_title_too_long():
    title = "x" * 201
    value = menu(external_link(title=title))

    assert validate_menu(value) == [f"{title}: Use at most 200 characters."]


def test_invalid_css_class():
    value = menu(external_link())
    value["items"][0]["css_class"] = "nav  double"

    assert validate_menu(value) == [
        "External: Use only letters, numbers, hyphens, and underscores, "
        "separated by single spaces."
    ]


def test_invalid_icon_name():
    value = menu(external_link())
    value["items"][0]["icon"] = "bi bi-house"

    assert validate_menu(value) == [
        "External: Use a valid Plone icon name, for example alarm or "
        "contenttype/document."
    ]


@pytest.mark.parametrize(
    "icon",
    ["alarm", "contenttype/document", "plone-copy", "logo.svg", ""],
)
def test_valid_icon_names(icon):
    value = menu(external_link())
    value["items"][0]["icon"] = icon

    assert validate_menu(value) == []


def test_folder_cannot_have_target():
    value = menu(folder())
    value["items"][0]["internal_uid"] = "target-uid"

    assert validate_menu(value) == ["Folder: A folder cannot have a target."]


def test_link_cannot_have_children():
    value = menu(external_link())
    value["items"][0]["children"] = []

    assert validate_menu(value) == ["External: A link cannot have children."]


def test_link_must_have_exactly_one_target():
    value = menu(internal_link(uid="target-uid"))
    value["items"][0]["external_url"] = "https://example.com"

    assert validate_menu(value) == [
        "Internal: Choose exactly one target: internal or external."
    ]


def test_link_without_target():
    value = menu(internal_link(uid=""))

    assert validate_menu(value) == [
        "Internal: Choose exactly one target: internal or external."
    ]


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "ftp://example.com",
        "https://",
        "https://.",
        "//example.com",
        "mailto:",
        "tel:",
        "https://example.com/has space",
    ],
)
def test_bad_external_urls(url):
    assert validate_menu(menu(external_link(url=url))) == [
        "External: Use an http(s), mailto, or tel URL."
    ]


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://localhost",
        "http://example.com/path?x=1",
        "mailto:test@example.com",
        "tel:+123456789",
    ],
)
def test_good_external_urls(url):
    assert validate_menu(menu(external_link(url=url))) == []


def test_missing_internal_target(portal):
    setSite(portal)

    assert validate_menu(menu(internal_link(uid="missing-uid"))) == [
        "Internal: The selected internal target no longer exists or is not visible "
        "to you."
    ]


def test_public_internal_target(portal):
    logout()
    setSite(portal)
    portal_uid = api.content.get_uuid(portal)

    assert validate_menu(menu(internal_link(uid=portal_uid))) == []


def test_private_internal_target(portal):
    login(portal.aq_parent, "admin")
    secret = api.content.create(
        container=portal,
        type="Document",
        id="secret",
        title="Secret",
    )
    secret_uid = api.content.get_uuid(secret)
    logout()
    setSite(portal)

    assert validate_menu(menu(internal_link(uid=secret_uid))) == [
        "Internal: The selected internal target no longer exists or is not visible "
        "to you."
    ]


def test_validator_is_registered(portal, http_request):
    field = IEditableMenu["menu"]
    adapter = getMultiAdapter(
        (portal, http_request, None, field, None),
        IValidator,
    )

    assert isinstance(adapter, MenuValidator)
    adapter.validate(menu(external_link()))

    with pytest.raises(Invalid):
        adapter.validate(menu(internal_link(uid="missing-uid")))

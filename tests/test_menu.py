from collective.megamenu.menu import get_menu
from plone import api
from plone.app.testing import login
from plone.app.testing import logout


MENU_A = {
    "version": 1,
    "items": [
        {
            "id": "a-folder",
            "type": "folder",
            "title": "A folder",
            "css_class": "",
            "icon": "",
            "children": [],
        }
    ],
}

MENU_B = {
    "version": 1,
    "items": [
        {
            "id": "b-folder",
            "type": "folder",
            "title": "B folder",
            "css_class": "",
            "icon": "",
            "children": [],
        }
    ],
}

EMPTY_MENU = {"version": 1, "items": []}


def create_folder(container, folder_id, title):
    return api.content.create(
        container=container,
        type="Folder",
        id=folder_id,
        title=title,
    )


def test_no_menu_anywhere(portal):
    logout()
    portal.menu = None

    assert get_menu(portal) == (None, None)


def test_site_root_menu(portal):
    logout()
    portal.menu = MENU_A

    assert get_menu(portal) == (MENU_A, portal)


def test_child_inherits_folder_menu(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    child = create_folder(section, "child", "Child")

    assert get_menu(child) == (MENU_A, section)


def test_unset_folder_inherits_through_multiple_levels(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    child = create_folder(section, "child", "Child")
    grandchild = create_folder(child, "grandchild", "Grandchild")

    assert get_menu(grandchild) == (MENU_A, section)


def test_nearest_ancestor_wins(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    child = create_folder(section, "child", "Child")
    child.menu = MENU_B

    assert get_menu(child) == (MENU_B, child)


def test_explicit_empty_menu_opts_out(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    child = create_folder(section, "child", "Child")
    child.menu = EMPTY_MENU

    menu, owner = get_menu(child)

    assert menu is None
    assert owner == child


def test_document_inherits_from_folder(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    document = api.content.create(
        container=section,
        type="Document",
        id="document",
        title="Document",
    )

    assert get_menu(document) == (MENU_A, section)


def test_malformed_value_is_treated_as_unset(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    child = create_folder(section, "child", "Child")
    child.menu = "not-a-dict"

    assert get_menu(child) == (MENU_A, section)


def test_empty_menu_without_version_is_treated_as_unset(portal):
    login(portal.aq_parent, "admin")
    section = create_folder(portal, "section", "Section")
    section.menu = MENU_A
    child = create_folder(section, "child", "Child")
    child.menu = {"items": []}

    assert get_menu(child) == (MENU_A, section)

"""Tests for linkintegrity integration."""

from collective.megamenu.linkintegrity.menu import iter_menu_link_uids
from collective.megamenu.linkintegrity.menu import MenuRetriever
from pathlib import Path
from plone import api
from plone.app.linkintegrity.browser.info import DeleteConfirmationInfo
from plone.app.linkintegrity.interfaces import IRetriever
from plone.app.linkintegrity.retriever import DXGeneral
from plone.app.linkintegrity.utils import getIncomingLinks
from plone.app.linkintegrity.utils import getOutgoingLinks
from plone.app.testing import login
from plone.base.interfaces import IEditingSchema
from plone.registry.interfaces import IRegistry
from zope.component import getAdapter
from zope.component import getUtility
from zope.lifecycleevent import modified

import pytest
import uuid


def link_item(target, title="Target"):
    return {
        "id": str(uuid.uuid4()),
        "type": "link",
        "title": title,
        "css_class": "",
        "icon": "",
        "internal_uid": api.content.get_uuid(target),
        "external_url": "",
        "open_in_new_tab": False,
    }


def external_item(url="https://example.com"):
    return {
        "id": str(uuid.uuid4()),
        "type": "link",
        "title": "External",
        "css_class": "",
        "icon": "",
        "internal_uid": "",
        "external_url": url,
        "open_in_new_tab": False,
    }


def menu(*items):
    return {"version": 1, "items": list(items)}


def incoming_sources(target):
    return {
        relation.from_object.absolute_url()
        for relation in getIncomingLinks(target)
        if relation.from_object is not None
    }


@pytest.fixture
def linkintegrity_checks(portal):
    registry = getUtility(IRegistry)
    editing = registry.forInterface(IEditingSchema, prefix="plone")
    previous = editing.enable_link_integrity_checks
    editing.enable_link_integrity_checks = True
    try:
        yield editing
    finally:
        editing.enable_link_integrity_checks = previous


def test_iter_menu_link_uids_nested_and_ignores_external():
    first = str(uuid.uuid4())
    second = str(uuid.uuid4())
    value = {
        "version": 1,
        "items": [
            {
                "id": str(uuid.uuid4()),
                "type": "folder",
                "title": "Folder",
                "children": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "link",
                        "title": "First",
                        "internal_uid": first,
                        "external_url": "",
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "type": "link",
                        "title": "External",
                        "internal_uid": "",
                        "external_url": "https://example.com",
                    },
                ],
            },
            {
                "id": str(uuid.uuid4()),
                "type": "link",
                "title": "Second",
                "internal_uid": second,
                "external_url": "",
            },
        ],
    }

    assert set(iter_menu_link_uids(value)) == {first, second}


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        {"items": None},
        {"items": [None, "not-a-dict", {}]},
    ],
)
def test_iter_menu_link_uids_handles_malformed_values(value):
    assert list(iter_menu_link_uids(value)) == []


def test_iter_menu_link_uids_ignores_blank_uids():
    value = {
        "version": 1,
        "items": [
            {
                "id": str(uuid.uuid4()),
                "type": "link",
                "title": "Blank",
                "internal_uid": "   ",
                "external_url": "",
            }
        ],
    }

    assert list(iter_menu_link_uids(value)) == []


def test_adapter_selection(portal):
    login(portal.aq_parent, "admin")
    folder = api.content.create(
        container=portal, type="Folder", id="adapter-folder", title="Folder"
    )
    document = api.content.create(
        container=portal, type="Document", id="adapter-document", title="Document"
    )

    assert isinstance(getAdapter(portal, IRetriever), MenuRetriever)
    assert isinstance(getAdapter(folder, IRetriever), MenuRetriever)
    assert isinstance(getAdapter(document, IRetriever), DXGeneral)
    assert not isinstance(getAdapter(document, IRetriever), MenuRetriever)


def test_menu_reference_creates_incoming_relation(portal, linkintegrity_checks):
    login(portal.aq_parent, "admin")
    target = api.content.create(
        container=portal, type="Document", id="target", title="Target"
    )
    portal.menu = menu(link_item(target))

    modified(portal)

    assert portal.absolute_url() in incoming_sources(target)


def test_menu_edit_updates_relations(portal, linkintegrity_checks):
    login(portal.aq_parent, "admin")
    target_a = api.content.create(
        container=portal, type="Document", id="target-a", title="Target A"
    )
    target_b = api.content.create(
        container=portal, type="Document", id="target-b", title="Target B"
    )

    portal.menu = menu(link_item(target_a))
    modified(portal)

    assert portal.absolute_url() in incoming_sources(target_a)

    portal.menu = menu(link_item(target_b))
    modified(portal)

    assert portal.absolute_url() not in incoming_sources(target_a)
    assert portal.absolute_url() in incoming_sources(target_b)


def test_inherited_menu_is_attributed_to_ancestor(portal, linkintegrity_checks):
    login(portal.aq_parent, "admin")
    target = api.content.create(
        container=portal, type="Document", id="target-inherited", title="Target"
    )
    child = api.content.create(
        container=portal, type="Folder", id="child", title="Child"
    )
    portal.menu = menu(link_item(target))
    modified(portal)

    modified(child)

    sources = incoming_sources(target)
    assert portal.absolute_url() in sources
    assert child.absolute_url() not in sources
    assert child.menu is None


def test_explicit_empty_menu_does_not_inherit(portal, linkintegrity_checks):
    login(portal.aq_parent, "admin")
    target = api.content.create(
        container=portal, type="Document", id="target-optout", title="Target"
    )
    child = api.content.create(
        container=portal, type="Folder", id="child-optout", title="Child"
    )
    portal.menu = menu(link_item(target))
    child.menu = menu()
    modified(portal)
    modified(child)

    assert child.absolute_url() not in incoming_sources(target)


def test_menu_retriever_keeps_richtext_links(portal, monkeypatch):
    login(portal.aq_parent, "admin")
    target = api.content.create(
        container=portal, type="Document", id="target-richtext", title="Target"
    )
    portal.menu = menu(link_item(target))
    monkeypatch.setattr(
        DXGeneral, "retrieveLinks", lambda self: {"resolveuid/rich-text-uid"}
    )

    links = MenuRetriever(portal).retrieveLinks()

    assert f"resolveuid/{api.content.get_uuid(target)}" in links
    assert "resolveuid/rich-text-uid" in links


def test_delete_confirmation_reports_menu_source(
    portal, http_request, linkintegrity_checks
):
    login(portal.aq_parent, "admin")
    target = api.content.create(
        container=portal, type="Document", id="target-delete", title="Target"
    )
    portal.menu = menu(link_item(target))
    modified(portal)

    view = DeleteConfirmationInfo(target, http_request)
    breaches = view.get_breaches([target])
    sources = [source for breach in breaches for source in breach.get("sources", [])]

    assert any(source["uid"] == api.content.get_uuid(portal) for source in sources)


def test_disabled_linkintegrity_creates_no_relation(portal):
    registry = getUtility(IRegistry)
    editing = registry.forInterface(IEditingSchema, prefix="plone")
    previous = editing.enable_link_integrity_checks
    editing.enable_link_integrity_checks = False
    try:
        login(portal.aq_parent, "admin")
        target = api.content.create(
            container=portal, type="Document", id="target-disabled", title="Target"
        )
        portal.menu = menu(link_item(target))

        modified(portal)

        assert portal.absolute_url() not in incoming_sources(target)
    finally:
        editing.enable_link_integrity_checks = previous


def test_external_urls_are_not_tracked(portal, linkintegrity_checks):
    login(portal.aq_parent, "admin")
    folder = api.content.create(
        container=portal, type="Folder", id="external-folder", title="External"
    )
    folder.menu = menu(external_item())

    modified(folder)

    assert list(getOutgoingLinks(folder)) == []


def test_site_root_target_is_not_tracked(portal, linkintegrity_checks):
    login(portal.aq_parent, "admin")
    portal.menu = menu(link_item(portal))

    modified(portal)

    assert list(getOutgoingLinks(portal)) == []


def test_linkintegrity_zcml_is_conditional():
    zcml = Path("src/collective/megamenu/configure.zcml").read_text()

    assert 'zcml:condition="installed plone.app.linkintegrity"' in zcml
    assert 'package=".linkintegrity"' in zcml


def test_lrf_uses_menu_retriever(portal):
    from plone.app.testing import applyProfile

    login(portal.aq_parent, "admin")
    applyProfile(portal, "plone.app.multilingual:default")
    applyProfile(portal, "collective.megamenu:default")
    lrf = api.content.create(container=portal, type="Folder", id="lrf", title="LRF")
    lrf.portal_type = "LRF"

    assert isinstance(getAdapter(lrf, IRetriever), MenuRetriever)

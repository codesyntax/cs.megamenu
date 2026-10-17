from collective.megamenu.viewlets.menu import MegaMenuViewlet
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from zope.component.hooks import setSite

import transaction


def link(item_id, title, *, internal_uid="", external_url="", open_in_new_tab=False):
    return {
        "id": item_id,
        "type": "link",
        "title": title,
        "css_class": "",
        "icon": "file-earmark",
        "internal_uid": internal_uid,
        "external_url": external_url,
        "open_in_new_tab": open_in_new_tab,
    }


def folder(item_id, title, *, children, css_class="", icon="box"):
    return {
        "id": item_id,
        "type": "folder",
        "title": title,
        "css_class": css_class,
        "icon": icon,
        "children": children,
    }


def menu(items):
    return {"version": 1, "items": items}


def render(portal, request):
    return MegaMenuViewlet(portal, request, None, None).index()


def test_viewlet_renders_menu_markup(portal, http_request):
    portal_uid = api.content.get_uuid(portal)
    logout()
    portal.menu = menu([
        folder(
            "folder-1",
            "Products",
            css_class="nav-products",
            children=[
                link("link-1", "Product A", internal_uid=portal_uid),
                link(
                    "link-2",
                    "Blog",
                    external_url="https://example.com/blog",
                    open_in_new_tab=True,
                ),
            ],
        )
    ])

    html = render(portal, http_request)

    assert 'id="portal-globalnav"' in html
    assert 'class="navbar-toggler"' in html
    assert "nav-products" in html
    assert "megamenu-icon" in html
    assert "<svg" in html
    assert '<a href="#" class="nav-link">' in html
    assert f'href="{portal.absolute_url()}"' in html
    assert 'target="_blank" rel="noopener noreferrer"' in html
    assert 'class="opener"' in html
    assert 'aria-label="Products"' in html


def test_viewlet_renders_nothing_without_menu(portal, http_request):
    logout()
    portal.menu = None

    assert render(portal, http_request).strip() == ""


def test_viewlet_renders_nothing_for_explicit_empty_menu(portal, http_request):
    logout()
    portal.menu = menu([])

    assert render(portal, http_request).strip() == ""


def test_viewlet_filters_private_internal_links_and_empty_folders(portal, http_request):
    login(portal.aq_parent, "admin")
    secret = api.content.create(
        container=portal,
        type="Document",
        id="secret",
        title="Secret",
    )
    secret_uid = api.content.get_uuid(secret)
    portal_uid = api.content.get_uuid(portal)
    portal.menu = menu([
        link("link-secret", "Secret", internal_uid=secret_uid),
        link("link-home", "Home", internal_uid=portal_uid),
        link("link-blog", "Blog", external_url="https://example.com/blog"),
        folder(
            "folder-secret",
            "Secret folder",
            children=[
                link("link-secret-child", "Secret child", internal_uid=secret_uid)
            ],
        ),
    ])
    logout()
    setSite(portal)

    html = render(portal, http_request)

    assert "Secret" not in html
    assert "Secret folder" not in html
    assert "Home" in html
    assert "Blog" in html


def test_viewlet_uses_nearest_ancestor_menu(portal, http_request):
    login(portal.aq_parent, "admin")
    section = api.content.create(
        container=portal,
        type="Folder",
        id="section",
        title="Section",
    )
    child = api.content.create(
        container=section,
        type="Folder",
        id="child",
        title="Child",
    )
    portal.menu = menu([
        link("link-root", "Root link", external_url="https://root.example")
    ])
    section.menu = menu([
        link("link-section", "Section link", external_url="https://section.example")
    ])
    logout()
    setSite(portal)

    html = MegaMenuViewlet(child, http_request, None, None).index()

    assert "Section link" in html
    assert "Root link" not in html


def test_viewlet_is_registered_on_the_site(functional_portal, request_factory):
    login(functional_portal.aq_parent, "admin")
    functional_portal.menu = menu([
        link(
            "link-custom", "Custom external", external_url="https://example.com/custom"
        )
    ])
    transaction.commit()

    session = request_factory(role="Anonymous", api=False)
    response = session.get("/")

    assert response.status_code == 200
    assert "Custom external" in response.text

"""Main navigation viewlet backed by the editable menu."""

from ..behaviors.menu import IEditableMenu
from ..menu import get_menu
from ..utils import resolve_internal_target
from html import escape
from plone.app.layout.viewlets.common import GlobalSectionsViewlet
from zope.component import getMultiAdapter


def resolve_link(item):
    """Return the URL for a link item, or ``None`` when it is not visible."""
    internal_uid = item.get("internal_uid") or ""
    if internal_uid:
        obj = resolve_internal_target(internal_uid)
        if obj is None:
            return None
        return obj.absolute_url()

    external_url = item.get("external_url") or ""
    return external_url or None


def filter_items(items):
    """Return a copy of the menu tree with invisible items removed."""
    visible = []
    for item in items:
        item_type = item.get("type")
        if item_type == "link":
            url = resolve_link(item)
            if url:
                visible.append({**item, "_url": url})
        elif item_type == "folder":
            children = filter_items(item.get("children") or [])
            if children:
                visible.append({**item, "children": children})
    return visible


def render_icon(icons, name):
    """Return the resolved Plone icon markup for ``name``, if any."""
    if not name or icons is None:
        return ""
    try:
        return f"{icons.tag(name, tag_class='megamenu-icon', tag_alt='')} "
    except (NotImplementedError, OSError, ValueError):
        return ""


def render_item(item, icons=None):
    """Render one visible item as a Barceloneta-compatible ``li``."""
    item_type = item.get("type")
    title = escape(item.get("title") or "", quote=True)
    icon_html = render_icon(icons, item.get("icon"))
    css_class = item.get("css_class") or ""
    classes = ["nav-item"]
    if item_type == "folder":
        classes.append("has_subtree")
    if css_class:
        classes.append(css_class)
    class_attr = escape(" ".join(classes), quote=True)

    if item_type == "folder":
        children = item.get("children") or []
        if not children:
            return ""
        opener_id = f"navitem-{item.get('id')}"
        opener_id = escape(opener_id, quote=True)
        opener = (
            f'<input id="{opener_id}" type="checkbox" class="opener">'
            f'<label for="{opener_id}" role="button" aria-label="{title}" '
            'aria-haspopup="true"></label>'
        )
        sub = (
            '<ul class="has_subtree dropdown">'
            + "".join(render_item(child, icons) for child in children)
            + "</ul>"
        )
        return (
            f'<li class="{class_attr}">'
            f'<a href="#" class="nav-link">{icon_html}{title}</a>'
            f"{opener}{sub}</li>"
        )

    url = item.get("_url") or ""
    if not url:
        return ""
    target = ""
    if item.get("open_in_new_tab"):
        target = ' target="_blank" rel="noopener noreferrer"'
    return (
        f'<li class="{class_attr}">'
        f'<a class="nav-link" href="{escape(url, quote=True)}"{target}>'
        f"{icon_html}{title}</a></li>"
    )


class MegaMenuViewlet(GlobalSectionsViewlet):
    """Replace the global sections with the nearest configured menu.

    Subclass this viewlet and set ``menu_field`` and ``menu_behavior`` to
    render an additional menu field with a custom viewlet registration.
    """

    menu_field = "menu"
    menu_behavior = IEditableMenu

    @property
    def visible_items(self):
        if not hasattr(self, "_visible_items"):
            menu, _owner = get_menu(
                self.context,
                field_name=self.menu_field,
                behavior=self.menu_behavior,
            )
            items = menu.get("items", []) if menu else []
            self._visible_items = filter_items(items)
        return self._visible_items

    @property
    def navtree(self):
        """The core template uses this as the "show navigation" condition."""
        return self.visible_items or None

    @property
    def icons(self):
        return getMultiAdapter((self.context, self.request), name="iconresolver")

    def render_globalnav(self):
        return "".join(render_item(item, self.icons) for item in self.visible_items)

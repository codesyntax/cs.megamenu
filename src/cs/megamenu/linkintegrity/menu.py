"""Linkintegrity retriever for menu internal UIDs."""

from ..behaviors.menu import IEditableMenu
from plone.app.linkintegrity.interfaces import IRetriever
from plone.app.linkintegrity.retriever import DXGeneral
from zope.component import adapter
from zope.interface import implementer


def iter_menu_link_uids(menu):
    """Yield internal UIDs from a stored menu value, defensively."""
    if not isinstance(menu, dict):
        return
    items = menu.get("items")
    if not isinstance(items, list):
        return
    stack = list(items)
    while stack:
        item = stack.pop()
        if not isinstance(item, dict):
            continue
        if item.get("type") == "link":
            uid = item.get("internal_uid")
            if isinstance(uid, str) and uid.strip():
                yield uid.strip()
        children = item.get("children")
        if isinstance(children, list):
            stack.extend(children)


@implementer(IRetriever)
@adapter(IEditableMenu)
class MenuRetriever(DXGeneral):
    """DXGeneral plus menu internal UID references.

    Subclass this adapter and set ``field_name`` to track an additional menu
    field defined by a custom behavior.
    """

    field_name = "menu"

    def retrieveLinks(self):
        links = super().retrieveLinks()
        links |= {
            f"resolveuid/{uid}"
            for uid in iter_menu_link_uids(getattr(self.context, self.field_name, None))
        }
        return links

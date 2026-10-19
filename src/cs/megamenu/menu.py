"""Menu resolution for the nearest configured ancestor."""

from .behaviors.menu import IEditableMenu
from AccessControl import Unauthorized
from plone.behavior.interfaces import IBehaviorAssignable


def has_menu_behavior(context, behavior=IEditableMenu):
    """Return whether the given menu behavior is enabled on context."""
    assignable = IBehaviorAssignable(context, None)
    return assignable is not None and assignable.supports(behavior)


def get_menu(context, field_name="menu", behavior=IEditableMenu):
    """Return ``(menu, owner)`` for the nearest configured menu field.

    ``field_name`` is the behavior field to read. ``behavior`` is the behavior
    interface or marker to check. The defaults read the original ``menu`` field
    on ``IEditableMenu``; pass another behavior and field name for additional
    menus.

    A ``None`` menu value means the object does not configure a menu, so the
    search continues up the acquisition chain. An explicitly saved empty menu
    (``{"version": 1, "items": []}``) is an opt-out: the search stops and
    ``(None, owner)`` is returned. Values with an unknown version or shape are
    treated as unset so a bad record cannot break navigation.
    """
    obj = context
    while obj is not None:
        try:
            if has_menu_behavior(obj, behavior):
                menu = getattr(obj, field_name, None)
                if (
                    isinstance(menu, dict)
                    and menu.get("version") == 1
                    and isinstance(menu.get("items"), list)
                ):
                    if menu["items"]:
                        return menu, obj
                    return None, obj
        except Unauthorized:
            pass
        obj = getattr(obj, "aq_parent", None)
    return None, None

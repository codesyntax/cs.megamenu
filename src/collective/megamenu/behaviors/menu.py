"""Behavior that adds the editable menu field."""

from .. import _
from ..schema import MENU_JSON_SCHEMA
from plone.autoform.interfaces import IFormFieldProvider
from plone.schema import JSONField
from plone.supermodel import model
from zope.interface import provider


@provider(IFormFieldProvider)
class IEditableMenu(model.Schema):
    """Behavior that adds a configurable menu tree."""

    model.fieldset(
        "megamenu",
        label=_("Mega menu"),
        fields=["menu"],
    )

    menu = JSONField(
        title=_("Menu"),
        description=_(
            "Custom menu for this folder and its descendants. "
            "Leave unset to inherit the nearest ancestor's menu."
        ),
        required=False,
        schema=MENU_JSON_SCHEMA,
    )

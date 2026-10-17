"""Module where all interfaces, events and exceptions live."""

from . import _
from .schema import MENU_JSON_SCHEMA
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.autoform.interfaces import IFormFieldProvider
from plone.schema import JSONField
from plone.supermodel import model
from zope.interface import provider
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IBrowserLayer(IPloneFormLayer, IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


@provider(IFormFieldProvider)
class IEditableMenu(model.Schema):
    """Behavior that adds a configurable menu tree."""

    menu = JSONField(
        title=_("Menu"),
        description=_(
            "Custom menu for this folder and its descendants. "
            "Leave unset to inherit the nearest ancestor's menu."
        ),
        required=False,
        schema=MENU_JSON_SCHEMA,
    )

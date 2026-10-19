"""Module where all interfaces, events and exceptions live."""

from plone.app.z3cform.interfaces import IPloneFormLayer
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IBrowserLayer(IPloneFormLayer, IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

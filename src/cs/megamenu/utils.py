"""Shared helpers for resolving internal menu targets."""

from AccessControl import Unauthorized
from plone import api
from plone.app.uuid.utils import uuidToCatalogBrain
from zExceptions import NotFound


def resolve_internal_target(uid):
    """Return the viewable object for a UID, or ``None``.

    The catalog lookup is unrestricted so a missing UID is distinguishable
    from an inaccessible one; the returned object is explicitly checked with
    the current user's View permission.
    """
    brain = uuidToCatalogBrain(uid)
    if brain is None:
        return None
    try:
        obj = brain.getObject()
    except (Unauthorized, NotFound, KeyError):
        return None
    if obj is None:
        return None
    if not api.user.has_permission("View", obj=obj):
        return None
    return obj

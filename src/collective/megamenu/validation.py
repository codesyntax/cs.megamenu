"""Semantic validation for editable menu values."""

from . import _
from .utils import resolve_internal_target
from urllib.parse import urlparse

import re


UUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
CSS_RE = re.compile(r"^$|^[A-Za-z_-][A-Za-z0-9_-]*( [A-Za-z_-][A-Za-z0-9_-]*)*$")
HOST_RE = re.compile(
    r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)*$"
)
TOP_KEYS = {"version", "items"}
FOLDER_KEYS = {"id", "type", "title", "css_class", "icon", "children"}
LINK_KEYS = {
    "id",
    "type",
    "title",
    "css_class",
    "icon",
    "internal_uid",
    "external_url",
    "open_in_new_tab",
}
TARGET_KEYS = {"internal_uid", "external_url", "open_in_new_tab"}
ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}
MAX_TITLE = 200
MAX_CSS = 200
MAX_ICON = 200

URL_ERROR = _("Use an http(s), mailto, or tel URL.")
CSS_ERROR = _(
    "Use only letters, numbers, hyphens, and underscores, separated by single spaces."
)
INTERNAL_TARGET_ERROR = _(
    "The selected internal target no longer exists or is not visible to you."
)
TITLE_REQUIRED = _("Title is required.")
TOO_LONG = _("Use at most 200 characters.")
UNIQUE_IDS = _("Menu item IDs must be unique and valid UUIDs.")
FOLDER_TARGET = _("A folder cannot have a target.")
LINK_CHILDREN = _("A link cannot have children.")
ONE_TARGET = _("Choose exactly one target: internal or external.")
ITEM_TYPE = _("A menu item must be a folder or a link.")
VERSION_ERROR = _("Unsupported menu version. Expected version 1.")


def _path_prefix(parts):
    return " → ".join(parts) + ": " if parts else ""


def _error(errors, path, message):
    errors.append(_path_prefix(path) + str(message))


def _check_unknown_keys(item, allowed, path, errors):
    for key in item:
        if key not in allowed:
            message = str(_("Unknown field: `${name}`.")).replace("${name}", key)
            _error(errors, path, message)


def _validate_external_url(url, path, errors):
    if not isinstance(url, str) or not url.strip():
        _error(errors, path, URL_ERROR)
        return
    if any(char.isspace() for char in url):
        _error(errors, path, URL_ERROR)
        return
    try:
        parsed = urlparse(url)
    except ValueError:
        _error(errors, path, URL_ERROR)
        return
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        _error(errors, path, URL_ERROR)
        return
    if scheme in {"http", "https"}:
        hostname = parsed.hostname or ""
        if not HOST_RE.fullmatch(hostname):
            _error(errors, path, URL_ERROR)
        return
    if scheme in {"mailto", "tel"} and not parsed.path:
        _error(errors, path, URL_ERROR)


def _validate_link(item, path, errors):
    _check_unknown_keys(item, LINK_KEYS | {"children"}, path, errors)
    if "children" in item:
        _error(errors, path, LINK_CHILDREN)

    internal_uid = item.get("internal_uid")
    external_url = item.get("external_url")
    has_internal = isinstance(internal_uid, str) and bool(internal_uid.strip())
    has_external = isinstance(external_url, str) and bool(external_url.strip())

    if has_internal == has_external:
        _error(errors, path, ONE_TARGET)
        return

    if has_internal:
        if not _is_valid_internal_uid(internal_uid):
            _error(errors, path, INTERNAL_TARGET_ERROR)
        return

    _validate_external_url(external_url, path, errors)


def _is_valid_internal_uid(uid):
    if any(char.isspace() for char in uid):
        return False
    return resolve_internal_target(uid) is not None


def _validate_id(item, path, seen_ids, errors):
    item_id = item.get("id")
    if (
        not isinstance(item_id, str)
        or not UUID_RE.fullmatch(item_id)
        or item_id in seen_ids
    ):
        _error(errors, path, UNIQUE_IDS)
    else:
        seen_ids.add(item_id)


def _validate_title(item, path, errors):
    title = item.get("title")
    if not isinstance(title, str) or not title.strip():
        _error(errors, path, TITLE_REQUIRED)
    elif len(title) > MAX_TITLE:
        _error(errors, path, TOO_LONG)


def _validate_css_like(value, path, errors, max_length):
    if not isinstance(value, str) or not CSS_RE.fullmatch(value):
        _error(errors, path, CSS_ERROR)
    elif len(value) > max_length:
        _error(errors, path, TOO_LONG)


def _validate_folder(item, path, seen_ids, errors):
    _check_unknown_keys(item, FOLDER_KEYS | TARGET_KEYS, path, errors)
    if any(key in item for key in TARGET_KEYS):
        _error(errors, path, FOLDER_TARGET)
    children = item.get("children")
    if isinstance(children, list):
        _validate_items(children, path, seen_ids, errors)


def _validate_item(item, path, seen_ids, errors):
    item_type = item.get("type")
    if item_type not in {"folder", "link"}:
        _error(errors, path, ITEM_TYPE)
        return

    _validate_id(item, path, seen_ids, errors)
    _validate_title(item, path, errors)
    _validate_css_like(item.get("css_class"), path, errors, MAX_CSS)
    _validate_css_like(item.get("icon"), path, errors, MAX_ICON)

    if item_type == "folder":
        _validate_folder(item, path, seen_ids, errors)
    else:
        _validate_link(item, path, errors)


def _validate_items(items, path, seen_ids, errors):
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        title_text = (
            title
            if isinstance(title, str) and title.strip()
            else str(_("Untitled item #{index}")).format(index=index)
        )
        _validate_item(item, [*path, title_text], seen_ids, errors)


def validate_menu(value):
    """Return a list of path-aware semantic errors for a menu value."""
    errors = []
    if value is None or not isinstance(value, dict):
        return errors

    _check_unknown_keys(value, TOP_KEYS, [], errors)
    if value.get("version") != 1:
        errors.append(str(VERSION_ERROR))

    items = value.get("items")
    if not isinstance(items, list):
        return errors

    _validate_items(items, [], set(), errors)
    return errors

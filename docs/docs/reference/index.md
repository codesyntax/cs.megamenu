---
myst:
  html_meta:
    "description": "cs.megamenu reference"
    "property=og:description": "cs.megamenu reference"
    "property=og:title": "cs.megamenu reference"
    "keywords": "Plone, cs.megamenu, reference, JSON schema"
---

# Reference 📖

## Behavior field 🧩

- Interface: `cs.megamenu.behaviors.menu.IEditableMenu`
- Behavior name: `cs.megamenu.menu`
- Fieldset: `megamenu` (label **Mega menu**)
- Field: `menu` (`plone.schema.JSONField`)
- Default: `None` (inherit)

The behavior is enabled on `Plone Site` and `Folder` by the default profile.
`LRF` is enabled when the type exists.

## JSON value 🗂️

```json
{
  "version": 1,
  "items": []
}
```

Every item has `id`, `type`, `title`, `css_class`, and `icon`.

Folder items have `children` and no target. Link items have exactly one of
`internal_uid` / `external_url`, plus `open_in_new_tab`, and no `children`.

Constraints:

| Field | Rule |
| --- | --- |
| `id` | UUID string, unique across the tree |
| `type` | `folder` or `link` |
| `title` | required, trimmed, at most 200 characters |
| `css_class` | CSS class list, at most 200 characters |
| `icon` | Plone icon name (letters, numbers, `_`, `.`, `/`, `-`), at most 200 characters; resolved through `@@iconresolver` |
| `internal_uid` | non-empty string, at most 64 characters, resolved on save |
| `external_url` | at most 2048 characters; `http`, `https`, `mailto`, or `tel` |
| `open_in_new_tab` | boolean on links |

Unknown properties are rejected. Empty menus and empty folders are valid.
Duplicate titles are allowed; duplicate IDs are not.

## Validation ✅

Client-side validation mirrors the server rules and shows inline errors in the
editor. Server-side validation is a `MenuValidator` registered for the menu
field and raises newline-separated, path-aware messages such as:

```text
Products → Product A: Choose exactly one target: internal or external.
```

## Linkintegrity 🔗

Internal menu links are registered with `plone.app.linkintegrity` when the menu
is saved. Deleting a referenced target shows Plone’s standard “Potential link
breakage” confirmation, naming the object that stores the menu.

- Works for menus on Plone Site, Folder, and LRF.
- Inherited menus are attributed to the ancestor that stores the menu.
- Only `internal_uid` references are tracked; external URLs are not.
- Soft dependency: if `plone.app.linkintegrity` is absent or
  `enable_link_integrity_checks` is off, menus still work without warnings.
- Existing menus are registered on their next save; there is no backfill.
- A menu link whose target is the Plone Site root itself is not tracked.

## Viewlet 🧭

- Replaces `plone.global_sections` in `plone.mainnavigation`.
- Registered for `cs.megamenu.interfaces.IBrowserLayer`.
- Permissions: `zope2.View`.

## Custom rendering 🧩

For custom markup, call `cs.megamenu.menu.get_menu(context)`. It walks up the
acquisition chain and returns `(menu, owner)`:

- `(menu, owner)` for the nearest non-empty configured menu.
- `(None, owner)` for an explicitly saved empty menu; `owner` is the object
  that opted out.
- `(None, None)` when no valid menu is found.

The returned `menu` is the stored JSON, not rendered markup. Use
`filter_items()` from `cs.megamenu.viewlets.menu` to resolve link URLs and
remove targets the current user cannot view:

```python
from cs.megamenu.menu import get_menu
from cs.megamenu.viewlets.menu import filter_items

menu, owner = get_menu(context)
items = filter_items(menu["items"]) if menu else []
```

Visible link items receive a `_url` key; inaccessible or dead links and empty
folders are omitted.

## Bundle 📦

- Registry prefix: `plone.bundles/cs.megamenu`
- Compilation: `++plone++cs.megamenu/bundles/cs.megamenu-remote.min.js`
- Depends on: `plone`

## Endpoints and assets 🔌

- Content browser vocabulary: `@@getVocabulary?name=plone.app.vocabularies.Catalog`
- Static assets: `++plone++cs.megamenu/`

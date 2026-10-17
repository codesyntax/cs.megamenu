---
myst:
  html_meta:
    "description": "collective.megamenu reference"
    "property=og:description": "collective.megamenu reference"
    "property=og:title": "collective.megamenu reference"
    "keywords": "Plone, collective.megamenu, reference, JSON schema"
---

# Reference 📖

## Behavior field 🧩

- Interface: `collective.megamenu.interfaces.IEditableMenu`
- Behavior name: `collective.megamenu.menu`
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
editor. Server-side validation is an `IValidator` for the menu field and raises
newline-separated, path-aware messages such as:

```text
Products → Product A: Choose exactly one target: internal or external.
```

## Viewlet 🧭

- Replaces `plone.global_sections` in `plone.mainnavigation`.
- Registered for `collective.megamenu.interfaces.IBrowserLayer`.
- Permissions: `zope2.View`.

## Bundle 📦

- Registry prefix: `plone.bundles/collective.megamenu`
- Compilation: `++plone++collective.megamenu/bundles/collective.megamenu-remote.min.js`
- Depends on: `plone`

## Endpoints and assets 🔌

- Content browser vocabulary: `@@getVocabulary?name=plone.app.vocabularies.Catalog`
- Static assets: `++plone++collective.megamenu/`

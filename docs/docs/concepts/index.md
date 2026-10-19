---
myst:
  html_meta:
    "description": "cs.megamenu concepts"
    "property=og:description": "cs.megamenu concepts"
    "property=og:title": "cs.megamenu concepts"
    "keywords": "Plone, cs.megamenu, concepts, menu, inheritance"
---

# Concepts 🧠

## Menu model 🗂️

A menu is an ordered tree of menu items stored in the `menu` behavior field.

Every item is either a **folder item** or a **link item**.

- A folder item is a placeholder. It groups children and has no navigation
  target; it renders as an `a.nav-link` with `href="#"` for Barceloneta
  feature parity.
- A link item is a leaf. It has exactly one target, either an internal Plone
  object or an external URL.

The stored value is native JSON:

```json
{
  "version": 1,
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "type": "folder",
      "title": "Products",
      "css_class": "nav-products",
      "icon": "folder",
      "children": [
        {
          "id": "22222222-2222-4222-8222-222222222222",
          "type": "link",
          "title": "Product A",
          "css_class": "",
          "icon": "contenttype/document",
          "internal_uid": "e5f6…",
          "external_url": "",
          "open_in_new_tab": false
        }
      ]
    }
  ]
}
```

## Inheritance 🧬

The menu in effect is the nearest ancestor with a configured menu.

- An **unset** field (`None`) means “inherit”; the search continues upward.
- An **explicitly saved empty menu** means “opt out”; the search stops and the
  viewlet renders nothing.
- If no ancestor configures a menu, the viewlet renders nothing.
- There is no fallback to Plone’s default main navigation.

This lets the site root define a site-wide menu, while a section can override
it or opt out.

## Link resolution and permissions 🔐

Internal links store the target’s raw UID. At render time the UID is looked up
through the catalog and checked against the current user’s `View` permission.

- An inaccessible or deleted internal link is omitted.
- A folder whose visible children are all omitted is omitted too.
- External links are always rendered.

## Rendering 🎨

A viewlet subclasses Plone’s `GlobalSectionsViewlet` and replaces the
`plone.global_sections` viewlet. It preserves the Barceloneta markup contract:

- `ul#portal-globalnav` with `navbar-nav`;
- `li.nav-item` and `a.nav-link`;
- `has_subtree`, `dropdown`, and the mobile `opener` input/label pair;
- `pat-navigationmarker` for the active/in-path behavior.

## Storage 💾

The menu is a native `dict` in a `plone.schema.JSONField`. Internal targets are
also registered with `plone.app.linkintegrity` when the menu is saved, so
deleting a referenced target shows Plone’s standard warning. External URLs and
links to the Plone Site root itself are not tracked. Linkintegrity relations
are created on the next save; existing menus are not backfilled.

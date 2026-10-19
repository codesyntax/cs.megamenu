---
myst:
  html_meta:
    "description": "Render the cs.megamenu menu with custom markup."
    "property=og:description": "Render the cs.megamenu menu with custom markup."
    "property=og:title": "Custom menu markup"
    "keywords": "Plone, cs.megamenu, custom, markup, get_menu"
---

# Custom menu markup 🧩

The default viewlet renders the menu as a Barceloneta navigation. To use your
own markup, call the resolver directly instead of overriding the viewlet.

## Get the menu

`cs.megamenu.menu.get_menu(context)` walks up the acquisition chain and returns
a `(menu, owner)` tuple:

- `(menu, owner)` for the nearest non-empty configured menu.
- `(None, owner)` for an explicitly saved empty menu; `owner` is the object that
  opted out.
- `(None, None)` when no valid menu is found.

`menu` is the stored JSON dictionary for a non-empty configured menu, not
rendered markup. It has the shape `{"version": 1, "items": [...]}`, where
`items` is a list of menu items. `get_menu` returns `None` for an explicitly
empty menu.

`owner` is the content object that supplied the menu. For an inherited menu it
is the ancestor that stores the menu, not the current context.

## Resolve links and permissions

The raw tree contains `internal_uid` and `external_url` values, not resolved
URLs. Use `filter_items()` from `cs.megamenu.viewlets.menu` to get the same
permission-filtered tree as the default viewlet:

```python
from cs.megamenu.menu import get_menu
from cs.megamenu.viewlets.menu import filter_items

menu, owner = get_menu(context)
items = filter_items(menu["items"]) if menu else []
```

`filter_items()` returns a new list and does not mutate the stored menu:

- Visible link items gain a `_url` key with the resolved internal or external
  target.
- Internal UIDs that are missing or not viewable by the current user are
  dropped.
- Folders with no visible children are omitted.

If you need the raw stored data, iterate `menu["items"]` directly.

## Example

```python
from cs.megamenu.menu import get_menu
from cs.megamenu.viewlets.menu import filter_items

menu, owner = get_menu(context)
items = filter_items(menu["items"]) if menu else []

for item in items:
    if item["type"] == "folder":
        children = ", ".join(child["title"] for child in item["children"])
        print(f"{item['title']}: {children}")
    else:
        print(f"{item['title']}: {item['_url']}")
```

Use `owner` if you need the object that supplied an inherited menu, for example
`owner.absolute_url()`.

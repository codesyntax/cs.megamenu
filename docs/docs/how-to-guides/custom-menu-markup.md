---
myst:
  html_meta:
    "description": "Render the cs.megamenu menu with custom templates."
    "property=og:description": "Render the cs.megamenu menu with custom templates."
    "property=og:title": "Custom menu rendering"
    "keywords": "Plone, cs.megamenu, custom, markup, get_menu"
---

# Custom menu rendering 🧩

The default viewlet renders the menu as a Barceloneta navigation. To use your
own markup, call the resolver directly instead of overriding the viewlet.

If you are adding a second menu field, start with
[Additional menu fields](additional-menus.md).

## Get the menu

`cs.megamenu.menu.get_menu(context, field_name="menu", behavior=IEditableMenu)`
walks up the acquisition chain and returns a `(menu, owner)` tuple. The
defaults read the built-in `menu` field; pass another field name and behavior
for an additional menu.

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

For a custom field, pass its field name and behavior; see
[Additional menu fields](additional-menus.md).

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

## Example: standalone viewlet with a custom template

The viewlet below is an example in a separate custom add-on (`myaddon`). It is
not part of `cs.megamenu`; copy and adapt it in your own package.

A regular Plone viewlet is a class plus a page template. The class exposes the
resolved menu items; the template uses a recursive macro to render nested
`<ul>`/`<li>` markup.

### Viewlet class

```python
# myaddon/viewlets/nested_menu.py
from cs.megamenu.behaviors.menu import IEditableMenu
from cs.megamenu.menu import get_menu
from cs.megamenu.viewlets.menu import filter_items
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class NestedMenuViewlet(ViewletBase):
    index = ViewPageTemplateFile("nested_menu.pt")
    menu_field = "menu"
    menu_behavior = IEditableMenu

    def items(self):
        menu, _owner = get_menu(
            self.context,
            field_name=self.menu_field,
            behavior=self.menu_behavior,
        )
        return filter_items(menu["items"]) if menu else []
```

For an additional menu, subclass this viewlet and set `menu_field` and
`menu_behavior`, or pass those values directly to `get_menu()`.

### Template

```xml
<metal:menu define-macro="menu">
  <ul class="nested-menu" tal:condition="items">
    <li tal:repeat="item items">
      <tal:folder tal:condition="python:item['type'] == 'folder'">
        <span tal:content="item/title">Title</span>
        <metal:children
            use-macro="template/macros/menu"
            tal:define="items python:item['children']" />
      </tal:folder>
      <tal:link tal:condition="python:item['type'] == 'link'">
        <a tal:attributes="href item/_url"
           tal:content="item/title">Title</a>
      </tal:link>
    </li>
  </ul>
</metal:menu>

<metal:main use-macro="template/macros/menu"
            tal:define="items view/items" />
```

The macro calls itself for folder children, so the markup nests to any depth.
`tal:content` escapes titles and `tal:attributes` escapes the `href`. The
template produces markup such as:

```html
<ul class="nested-menu">
  <li><span>Products</span>
    <ul class="nested-menu">
      <li><a href="/plone/products/product-a">Product A</a></li>
    </ul>
  </li>
</ul>
```

### Register the viewlet

```xml
<browser:viewlet
    name="myaddon.nested_menu"
    manager="plone.app.layout.viewlets.interfaces.IPortalFooter"
    class=".viewlets.nested_menu.NestedMenuViewlet"
    permission="zope2.View"
    layer="myaddon.interfaces.IBrowserLayer"
    />
```

Add the `browser` namespace to your ZCML root
(`xmlns:browser="http://namespaces.zope.org/browser"`). The
`ViewPageTemplateFile("nested_menu.pt")` path resolves the template relative to
the module.

### Notes

- `filter_items()` resolves URLs, drops inaccessible or dead internal links,
  and omits empty folders.
- Folder items are placeholders, so the example renders a `<span>`. Use
  `<a href="#">` for focusable folder labels with Barceloneta parity.
- For an additional menu field, subclass `NestedMenuViewlet` and set
  `menu_field = "footer_menu"` and `menu_behavior = IFooterMenu`, or pass those
  values directly to `get_menu()`. Choose the viewlet name and manager for your
  menu’s location. See [Additional menu fields](additional-menus.md).
- Add `target="_blank"` and `rel="noopener noreferrer"` for link items with
  `open_in_new_tab` if your markup should preserve that behavior.
- An empty menu renders no `<ul>` because of `tal:condition="items"`.

Use `owner` if you need the object that supplied an inherited menu, for example
`owner.absolute_url()`.

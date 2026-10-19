---
myst:
  html_meta:
    "description": "Define additional menu fields and reuse the cs.megamenu widget."
    "property=og:description": "Define additional menu fields and reuse the cs.megamenu widget."
    "property=og:title": "Additional menus"
    "keywords": "Plone, cs.megamenu, additional menus, behavior, widget"
---

# Additional menus 🧩

`cs.megamenu` ships one behavior with a `menu` field (`IEditableMenu`) and a
viewlet for the main navigation. You can define additional menu fields in your
own behavior and reuse the editor widget, validator, resolver, linkintegrity
retriever, and viewlet base class.

The code in this guide is an example for a separate add-on (`myaddon`). It is
not part of `cs.megamenu`; copy and adapt it in your own package.

Use a distinct field name and behavior for each menu. The examples below add a
`footer_menu` field.

## Define the field and behavior

Create a behavior schema with a `JSONField` that uses `MENU_JSON_SCHEMA`, and
apply the menu widget to that field with `plone.autoform.directives.widget`:

```python
# myaddon/behaviors/footer.py
from cs.megamenu.schema import MENU_JSON_SCHEMA
from cs.megamenu.widgets.menu import MegaMenuFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.schema import JSONField
from plone.supermodel import model
from zope.interface import provider


@provider(IFormFieldProvider)
class IFooterMenu(model.Schema):
    """Adds a footer menu field."""

    directives.widget("footer_menu", MegaMenuFieldWidget)

    footer_menu = JSONField(
        title="Footer menu",
        description="Menu rendered in the site footer.",
        required=False,
        schema=MENU_JSON_SCHEMA,
    )
```

Register the behavior in your package’s ZCML. Remember the `plone` namespace
and the `plone.behavior` meta include:

```xml
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    >

  <include package="plone.behavior" file="meta.zcml" />

  <plone:behavior
      name="myaddon.footer_menu"
      title="Footer menu"
      description="Adds a footer menu field."
      provides=".behaviors.footer.IFooterMenu"
      />
</configure>
```

Enable the behavior on the content types in your profile, for example:

```xml
<object meta_type="Dexterity FTI" name="Plone Site">
  <property name="behaviors" purge="false">
    <element value="myaddon.footer_menu" />
  </property>
</object>
```

The schema-only behavior also acts as the behavior marker, so the object
provides `IFooterMenu` when the behavior is enabled.

## Register the validator

The semantic validator is reusable. `cs.megamenu` already registers the
`MenuValidator` adapter; add a discriminator for your field so it is selected
for `footer_menu` as well:

```python
# myaddon/validators/menu.py
from cs.megamenu.validators.menu import MenuValidator
from myaddon.behaviors.footer import IFooterMenu
from z3c.form import validator

validator.WidgetValidatorDiscriminators(
    MenuValidator,
    field=IFooterMenu["footer_menu"],
)
```

Import this module from your package so the discriminator is registered.

## Resolve the menu

`get_menu()` accepts the field name and behavior:

```python
from cs.megamenu.menu import get_menu
from myaddon.behaviors.footer import IFooterMenu

menu, owner = get_menu(
    context,
    field_name="footer_menu",
    behavior=IFooterMenu,
)
```

Use `filter_items()` for resolved URLs and permission filtering:

```python
from cs.megamenu.viewlets.menu import filter_items

items = filter_items(menu["items"]) if menu else []
```

See [Custom menu markup](../how-to-guides/custom-menu-markup.md) for the full
return contract and a rendering example.

## Track link integrity

The default retriever reads the `menu` field. Subclass it for your field and
register the adapter for your behavior:

```python
# myaddon/linkintegrity.py
from cs.megamenu.linkintegrity.menu import MenuRetriever
from myaddon.behaviors.footer import IFooterMenu
from plone.app.linkintegrity.interfaces import IRetriever
from zope.component import adapter
from zope.interface import implementer


@implementer(IRetriever)
@adapter(IFooterMenu)
class FooterMenuRetriever(MenuRetriever):
    field_name = "footer_menu"
```

Register it conditionally so your package still works without
`plone.app.linkintegrity`:

```xml
<!-- myaddon/linkintegrity.zcml -->
<configure xmlns="http://namespaces.zope.org/zope">
  <adapter factory=".linkintegrity.FooterMenuRetriever" />
</configure>
```

```xml
<!-- myaddon/configure.zcml -->
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:zcml="http://namespaces.zope.org/zcml"
    >
  <include
      file="linkintegrity.zcml"
      zcml:condition="installed plone.app.linkintegrity"
      />
</configure>
```

## Render a custom viewlet

Subclass `MegaMenuViewlet` and point it at your field and behavior:

```python
# myaddon/viewlets/footer.py
from cs.megamenu.viewlets.menu import MegaMenuViewlet
from myaddon.behaviors.footer import IFooterMenu


class FooterMenuViewlet(MegaMenuViewlet):
    menu_field = "footer_menu"
    menu_behavior = IFooterMenu
```

Register it under a new viewlet name and the manager used by your template.
The base class reuses resolution, permission filtering, icon rendering, and the
Barceloneta markup.

## Checklist

- The field name must match in `directives.widget()`, `get_menu()`, the
  retriever’s `field_name`, and the viewlet’s `menu_field`.
- Use a separate behavior and field for each menu.
- Enable the behavior on the content types where the menu should be available.
- Import the validator module so its field discriminator is registered.
- Include the linkintegrity retriever only when `plone.app.linkintegrity` is
  installed.

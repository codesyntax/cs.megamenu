---
myst:
  html_meta:
    "description": "Terms and definitions used by cs.megamenu."
    "property=og:description": "Terms and definitions used by cs.megamenu."
    "property=og:title": "Glossary"
    "keywords": "Plone, cs.megamenu, glossary, menu"
---

# Glossary 📚

```{glossary}
:sorted: true

Menu
    The ordered tree of menu items configured for a Plone Site, an LRF, or a
    Folder.

Menu item
    A single node in a menu. Every menu item is either a folder item or a link
    item.

Folder item
    A placeholder menu item that groups other menu items. It has children and
    no target; it is not clickable.

Link item
    A leaf menu item that points to one target. It has no children.

Internal link
    A link item whose target is a Plone object, identified by the object’s UID.

External link
    A link item whose target is a URL outside the Plone site.

Behavior
    The Plone behavior that adds the menu configuration to an enabled content
    type.

Viewlet
    The browser viewlet that renders the menu in place of Plone’s main
    navigation.

LRF
    A Language Root Folder, the folder type used for a language branch in a
    multilingual Plone site.

Nearest ancestor
    The closest ancestor of the current context that has the menu behavior
    enabled. It determines which menu is in effect.

Unset menu
    A `None` menu value. It means the object does not configure a menu and
    inherits from the nearest ancestor.

Explicit opt-out
    A nearest ancestor whose menu has been explicitly saved empty. It stops
    inheritance and causes the viewlet to render nothing.
```

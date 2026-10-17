# Glossary

- **Menu**: the ordered tree of menu items configured for a Plone Site, an LRF, or a Folder.
- **Menu item**: a single node in a menu. Every menu item is either a folder item or a link item.
- **Folder item**: a placeholder menu item that groups other menu items. It has children and no target; it is not clickable.
- **Link item**: a leaf menu item that points to one target. It has no children.
- **Internal link**: a link item whose target is a Plone object, identified by the object's UID.
- **External link**: a link item whose target is a URL outside the Plone site.
- **Behavior**: the Plone behavior that adds the menu configuration to an enabled content type.
- **Viewlet**: the browser viewlet that renders the menu in place of Plone's main navigation.
- **LRF**: a Language Root Folder, the folder type used for a language branch in a multilingual Plone site.
- **Nearest ancestor**: the closest ancestor of the current context that has the menu behavior enabled. It determines which menu is in effect.
- **Unset menu**: a `None` menu value. It means the object does not configure a menu and inherits from the nearest ancestor.
- **Explicit opt-out**: a nearest ancestor whose menu has been explicitly saved empty. It stops inheritance and causes the viewlet to render nothing.
- **Main navigation**: the navigation area that Plone normally renders with the `plone.global_sections` viewlet.

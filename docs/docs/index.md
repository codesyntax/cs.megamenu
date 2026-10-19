---
myst:
  html_meta:
    "description": "An editable, JSON-backed megamenu for Plone 6 Classic UI."
    "property=og:description": "An editable, JSON-backed megamenu for Plone 6 Classic UI."
    "property=og:title": "cs.megamenu"
    "keywords": "cs.megamenu, Plone, Classic UI, navigation, menu"
---

# cs.megamenu

`cs.megamenu` adds an editable menu to Plone 6 Classic UI. The menu is
stored as JSON on a content object, edited with a tree widget in the standard
edit form, and rendered by a viewlet that replaces Plone’s main navigation.

## Features ✨

- Nested folder placeholders and leaf links.
- Internal links stored as UIDs and permission-filtered at render time.
- External links, per-item CSS classes, Plone icon names, and open-in-new-tab.
- Nearest-ancestor inheritance with an explicit empty opt-out.
- Optional Language Root Folder support with `plone.app.multilingual`.

## Quick start 🚀

Install the add-on from **Site Setup → Add-ons**.

For a source checkout:

```shell
make install
make start
```

Then edit the Plone Site root or a Folder, switch to the **Mega menu**
fieldset, and use the **Menu** field.

```{warning}
There is no fallback to Plone’s default main navigation. If no menu is
configured, or the effective menu is explicitly empty, the main navigation
renders nothing.
```

## Documentation 📚

```{toctree}
:caption: How-to guides
:maxdepth: 2
:hidden: true

how-to-guides/index
```

```{toctree}
:caption: Reference
:maxdepth: 2
:hidden: true

reference/index
```

```{toctree}
:caption: Tutorials
:maxdepth: 2
:hidden: true

tutorials/index
```

```{toctree}
:caption: Concepts
:maxdepth: 2
:hidden: true

concepts/index
```

```{toctree}
:caption: Appendices
:maxdepth: 2
:hidden: true

glossary
genindex
```

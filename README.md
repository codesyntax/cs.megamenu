<div align="center">
    <h1 align="center">collective.megamenu</h1>
</div>
<div align="center">

[![PyPI](https://img.shields.io/pypi/v/collective.megamenu)](https://pypi.org/project/collective.megamenu/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/collective.megamenu)](https://pypi.org/project/collective.megamenu/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/collective.megamenu)](https://pypi.org/project/collective.megamenu/)
[![PyPI - License](https://img.shields.io/pypi/l/collective.megamenu)](https://pypi.org/project/collective.megamenu/)
[![PyPI - Status](https://img.shields.io/pypi/status/collective.megamenu)](https://pypi.org/project/collective.megamenu/)


[![PyPI - Plone Versions](https://img.shields.io/pypi/frameworkversions/plone/collective.megamenu)](https://pypi.org/project/collective.megamenu/)

[![CI](https://github.com/collective/collective.megamenu/actions/workflows/main.yml/badge.svg)](https://github.com/collective/collective.megamenu/actions/workflows/main.yml)
![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000)

[![GitHub contributors](https://img.shields.io/github/contributors/collective/collective.megamenu)](https://github.com/collective/collective.megamenu)
[![GitHub Repo stars](https://img.shields.io/github/stars/collective/collective.megamenu?style=social)](https://github.com/collective/collective.megamenu)

</div>

An editable, JSON-backed megamenu for Plone 6 Classic UI.

## Features ✨

- A `menu` behavior enabled on **Plone Site**, **Folder**, and (when
  `plone.app.multilingual` is installed) **LRF**.
- Unlimited nesting of **folder items** (placeholders) and **link items**
  (leaves).
- Internal links stored as raw Plone UIDs and resolved at render time.
- Internal menu targets participate in Plone’s linkintegrity checks, so deleting
  referenced content shows the standard link-breakage warning.
- External links validated to `http`, `https`, `mailto`, and `tel`.
- Per-item CSS class and Plone icon name; links may open in a new tab.
- A master-detail editor in the standard edit form, with a per-node content
  browser for internal targets, inline validation, and a “Use inherited menu”
  action.
- The nearest ancestor with a configured menu wins. An unset menu inherits;
  an explicitly saved empty menu opts out.
- A viewlet that replaces `plone.global_sections` with the menu, preserving the
  Barceloneta mobile navigation markup.
- Internal links the current user cannot view are filtered out; folders whose
  visible children are all filtered out are omitted.
- Server-side validation with readable, path-aware messages.

## Requirements 📋

- Plone 6 Classic UI (tested with Plone 6.2).
- Python 3.10 or newer.
- Node.js 18 or newer, only for building the editor bundle.
- `plone.app.multilingual` only if you want LRF support.

## Installation 🚀

Install the add-on from **Site Setup → Add-ons**.

For a local development site:

```shell
make install
make create-site
make start
```

## Usage 🧭

### Configure the site menu 🛠️

1. Log in as a user who can edit the Plone Site root.
2. Open the site root edit form (`/Plone/@@edit`) and switch to the **Mega menu** fieldset.
3. Use the **Menu** field to add folders and links.
4. Save the form.

A saved menu on the site root is used site-wide unless a descendant configures
its own menu.

### Configure a folder menu 📁

Every Folder has the behavior. Open the folder edit form, switch to the
**Mega menu** fieldset, and configure its **Menu** field. The nearest ancestor
with a configured menu supplies the menu for its descendants.

- Leave the field **unset** to inherit the nearest ancestor menu.
- Use **Use inherited menu** in the editor to clear the field back to inherit.
- Save an **empty** menu to explicitly opt out for that folder and its
  descendants. The viewlet renders nothing there.

### Choose the effective menu 🧭

- The nearest ancestor with a configured menu wins.
- `None` (unset) continues up the acquisition chain.
- An explicitly saved empty menu stops the search and renders no navigation.
- If no menu is configured, the viewlet renders nothing. There is **no
  fallback** to Plone’s default main navigation; this is intentional.

### Internal and external links 🔗

- **Internal** links use the **Internal** tab and Plone’s content browser, and store the target’s UID.
  The UID is resolved on render with the current user’s View permission.
  Deleted or inaccessible targets are omitted.
- **External** links use the **External** tab and accept `http`, `https`, `mailto`, and `tel` URLs.
- **Open in a new tab** adds `target="_blank"` and
  `rel="noopener noreferrer"`.

### Language Root Folders 🌐

When `plone.app.multilingual` is installed, the behavior is enabled on `LRF`.
The add-on profile’s post-handler adds the behavior when the `LRF` type exists.
If you install PAM **after** `collective.megamenu`, reapply the
`collective.megamenu:default` profile.

### Custom styling 🎨

- **CSS class** is added to the menu item’s `<li>`.
- **Icon** is a Plone icon name such as `alarm` or `contenttype/document`.
  The editor preview and the viewlet resolve it with `@@iconresolver`; the
  viewlet renders an inline SVG with the `megamenu-icon` class.
- The viewlet preserves the standard `#portal-globalnav` and Barceloneta classes,
  so themes and the mobile offcanvas continue to work.

## Development 🧑‍💻

Install the test environment and run the Python tests:

```shell
make install
make test
```

Run lint and formatting checks:

```shell
make check
```

Build the JavaScript bundle after changing `resources/`:

```shell
npm install
npm run build
```

The build writes the remote bundle and its chunks to
`src/collective/megamenu/browser/static/bundles/`.

Run the browser checks against a running Plone site:

```shell
make test-browser
```

Update translations with:

```shell
make i18n
```

### Project layout

- `src/collective/megamenu/behaviors/menu.py` — behavior schema and `menu` field.
- `src/collective/megamenu/validators/` — form validator and semantic validation.
- `src/collective/megamenu/widgets/` — master-detail editor widget and template.
- `src/collective/megamenu/viewlets/menu.py` — main navigation viewlet.
- `src/collective/megamenu/linkintegrity/` — menu reference tracking for Plone linkintegrity.
- `src/collective/megamenu/browser/` — static assets and published bundles.
- `resources/pat-megamenu/` — Patternslib editor source.

## Limitations ⚠️

- Classic UI only; there is no Volto/headless integration.
- No drag-and-drop; use the move up/down buttons.
- Folder items are placeholders and cannot have a target.
- Internal links are stored as UIDs, not relation-field backrefs. Existing
  targets are registered with `plone.app.linkintegrity` when the menu is saved;
  external URLs are not tracked. Dead targets are omitted at render time.
- Existing menus are registered with linkintegrity on their next save; there is
  no backfill.
- A menu link whose target is the Plone Site root itself is not tracked by
  linkintegrity.
- There is no fallback to the default main navigation.
- Menu labels are not translated per language.

## License 📄

The project is licensed under GPLv2.

## Credits and acknowledgements 🙏

Generated using [Cookieplone (2.0.2)](https://github.com/plone/cookieplone) and [cookieplone-templates (2e19702)](https://github.com/plone/cookieplone-templates/commit/2e19702a8c4c221b540f70eea38f6c2981329f5c) on 2026-10-17 09:34:24.128161. A special thanks to all contributors and supporters!

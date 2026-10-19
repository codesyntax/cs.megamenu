<div align="center">
    <h1 align="center">cs.megamenu</h1>
</div>
<div align="center">

[![PyPI](https://img.shields.io/pypi/v/cs.megamenu)](https://pypi.org/project/cs.megamenu/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cs.megamenu)](https://pypi.org/project/cs.megamenu/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/cs.megamenu)](https://pypi.org/project/cs.megamenu/)
[![PyPI - License](https://img.shields.io/pypi/l/cs.megamenu)](https://pypi.org/project/cs.megamenu/)
[![PyPI - Status](https://img.shields.io/pypi/status/cs.megamenu)](https://pypi.org/project/cs.megamenu/)


[![PyPI - Plone Versions](https://img.shields.io/pypi/frameworkversions/plone/cs.megamenu)](https://pypi.org/project/cs.megamenu/)

[![CI](https://github.com/codesyntax/cs.megamenu/actions/workflows/main.yml/badge.svg)](https://github.com/codesyntax/cs.megamenu/actions/workflows/main.yml)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://codesyntax.github.io/cs.megamenu/)
![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000)

[![GitHub contributors](https://img.shields.io/github/contributors/codesyntax/cs.megamenu)](https://github.com/codesyntax/cs.megamenu)
[![GitHub Repo stars](https://img.shields.io/github/stars/codesyntax/cs.megamenu?style=social)](https://github.com/codesyntax/cs.megamenu)

</div>

An editable, JSON-backed megamenu for Plone 6.2 Classic UI.

See the [documentation](https://codesyntax.github.io/cs.megamenu/) for usage,
reference, and development guides.

<div align="center">
  <img src="https://codesyntax.github.io/cs.megamenu/_static/menu.svg" alt="A menu bar with an open submenu" width="420">
</div>

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

- Plone 6.2 Classic UI.
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
If you install PAM **after** `cs.megamenu`, reapply the
`cs.megamenu:default` profile.

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
`src/cs/megamenu/browser/static/bundles/`.

Build the Sphinx documentation with `make -C docs html`; see
[`docs/README.md`](docs/README.md) for details.

Run the browser checks against a running Plone site:

```shell
make test-browser
```

Update translations with:

```shell
make i18n
```

### Project layout

- `src/cs/megamenu/behaviors/menu.py` — behavior schema and `menu` field.
- `src/cs/megamenu/validators/` — form validator and semantic validation.
- `src/cs/megamenu/widgets/` — master-detail editor widget and template.
- `src/cs/megamenu/viewlets/menu.py` — main navigation viewlet.
- `src/cs/megamenu/linkintegrity/` — menu reference tracking for Plone linkintegrity.
- `src/cs/megamenu/browser/` — static assets and published bundles.
- `resources/pat-megamenu/` — Patternslib editor source.

### Custom menu markup

To render the menu yourself, use `cs.megamenu.menu.get_menu(context)` and
`filter_items()`. See
[Custom menu markup](https://codesyntax.github.io/cs.megamenu/how-to-guides/custom-menu-markup.html)
in the documentation for the return contract and a complete example.

To define additional menu fields and reuse the widget in a custom behavior, see
[Additional menus](https://codesyntax.github.io/cs.megamenu/how-to-guides/additional-menus.html).

## Release process 🚀

Prepare the release from a clean `main` branch with the latest changes pulled.

1. Add a news fragment under `news/` named `<issue>.<type>`, for example
   `42.feature`. The configured types are `breaking`, `feature`, `bugfix`,
   `internal`, `documentation`, and `tests`.
2. Run `make i18n` after changing translatable strings. Commit the updated
   `.pot` and `.po` files. The `.mo` files are compiled during release and are
   not committed.
3. Compile the editor bundle:

   ```shell
   npm install
   npm run build
   ```

   `npm install` is only needed when JS dependencies change; commit any
   `package.json` or `package-lock.json` updates together with the rebuilt
   bundle. `npm run build` writes `cs.megamenu-remote.min.js`,
   `cs.megamenu.min.js`, their source maps, and the chunk files under
   `src/cs/megamenu/browser/static/bundles/`. Commit the rebuilt files; do not
   edit them by hand.
4. Run the checks and tests:

   ```shell
   make check
   make test
   ```

   Optionally run the browser checks against a running Plone site with
   `make test-browser` (set `PLONE_URL` if it is not on the default
   `http://127.0.0.1:8080/Plone`).
5. Run the release:

   ```shell
   make release
   ```

   This installs the release extras and runs `fullrelease`. The configured
   `zestreleaser.towncrier` plugin turns the `news/` fragments into
   `CHANGELOG.md`, `zest.pocompile` compiles the translations, and the release
   tool bumps the version in `src/cs/megamenu/__init__.py`, creates the tag,
   uploads to PyPI, and prepares the post-release version bump.

Review and push the commits and tags created by the release tool. The release
tool does **not** rebuild the JavaScript bundle, so the committed bundle from
step 3 is the one shipped in the release.

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

## Disclaimer ⚠️

This add-on was written with assistance from [OpenCode](https://opencode.ai/),
[DeepSeek Flash 4.1](https://www.deepseek.com/), and
[Matt Pocock's skills](https://github.com/mattpocock/skills). Review and test
the code in your own environment before using it in production.

## License 📄

The project is licensed under GPLv2.

## Credits and acknowledgements 🙏

Generated using [Cookieplone (2.0.2)](https://github.com/plone/cookieplone) and [cookieplone-templates (2e19702)](https://github.com/plone/cookieplone-templates/commit/2e19702a8c4c221b540f70eea38f6c2981329f5c) on 2026-10-17 09:34:24.128161. A special thanks to all contributors and supporters!

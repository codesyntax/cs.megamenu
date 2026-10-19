# collective.megamenu — wayfinder map

> Status: route clear. The destination artifact is [spec.md](spec.md).

## Destination

A build-ready spec in `.scratch/collective-megamenu/000-initial/spec.md` plus an implementation ticket breakdown for `collective.megamenu`: a Plone 6.2 Classic UI addon providing an `IEditableMenu` behavior (JSON menu tree) on Plone Site, LRF, and Folder, a Patternslib tree editor widget in the standard edit form, and a viewlet that replaces the main navigation with the nearest configured menu.

## Notes

- Domain: Plone 6.2 Classic UI, Python 3.10+, pytest-plone. No Volto/headless.
- Skills every session should consult: `plone-expert-developer`, `grilling`, `domain-modeling`, and `tdd` when implementation starts.
- Tracker: local markdown under `.scratch/collective-megamenu/000-initial/`. No remote or tracker is configured.
- Package rename: the repo currently says `collective.editablemenu`; the destination is `collective.megamenu`. Both PyPI and `collective/collective.megamenu` were free when checked on 2026-10-17.
- Research asset: [`research/plone-6.2-apis.md`](research/plone-6.2-apis.md).

### Foundation decisions from charting

- Classic UI only.
- Behavior targets: `Plone Site`, `LRF`, and `Folder`. `LRF` is the Language Root Folder from `plone.app.multilingual`; its support is conditional on that package being installed.
- A behavior on an ancestor supplies the menu. An unset field (`None`) means inherit; the nearest ancestor with a non-`None` menu wins. An explicitly saved empty menu is an explicit opt-out: the viewlet renders nothing.
- No fallback to Plone's default navigation. If no menu is configured, or the resolved menu is empty, the main-navigation viewlet renders nothing.
- Menu node model:
  - every item has `id`, `type`, `title`, `css_class`, and `icon`;
  - `type: "folder"` items are placeholders: they have `children` and no target;
  - `type: "link"` items are leaves: exactly one of `internal_uid` or `external_url`, no children;
  - `open_in_new_tab` exists only on link items;
  - `icon` is a Plone icon name (for example `alarm`) resolved through
  `@@iconresolver`;
  - `css_class` is free-form per item.
- Internal links store raw UIDs. They are resolved at render time with a permission check.
- Permission filtering: inaccessible internal-link leaves are omitted; folders whose visible children are all omitted are omitted too; external links always render.
- The stored value is native JSON (not a JSON string), shaped as `{"version": 1, "items": [...]}`.
- Editor: inline in the standard edit form, using the chosen **master-detail** layout: menu tree on the left, inspector for the selected node on the right. Buttons add folder, add link, add child, delete, move up/down. Each node edits title, CSS class, icon, and (for links) internal/external target and open-in-new-tab. Internal link selection uses Plone's content browser. No drag-and-drop.
- Site-root editing relies on the standard `@@edit` form; the user reports it exposes behavior fields on the Plone Site root. This is an assumption to verify in the first implementation spike.
- Main navigation replacement: subclass `GlobalSectionsViewlet` and re-register `plone.global_sections` for `IMainNavigation` on the addon browser layer. Preserve Barceloneta's mobile offcanvas contract (`#portal-globalnav`, `navbar-nav`, `nav-item`, `nav-link`, `has_subtree`, `dropdown`, `opener`, `pat-navigationmarker`).
- Field: `plone.schema.JSONField` with a JSON Schema. Classic UI's default widget is a textarea; the addon applies its custom widget to the behavior's `menu` field with `plone.autoform.directives.widget` and reuses the core `JSONDataConverter`.
- Widget frontend: Patternslib pattern built with the standard plonecli/webpack setup; bundle registered through `plone.base.interfaces.IBundleRegistry`, depending on `plone`.

## Decisions so far

- [Recorded Plone 6.2 API constraints](issues/01-plone-6.2-api-constraints.md): JSONField and custom-widget registration, site-root behavior support, main-nav viewlet contract, UID resolution, bundle registration, and prior art.
- [Conditional LRF behavior registration](issues/02-conditional-lrf-registration.md): import `types/LRF.xml` without listing LRF in `types.xml` (missing FTIs are skipped); use the addon profile's `post_handler` (PAM installed later requires reapplying the addon profile); uninstall with `remove="true"` and `purge="false"`.
- [Content browser integration for per-node internal links](issues/03-content-browser-per-node.md): use `pat-contentbrowser` per link node with a hidden input and Python-built options; scan new nodes; unmount the Svelte app on delete; keep one hidden JSON textarea for the converter.
- [Tree editor prototype](issues/04-tree-editor-prototype.md): chose Variant A, master-detail (tree left, inspector right), with row actions, inspector fields, inline validation, and no additional changes requested.
- [Finalize JSON Schema and validation rules](issues/05-json-schema-validation.md): draft-07 schema with separate folder/link item definitions; UUID IDs; exact text/CSS/icon-name/URL limits; path-aware server validation; inline client validation; empty menus and empty folders allowed.

## Not yet specified

None. The route is clear; the remaining implementation detail is specified in [`spec.md`](spec.md).

## Out of scope

- Volto/headless support.
- Drag-and-drop reordering.
- Folder items with targets; folders are placeholders only, for accessibility and dropdown reasons.
- Image uploads; icons are Plone icon names resolved through `@@iconresolver`.
- Item descriptions.
- Per-item visibility rules.
- Translated menu labels.
- Caching or performance tuning.
- Automatic submenu generation from Plone folders.
- Link-integrity/backrefs or relation fields for menu links.
- Multiple menus per object.
- Fallback to Plone's default main navigation.
- Permission filtering of external links.
- A separate “no navigation at all” toggle; an empty menu already renders nothing.

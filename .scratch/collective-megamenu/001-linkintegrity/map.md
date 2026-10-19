# Linkintegrity support — wayfinder map

Labels: wayfinder:map
Status: route clear

## Destination

A build-ready spec for tracking menu `internal_uid` references with `plone.app.linkintegrity`, so deleting content referenced by a menu shows Plone's standard linkintegrity warning. The destination artifact is [spec.md](spec.md), now implemented in `src/cs/megamenu/linkintegrity/`.

## Notes

- Tracker: local markdown under `.scratch/collective-megamenu/001-linkintegrity/`.
- Standard linkintegrity flow: use Plone's existing delete confirmation and "Delete anyway" behavior; do not build a custom warning UI.
- Track every `internal_uid` in each stored menu tree, covering Plone Site, Folder, and LRF. Inherited menus are covered by the ancestor that stores them. External URLs are out of scope.
- The relation source is the object that stores the menu (the ancestor for inherited menus); the standard warning names that object.
- Soft dependency: menu editing and rendering must work without `plone.app.linkintegrity`; tracking activates only when it is installed and `enable_link_integrity_checks` is on. When the setting is off, stay off and respect Plone's behavior.
- No backfill for existing menus: references are tracked on the next save.
- Target version: Plone 6.0–6.2, with Plone 6.2 as the tested environment. The relevant linkintegrity API is stable across the range.
- Site-root target limitation: core linkintegrity skips `IPloneSiteRoot` targets, so a menu item pointing at the site root itself is not tracked. Accepted because the site root is never deleted by a content editor.

## Decisions so far

- [Linkintegrity integration points and site-root coverage](issues/01-linkintegrity-integration-research.md): use one `IRetriever` adapter for `IEditableMenu` that subclasses `DXGeneral` and unions `resolveuid/<uid>` menu links with RichText links; the site root is covered by the core handlers; register behind a conditional ZCML include.

## Not yet specified

None. The route is clear and the spec is written at [spec.md](spec.md).

## Out of scope

- Tracking external URLs.
- Custom linkintegrity warning UI, or naming the specific menu item in the warning.
- Backfilling existing menus or adding an upgrade step.
- Hard-blocking deletion; use Plone's standard warning and "Delete anyway" flow.
- Tracking references outside the menu.
- Tracking a menu reference whose target is the Plone Site root itself. Core linkintegrity skips `IPloneSiteRoot` targets, and the site root is not a normal deletable target.
- Volto/headless support for linkintegrity.

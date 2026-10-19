# Linkintegrity integration points and site-root coverage

Type: research
Status: resolved
Blocked by: none
Labels: wayfinder:research

## Question

Investigate how `collective.megamenu` should add menu `internal_uid` references to `plone.app.linkintegrity` on Plone 6.2.

Answer:

- Does the schema-only `IEditableMenu` behavior apply a marker interface to objects (Plone Site, Folder, LRF), and can an `IRetriever` adapter be registered for that marker?
- Does the Plone Site root provide `IDexterityHasRelations` and fire the standard linkintegrity subscribers? If not, what fallback is needed?
- How does `IRetriever.retrieveLinks` handle `resolveuid/<uid>` URLs, and how should a menu retriever combine menu UIDs with RichText links without dropping the latter?
- How should the integration be conditionally registered when `plone.app.linkintegrity` is absent (soft dependency)?
- Are there API differences between Plone 6.0, 6.1, and 6.2?
- What prior art exists for integrating custom reference sources with linkintegrity, and what tests should the spec require?

Capture the findings in `research/linkintegrity-integration.md` and return a concise summary with file/API references and a recommended integration mechanism.

## Answer

Resolved by a research subagent. Full findings: [research/linkintegrity-integration.md](../research/linkintegrity-integration.md).

Recommendation: register one `IRetriever` adapter for the `IEditableMenu` behavior marker. It subclasses `DXGeneral`, calls `super().retrieveLinks()` to keep RichText links, and unions in `resolveuid/<uid>` for every nested link item's non-empty `internal_uid`.

Key facts:

- The schema-only behavior applies `IEditableMenu` as a marker; `@adapter(IEditableMenu)` wins over the core `DXGeneral` adapter.
- Folder, LRF, and the Plone Site root all provide `IDexterityHasRelations`; the core linkintegrity subscribers already fire for them. No fallback subscriber is needed.
- `getObjectsFromLinks` expects URL strings and has an explicit `resolveuid/<uid>` branch, so the retriever must return those strings rather than `RelationValue`s.
- Isolate the module behind `zcml:condition="installed plone.app.linkintegrity"`; do not import linkintegrity anywhere else. The core handlers already gate on `enable_link_integrity_checks`.
- The relevant API is stable across Plone 6.0–6.2.
- Known limitation: `getObjectsFromLinks` skips `IPloneSiteRoot` targets, so a menu link whose target is the site root itself is not tracked.

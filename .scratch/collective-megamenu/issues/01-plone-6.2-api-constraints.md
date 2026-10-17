# Plone 6.2 API constraints for the addon

Type: research
Status: resolved
Blocked by: none

## Question

What are the exact Plone 6.2 Classic UI APIs and constraints for: `plone.schema.JSONField` and custom widgets; enabling a behavior on the Plone Site root, `Folder`, and `LRF`; replacing the main navigation viewlet; resolving internal UIDs; registering a Patternslib bundle; and prior art?

## Answer

Resolved by a research subagent. Full findings: [research/plone-6.2-apis.md](../research/plone-6.2-apis.md).

Summary:

- `plone.schema.JSONField` is available through `Products.CMFPlone`; declare `plone.schema>=3.0.0` explicitly. In Classic UI the effective default widget is `plone.app.z3cform.widgets.text.TextAreaFieldWidget` registered for `IJSONField` + `IPloneFormLayer`; the `JSONDataConverter` round-trips native Python values. A custom widget must register for the same or a more specific layer.
- The Plone Site root is behavior-assignable through its Dexterity FTI (`profiles/default/types/Plone_Site.xml`, `purge="false"`). `Folder` uses `types/Folder.xml`. `LRF` is a `plone.app.multilingual` type, not a core type.
- Main navigation is viewlet `plone.global_sections`, manager `IMainNavigation` (`plone.mainnavigation`), class `GlobalSectionsViewlet`, template `sections.pt`. Subclass it and re-register the same name/manager on the addon browser layer; preserve the Barceloneta mobile offcanvas markup.
- Internal UIDs resolve with `plone.app.uuid.utils.uuidToObject` (restricted final traversal) and `uuidToURL` (unrestricted); `@@resolveuid` redirects. Store raw UIDs and resolve at render time.
- Patternslib is already in the `plone` bundle. Register the addon bundle through `plone.base.interfaces.IBundleRegistry` with `depends=plone`.
- Prior art: RedTurtle's `collective.editablemenu` 3.0.3 is the closest existing addon, but this effort is a fresh implementation because the requested behavior/JSONField data model and editor differ.

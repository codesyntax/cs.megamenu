# Plone 6.2 API constraints for the addon

Type: research
Status: resolved
Blocked by: none

## Question

What are the exact Plone 6.2 Classic UI APIs and constraints for: `plone.schema.JSONField` and custom widgets; enabling a behavior on the Plone Site root, `Folder`, and `LRF`; replacing the main navigation viewlet; resolving internal UIDs; registering a Patternslib bundle; and prior art?

## Answer

Resolved by a research subagent. Full findings: [research/plone-6.2-apis.md](../research/plone-6.2-apis.md).

Summary:

- `plone.schema.JSONField` is available through `Products.CMFPlone`; declare `plone.schema>=3.0.0` explicitly. In Classic UI the effective default widget is `plone.app.z3cform.widgets.text.TextAreaFieldWidget` registered for `IJSONField` + `IPloneFormLayer`; the `JSONDataConverter` round-trips native Python values. The addon scopes its custom widget to the behavior's `menu` field with `plone.autoform.directives.widget`, so other JSON fields keep the default widget.
- The Plone Site root is behavior-assignable through its Dexterity FTI (`profiles/default/types/Plone_Site.xml`, `purge="false"`). `Folder` uses `types/Folder.xml`. `LRF` is a `plone.app.multilingual` type, not a core type.
- Main navigation is viewlet `plone.global_sections`, manager `IMainNavigation` (`plone.mainnavigation`), class `GlobalSectionsViewlet`, template `sections.pt`. Subclass it and re-register the same name/manager on the addon browser layer; preserve the Barceloneta mobile offcanvas markup.
- Internal UIDs are stored raw and resolved at render time with the shared `resolve_internal_target` helper: `uuidToCatalogBrain`, `brain.getObject()`, and an explicit `View` permission check. Missing or inaccessible targets are omitted.
- Patternslib is already in the `plone` bundle. Register the addon bundle through `plone.base.interfaces.IBundleRegistry` with `depends=plone`.
- Prior art: RedTurtle's `collective.editablemenu` 3.0.3 is the closest existing addon, but this effort is a fresh implementation because the requested behavior/JSONField data model and editor differ.

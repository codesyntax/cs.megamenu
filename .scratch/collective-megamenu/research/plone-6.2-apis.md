# Plone 6.2 API constraints for `collective.megamenu`

Research for [ticket 01](../issues/01-plone-6.2-api-constraints.md). Baseline: Plone 6.2.2, `plone.schema` 3.0.0, `plone.app.z3cform` 5.0.2, `plone.app.layout` 6.0.2, `plonetheme.barceloneta` 4.1.1, `plone.staticresources` 3.0.9, `plone.app.uuid` 3.0.0.

Sources are linked at the end of each section.

## 1. `plone.schema.JSONField`

Import and constructor:

```python
from plone.schema import JSONField

menu = JSONField(
    title="Menu",
    required=False,
    schema="""{
      "type": "object",
      "properties": {
        "version": {"type": "integer"},
        "items": {"type": "array"}
      },
      "required": ["version", "items"]
    }""",
)
```

Key facts:

- `JSONField.schema` is a **JSON Schema string**, not a Zope interface.
- The stored value is a native Python `dict`/`list`, not a JSON string.
- `plone.schema` is a transitive dependency of `Products.CMFPlone` 6.2, but the addon should declare `plone.schema>=3.0.0` explicitly.
- `JSONField._validate()` runs `jsonschema.validate(value, self.json_schema)` and converts failures to `zope.schema.interfaces.WrongContainedType`, which z3c.form renders as a field error.
- Malformed JSON that is not valid JSON and not a Python-literal representation can raise a lower-level exception; test the actual error path.

Classic UI widget resolution:

- `plone.schema` registers `JSONWidget` (a `TextAreaWidget`) for `IJSONField` + `plone.schema.interfaces.IFormLayer`.
- `plone.app.z3cform` registers its own `TextAreaFieldWidget` for `IJSONField` + `IPloneFormLayer`. `IPloneFormLayer` is more specific, so this is the widget Classic UI actually uses.
- The `JSONDataConverter` is registered for `IJSONField` + `IWidget`; it serializes with `json.dumps(value, indent=1)` and deserializes with `field.fromUnicode()`. The round-trip is a native Python value.
- To replace the widget, register an adapter for `IJSONField` + `IPloneFormLayer` (or a more specific addon layer), e.g.:

```xml
<adapter
    factory=".widgets.MenuFieldWidget"
    for="plone.schema.jsonfield.IJSONField
         plone.app.z3cform.interfaces.IPloneFormLayer"
    />
```

- `plone.autoform.directives.widget("menu", MenuWidget)` can also be used, but the layer-specific registration is what beats the core Classic UI widget.

Sources:

- <https://github.com/plone/plone.schema/blob/3.0.0/src/plone/schema/jsonfield.py>
- <https://github.com/plone/plone.schema/blob/3.0.0/src/plone/schema/browser/jsonfield.py>
- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets.zcml>
- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/interfaces.py>

## 2. Behaviors on Plone Site, Folder, and LRF

The Plone Site root is a Dexterity container (`plone.dexterity.content.Container`) and is behavior-assignable through `DexterityBehaviorAssignable` (adapter for `IDexterityContent`). Its FTI is named `Plone Site`.

Enable a behavior through the FTI `behaviors` property with `purge="false"` so core behaviors survive:

```text
profiles/default/types/Plone_Site.xml
profiles/default/types/Folder.xml
profiles/default/types/LRF.xml
```

```xml
<?xml version="1.0"?>
<object name="Folder" meta_type="Dexterity FTI">
  <property name="behaviors" purge="false">
    <element value="collective.megamenu.behavior" />
  </property>
</object>
```

Behavior registration:

```xml
<plone:behavior
    name="collective.megamenu.behavior"
    title="Editable menu"
    description="A configurable menu tree"
    provides=".interfaces.IEditableMenu"
    />
```

The behavior interface should be a form-field provider:

```python
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider


@provider(IFormFieldProvider)
class IEditableMenu(model.Schema): ...
```

`LRF` is the Language Root Folder type from `plone.app.multilingual` (`plone/app/multilingual/profiles/default/types/LRF.xml`). It is not provided by `Products.CMFPlone` or `plone.app.contenttypes`. Enabling the behavior on `LRF` must therefore be conditional on PAM being installed. See [ticket 02](../issues/02-conditional-lrf-registration.md).

Gotcha: the site root is behavior-assignable, but it is not normally edited through the ordinary content edit tab. The user reports that the standard `@@edit` form does expose behavior fields on the site root; verify this in the first implementation spike. If not, a dedicated edit view is the fallback.

Sources:

- <https://github.com/plone/Products.CMFPlone/blob/6.2.x/src/Products/CMFPlone/Portal.py>
- <https://github.com/plone/plone.dexterity/blob/master/src/plone/dexterity/behavior.py>
- <https://github.com/plone/plone.dexterity/blob/master/src/plone/dexterity/configure.zcml>
- <https://github.com/plone/Products.CMFPlone/blob/6.2.x/src/Products/CMFPlone/profiles/default/types/Plone_Site.xml>
- <https://github.com/plone/plone.app.multilingual/blob/master/src/plone/app/multilingual/profiles/default/types/LRF.xml>
- <https://6.docs.plone.org/backend/behaviors.html>

## 3. Classic UI main navigation

Plone 6.2 registration:

| Item | Value |
| --- | --- |
| Viewlet name | `plone.global_sections` |
| Class | `plone.app.layout.viewlets.common.GlobalSectionsViewlet` |
| Template | `plone.app.layout.viewlets.sections.pt` |
| Manager interface | `plone.app.layout.viewlets.interfaces.IMainNavigation` |
| Manager name | `plone.mainnavigation` |
| Permission | `zope2.View` |

Recommended replacement: subclass `GlobalSectionsViewlet`, override the navigation rendering, and re-register the same viewlet name/manager on the addon browser layer.

```xml
<browser:viewlet
    name="plone.global_sections"
    manager="plone.app.layout.viewlets.interfaces.IMainNavigation"
    class=".viewlets.MegaMenuViewlet"
    layer="collective.megamenu.interfaces.IMegaMenuLayer"
    permission="zope2.View"
    />
```

This preserves ordering, `@@manage-viewlets`, and the original name. The core viewlet's `render_globalnav()` builds the tree in Python, so a pure template override only changes the wrapper; subclassing is needed for logic changes.

Barceloneta 4.1.1 mobile contract:

- The theme's offcanvas contains `ul#portal-globalnav`; the visible toggle is `.navbar-toggler` with `data-bs-toggle="offcanvas"` and `data-bs-target="#offcanvasNavbar"`.
- A replacement must preserve:
  - `ul.navbar-nav#portal-globalnav`
  - `li.nav-item`
  - `a.nav-link`
  - `has_subtree` on a parent `li`
  - `dropdown has_subtree` on a nested `ul`
  - the mobile CSS-only opener: an `input.opener` plus a `label` with `role="button"` and an `aria-label`
  - `pat-navigationmarker` on the surrounding nav/wrapper
  - active/in-path classes such as `selected`, `current`, `inPath`, `active`
- Without the opener checkbox/label pair, submenus stay hidden on mobile.
- If the viewlet replaces only the `ul` contents, the theme's offcanvas and Bootstrap JS continue to work.

Sources:

- <https://github.com/plone/plone.app.layout/blob/6.0.2/src/plone/app/layout/viewlets/configure.zcml>
- <https://github.com/plone/plone.app.layout/blob/6.0.2/src/plone/app/layout/viewlets/sections.pt>
- <https://github.com/plone/plonetheme.barceloneta/blob/4.1.1/src/plonetheme/barceloneta/theme/index.html>
- <https://github.com/plone/plonetheme.barceloneta/blob/4.1.1/src/plonetheme/barceloneta/theme/css/barceloneta.css>
- <https://github.com/plone/mockup/blob/master/src/pat/navigationmarker/navigationmarker.js>
- <https://6.docs.plone.org/classic-ui/viewlets.html>

## 4. Internal links

Resolution helpers:

```python
from plone.app.uuid.utils import uuidToObject, uuidToURL
```

- `uuidToURL(uid)` uses `portal_catalog.unrestrictedSearchResults(UID=uid)` and returns `brain.getURL()` or `None`. It does **not** check View permission.
- `uuidToObject(uid)` resolves the physical path and uses `restrictedTraverse` for the final object, so View permission is checked.
- `plone.api.content.get(UID=uid)` delegates to `uuidToObject`.
- `@@resolveuid` (`plone.outputfilters.browser.resolveuid.ResolveUIDView`) redirects with HTTP 301 to `/resolveuid/<uid>` and raises NotFound for a missing UID.
- For permission filtering, use `uuidToObject` (or `api.content.get`) and omit the leaf when it returns `None`.
- A raw UID inside a JSON blob is not a relation; Plone's link integrity does not track it automatically. That is acceptable for v1 (link integrity is out of scope), but it means deleted objects leave dangling UIDs.

Content browser reuse:

- `plone.app.z3cform.widgets.contentbrowser.ContentBrowserWidget` and `RelatedItemsWidget` are the standard Classic UI widgets.
- They normally adapt a `schema.Choice` field with `plone.app.vocabularies.Catalog` and store a semicolon-separated UID string.
- For a custom JSON widget, either subclass the content browser widget and provide a custom converter, or render a `Choice`-style input per node and let the Patternslib content browser pattern handle selection. See [ticket 03](../issues/03-content-browser-per-node.md) for the per-node integration research.

Recommended storage: raw UID, resolved at render time. `resolveuid/<uid>` is usable directly as an `href`, but a raw UID is cleaner for JSON and lets the renderer decide how to resolve and permission-check.

Sources:

- <https://github.com/plone/plone.app.uuid/blob/master/src/plone/app/uuid/utils.py>
- <https://github.com/plone/plone.outputfilters/blob/master/src/plone/outputfilters/browser/resolveuid.py>
- <https://github.com/plone/plone.api/blob/master/src/plone/api/content.py>
- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/contentbrowser.py>
- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/relateditems.py>
- <https://6.docs.plone.org/backend/relations.html>

## 5. Frontend assets

Register the addon bundle in `profiles/default/registry/bundles.xml`:

```xml
<?xml version="1.0"?>
<registry>
  <records
      interface="plone.base.interfaces.IBundleRegistry"
      prefix="plone.bundles/collective.megamenu">
    <value key="enabled">True</value>
    <value key="jscompilation">++plone++collective.megamenu/bundles/collective.megamenu-remote.min.js</value>
    <value key="csscompilation">++plone++collective.megamenu/bundles/collective.megamenu.min.css</value>
    <value key="depends">plone</value>
    <value key="load_async">False</value>
    <value key="load_defer">False</value>
  </records>
</registry>
```

- Static files live under `browser/static/bundles/` and are served as `++plone++collective.megamenu/...`.
- `plone.staticresources` already ships Patternslib in the `plone` bundle, so the addon does not need to ship its own copy at runtime.
- The addon's `package.json` should still declare `@patternslib/patternslib` (and usually `@plone/mockup`) so the webpack/module-federation build can share the modules.
- After changing `bundles.xml`, reapply the addon profile or add an upgrade step; a restart alone does not re-import registry XML.
- The standard `plonecli add mockup_pattern` scaffold is the recommended build setup.

Sources:

- <https://6.docs.plone.org/classic-ui/static-resources.html>
- <https://github.com/plone/plone.base/blob/master/src/plone/base/interfaces/resources.py>
- <https://github.com/plone/plone.staticresources/blob/3.0.9/src/plone/staticresources/profiles/default/registry/bundles.xml>
- <https://github.com/plone/bobtemplates.plone/tree/main/bobtemplates/plone/mockup_pattern>
- <https://6.docs.plone.org/classic-ui/mockup.html>

## 6. Prior art

`collective.editablemenu` by RedTurtle:

- PyPI 3.0.3, released 2026-06-23; Plone 6 compatible; GPLv2.
- Repository: <https://github.com/RedTurtle/collective.editablemenu>
- Features: manual entries, per-entry conditions, automatic submenu from a folder, static submenu from pages, multiple menu configurations bound to paths, custom JS events.
- Implementation: control panel is a React app using `redturtle.reactbundle`; configuration is JSON; not a behavior/JSONField design.
- Fit: closest prior art, useful as a reference for menu semantics and edge cases, but the requested data model and editor are different enough that a fresh implementation is justified.

Other related addons are old or partial: `quintagroup.megamenu` (Plone 4 era), `collective.navigation` (WIP 2019), `4teamwork/ftw.dropdownmenu` (2015), `ida/adi.dropdownmenu` (2016), `medialog.dropdownmenu` (GitHub only, 2024), `collective.navigationtoggle` (2020), `collective.megadrop` (2013), `collective.sidebar` (sidebar, not main nav), `kenmanheimer/volto-navigation-dropdown` (Volto only).

Naming: RedTurtle's PyPI project already owns the `collective.editablemenu` distribution name. The destination for this effort is `collective.megamenu`, which was free on PyPI and in the `collective` GitHub org when checked on 2026-10-17.

Sources:

- <https://pypi.org/project/collective.editablemenu/>
- <https://github.com/RedTurtle/collective.editablemenu>
- <https://github.com/collective/collective.navigation>
- <https://pypi.org/project/quintagroup.megamenu/>
- <https://github.com/espenmn/medialog.dropdownmenu>
- <https://github.com/RedTurtle/collective.navigationtoggle>

## 7. Open verification items

1. Does the standard `@@edit` form on the Plone Site root actually render behavior fields from the addon? The user reports yes; verify in the first implementation spike.
2. What is the safest conditional mechanism for the `LRF` behavior? See [ticket 02](../issues/02-conditional-lrf-registration.md).
3. How exactly should the content browser be initialized per node in the dynamic tree? See [ticket 03](../issues/03-content-browser-per-node.md).
4. Malformed JSON error paths: confirm the widget surfaces a friendly field error rather than a traceback.

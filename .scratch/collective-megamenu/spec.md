# collective.megamenu — Implementation Specification

Status: ready for implementation
Source of decisions: [wayfinder map](map.md) and its child tickets
Date: 2026-10-17
Target: Plone 6.2, Classic UI, Python 3.10+

## 1. Summary

`collective.megamenu` is a Plone 6.2 Classic UI addon that lets editors configure a custom menu on a Plone Site, an LRF, or a Folder. The menu is stored as JSON on the content object through a behavior. Editors build the menu with a tree widget in the standard edit form. A viewlet replaces Plone's main navigation with the menu from the nearest ancestor that has the behavior enabled.

The menu supports:

- infinitely nested folders, which are placeholders and not clickable;
- leaf links to internal Plone content or external URLs;
- internal links stored as raw Plone UIDs and resolved at render time;
- an optional CSS class and an optional CSS-class icon on every item;
- an “open in new tab” option on links;
- inline validation in the editor and permission-filtered rendering.

## 2. Goals and non-goals

### Goals

- A behavior that adds a JSON-backed `menu` field to Plone Site, LRF, and Folder.
- Nearest-ancestor menu resolution, with an untouched field inheriting and an explicitly saved empty menu acting as an explicit opt-out.
- A master-detail editor: tree on the left, inspector on the right.
- A viewlet that replaces `plone.global_sections` and preserves Barceloneta's mobile navigation contract.
- Internal link targets resolved with the current user's View permission.
- Conditional LRF support without a hard dependency on `plone.app.multilingual`.
- Tests for the schema, resolver, viewlet, and editor workflows.

### Non-goals

- Volto/headless support.
- Drag-and-drop reordering.
- Folder items with targets; folders are placeholders only.
- Image icons or a fixed icon vocabulary.
- Item descriptions, per-item visibility rules, translated menu labels.
- Caching or performance tuning.
- Automatic submenu generation from Plone folders.
- Link-integrity/backrefs or relation fields for menu links.
- Multiple menus per object.
- Fallback to Plone's default main navigation.
- Permission filtering of external links.
- A separate “no navigation at all” toggle; an empty menu already renders nothing.

## 3. Package identity and rename

The repository currently uses the distribution name `collective.editablemenu`, which is already RedTurtle's PyPI project. The addon must be renamed to **`collective.megamenu`** in the first implementation ticket.

Rename checklist:

- `pyproject.toml`: project name, URLs, classifiers if needed, package discovery.
- `src/collective/editablemenu/` → `src/collective/megamenu/`.
- All imports, ZCML `package=` references, profile names, browser layer, behavior name, i18n domain, bundle names, static paths, test imports.
- `Makefile`, `mx.ini`, `instance.yaml`, `.cookieplone.json`, `.github/`, `scripts/`, `docs/`, `README.md`, `CHANGELOG.md`, `CONTRIBUTORS.md`.
- Distribution/profile names: `collective.megamenu`, `collective.megamenu:default`, `collective.megamenu:uninstall`.
- Browser layer: `collective.megamenu.interfaces.IBrowserLayer`.
- Behavior name: `collective.megamenu.menu`.
- Bundle: `plone.bundles/collective.megamenu`, served from `++plone++collective.megamenu/...`.
- Confirm `collective.megamenu` is still free on PyPI and in the `collective` GitHub org before release.

## 4. Domain model

See [GLOSSARY.md](../../GLOSSARY.md) for the terms. In short:

- A **menu** is an ordered tree of menu items.
- A **menu item** is a folder item or a link item.
- A **folder item** is a placeholder that groups children. It is not clickable and has no target.
- A **link item** is a leaf with exactly one target: an internal Plone object (raw UID) or an external URL.
- The **nearest ancestor** with the behavior enabled supplies the menu. An unset field (`None`) means inherit; an explicitly saved empty menu is an **explicit opt-out** and renders no menu.

### Stored value

Native JSON (a Python `dict`), not a JSON string:

```json
{
  "version": 1,
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "type": "folder",
      "title": "Products",
      "css_class": "nav-products",
      "icon": "bi bi-box",
      "children": [
        {
          "id": "22222222-2222-4222-8222-222222222222",
          "type": "link",
          "title": "Product A",
          "css_class": "",
          "icon": "bi bi-file-earmark",
          "internal_uid": "e5f6…",
          "external_url": "",
          "open_in_new_tab": false
        }
      ]
    }
  ]
}
```

Rules:

- `id` is a UUID4 string, unique across the tree.
- `type` is `folder` or `link`.
- Folder items have `children`; links have exactly one target and no `children`.
- `title` is required, trimmed, max 200 characters.
- `css_class` and `icon` are optional CSS class lists, max 200 characters.
- `internal_uid` is a raw Plone UID, max 64 characters.
- `external_url` is max 2048 characters and uses `http`, `https`, `mailto`, or `tel`.
- `open_in_new_tab` is a boolean on links only.
- The field value is `None` when no menu has been configured; `None` means inherit.
- `items` may be empty; an explicitly saved empty menu is valid and means explicit opt-out.
- Empty folder items are valid in storage but are omitted from the rendered menu.
- Duplicate titles are allowed.

## 5. Behavior and field

### Interface

Create `IEditableMenu` in `interfaces.py` as a form-field provider:

```python
from plone.autoform.interfaces import IFormFieldProvider
from plone.schema import JSONField
from plone.supermodel import model
from zope.interface import provider
from zope.i18nmessageid import MessageFactory

_ = MessageFactory("collective.megamenu")


@provider(IFormFieldProvider)
class IEditableMenu(model.Schema):
    model.fieldset(
        "megamenu",
        label=_("Mega menu"),
        fields=["menu"],
    )

    menu = JSONField(
        title=_("Menu"),
        description=_(
            "Custom menu for this folder and its descendants. "
            "Leave unset to inherit the nearest ancestor's menu."
        ),
        required=False,
        schema=MENU_JSON_SCHEMA,
    )
```

- Put the schema string in a dedicated module (`schema.py`) and import it. The asset is [research/menu-schema.json](research/menu-schema.json).
- `plone.schema>=3.0.0` must be declared in `pyproject.toml`.
- The `menu` field lives in its own `megamenu` fieldset, labelled **Mega menu**, so the edit form gets a dedicated tab.
- Do not set a mutable default. The field default is `None`, which means inherit.

### Registration

```xml
<configure xmlns:plone="http://namespaces.plone.org/plone">
  <plone:behavior
      name="collective.megamenu.menu"
      title="Editable menu"
      description="A configurable menu tree."
      provides=".interfaces.IEditableMenu"
      />
</configure>
```

Enable it on the target types through their FTIs with `purge="false"`:

- `profiles/default/types/Plone_Site.xml`
- `profiles/default/types/Folder.xml`
- `profiles/default/types/LRF.xml` (conditional; see section 8)

Do not list `LRF` in `types.xml`. GenericSetup only imports FTIs that already exist; when PAM is absent the `types/LRF.xml` file is silently skipped.

### Site-root editing

The standard `@@edit` form is expected to expose behavior fields on the Plone Site root. Verify this in an acceptance test. If it does not, add a dedicated edit view for the site root as a follow-up; do not silently introduce a control panel.

## 6. Menu resolution

Create a resolver utility, for example `get_menu(context)` in `menu.py`.

Algorithm:

1. Start at the current context and walk up the acquisition chain to the Plone Site root, including the current object.
2. For each object, check whether the `IEditableMenu` behavior is enabled using the behavior-assignable adapter, not `providedBy` on the object.
3. Read the object's `menu` value:
   - if it is `None`, the object does not configure a menu; continue up the chain;
   - if it is an explicitly saved empty menu (`{"version": 1, "items": []}`), it is an explicit opt-out; stop and return `None`;
   - if it has items, it wins; return the menu and the owning object.
4. If no object configures a menu, return `None`.

The viewlet renders nothing when the resolver returns `None`. There is no fallback to Plone's default navigation.

Permission edge case: do not add an extra View check on the menu-owning folder. If the current context is viewable, the menu is rendered and each internal link is permission-filtered individually. If reading the behavior value raises an authorization error, treat it as absent and continue up the chain.

No caching in v1.

## 7. Viewlet and main navigation replacement

### Registration

Subclass `plone.app.layout.viewlets.common.GlobalSectionsViewlet` and re-register the same viewlet name and manager on the addon browser layer:

```xml
<browser:viewlet
    name="plone.global_sections"
    manager="plone.app.layout.viewlets.interfaces.IMainNavigation"
    class=".viewlets.MegaMenuViewlet"
    layer="collective.megamenu.interfaces.IBrowserLayer"
    permission="zope2.View"
    />
```

This preserves ordering, `@@manage-viewlets`, and the core contract. Override the navigation rendering in the class; do not only override `sections.pt`, because the core builds the tree in Python.

### Markup contract

Preserve the Barceloneta mobile offcanvas contract:

- `ul.navbar-nav#portal-globalnav`
- `li.nav-item`
- `a.nav-link` for links; `span.nav-link` for folder labels
- `has_subtree` on a parent `li`
- `dropdown has_subtree` on a nested `ul`
- the mobile opener pair: `<input class="opener">` plus `<label role="button" aria-label="…">`
- `pat-navigationmarker` on the nav wrapper
- active/in-path classes: `selected`, `current`, `inPath`, `active`, added by the theme's `pat-navigationmarker` pattern on the surrounding nav; the viewlet preserves that wrapper

Minimal shape:

```html
<nav class="navbar navbar-expand-lg pat-navigationmarker" aria-label="Main navigation">
  <ul class="navbar-nav" id="portal-globalnav">
    <li class="nav-item has_subtree nav-products">
      <span class="nav-link">
        <i class="bi bi-box" aria-hidden="true"></i>
        Products
      </span>
      <input id="navitem-1111" type="checkbox" class="opener">
      <label for="navitem-1111" role="button" aria-label="Products"></label>
      <ul class="dropdown has_subtree">
        <li class="nav-item">
          <a class="nav-link" href="/plone/products/product-a">
            <i class="bi bi-file-earmark" aria-hidden="true"></i>
            Product A
          </a>
        </li>
      </ul>
    </li>
  </ul>
</nav>
```

Notes:

- Add the item's `css_class` to the `li`, alongside the viewlet's own classes.
- Render the icon only when it is non-empty; always escape it.
- Folders with children get the opener pair. Folders without children are omitted at render time.
- Do not claim modal behavior for the mobile menu; rely on Barceloneta's CSS-only opener.

### Link rendering and filtering

- Internal link: resolve `internal_uid` with `uuidToCatalogBrain`, get the object, and check `api.user.has_permission("View", obj=obj)`. If the brain or object is missing, or the check fails, omit the leaf. Use `obj.absolute_url()` for the `href`. This avoids `uuidToObject`'s site-root edge case, where the portal UID can resolve to a wrapper without `absolute_url`.
- External link: render the URL. The scheme was validated at save time; escape the value.
- If `open_in_new_tab` is true, add `target="_blank"` and `rel="noopener noreferrer"`.
- After filtering, omit any folder whose visible children list is empty.
- If the whole filtered tree is empty, render nothing.
- Do not use `unrestrictedSearchResults` for rendering.

## 8. LRF support

`LRF` is the Language Root Folder type from `plone.app.multilingual` (PAM). It is not a core type.

- Ship `profiles/default/types/LRF.xml` with `<property name="behaviors" purge="false">` and the behavior.
- Do not list `LRF` in `types.xml`.
- Register the behavior unconditionally and never import PAM.
- Use the addon profile's **`post_handler`**, `setuphandlers.add_behavior_to_lrf`, instead of a `ProfileImportedEvent` subscriber. It checks the `LRF` FTI and appends the behavior if missing.
- This covers PAM installed before the addon and site creation when both are selected. If PAM is installed after the addon, reapply the addon profile; there is no automatic PAM-profile subscription.
- The post_handler is idempotent; the declarative `types/LRF.xml` and the handler may both add the behavior without creating duplicates.
- Uninstall: `profiles/uninstall/types/LRF.xml` with `<element value="collective.megamenu.menu" remove="true"/>` and `purge="false"`; omitting `purge="false"` would wipe PAM's behaviors.
- No upgrade step is needed for the initial release. If LRF support is added after a release, use `<genericsetup:upgradeDepends import_steps="types"/>`.

Test without PAM, with PAM installed before the addon, and with PAM installed after the addon followed by reapplying the addon profile.

## 9. Editor widget

### Layout

Use the chosen **master-detail** layout (prototype Variant A):

- Left pane: menu tree with a toolbar containing “Add folder” and “Add link”.
- Right pane: inspector for the selected node.
- Tree row: expand/collapse toggle (folders), icon, title, type badge, target summary, error dot, and row actions (add folder child, add link child, move up, move down, delete).
- Inspector: title, CSS class, icon with preview, target editor for links, and actions (add child, move up, move down, delete).
- New items: default title “Untitled folder” / “Untitled link”, default icon, selected and focused.
- Delete folder with children: confirm; delete the node and its descendants; select the nearest sibling or parent.
- Move up/down within siblings.
- Expand/collapse state is UI-only.
- Empty state: centered card with “Add folder” and “Add link”. When the field is unset (`None`), the card also says the nearest ancestor menu is inherited.
- “Use inherited menu” action: shown when the field has a value; it clears the field to `None`. Deleting the last item instead leaves an explicitly saved empty menu, which opts out.

Do not implement drag-and-drop.

### Fields

- `title`: text input, required, trimmed, max 200.
- `css_class`: text input, optional; added to the `li` at render time.
- `icon`: text input for a CSS class list (for example `bi bi-house`), with a live `<i>` preview.
- Target editor, links only:
  - radio: internal / external;
  - internal: selected target summary + “Choose…” + “Clear”;
  - external: URL text input;
  - checkbox: open in new tab.
- Folders show a help note: “Folders are placeholders and are not clickable.”
- Empty folders show a non-blocking note: “This folder has no children and will not appear in the menu.”

### Internal link picker

Follow [research/content-browser-per-node.md](research/content-browser-per-node.md):

- One hidden `.pat-contentbrowser` input for the selected link node in the master-detail inspector, unique id, `maximumSelectionSize: 1`. The picker is re-initialized when the selection changes.
- Generate options once in Python with `get_contentbrowser_options()`; set `basePath` to the site root for site-wide menus.
- Prefill the input's `value` with `internal_uid` before initialization.
- Initialize new nodes with scoped `registry.scan(node, ["contentbrowser"])`.
- Only one picker active at a time; destroy the previous one.
- On delete: `unmount(pattern.component_content_browser)`, then `pattern.destroy()`, then remove the wrapper. `BasePattern.destroy()` alone leaks the Svelte app.
- Read the UID from the input's `change` event; guard against the mount-time empty change so rendering does not erase a dangling UID.
- Restore focus to the node's “Choose…” button after selection or cancellation.
- Do not use `RelatedItemsWidget`.

The stored menu title is separate from the target's title. The inspector may display the target title/path as secondary information, but it must not overwrite a user-edited menu title. Exception: when a new link still has the default title, picking a target may prefill the title.

### Client-side validation

- Mirror the validation table in section 10.
- Show inline errors in the inspector and error dots in the tree.
- On Save, validate the whole tree, prevent submission if invalid, select and focus the first invalid node.
- Trim titles and lowercase external URL schemes before serialization.
- Keep a fixture suite that runs the same valid/invalid samples through the JS validator and the server validator.

### Server-side validation

- The field's JSON Schema enforces the structural rules.
- `validate_menu(value)` enforces the semantic rules using the current site and security context: duplicate IDs, folder/link field exclusivity, title/CSS/icon limits, external URL syntax, and internal UID resolution with the current user's permissions.
- Register `MenuValidator` (a `z3c.form.validator.SimpleFieldValidator`) with `WidgetValidatorDiscriminators` for `IEditableMenu["menu"]`. It runs `validate_menu` before the field's JSON Schema and raises `zope.interface.Invalid` with the newline-separated path-aware messages.
- Internal UID checks use the shared `resolve_internal_target` helper (catalog brain, `getObject`, then an explicit `View` permission check), the same helper the viewlet uses.
- Raise `zope.interface.Invalid` with path-aware messages, for example `Products → Product A: Choose exactly one target: internal or external.`
- Server errors appear as one field-level message list under the Menu field; they are not mapped back to individual nodes.
- A raw UID in JSON is not a relation; deleted targets are caught at save time and again at render time.

### Frontend bundle

- Implement the editor as a Patternslib pattern (for example `megamenu`) triggered on the widget root.
- Register the bundle in `profiles/default/registry/bundles.xml` with `interface="plone.base.interfaces.IBundleRegistry"`, prefix `plone.bundles/collective.megamenu`, `depends=plone`.
- Static output lives under `browser/static/bundles/` and is served from `++plone++collective.megamenu/...`.
- Declare `@patternslib/patternslib`, `@plone/mockup`, and `svelte` in the addon's `package.json`. Pin `svelte` to the version shared by the target Plone bundle (5.57.0 in Plone 6.2) to avoid a module-federation version warning.
- Use the standard `plonecli add mockup_pattern`-style webpack/module-federation scaffold at the repository root. Build with `npm install && npm run build`; the output goes to `src/collective/megamenu/browser/static/bundles/`.
- The widget renders one hidden textarea with the submitted JSON. The core `JSONDataConverter` continues to handle serialization; no custom converter is needed.
- Do not render the raw JSON preview in production; it was a prototype aid.
- Register the widget adapter and widget template for the addon's `IBrowserLayer`, not directly for `IPloneFormLayer`. `IBrowserLayer` extends `IPloneFormLayer`; the more specific registration wins over the core JSON textarea widget without causing a ZCML configuration conflict.
- Patternslib gives each pattern instance a `uuid` property. Do not name a pattern method `uuid`; use a distinct name such as `newId()`.

### Accessibility

- Use real `<button>` elements for every action.
- Use a nested list with `aria-expanded` on folder toggles; do not use `role="tree"` unless full tree keyboard navigation is implemented.
- Visible focus styles and a logical tab order.
- Label the picker button with the node title.
- Add an `aria-live="polite"` summary after a target is selected.
- Restore focus after the content browser closes.
- Document the content browser's upstream a11y gaps; do not replicate them.

## 10. JSON Schema and validation

The schema asset is [research/menu-schema.json](research/menu-schema.json). It is draft-07, uses `definitions` and recursive `$ref`s, and has separate `folderItem` / `linkItem` definitions so `additionalProperties: false` works at every level.

Key points:

- `jsonschema` does not enforce `format` without a format checker; UUIDs use an explicit regex.
- JSON Schema structural errors are generic; the semantic validator supplies readable path-aware messages.
- `version` must be `1`; unknown versions are rejected.
- `items` and `children` may be empty.
- Empty folders are valid in storage and omitted at render.

| Rule | Enforcement | User-facing message |
| --- | --- | --- |
| Top-level shape, version, unknown fields | JSON Schema | Field-level server error with path |
| `version` is 1 | JSON Schema + server validator | “Unsupported menu version. Expected version 1.” |
| `items` is an array; may be empty | JSON Schema | — |
| `id` is a UUID, unique across the tree | JSON Schema + server validator | “Menu item IDs must be unique and valid UUIDs.” |
| `type` is `folder` or `link` | JSON Schema | “A menu item must be a folder or a link.” |
| `title` required, trimmed, max 200 | Client + server; JSON Schema for shape | “Title is required.” / “Use at most 200 characters.” |
| `css_class` optional, max 200, CSS class list | Client + server; JSON Schema for shape | “Use only letters, numbers, hyphens, and underscores, separated by single spaces.” |
| `icon` optional, max 200, CSS class list | Client + server; JSON Schema for shape | Same as CSS class |
| Folder has `children`; no target fields | JSON Schema + server validator | “A folder cannot have a target.” |
| Link has exactly one target; no `children` | JSON Schema + server validator | “Choose exactly one target: internal or external.” / “A link cannot have children.” |
| `internal_uid` non-empty, max 64, resolves and is viewable | Server (client checks only empty/whitespace; existence and visibility are resolved server-side) | “The selected internal target no longer exists or is not visible to you.” |
| `external_url` max 2048, allowed scheme, valid host/recipient | Client + server | “Use an http(s), mailto, or tel URL.” |
| `open_in_new_tab` is boolean | JSON Schema | — |
| Unknown property | JSON Schema + server validator | “Unknown field: `<name>`.” |
| Empty folder | Allowed in storage | Non-blocking editor warning |
| Duplicate titles | Allowed | — |
| Unset menu (`None`) | Allowed | Inherits from the nearest ancestor |
| Explicitly saved empty menu | Allowed | Opts out and renders no menu |

Client-side errors appear inline in the inspector and as error dots in the tree. Server-side errors are a newline-separated list under the Menu field, with path segments built from item titles (`Untitled item #N` for untitled items).

## 11. Permissions and security

- Viewlet permission: `zope2.View`.
- Editing uses the standard edit permission of the content type; site-root editing uses the standard `@@edit` permissions.
- Internal UIDs are resolved through the catalog and checked with `api.user.has_permission("View", obj=obj)`; inaccessible or missing leaves are omitted.
- External URLs are scheme-allowlisted and HTML-escaped. New-tab links use `rel="noopener noreferrer"`.
- Titles, CSS classes, and icons are plain text and escaped in HTML/attributes.
- The JSON is stored as a native dict; no HTML rendering.
- The standard edit form handles CSRF. If a custom write endpoint is added, protect it with `plone.protect`.
- The content browser's `@@getVocabulary` requires `zope2.View`; its prefilled-UID POST is read-only and needs no CSRF token.
- Do not use `unrestrictedSearchResults` for rendering or validation.

## 12. Testing and acceptance

### pytest-plone

- Behavior is installed on Folder and Plone Site; the field default is `None` (inherit).
- LRF behavior is installed only when PAM is present; test PAM before/after the addon.
- JSON Schema accepts the valid fixtures and rejects the invalid fixtures.
- Server validator covers duplicate IDs, titles, CSS/icon patterns, URL schemes, folder/link exclusivity, and UID resolution/permission failures.
- Resolver covers nearest ancestor, unset inheritance, explicit empty opt-out, no behavior, site root, LRF, and inheritance.
- Viewlet covers: custom menu replaces the main nav; no menu renders nothing; an explicit empty menu renders nothing; inaccessible internal leaves are omitted; empty folders are omitted; external links always render; icons/CSS classes/open-in-new-tab render correctly; mobile markup contract is present.
- Site root `@@edit` exposes the Menu field and saves the JSON.

### Robot / browser

- An editor can add a folder, add a link, add a child, move up/down, delete, and save.
- The internal link picker opens, selects a target, and survives a delete/re-add cycle without leaking the Svelte app.
- Client-side validation blocks an invalid save and focuses the first invalid node.
- The Barceloneta mobile toggle and submenu openers still work with the replaced navigation.

### Acceptance criteria

- A fresh install shows no main navigation until a menu is configured. This is intentional; document it in the README.
- A menu configured on the site root is used site-wide. A section folder with a non-empty menu overrides it; an untouched folder inherits it; an explicitly saved empty menu on a folder suppresses it.
- An internal link to an object the current user cannot view is absent from the rendered menu.
- A folder with no visible children is absent.
- An external link with a disallowed scheme cannot be saved.
- The menu is stored as native JSON and round-trips through the edit form unchanged except for normalisation (trimmed titles, lowercased URL schemes).

## 13. Implementation ticket breakdown

Each ticket should be a tracer bullet with tests. The order respects dependencies.

1. **Rename and scaffold** — rename the package to `collective.megamenu`, update metadata/ZCML/profiles/docs/CI, add `plone.schema` dependency, add the pattern/webpack scaffold. Depends on: nothing.
2. **Behavior and schema** — add `IEditableMenu`, the JSON Schema string, the field, behavior registration, and enable it on Folder and Plone Site. Depends on: 1.
3. **Server validation** — add the context-aware `validate_menu` validator and tests. Depends on: 2.
4. **Menu resolver** — add `get_menu(context)` and tests. Depends on: 2.
5. **Viewlet** — replace `plone.global_sections`, render the Barceloneta contract, filter links, omit empty folders, and test. Depends on: 4.
6. **Widget scaffold** — custom `IJSONField`/`IBrowserLayer` widget, template, hidden textarea, content browser options. Depends on: 2.
7. **Tree editor** — Variant A master-detail editor, add/delete/move, fields, serialization, client validation, bundle. Depends on: 6, 3.
8. **Content browser picker** — per-node `pat-contentbrowser` integration, scan/unmount lifecycle. Depends on: 7.
9. **LRF support** — conditional FTI registration and profile post_handler. Depends on: 2.
10. **Hardening and release** — i18n, docs, README warning about no default navigation, Robot tests, changelog, release metadata. Depends on: 5, 8, 9.

## 14. Risks and assumptions

- The standard `@@edit` form exposes behavior fields on the Plone Site root. Verify early; the fallback is a dedicated edit view.
- The content browser is a single-picker component; per-node lifecycle and Svelte cleanup are the main technical risk. The research recommends the pattern but flags performance and accessibility issues.
- Barceloneta's mobile offcanvas expects specific markup. Verify in a real browser; the research records the contract.
- The addon replaces the main navigation and renders nothing when no menu is configured. This is intentional and must be documented.
- Raw UIDs in JSON are not relations; deletion/backrefs are not tracked. Save-time and render-time checks cover dead targets but not link integrity.
- `jsonschema` draft-07 support was verified with the installed version; keep the schema free of newer draft features.
- LRF support depends on PAM's FTI shape; the addon profile's post_handler is the chosen approach. PAM installed after the addon requires reapplying the addon profile.

## 15. References

- [Wayfinder map](map.md)
- [Plone 6.2 API research](research/plone-6.2-apis.md)
- [Conditional LRF registration](research/conditional-lrf-registration.md)
- [Content browser per-node integration](research/content-browser-per-node.md)
- [JSON Schema asset](research/menu-schema.json)
- [Glossary](../../GLOSSARY.md)
- Plone 6.2 docs: <https://6.docs.plone.org/>
- `plone.schema` source: <https://github.com/plone/plone.schema>
- `plone.app.layout` main navigation: <https://github.com/plone/plone.app.layout>
- Barceloneta: <https://github.com/plone/plonetheme.barceloneta>
- Mockup content browser: <https://github.com/plone/mockup>

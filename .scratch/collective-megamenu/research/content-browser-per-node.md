# Content browser integration for per-node internal links

Research for [ticket 03](../issues/03-content-browser-per-node.md). Baseline: Plone 6.2.2, `plone.app.z3cform` 5.0.2, `plone.app.content` 5.0.0, `plone.staticresources` 3.0.9, `@plone/mockup` 5.6.14, `@patternslib/patternslib` 9.11.0.

Sources are linked at the end of each section.

## 0. Recommendation

Use the modern Patternslib **`contentbrowser`** pattern, not `RelatedItemsWidget`, and not `ContentBrowserWidget` as the JSON field widget.

- Keep the addon's custom JSON field widget (`MenuWidget`, registered for `IJSONField` + `IPloneFormLayer`). It renders the inline tree plus one hidden input per link node with class `pat-contentbrowser`.
- Generate the pattern options once in Python with `get_contentbrowser_options()` from `plone.app.z3cform.widgets.contentbrowser`, then attach the JSON to each node input as `data-pat-contentbrowser`.
- Set the input's `value` to the node's existing UID before initializing the pattern, and read the UID back from the input's `change` event.
- Initialize new node inputs with a scoped `registry.scan(node, ["contentbrowser"])`. On delete, call Svelte's `unmount()`, then the pattern's `destroy()`, then remove the wrapper. `BasePattern.destroy()` only removes the marker; it does **not** unmount the Svelte app.
- Keep one hidden textarea carrying the whole JSON document. The existing `JSONDataConverter` then continues to work; no custom Python converter is required.
- Fall back to a UID autocomplete (`AjaxSelectWidget` / `pat-select2`) only if the per-node Svelte lifecycle proves too expensive or fragile. Do not use `RelatedItemsWidget`.

The main risks are lifecycle management and accessibility, not the backend. The content browser was designed as a single field-level picker, not as N independent pickers inside a dynamic tree.

## 1. Which widget and pattern to instantiate

| Option | Pattern | Fit for this addon |
| --- | --- | --- |
| `ContentBrowserWidget` | `contentbrowser` (Svelte) | The modern Classic UI picker. It is registered by default for `IRelationChoice`, `IRelationList`, and `IChoice` with a `CatalogSource`. It adapts a `Choice`/`Collection` field, so it cannot be the widget for the JSON field itself. Reuse its option builder. |
| `RelatedItemsWidget` | `relateditems` (legacy select2/jQuery) | Not recommended. It still exists and has tests, but it is no longer the default registration for relation fields. Its input template registration is display-only and the class is kept for backwards compatibility. |
| Custom subclass of `ContentBrowserWidget` | `contentbrowser` | Only useful if the addon implements each link target as a real z3c.form subwidget. That brings z3c.form naming, extraction, and conversion machinery that the inline tree does not need. A custom JSON widget that embeds raw pattern inputs is simpler. |

`ContentBrowserWidget` and `RelatedItemsWidget` assume a `Choice` or `Collection` field and store a semicolon-separated UID string. `RelatedItemsWidget` additionally depends on the old `relateditems` select2 pattern. The JSON field is a `dict`, and the tree needs a picker per node, so neither widget can be dropped in unchanged.

Relevant source:

- `ContentBrowserWidget` is registered for relation and catalog-choice fields in <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets.zcml>
- `ContentBrowserWidget` implementation and `get_contentbrowser_options()` in <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/contentbrowser.py>
- `RelatedItemsWidget` implementation in <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/relateditems.py>
- Deprecated import aliases for `RelatedItemsWidget` in <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widget.py>

## 2. Required markup and pattern options

The pattern trigger is `.pat-contentbrowser`. It reads `data-pat-contentbrowser` as a JSON object. On init it hides the input and inserts a sibling `div.content-browser-wrapper` that hosts the Svelte application.

Minimal per-node markup:

```html
<div class="megamenu-picker">
  <input type="text"
         class="pat-contentbrowser"
         id="megamenu-picker-NODE_ID"
         value="EXISTING_UID_OR_EMPTY"
         data-pat-contentbrowser='{"vocabularyUrl": "...", "separator": ";", "maximumSelectionSize": 1}' />
</div>
```

Important: give every input a unique `id`, and do not give it a `name` that matches a form field. The pattern generates an id only when none exists, and the selected-items component looks the input up with `document.getElementById(fieldId)`. Duplicate ids after cloning a node break the wrong node. Inputs without a `name` are not submitted; the JSON textarea is the only submitted value.

`get_contentbrowser_options()` produces these keys:

| Key | Meaning | Notes for per-node use |
| --- | --- | --- |
| `vocabularyUrl` | JSON endpoint for browsing/searching | Required. Use `<site>/@@getVocabulary?name=plone.app.vocabularies.Catalog` (optionally `&field=menu`). Do not use `++widget++.../@@getSource` unless the input really belongs to a z3c.form widget. |
| `separator` | Value separator | `";"` by default. For a single selection the value is one UID. |
| `basePath` | Folder where browsing starts | Defaults to the edited object, or its parent if it is not folderish. For a site-wide menu, override it to the site root; otherwise each edit starts inside the current folder. |
| `rootPath` | Breadcrumb/search boundary | The Plone site path, not the navigation root. |
| `rootUrl` | Public site URL | Used to build submission/upload URLs. |
| `contextPath` | Path of the currently edited object | Emitted by the widget helper, but **ignored by mockup 5.6.14's contentbrowser**. It does not prevent selecting the object being edited. |
| `favorites` | List of `{title, path}` shortcuts | Emitted only when the default base path differs from the navigation root. |
| `initialValues` | `{uid: title}` map | Emitted by `get_contentbrowser_options()` when a value is passed, but **not read by the contentbrowser pattern**. It is a select2 option. Use the input's `value` or the `selection` option instead. |
| `maximumSelectionSize` | Selection limit | Set to `1` for a link target. |
| `mode` | `"browse"` or `"search"` | Default `"browse"`; the pattern switches to search when the user types. |
| `selectableTypes` | Portal types that may be selected | Optional; useful to exclude folders or non-linkable types. |
| `browseableTypes` | Folder types that may be opened | Optional. |
| `searchIndex` | Index used by the search box | Defaults to `SearchableText`. |
| `maxDepth` | Maximum breadcrumb columns | Defaults to `999`. |
| `attributes` | Metadata requested per result | The pattern's default includes `UID`, `Title`, `Description`, `portal_type`, `path`, `getURL`, `getIcon`, `is_folderish`, `review_state`, `created`, `modified`. |
| `recentlyUsed`, `recentlyUsedKey` | localStorage-backed recent items | Disabled by default in the Python helper. If enabled, use one stable key for the whole menu field so all nodes share the list. |
| `bSize` | Page size | Default `20` in the Svelte app; the Python helper does not set it. |

The parser accepts both camelCase options and dashed data attributes; the JSON object above is the normal form. The parser also defines `width`, `selection`, `query`, `upload`, `sortOn`, and `sortOrder`, though not all of them are consumed by every UI path.

Gotchas found in the 5.6.14 source:

- `initialValues` is only consumed by `pat-select2`, not by `pat-contentbrowser`.
- `contextPath` is stored in the config but never used by the browser. Enforce any self-link prohibition in the addon or server-side.
- `basePath` is a starting point, not a restriction. The browser can navigate up to `rootPath`.
- The pattern hides the input with `display: none`; style and focus the generated wrapper, not the input.

Sources:

- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/contentbrowser.py>
- <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/contentbrowser.js>
- <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/App.svelte>
- <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/SelectedItems.svelte>
- <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/ContentStore.js>
- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/templates/link_input.pt>
- <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/base.py>

## 3. Initializing nodes added after page load

`registry.scan()` is the supported way to initialize patterns on new DOM. It parses the data attribute, creates the pattern, and stores the instance on the element as `el["pattern-contentbrowser"]`.

```js
import registry from "@patternslib/patternslib/src/core/registry";

function initPicker(container, optionsJson) {
  const input = container.querySelector(".pat-contentbrowser");
  input.id = `megamenu-picker-${container.dataset.nodeId}`;
  input.value = container.dataset.internalUid || "";
  input.setAttribute("data-pat-contentbrowser", optionsJson);

  // Scope the scan to this subtree; do not rescan document.body.
  registry.scan(container, ["contentbrowser"]);
}
```

Initialization is asynchronous: the pattern constructor schedules `init()` with `setTimeout(..., 0)`. If code needs to act after initialization, listen for the bubbling `init.contentbrowser.patterns` event on the container, or instantiate the registered pattern directly and await `events.await_pattern_init(instance)`. Do not assume the instance exists immediately after `registry.scan()`.

Scoped scanning matters. Scanning `document.body` again is unnecessary and can re-walk the whole form. `scan` also filters elements inside `.disable-patterns`, `<pre>`, and `.cant-touch-this`.

### Cleanup on delete

This is the main trap. `BasePattern.destroy()` only deletes the pattern marker:

```js
destroy() {
    delete this.el[`pattern-${this.name}`];
}
```

It does not call Svelte's `unmount()`, does not remove the inserted `.content-browser-wrapper`, and does not remove event listeners created by Svelte actions. The contentbrowser pattern stores the mounted app as `this.component_content_browser`. Clean up explicitly:

```js
import { unmount } from "svelte";

async function destroyPicker(container) {
  const input = container.querySelector(".pat-contentbrowser");
  const pattern = input?.["pattern-contentbrowser"];

  if (pattern) {
    if (pattern.component_content_browser) {
      await unmount(pattern.component_content_browser);
    }
    pattern.destroy();
  }
  container.replaceChildren();
}
```

The addon bundle already depends on the `plone` bundle, which loads Svelte, so `import { unmount } from "svelte"` should resolve through the shared module-federation runtime. Declare `svelte` as a dependency in the addon's `package.json` alongside `@plone/mockup` and `@patternslib/patternslib`.

Deleting a node while its pattern is still initializing is a race: the constructor's `setTimeout` can still run and mount into a detached container. Either await initialization before allowing deletion, or mark the node as discarded and destroy again after the `init` event fires.

### Reordering and cloning

Moving an already initialized node in the DOM is safe; the pattern instance and wrapper move with it. Cloning an initialized node is not safe: `cloneNode()` copies the wrapper element but not the JavaScript property holding the pattern instance, and it copies the old id. Build new nodes from a `<template>` or strip `.content-browser-wrapper`, clear the id, and rescan.

### One picker at a time

The contentbrowser's keyboard helpers use global selectors (`document.querySelector(".levelColumns")`, `.levelColumn`, `.contentItem`). Two overlays open at once can scroll or focus the wrong one. Keep at most one picker active, or close/destroy the previous one before opening another. Because the pattern has no public "open" API, the practical approach is to let each node own a picker and destroy the previous node's picker when another opens.

Sources:

- `registry.scan()` and pattern lookup: <https://github.com/Patternslib/Patterns/blob/9.11.0/src/core/registry.js>
- async constructor and `destroy()`: <https://github.com/Patternslib/Patterns/blob/9.11.0/src/core/basepattern.js>
- contentbrowser init, wrapper insertion, mounted component: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/contentbrowser.js>
- `await_pattern_init`: <https://github.com/Patternslib/Patterns/blob/9.11.0/src/core/events.js>
- Svelte 5 `unmount()`: <https://github.com/sveltejs/svelte/blob/svelte@5.57.0/packages/svelte/src/internal/client/render.js>

## 4. Reading and prefilling the UID

The pattern writes the selection back into the hidden input as separator-joined UIDs and dispatches a `change` event:

```js
selectedItemsNode.value = selectedUids.join($config.separator);
selectedItemsNode.dispatchEvent(events.change_event());
```

For a single link target, read one UID:

```js
input.addEventListener("change", () => {
  const uid = input.value.split(";")[0] || null;
  container.dataset.internalUid = uid || "";
  serializeTree(); // write the whole model to the JSON textarea
});
```

Prefilling is done before initialization by setting `input.value` to the stored `internal_uid`. The selected-items component reads `config.selection` first, then falls back to the input's value, then fetches the item metadata (title, path, icon) from the vocabulary endpoint. `selection: ["<uid>"]` is an alternative, but setting the input value is what core does in `link_input.pt` and avoids duplicating the UID in two places.

### Mount-time change gotcha

`SelectedItems.svelte` dispatches a `change` event during its initial effect, even when the user has done nothing. If the stored UID is missing or not viewable, the fetch returns no item, the selected list becomes empty, and the effect writes an empty value back to the input. A naive `change` listener will therefore erase `internal_uid` merely by rendering the form, and will also mark the form dirty on load.

Guard the listener:

- Compare the incoming UID with the node's current UID and ignore no-op changes.
- Ignore programmatic changes until the user has interacted with the picker (track `click`/`keydown` in the container).
- Treat an empty value as a real clear only after interaction with the pattern's remove button.

### Showing the target title in the tree

The JSON model stores only the raw UID. The selected-item UI displays the target title inside the pattern's own DOM, but scraping `.selected-item .item-title` couples the tree to mockup internals. Better options:

- Show the user-edited menu item title in the tree, with the target UID or resolved path as secondary text.
- Resolve the UID once in JavaScript via `@@getVocabulary` (query by `UID`) and cache the title for display.
- Resolve titles server-side when rendering the view.

Never use the target title as the stored menu title; they are different concepts.

Sources:

- value write-back and change event: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/SelectedItems.svelte>
- initial selection fetch and ordering: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/utils.js>
- core input markup and value: <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/templates/link_input.pt>

## 5. Python, ZCML, and JS integration points

### Python widget

Reuse `get_contentbrowser_options()` rather than duplicating path and vocabulary logic. Compute the JSON once per widget render; the per-node input only varies by `value` and `id`.

```python
import json

from plone.app.z3cform.interfaces import ITextAreaWidget
from plone.app.z3cform.widgets.contentbrowser import get_contentbrowser_options
from plone.app.z3cform.widgets.text import TextAreaWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from zope.interface import implementer
from zope.interface import implementer_only


class IMenuWidget(ITextAreaWidget):
    """Marker for the menu tree widget template."""


@implementer_only(IMenuWidget)
class MenuWidget(TextAreaWidget):
    klass = "megamenu-widget"

    def contentbrowser_options_json(self):
        options = get_contentbrowser_options(
            self.context,
            "",  # initial values come from each node's input value
            ";",
            "plone.app.vocabularies.Catalog",
            "@@getVocabulary",
            field_name="menu",  # replace with the actual JSON field name
        )
        options["maximumSelectionSize"] = 1
        options["mode"] = "browse"
        # Optional: start browsing at the site root instead of the edited folder.
        # options["basePath"] = "/".join(
        #     self.context.portal_url.getPortalObject().getPhysicalPath()
        # )
        return json.dumps(options)


@implementer(IFieldWidget)
def MenuFieldWidget(field, request):
    return FieldWidget(field, MenuWidget(request))
```

Passing `field_name="menu"` appends `&field=menu` to the vocabulary URL. `VocabularyView` then consults the `IFieldPermissionChecker` for that field, or falls back to the vocabulary's default permission. If the checker cannot resolve the JSON field, omit `field_name` and rely on the catalog's View permission.

### ZCML

```xml
<configure xmlns="http://namespaces.zope.org/zope"
           xmlns:z3c="http://namespaces.zope.org/z3c">

  <adapter
      factory=".widgets.MenuFieldWidget"
      for="plone.schema.jsonfield.IJSONField
           plone.app.z3cform.interfaces.IPloneFormLayer"
      />

  <z3c:widgetTemplate
      widget=".widgets.IMenuWidget"
      template="templates/menu_input.pt"
      layer="plone.app.z3cform.interfaces.IPloneFormLayer"
      mode="input"
      />

</configure>
```

Registering for `IJSONField` + `IPloneFormLayer` overrides the core Classic UI textarea widget. `plone.autoform.directives.widget("menu", MenuFieldWidget)` is an alternative, but the layer-specific adapter is what consistently wins for the behavior field.

### Template

The template must render:

1. the single submitted textarea with `name="${view/name}"` and the JSON value;
2. the tree editor root;
3. a `<template>` for new link nodes containing the `.pat-contentbrowser` input and a real `<button>` to open/choose;
4. the options JSON in a data attribute or a `<script type="application/json">` block for the addon JS to copy onto each node input.

Keep the per-node input outside the submitted name space. Only the textarea is submitted.

### Data converter

Leave the core `JSONDataConverter` in place:

- `toWidgetValue()` serializes the dict with `json.dumps(value, indent=True)`;
- `toFieldValue()` calls `field.fromUnicode(value)`, which JSON-decodes, then `jsonschema.validate()` via `JSONField._validate()`.

If the widget keeps one textarea, no custom converter is needed. A custom converter is only necessary if the widget invents per-node input names and assembles the dict on the server; that adds no value here and makes error reporting harder. Register a converter for `IJSONField` + `IMenuWidget` only if the widget changes the serialized format.

### JS bundle

The Patternslib `contentbrowser` pattern is already registered by the `plone` bundle; the addon does not need to import or re-register it. The addon bundle should:

- depend on `plone` in the registry, so `contentbrowser`, `select2`, Svelte, and Patternslib are present;
- import `registry` from Patternslib and `unmount` from Svelte;
- parse the tree model from the JSON textarea, render nodes, attach buttons, and serialize back on every mutation;
- call `registry.scan(node, ["contentbrowser"])` for new node inputs and perform the explicit unmount/destroy cleanup on delete.

Sources:

- `get_contentbrowser_options()`: <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/contentbrowser.py>
- text area widget and template registration: <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/text.py> and <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets.zcml>
- `JSONDataConverter`: <https://github.com/plone/plone.schema/blob/3.0.0/src/plone/schema/browser/jsonfield.py>
- `JSONField.fromUnicode()` and validation: <https://github.com/plone/plone.schema/blob/3.0.0/src/plone/schema/jsonfield.py>
- bundle registration and shared Patternslib: [plone-6.2-apis.md](plone-6.2-apis.md)

## 6. CSRF and permission constraints

### Vocabulary endpoint

`@@getVocabulary` is registered for `*` with permission `zope2.View`:

```xml
<browser:page
    name="getVocabulary"
    for="*"
    class=".vocabulary.VocabularyView"
    permission="zope2.View"
    />
```

`plone.app.vocabularies.Catalog` is in the view's `PERMISSIONS` map with `View`. On a navigation root (including the Plone site root), the view short-circuits the field-permission check when the vocabulary is in that map; otherwise it validates `field_name` through `IFieldPermissionChecker`, falling back to the vocabulary's default permission.

The catalog query itself applies security, so the picker only lists objects the current user can view. `contextPath` being ignored means the edited object itself can appear; filter it in JS if self-links are forbidden, and reject it on the server if the schema forbids it.

### POST for prefilled UIDs

`get_items_from_uids()` sends a `POST` to the vocabulary URL for prefilled selections, to avoid URL-length limits. This is a read-only request. Plone's automatic CSRF protection runs at transaction commit time and only rejects requests that registered database writes. A read-only vocabulary POST registers no writes, so it passes without a token. The standard edit form's final POST already contains `_authenticator` from Plone's form transform.

If the addon adds any endpoint that writes (for example, a "resolve and store title" endpoint), it must add a CSRF token explicitly via `_authenticator`, an `X-CSRF-TOKEN` header, or `plone.protect`'s `@protect(CheckAuthenticator)`. Do not rely on the contentbrowser request helper to send one; it does not.

### Server-side revalidation

Selection-time filtering is not enough. On submit:

- resolve every `internal_uid` with `uuidToObject()` (permission-checked) or `plone.api.content.get(UID=...)`;
- reject or drop UIDs that are missing or not viewable;
- remember that a raw UID in JSON is not a relation, so Plone's link integrity will not clean it up when the target is deleted.

Sources:

- `@@getVocabulary` registration: <https://github.com/plone/plone.app.content/blob/5.0.0/src/plone/app/content/browser/configure.zcml>
- vocabulary permission map and `VocabularyView`: <https://github.com/plone/plone.app.content/blob/5.0.0/src/plone/app/content/browser/vocabulary.py>
- read-only POST and UID fetch: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/utils.js>
- CSRF transaction model and token placement: <https://6.docs.plone.org/classic-ui/csrf.html>
- automatic protection checks registered writes: <https://github.com/plone/plone.protect/blob/6.0.0/src/plone/protect/auto.py>
- UID resolution helpers: [plone-6.2-apis.md](plone-6.2-apis.md)

## 7. Accessibility and keyboard behavior

The content browser has usable keyboard navigation, but it is not a fully accessible modal dialog in 5.6.14.

What works:

- `Escape` closes the browser.
- `ArrowDown` / `ArrowUp` move between items in a column.
- `ArrowRight` enters the next column; `ArrowLeft` returns to the previous column.
- `Space` adds/removes an item in multi-select mode; `Enter` selects the item (single-select `maximumSelectionSize=1` calls `addItem()`).
- The search field, close button, home button, and the pattern's "Select" button are focusable.
- Selected items have a remove button with `aria-label="remove"`.
- The item rows have `role="button"` and a `title` attribute.

What to account for in the dynamic tree:

- The overlay is a `<nav class="content-browser">`, not a `role="dialog"` / `aria-modal="true"` element. There is no focus trap and no inert background. Keyboard users can tab into the form behind the overlay. For the addon, treat it as a non-modal panel or add a wrapper with dialog semantics and a focus trap; do not claim modal behavior that the pattern does not provide.
- Item rows use `tabindex={n}` where `n` is the item index. Positive `tabindex` values are an anti-pattern and can produce an unexpected tab order. In practice the row keydown handler also calls `preventDefault()` for every key, including `Tab`, which can block tabbing out of a row. Verify this in a real browser and provide an escape path (close button, `Escape`) and focus restoration.
- `closeBrowser()` does not restore focus to the element that opened the picker. After selection or cancellation, focus the node's "Choose" button (or the node itself) explicitly.
- The pattern has no accessible name for the overlay and does not announce the selected item. Add an `aria-live="polite"` summary in the tree ("Target selected: Title") and label the node's picker button with the node title.
- Only one overlay should be open. The global selectors used by the keyboard helpers make concurrent overlays unreliable.
- Do not rely on the pattern's drag-to-sort selected-items behavior for single selection; with `maximumSelectionSize=1` it is not initialized.

For the tree itself, use real `<button>` elements for add/delete/move/choose, `aria-expanded` on folder toggles, visible focus styles, and a logical tab order. Do not make the whole node clickable. The content browser's internal gaps should be documented as upstream limitations, not replicated.

Sources:

- keyboard handlers, role/tabindex, focus behavior: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/ContentBrowser.svelte>
- selected item remove button: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/SelectedItem.svelte>
- overlay wrapper and toolbars: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/ContentBrowser.svelte>

## 8. Comparison: content browser vs UID autocomplete

| Criterion | Content browser (`pat-contentbrowser`) | UID autocomplete (`AjaxSelectWidget` / `pat-select2`) |
| --- | --- | --- |
| Interaction | Browse folders, breadcrumbs, favorites, search, preview, thumbnails | Type-ahead search only |
| Markup | Hidden `.pat-contentbrowser` input plus generated Svelte UI | A single visible `input.pat-select2` |
| Options | `vocabularyUrl`, `basePath`, `rootPath`, `rootUrl`, `favorites`, `selectableTypes`, `maximumSelectionSize`, ... | `vocabularyUrl`, `separator`, `maximumSelectionSize`, `initialValues`, `allowNewItems` |
| Prefill | Input `value` or `selection`; metadata fetched from catalog | `initialValues` map is read by select2 |
| Dynamic init | `registry.scan(node, ["contentbrowser"])`; Svelte async mount | `registry.scan(node, ["select2"])` |
| Cleanup | Must `unmount()` the Svelte app and remove the wrapper | Simpler; no Svelte app per node |
| Accessibility | Keyboard nav exists, but no dialog semantics, no focus trap, positive tabindex/Tab issue | select2 3.5.4 has known keyboard/ARIA limitations; one input is easier to label |
| UX for editors | Familiar Plone picker; good for users who do not know titles | Fast when the title is known; poor for exploration |
| Cost per node | Svelte app instance per node; heavier, especially if eager | Lighter, but still one select2 instance per node |
| Failure modes | Lifecycle leaks, duplicate ids, concurrent overlays, mount-time change | Vocabulary/select2 only; fewer moving parts |

`AjaxSelectWidget` is attractive because it is one input and its pattern already understands `initialValues`:

```python
from plone.app.z3cform.widgets.select import AjaxSelectFieldWidget

# For a real Choice field, the widget emits:
# {
#   "vocabularyUrl": ".../@@getVocabulary?name=plone.app.vocabularies.Catalog",
#   "maximumSelectionSize": 1,
#   "separator": ";",
#   "initialValues": {"<uid>": "<title>"},
# }
```

For a raw per-node input, the equivalent is:

```html
<input type="text"
       class="pat-select2"
       value="EXISTING_UID"
       data-pat-select2='{"vocabularyUrl": ".../@@getVocabulary?name=plone.app.vocabularies.Catalog", "maximumSelectionSize": 1, "separator": ";"}' />
```

Tradeoff summary:

- Choose the content browser if the editor must be able to explore the site, recognize objects visually, and pick folders/collections without knowing exact titles. That matches a menu-editing workflow.
- Choose the autocomplete if the tree is large, the picker must be extremely cheap, and users know what they are looking for. It loses browsing, previews, and folder navigation.
- Do not choose `RelatedItemsWidget`: it is the legacy select2 implementation with the same "search only" limitation plus older code.

Sources:

- `AjaxSelectWidget` options and `pattern = "select2"`: <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/select.py>
- select2 `initialValues` handling: <https://github.com/plone/mockup/blob/5.6.14/src/pat/select2/select2.js>
- contentbrowser pattern options: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/contentbrowser.js>

## 9. Recommendation and open verification items

### Recommendation

Implement the link target picker with the contentbrowser pattern inside the custom JSON widget:

1. One hidden `.pat-contentbrowser` input per link node, unique id, `maximumSelectionSize: 1`.
2. Options generated by `get_contentbrowser_options()` and embedded once per widget render.
3. Prefill by setting the input value to `internal_uid`.
4. Initialize new nodes with a scoped `registry.scan(node, ["contentbrowser"])`; keep only one picker active.
5. On delete, `unmount()` the Svelte component, call `destroy()`, and remove the container.
6. Read the UID from the input's `change` event, guard against the mount-time empty change, and write the whole model to a single hidden JSON textarea.
7. Leave `JSONDataConverter` unchanged; revalidate UIDs server-side.

If the lifecycle or performance work grows beyond the budget for v1, switch the per-node picker to `AjaxSelectWidget`/`pat-select2`. It is a smaller integration and still uses `plone.app.vocabularies.Catalog`. It is a deliberate UX downgrade, not an equivalent replacement.

### Open verification items

1. Confirm the `contextPath` and `initialValues` behavior in a real Plone 6.2.2 browser session; the source says both are unused by `pat-contentbrowser` 5.6.14.
2. Measure the cost of mounting one Svelte app per link node with a realistic tree (for example 50 link nodes). If it is noticeable, mount lazily on first "Choose" click or use one shared picker.
3. Verify `Tab` behavior inside `.contentItem` in the target browsers; the keydown handler prevents the default for every key.
4. Confirm that a read-only POST to `@@getVocabulary` for prefilled UIDs is not challenged by `plone.protect` in the target deployment, including any addon subscribers that might write during vocabulary lookup.
5. Verify focus restoration and overlay closing when a node is deleted while its picker is open.
6. Decide whether self-links (the object being edited) are forbidden. If yes, filter them in JS and enforce the rule server-side; `contextPath` alone will not do it.
7. Decide whether `basePath` should be the edited folder or the site root for menus; the helper defaults to the edited folder.

Sources:

- `contextPath` and `initialValues` in the helper: <https://github.com/plone/plone.app.z3cform/blob/5.0.2/src/plone/app/z3cform/widgets/contentbrowser.py>
- contentbrowser app props and config: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/App.svelte>
- selected-items initial value logic: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/SelectedItems.svelte>
- keyboard handler: <https://github.com/plone/mockup/blob/5.6.14/src/pat/contentbrowser/src/ContentBrowser.svelte>

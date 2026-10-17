# Content browser integration for per-node internal links

Type: research
Status: resolved
Blocked by: none

## Question

The tree editor lets every link node pick an internal Plone object. How can the widget reuse Plone 6.2 Classic UI's content browser / related-items pattern inside a dynamically added tree node?

Cover:

- which widget/pattern to instantiate (`ContentBrowserWidget`, `RelatedItemsWidget`, or a custom subclass);
- the required input markup and `pattern_options` (vocabulary URL, base path, root path, context path, initial values);
- how to initialize the pattern on nodes added after page load and how to clean it up on delete;
- how to read the selected UID back into the JSON node and how to prefill an existing UID;
- the Python/ZCML/JS integration points and any CSRF or permission constraints;
- accessibility and keyboard behavior of the content browser in this context.

Compare reusing the existing widget with a simpler UID autocomplete/search view. Recommend one and state the tradeoffs.

## Answer

Resolved by a research subagent. Full findings: [research/content-browser-per-node.md](../research/content-browser-per-node.md).

Recommendation: use the modern `pat-contentbrowser` pattern inside the custom JSON widget, not `RelatedItemsWidget`, and not `ContentBrowserWidget` as the JSON widget itself. Each link node gets a unique-id hidden `.pat-contentbrowser` input with `maximumSelectionSize: 1`; its value holds the existing UID. Build the options once in Python with `get_contentbrowser_options()` and inject them as `data-pat-contentbrowser`. Initialize new nodes with scoped `registry.scan(node, ["contentbrowser"])`. On delete, call Svelte 5 `unmount(pattern.component_content_browser)`, then `pattern.destroy()`, then remove the wrapper; `BasePattern.destroy()` alone leaks the Svelte app. Read the UID from the input's `change` event, guarding against the mount-time change that can erase dangling UIDs. Keep one hidden textarea with the whole JSON so the existing `JSONDataConverter` and JSON Schema validation continue to work.

Gotchas: `initialValues` is ignored by `pat-contentbrowser`; prefill via the input value. `contextPath` is ignored, so self-links are not prevented automatically. `@@getVocabulary` requires View; the prefilled-UID POST is read-only and needs no CSRF token. Accessibility gaps: no dialog role or focus trap, positive `tabindex`, `Tab` prevented on item rows, and no focus restoration. Fallback: `AjaxSelectWidget`/`pat-select2` is simpler but search-only and uses legacy select2.

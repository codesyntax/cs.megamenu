# Tree editor prototype

Type: prototype
Status: resolved
Blocked by: 03

## Question

What should the menu tree editor look and feel like?

Build a rough, interactive prototype inside a standard Plone edit form:

- add folder, add link, add child, delete, move up/down;
- edit title, CSS class, icon, external URL, and open-in-new-tab;
- pick an internal target through Plone's content browser;
- expand/collapse nested folders;
- show validation errors in place.

Make the interaction concrete enough to react to: where the buttons live, how a newly added node is focused, how the content browser opens per node, what the empty state looks like, and how the tree behaves at depth. The prototype is a decision aid, not the final implementation. Link the prototype artifact from this ticket.

## Prototype

- Open: [index.html](../prototypes/tree-editor/index.html)
- Run: `cd .scratch/collective-megamenu/prototypes/tree-editor && python3 -m http.server 8765`, then open `http://127.0.0.1:8765/?variant=A` (or `?variant=B`, `?variant=C`).
- Screenshots: [A — master/detail](../prototypes/tree-editor/variant-A.png), [B — inline cards](../prototypes/tree-editor/variant-B.png), [C — columns](../prototypes/tree-editor/variant-C.png).

Variants:

- **A — Master/detail**: tree on the left, selected node's fields in an inspector on the right. Compact; good for large trees.
- **B — Inline cards**: accordion cards with all fields inline under the selected node. Everything visible; gets long at depth.
- **C — Columns**: Miller-style columns for navigating into folders, with an inspector on the right. Good for deep nesting.

All three use the settled model: folders are placeholders, links are leaves, icons are CSS classes, internal targets are UIDs, and validation appears in place. The content browser is mocked; the real widget will use Plone's content browser.

Verified in headless Chrome: add folder/link, inline validation, internal target picking, save, variant switching, and depth navigation.

## Answer

Variant **A — master/detail** chosen.

- Tree on the left, inspector on the right.
- Row-level actions for add child, move up/down, and delete; the inspector repeats the relevant actions.
- Inspector fields: title, CSS class, icon, target (links only), open-in-new-tab.
- Internal target picker opens from the inspector. The prototype mocks it; the implementation uses Plone's content browser.
- Inline validation in the inspector plus error dots in the tree; Save validates the whole tree.
- Empty state lives in the tree pane.
- No additional changes requested.

The prototype is a throwaway decision aid. The artifact is [index.html](../prototypes/tree-editor/index.html), with screenshots A/B/C in the same folder. The next effort should implement only the validated decision, not copy the prototype code.

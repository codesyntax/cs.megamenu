# Finalize JSON Schema and validation rules

Type: grilling
Status: resolved
Blocked by: none

## Question

Finalize the JSON Schema and server-side validation rules for the menu value.

The settled model:

- top-level `{"version": 1, "items": [...]}`;
- every item has `id` (UUID), `type` (`folder` or `link`), `title`, `css_class`, and `icon`;
- folder items have `children` and no target;
- link items have exactly one of `internal_uid` or `external_url`, no children, and `open_in_new_tab`;
- internal targets are raw UIDs;
- icons are CSS class strings.

Decide the remaining constraints:

- required versus optional fields and allowed empty values;
- maximum lengths and allowed characters for titles, CSS classes, and icons;
- allowed URL schemes and validation for external URLs;
- duplicate IDs, duplicate titles, and cyclic/`children` edge cases;
- whether empty placeholder folders are valid in storage or only in the editor;
- exact user-facing validation messages and where they appear;
- the JSON Schema text and the converter/widget behavior that enforces it.

Produce the JSON Schema text and a validation table that the spec can adopt.

## Answer

The JSON Schema asset is [research/menu-schema.json](../research/menu-schema.json). It is draft-07, uses `definitions` and recursive `$ref`s, and has separate `folderItem` / `linkItem` definitions so `additionalProperties: false` works at every level.

### Schema decisions

- Top level: `{"version": 1, "items": [...]}`, both required, `additionalProperties: false`.
- `items` may be empty; an empty menu is valid and means explicit opt-out.
- Every item has `id` (UUID string), `type` (`folder` or `link`), `title`, `css_class`, and `icon`.
- Folder items: `children` required, may be empty; no target fields.
- Link items: exactly one of `internal_uid` / `external_url`, `open_in_new_tab` required; no `children`.
- `id` uniqueness is not expressible in JSON Schema; the server-side validator checks it.
- `title`: trimmed non-empty, max 200, at least one non-whitespace character.
- `css_class` and `icon`: max 200, zero or more space-separated CSS identifiers, single spaces only.
- `internal_uid`: max 64, non-whitespace; the real check is resolving it with the current user's permissions.
- `external_url`: max 2048, schemes limited to `http`, `https`, `mailto`, and `tel`; host/recipient checked server-side.
- `version` must be `1`; unknown versions are rejected.
- Unknown properties are rejected.

### Validation table

| Rule | Enforcement | User-facing message |
| --- | --- | --- |
| Top-level shape, version, unknown fields | JSON Schema | Field-level server error with path; structural failures are a safety net |
| `version` is 1 | JSON Schema + server validator | “Unsupported menu version. Expected version 1.” |
| `items` is an array; may be empty | JSON Schema | — |
| `id` is a UUID, unique across the tree | JSON Schema (UUID) + server validator (uniqueness) | “Menu item IDs must be unique and valid UUIDs.” |
| `type` is `folder` or `link` | JSON Schema | “A menu item must be a folder or a link.” |
| `title` required, trimmed, max 200 | Client + server; JSON Schema for shape | “Title is required.” / “Use at most 200 characters.” |
| `css_class` optional, max 200, CSS class list | Client + server; JSON Schema for shape | “Use only letters, numbers, hyphens, and underscores, separated by single spaces.” |
| `icon` optional, max 200, CSS class list | Client + server; JSON Schema for shape | Same as CSS class |
| Folder has `children`; no target fields | JSON Schema + server validator | “A folder cannot have a target.” |
| Link has exactly one target; no `children` | JSON Schema + server validator | “Choose exactly one target: internal or external.” / “A link cannot have children.” |
| `internal_uid` non-empty, max 64, resolves and is viewable | Client + server (context-aware) | “The selected internal target no longer exists or is not visible to you.” |
| `external_url` max 2048, allowed scheme, valid host/recipient | Client + server | “Use an http(s), mailto, or tel URL.” |
| `open_in_new_tab` is boolean | JSON Schema | — |
| Unknown property | JSON Schema + server validator | “Unknown field: `<name>`.” |
| Empty folder | Allowed in storage | Non-blocking editor warning: “This folder has no children and will not appear in the menu.” |
| Duplicate titles | Allowed | — |
| Empty menu | Allowed | — |

### Error presentation

- Client-side: inline per-field errors in the inspector; error dots in the tree; Save selects and focuses the first invalid node. The widget attaches a submit listener to the standard edit form, prevents submission while invalid, and leaves server-side validation authoritative.
- Server-side: one field-level, path-aware message list under the menu field, for example `Products → Product A: Choose exactly one target: internal or external.` Multiple errors are newline-separated. Server errors are not mapped back to individual tree nodes.
- Path segments use item titles; an untitled item is shown as `Untitled item #N` so the message is still actionable.

### Enforcement points

- The field carries the JSON Schema via `plone.schema.JSONField.schema`. `JSONField._validate()` runs `jsonschema.validate()` and raises a field error.
- A context-aware `validate_menu(value, context)` walks the tree for the semantic rules (duplicate IDs, folder/link field exclusivity, title/CSS/icon limits, URL syntax, UID resolution with `uuidToObject` or `plone.api.content.get`). It raises `zope.interface.Invalid` with the path-aware message; register it as an `IValidator` for the behavior on `IPloneFormLayer` (or call it from the edit form) so it has the context.
- The widget/converter trims titles and lowercases the external URL scheme before serialization. The server revalidates; a raw UID in JSON is not a relation, so a deleted target is caught at save time and again at render time.
- Client-side validation is hand-coded to mirror this table. Keep a fixture suite that runs the same valid/invalid samples through both the JS validator and the server validator so the rules cannot drift.
- `jsonschema` does not enforce `format` without a format checker, so UUIDs use an explicit regex. JSON Schema structural errors are intentionally generic; the semantic validator supplies the readable path-aware messages.

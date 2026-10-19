# Linkintegrity support — Implementation Specification

Implementation status: implemented in `src/collective/megamenu/linkintegrity/`.

## 1. Summary

`collective.megamenu` stores internal menu targets as raw Plone UIDs in the
`menu` JSON field. `plone.app.linkintegrity` does not inspect that field, so
deleting content referenced by a menu shows no warning. This specification adds
a behavior-specific `IRetriever` adapter so menu UIDs participate in Plone's
standard linkintegrity relation store and delete confirmation.

The implementation follows Plone's existing linkintegrity flow. It does not add
a custom warning screen, a parallel relation store, or a hard deletion block.

## 2. Goals and non-goals

### Goals

- Track every non-empty `internal_uid` in the menu stored on a behavior-enabled
  object.
- Cover **Plone Site**, **Folder**, and **LRF**.
- Attribute inherited-menu references to the ancestor that stores the menu.
- Preserve the standard linkintegrity delete confirmation and “Delete anyway”
  flow.
- Keep `plone.app.linkintegrity` a soft dependency.
- Respect `enable_link_integrity_checks`.
- Preserve existing RichText link tracking.
- Support Plone 6.0–6.2, with Plone 6.2 as the tested environment.

### Non-goals

- Tracking external URLs.
- Custom warning text or naming the specific menu item.
- Backfilling existing menus or adding an upgrade step.
- Hard-blocking deletion.
- Tracking a menu reference whose target is the Plone Site root itself.
- Tracking references outside the menu.
- Volto/headless support.

## 3. How linkintegrity works

`plone.app.linkintegrity` discovers outgoing references through `IRetriever`
adapters. The core `DXGeneral` retriever is registered for
`IDexterityContent` and extracts URLs from `RichText` fields.

On object added, modified, and copied events for `IDexterityHasRelations`, the
core `modifiedContent` handler:

1. Calls `IRetriever(obj, None).retrieveLinks()`.
2. Resolves the returned URLs with `getObjectsFromLinks`.
3. Replaces the object's outgoing `isReferencing` relations with the result.

The delete confirmation reads incoming relations from the `zc.relation` catalog
with `getIncomingLinks(obj, from_attribute=None)` and shows the standard
“Potential link breakage” screen for each accessible source.

Dexterity content, including `Folder`, `LRF`, and `PloneSite`, provides
`IDexterityHasRelations`. A schema-only behavior registers its interface as a
marker, so objects with `collective.megamenu.menu` provide `IEditableMenu`.

## 4. Integration design

### 4.1 Trigger

Register one `IRetriever` adapter for `IEditableMenu`:

```python
@implementer(IRetriever)
@adapter(IEditableMenu)
class MenuRetriever(DXGeneral):
    """DXGeneral plus menu internal UID references."""

    def retrieveLinks(self):
        links = super().retrieveLinks()
        links |= {
            f"resolveuid/{uid}"
            for uid in iter_menu_link_uids(getattr(self.context, "menu", None))
        }
        return links
```

`IEditableMenu` is more specific than `IDexterityContent`, so this adapter wins
for objects with the behavior. Objects without the behavior continue to use the
core `DXGeneral` retriever.

`super().retrieveLinks()` is mandatory. It preserves RichText references for
the same object. `plone.restapi`'s `BlocksRetriever` is prior art for the same
adapter pattern but omits `super()` and therefore drops RichText links; do not
copy that omission.

### 4.2 Module layout

```text
src/collective/megamenu/linkintegrity/
├── __init__.py          # empty; must not import menu.py
├── menu.py              # iter_menu_link_uids + MenuRetriever
└── configure.zcml       # <adapter factory=".menu.MenuRetriever" />
```

`linkintegrity/menu.py` is the only module that imports
`plone.app.linkintegrity`. Do not import it from `__init__.py`, `menu.py`,
`utils.py`, the behavior module, tests' shared helpers, or anything loaded
unconditionally.

### 4.3 Registration

Add the ZCML namespace to the top-level `configure.zcml`:

```xml
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:i18n="http://namespaces.zope.org/i18n"
    xmlns:zcml="http://namespaces.zope.org/zcml"
    i18n_domain="collective.megamenu"
    >
```

Include the package conditionally:

```xml
<include
    package=".linkintegrity"
    zcml:condition="installed plone.app.linkintegrity"
    />
```

`linkintegrity/configure.zcml`:

```xml
<configure xmlns="http://namespaces.zope.org/zope">
  <adapter factory=".menu.MenuRetriever" />
</configure>
```

The `installed` condition tests package availability. When the package is
absent, the include is skipped, `linkintegrity/menu.py` is never imported, and
the menu still saves and renders.

### 4.4 Soft dependency

Do not add `plone.app.linkintegrity` to `project.dependencies`. It ships with a
normal Plone installation. The conditional ZCML include keeps the addon
importable without it.

The core `check_linkintegrity_dependencies` already gates the handlers on
`enable_link_integrity_checks`, intid, the relation catalog, and `portal_url`.
No additional runtime gate is needed. When the setting is off, menu tracking
stays off and the delete confirmation shows no linkintegrity breach.

## 5. Reference extraction

### 5.1 `iter_menu_link_uids`

```python
def iter_menu_link_uids(menu):
    """Yield internal UIDs from a stored menu value, defensively."""
    if not isinstance(menu, dict):
        return
    items = menu.get("items")
    if not isinstance(items, list):
        return
    stack = list(items)
    while stack:
        item = stack.pop()
        if not isinstance(item, dict):
            continue
        if item.get("type") == "link":
            uid = item.get("internal_uid")
            if isinstance(uid, str) and uid.strip():
                yield uid.strip()
        children = item.get("children")
        if isinstance(children, list):
            stack.extend(children)
```

Rules:

- Only `type == "link"` items contribute.
- Only non-empty, non-whitespace string `internal_uid` values contribute.
- `external_url` is ignored.
- `children` are traversed at any depth.
- Duplicate UIDs are harmless; the returned set collapses them.
- `None`, `{}`, non-list `items`, and malformed items do not raise.
- The menu item's own `id` is not a reference.

### 5.2 URL form

`retrieveLinks()` must return URL strings, not relation objects.
`getObjectsFromLinks` calls `urlsplit` on each value, and `findObject` has an
explicit `resolveuid` branch. Use:

```text
resolveuid/<uid>
```

Do not return a bare UID or an absolute `obj.absolute_url()`:

- A bare UID is traversed as a child id and fails.
- An absolute URL requires resolving the target at save time and stores a path
  that can break on rename or move.
- `resolveuid/<uid>` is local, rename-safe, and explicitly supported.

### 5.3 Source attribution

The retriever reads the menu stored on the object itself. It does not resolve
the effective inherited menu.

- An object with a configured menu stores the relations for that menu.
- A descendant with `menu=None` contributes no menu relations, even though the
  viewlet inherits an ancestor menu.
- The relation source is therefore the object that stores the menu.
- The standard delete warning names that source object.

This matches the decision that inherited-menu references are attributed to the
ancestor that owns the menu.

### 5.4 Site-root target limitation

`getObjectsFromLinks` skips targets providing `IPloneSiteRoot`. A menu item
whose `internal_uid` is the site root itself therefore produces no relation.
This is accepted:

- The site root is not a normal deletable target for content editors.
- A workaround would bypass core linkintegrity behavior.

Document it as a known limitation.

## 6. Lifecycle behavior

### 6.1 Add, modify, copy

The core linkintegrity subscribers already fire on `IObjectAddedEvent`,
`IObjectModifiedEvent`, and `IObjectCopiedEvent` for `IDexterityHasRelations`.
No fallback subscriber is needed.

- Creating or saving a menu-owning object stores its menu relations.
- Editing a link from target A to target B drops A's incoming relation from
  that source and adds B's.
- Removing a link, clearing the menu to `None`, or saving an explicitly empty
  menu drops the old relations on the next save.
- Copying a menu-owning object recreates the relations from the copy through the
  standard copied-event handler.

### 6.2 Delete the target

The standard delete confirmation shows the menu owner as an accessible source.
“Delete anyway” proceeds through Plone's normal deletion flow.

### 6.3 Delete the source

Deleting a menu-owning object removes its outgoing `isReferencing` relations
through the core `removedContent` handler on linkintegrity 4.0.2+. This is
expected on the supported Plone 6.1 and 6.2 releases. On very early Plone 6.0
releases (linkintegrity 3.6.1), core may leave relations behind; that is core
behavior, not an integration API difference.

### 6.4 Disabled or absent linkintegrity

- Installed but `enable_link_integrity_checks` off: core returns before the
  retriever runs; no relation is created and no warning appears.
- Package absent: the conditional include is skipped; no adapter is registered;
  menus still save and render.
- No custom persistent storage is added. Relations are owned by linkintegrity.

### 6.5 Existing menus

No backfill. Existing menus are tracked on the next add/modify/copy event for
the object that stores the menu. The core `@@updateLinkIntegrityInformation`
view remains available as a manual Plone maintenance tool, but it is not part
of this feature.

## 7. Compatibility

The relevant API is stable across the supported range:

| Plone | linkintegrity | Relevant difference |
| --- | --- | --- |
| 6.0.0–6.0.2 | 3.6.1 | DX retriever API identical; no source-deletion cleanup |
| 6.0.5–6.0.15 | 4.0.x | Source-deletion cleanup from 4.0.2 |
| 6.1.x | 4.0.6 | Same retriever API |
| 6.2.x | 5.0.0 | PEP 420/src layout only; retriever/handler API unchanged |

`IRetriever.retrieveLinks()`, `DXGeneral`, `getObjectsFromLinks`, the
`resolveuid` branch, `isReferencing`, `getIncomingLinks`, and the
`IDexterityHasRelations` subscribers are stable across the range.

## 8. Testing and acceptance

### 8.1 Retriever unit tests

- `iter_menu_link_uids` finds nested links and traverses folder children.
- External-only links, empty UIDs, and the menu item's own `id` produce nothing.
- Duplicate UIDs collapse.
- `None`, `{}`, non-list `items`, and malformed items do not raise.
- `MenuRetriever.retrieveLinks()` returns `resolveuid/<uid>` for internal UIDs.
- `MenuRetriever.retrieveLinks()` preserves RichText links from `super()`.

### 8.2 Adapter selection

- `getAdapter(folder, IRetriever)` returns `MenuRetriever`.
- `getAdapter(portal, IRetriever)` returns `MenuRetriever`.
- `getAdapter(document_without_behavior, IRetriever)` returns `DXGeneral`.

### 8.3 Relation and event tests

- Folder: setting a menu and firing `modified` creates an `isReferencing`
  relation to the target.
- Plone Site root: same, through the standard handlers.
- LRF: same when `plone.app.multilingual` is installed and the behavior is
  assigned; skip or xfail without PAM.
- Inherited menu: a child with `menu=None` adds no child-sourced relation; the
  ancestor remains the source.
- Explicit empty menu: a descendant opt-out creates no relations.
- Menu edit: changing target A to B drops A's source relation and adds B's.
- RichText regression: one RichText link and one menu link on the same object
  produce both incoming relations.
- Multiple sources: the same target in a portal menu and a folder menu yields
  two incoming sources.
- Copy/paste: copying a menu-owning object creates references from the copy.
- Source deletion: deleting the menu owner removes its outgoing relations.
- Missing target: an unknown UID produces no relation and no exception.

### 8.4 Delete confirmation

- A menu reference produces the standard “Potential link breakage” breach whose
  source is the menu owner's title and URL.
- `enable_link_integrity_checks = False` produces no relation and no breach.
- External-only menus produce no breach.
- A menu link to `/` is not tracked (documented site-root limitation).

### 8.5 Soft-dependency tests

- Import `collective.megamenu` in an environment without
  `plone.app.linkintegrity`; the package imports and menus render.
- The addon `configure.zcml` uses
  `zcml:condition="installed plone.app.linkintegrity"`.
- Menu editing and rendering work with linkintegrity absent, installed but
  disabled, and installed and enabled.

### 8.6 Browser acceptance

- Editor creates a target page, configures a menu link, and saves.
- Deleting the target from `folder_contents` shows the standard warning naming
  the menu owner; “Delete anyway” completes deletion.
- Removing the menu link and saving, then deleting the target, shows no warning.
- An inherited root menu reference names the site root in the warning.

## 9. Implementation plan

1. **Retriever module** — add `linkintegrity/menu.py` with
   `iter_menu_link_uids` and `MenuRetriever`; keep the package `__init__.py`
   import-free.
2. **Conditional registration** — add `linkintegrity/configure.zcml`, add
   `xmlns:zcml` to the top-level `configure.zcml`, and include the package with
   `zcml:condition="installed plone.app.linkintegrity"`.
3. **Tests** — add retriever, adapter-selection, relation/event,
   delete-confirmation, and soft-dependency tests.
4. **Documentation** — note the feature and the site-root target limitation in
   the README and user docs.

## 10. Risks and assumptions

- Assumes the standard Plone linkintegrity setup (intid and relation catalog).
  The core handlers already verify those prerequisites.
- A menu with a large number of internal UIDs adds one relation per unique UID
  on save. This matches the standard linkintegrity cost model.
- The site-root target limitation is accepted and documented.
- No migration/backfill is provided; existing menus are protected after their
  next save.

## 11. References

- Research: [`research/linkintegrity-integration.md`](research/linkintegrity-integration.md)
- Issue: [`issues/01-linkintegrity-integration-research.md`](issues/01-linkintegrity-integration-research.md)
- `plone.app.linkintegrity` `retriever.py`, `handlers.py`, `configure.zcml`,
  `browser/info.py`, `utils.py` (installed Plone 6.2.2 stack).
- `plone.behavior.metaconfigure` and `plone.dexterity.content` for behavior
  markers.
- `plone.app.relationfield` for `IDexterityHasRelations`.
- `plone.restapi.blocks_linkintegrity.BlocksRetriever` as prior art, with the
  important difference that `MenuRetriever` calls `super()`.

# Linkintegrity integration for menu `internal_uid` references

Research for ticket [01-linkintegrity-integration-research](../issues/01-linkintegrity-integration-research.md).

Verified against the installed stack:

- Plone 6.2.2 (`plone.app.linkintegrity` 5.0.0, `plone.app.relationfield` 5.0.0,
  `plone.dexterity` 4.0.0).
- Runtime probes against the addon's `INTEGRATION_TESTING` layer (results below).
- Source comparison of `plone.app.linkintegrity` 3.6.1, 4.0.0, 4.0.6 and 5.0.0.

## Bottom line

Register a custom `IRetriever` adapter for the `IEditableMenu` behavior marker.
The adapter should subclass `plone.app.linkintegrity.retriever.DXGeneral`, call
`super().retrieveLinks()` to keep RichText links, and add
`resolveuid/<uid>` for every link item's non-empty `internal_uid`.

This works for Folder, LRF and the Plone Site root. The site root is itself a
Dexterity `Container` in Plone 6.0–6.2, so it already provides
`IDexterityHasRelations` and the standard linkintegrity subscribers already fire
for it. No dedicated event subscriber is needed.

Registration must be isolated behind
`zcml:condition="installed plone.app.linkintegrity"` and the module that imports
`DXGeneral`/`IRetriever` must only be loaded from that conditional ZCML block.

## 1. The schema-only behavior does provide the marker

`IEditableMenu` is registered with `<plone:behavior>` and no factory. In
`plone.behavior.metaconfigure.behaviorDirective`, a schema-only behavior sets
`marker = provides`:

```python
if marker is None and factory is None:
    # a schema only behavior means usually direct attribute settings on the
    # object itself, so the object itself provides the interface.
    marker = provides
```

`plone.dexterity.content.FTIAwareSpecification` then adds every registered
behavior marker to the object's dynamically computed `__providedBy__`:

```python
assignable = get_assignable(inst)
if assignable is not None:
    for behavior_registration in assignable.enumerateBehaviors():
        if behavior_registration.marker:
            dynamically_provided.append(behavior_registration.marker)
...
all_spec = Provides(cls, *dynamically_provided)
```

So an object of a type whose FTI lists `collective.megamenu.menu` provides
`IEditableMenu` through `providedBy()`/`IEditableMenu.providedBy()`. This is not
persisted in the ZODB; it is recomputed from the FTI behavior list and cached on
`_v__providedBy__`.

Runtime result on Plone 6.2.2:

```text
FOLDER  <class 'plone.app.contenttypes.content.Folder'>
IDexterityContent            True
IDexterityHasRelations       True
IEditableMenu                True
IBehaviorAssignable(folder).supports(IEditableMenu)  True

PORTAL  <class 'Products.CMFPlone.Portal.PloneSite'>
IDexterityContent            True
IDexterityHasRelations       True
IEditableMenu                True
IBehaviorAssignable(portal).supports(IEditableMenu)  True
```

A test adapter registered with `@adapter(IEditableMenu)` was selected by
`getAdapter(folder, IRetriever)` and `getAdapter(portal, IRetriever)`, overriding
the core `DXGeneral` registration for `IDexterityContent`. Objects without the
behavior still get `DXGeneral`, so their RichText links keep working.

Conclusion: yes, the marker is applied, and an `IRetriever` adapter can be
registered specifically for `IEditableMenu`.

## 2. The Plone Site root is covered by the standard path

`Products.CMFPlone.Portal.PloneSite` inherits from
`plone.dexterity.content.Container` in the whole target range:

- Plone 6.0.2: `class PloneSite(Container, SkinnableObjectManager, UniqueObject)`
- Plone 6.0.15: same
- Plone 6.1.3: `class PloneSite(Container, SkinnableObjectManager)`
- Plone 6.2.2: same

`DexterityContent` implements `IDexterityContent`, and
`plone.app.relationfield` adds `IDexterityHasRelations` to that class in ZCML:

```xml
<class class="plone.dexterity.content.DexterityContent">
  <implements interface=".interfaces.IDexterityHasRelations" />
</class>
```

`plone.app.linkintegrity` subscribes `modifiedContent` to
`IObjectAddedEvent`, `IObjectModifiedEvent` and `IObjectCopiedEvent`, and
`removedContent` to `IObjectWillBeRemovedEvent`, all for
`IDexterityHasRelations`:

```xml
<subscriber
    for="plone.app.relationfield.interfaces.IDexterityHasRelations
         zope.lifecycleevent.interfaces.IObjectModifiedEvent"
    handler=".handlers.modifiedContent"
    />
```

Runtime probe: setting a menu on the portal and calling
`zope.lifecycleevent.modified(portal)` created a `RelationValue` from
`/plone` to the target, and `getIncomingLinks(target)` returned the Plone Site.
So the site root does fire the standard path.

No fallback subscriber is required. The only site-root edge case is when the
site root is the **target** rather than the source: `getObjectsFromLinks()`
explicitly skips targets providing `IPloneSiteRoot`:

```python
if obj and not IPloneSiteRoot.providedBy(obj):
    ...
```

A menu pointing at the site root itself therefore produces no relation. If the
spec needs that, it needs a separate mechanism; otherwise document it as a
known limitation. (Deleting the site root is not a normal Plone operation
anyway: `DeleteConfirmationInfo.__call__` returns immediately when the context
is `IPloneSiteRoot`.)

A fallback subscriber would have to duplicate `modifiedContent`'s gating,
`getObjectsFromLinks`, `updateReferences`, and intid handling, and could
double-write alongside the core handler. Do not use one.

## 3. Preserve RichText links: subclass and union

Recommended implementation:

```python
from plone.app.linkintegrity.interfaces import IRetriever
from plone.app.linkintegrity.retriever import DXGeneral
from zope.component import adapter
from zope.interface import implementer

from .behaviors.menu import IEditableMenu


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
            if uid:
                yield uid
        children = item.get("children")
        if isinstance(children, list):
            stack.extend(children)


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

Why this shape:

- `IEditableMenu` is more specific than `IDexterityContent` in adapter lookup,
  so this adapter wins for menu-enabled objects (verified at runtime).
- `super().retrieveLinks()` keeps `DXGeneral`'s RichText extraction. This is
  essential: `plone.restapi`'s `BlocksRetriever` is prior art for the same
  adapter pattern but does **not** call `super()`, so RichText links are lost
  for blocks-enabled content. Do not copy that omission.
- Subclassing inherits future fixes to `DXGeneral`; composing
  `DXGeneral(self.context).retrieveLinks()` is equivalent today but less
  future-proof.
- Do not register a replacement adapter for `IDexterityContent`: it would
  replace `DXGeneral` for every Dexterity object and force a menu check in a
  global hot path.
- A separate subscriber is the wrong layer. `IRetriever` is the documented
  extension point (`plone.app.linkintegrity` README: "You can easily write
  custom adapters implementing the `IRetriever` interface for your content
  type"). A subscriber would run in addition to the core one.

The menu value is read from the object that stores it. For an inheriting
descendant, `menu` is `None` and the retriever adds nothing; only the ancestor
that owns the menu is the relation source. That matches the wayfinder decision
that inherited references are attributed to the ancestor.

## 4. `retrieveLinks()` must return `resolveuid/<uid>` strings

`retrieveLinks()` returns a set of URL strings, not relation objects:

- `getObjectsFromLinks(base, links)` immediately calls `urlsplit(link)` on each
  item. A `RelationValue` is not a string and would fail.
- `findObject()` has an explicit `resolveuid` branch: it takes the component
  after `resolveuid`, looks up `uuidToCatalogBrain(uid)`, and returns the
  target with `_unrestrictedGetObject()`:

```python
if "resolveuid" in components:
    uid = components[components.index("resolveuid") + 1]
    brain = uuidToCatalogBrain(uid)
    if brain is not None:
        obj = brain._unrestrictedGetObject()
        if obj:
            return obj, path
```

Therefore `resolveuid/<uid>` is exactly the supported form. It also avoids
path staleness and base-URL differences between a menu on the site root, a
Folder or an LRF. A bare `<uid>` would not work: `findObject` would try to
traverse it as a child id relative to the source's parent. An absolute
`obj.absolute_url()` would work but requires resolving the target while saving
and stores a path that can break on rename/move.

Handling details:

- Ignore external URLs entirely; only `internal_uid` is yielded.
- Ignore empty/whitespace UIDs and folder items (they have no target).
- Recurse `children` to cover the whole tree.
- Return a `set`; duplicates collapse naturally.
- Be defensive about `menu is None`, non-dict values, non-list `items`, and
  malformed items so a bad record cannot break content editing.
- Missing UIDs are skipped by `findObject` (`brain is None`). Objects without an
  intid yet are skipped by `ensure_intid` returning `None`.
- Targets providing `IPloneSiteRoot` are skipped (see section 2).
- `getObjectsFromLinks` only records local links: empty scheme/host, or the
  same scheme/host as the source. `resolveuid/...` is local.

## 5. Soft dependency registration

Keep `plone.app.linkintegrity` optional at import and ZCML level.

`configure.zcml`:

```xml
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:zcml="http://namespaces.zope.org/zcml"
    >

  <!-- ...existing includes... -->

  <include
      file="linkintegrity.zcml"
      package="collective.megamenu"
      zcml:condition="installed plone.app.linkintegrity"
      />

</configure>
```

`linkintegrity.zcml`:

```xml
<configure xmlns="http://namespaces.zope.org/zope">
  <adapter factory=".linkintegrity.MenuRetriever" />
</configure>
```

`linkintegrity.py` is the only module that imports `plone.app.linkintegrity`
(`IRetriever`, `DXGeneral`). Do not import it from `__init__.py`, `menu.py`,
`utils.py`, the behavior module, tests' shared helpers, or anything loaded
unconditionally.

Why the condition is safe:

- `installed <package>` is a ZCML condition evaluated with `__import__`; it
  returns true when the module can be imported and false on `ImportError`
  (`zope.configuration.xmlconfig.ConfigurationHandler.evaluateCondition`).
- It tests package availability, not whether the linkintegrity GenericSetup
  profile is applied to a particular site. That is acceptable: the retriever
  registration is inert unless the core handler calls it, and the core handler
  is registered by the package itself when it is importable.
- ZCML is processed once per process. Installing the Python package later
  requires a restart; installing/uninstalling the GenericSetup profile on a
  running process does not change the adapter registration.
- Do not add `plone.app.linkintegrity` to `project.dependencies`. Plone already
  ships it in normal installs; `installed` covers the truly absent case. If an
  explicit extra is desired, use an optional extra, never a hard dependency.

Runtime gating is already handled by core:

```python
def check_linkintegrity_dependencies(obj):
    ...
    if not editing_settings.enable_link_integrity_checks:
        return False
    ...
```

When `enable_link_integrity_checks` is off, `modifiedContent` returns before
`IRetriever(obj, None)`, so no relation is created or updated. The delete
confirmation also checks `linkintegrity_enabled()` first. The menu editor and
viewlet must not depend on linkintegrity for their own behavior.

When the package is absent:

- The conditional include is skipped, so `linkintegrity.py` is never imported.
- No `IRetriever` adapter is registered for `IEditableMenu`; menus still save
  and render.
- No relations are written and no standard warning appears.

## 6. Version differences (Plone 6.0–6.2)

| Plone release | `plone.app.linkintegrity` | Relevant difference |
| --- | --- | --- |
| 6.0.0–6.0.2 | 3.6.1 | Also has `ATGeneral`; DX `IRetriever`/`DXGeneral` API identical; no `removedContent` cleanup |
| 6.0.5 | 4.0.1 | DX-only; cleanup fix in 4.0.2 |
| 6.0.10 | 4.0.3 | cleanup fix present |
| 6.0.15 | 4.0.6 | same retriever API |
| 6.1.x (6.1.0, 6.1.3 checked) | 4.0.6 | same retriever API |
| 6.2.x (6.2.2 checked) | 5.0.0 | PEP 420 namespace + src layout; Plone 6.2/Python 3.10+; retriever/handler API unchanged |

The parts this integration depends on are stable across the range:

- `IRetriever.retrieveLinks()`.
- `DXGeneral` import path and constructor.
- `getObjectsFromLinks` and the `resolveuid` branch of `findObject`.
- `isReferencing` relation attribute and `getIncomingLinks(obj, from_attribute=None)`
  in the delete confirmation.
- `IDexterityHasRelations` subscribers on added/modified/copied/removed.

Source diff: 4.0.0 → 4.0.6 only adds `removedContent` (removes outgoing
`isReferencing` relations when the source is deleted), plus style changes.
4.0.6 → 5.0.0 is layout/PEP 420 and whitespace only. Plone 6.0.0–6.0.2's 3.6.1
has the same DX code path plus Archetypes support; no `removedContent`, so
outgoing relations may linger after deleting a menu owner on those very early
release. That is core behavior, not an integration API difference.

Site root support is also stable: `PloneSite` subclasses the Dexterity
`Container` in 6.0.2, 6.0.15, 6.1.3 and 6.2.2, and the
`IDexterityHasRelations` class directive is identical in
`plone.app.relationfield` 3.0.6, 4.0.3 and 5.0.0.

## 7. Prior art

1. **`plone.app.linkintegrity` itself** — `DXGeneral` is the reference adapter.
   Its README's "Customization" section explicitly recommends custom
   `IRetriever` adapters for a content type.
2. **`plone.restapi.blocks_linkintegrity.BlocksRetriever`** — the closest
   real-world precedent for a behavior/feature marker:

   ```python
   @implementer(IRetriever)
   @adapter(IBlocks)
   class BlocksRetriever(DXGeneral):
       def retrieveLinks(self): ...
   ```

   registered with `<adapter factory=".blocks_linkintegrity.BlocksRetriever" />`.
   It proves the marker-based adapter pattern and adapter precedence. It also
   shows the trap: it does not call `super().retrieveLinks()`, so RichText
   links are not returned for blocks-enabled content. Our retriever must union
   with `super()`.
3. **`plone.app.relationfield`** — shows the correct behavior-assignable /
   marker approach (`IDexterityHasRelations` via a class directive) and which
   events the relation machinery listens to. It is not a linkintegrity
   retriever, but it is the model for how a behavior-driven relation source is
   wired.

No installed addon other than `plone.restapi` registers an `IRetriever`.

## 8. Tests and acceptance criteria for the spec

### Retriever unit tests (no event needed)

1. `iter_menu_link_uids`:
   - nested links are found;
   - folder items and their `children` are traversed;
   - external-only links produce nothing;
   - empty `internal_uid` produces nothing;
   - duplicate UIDs collapse;
   - `None`, `{}`, non-list `items`, and malformed items do not raise.
2. `MenuRetriever.retrieveLinks()` on a menu-enabled Folder:
   - returns `resolveuid/<uid>` for each internal UID;
   - does not return the menu item `id` (item UUID) or `external_url`;
   - preserves any RichText links from `super()`.
3. Adapter selection:
   - `getAdapter(folder, IRetriever)` is `MenuRetriever`;
   - `getAdapter(portal, IRetriever)` is `MenuRetriever`;
   - `getAdapter(document_without_behavior, IRetriever)` is `DXGeneral`.

### Event and relation tests

4. Folder: set a menu, call `modified(folder)`, assert a `RelationValue` with
   `from_attribute == "isReferencing"` exists and `to_object` is the target.
5. Plone Site root: same via `modified(portal)`. Assert
   `getIncomingLinks(target)` contains the portal.
6. LRF: same, only when `plone.app.multilingual` is installed and the behavior
   is assigned. Skip or xfail without PAM per the addon's existing conditional
   LRF strategy.
7. Inherited menu: portal has a menu, child folder has `menu=None`. Modifying
   the child adds no child-sourced relations; the portal remains the source.
   Deleting the target must name the portal.
8. Explicit opt-out: a descendant with an explicitly empty menu does not
   inherit and does not create references; clearing a previously set menu on
   `modified` removes that source's old relations.
9. Menu edit: change a link from target A to target B, call `modified(owner)`;
   assert A no longer has an incoming relation from the owner and B does.
   Also test removing a link without adding a replacement.
10. RichText + menu: assign the behavior to a type with a `RichText` field (for
    example a Document in a dedicated test FTI), put one RichText link and one
    menu link in the same object, modify it, and assert both incoming
    relations. This is the regression test for the `BlocksRetriever` mistake.
11. Multiple sources: the same target in a portal menu and a folder menu yields
    two incoming sources; the delete warning lists both.
12. Copy/paste: copy a menu-owning object and assert the standard
    `IObjectCopiedEvent` subscriber creates references from the copy. This
    confirms the existing copied-event coverage applies to menus.
13. Source deletion: delete a menu-owning object and assert its outgoing
    `isReferencing` relations are cleaned up (linkintegrity >= 4.0.2; expected
    on all supported 6.1/6.2 releases).
14. Missing target: a menu UID not present in the catalog produces no relation
    and no exception; the viewlet omits it.

### Delete-confirmation tests

15. Delete confirmation: with a menu reference, `DeleteConfirmationInfo`
    (`delete_confirmation_info` view) reports a breach whose `sources` contains
    the menu owner's title/URL. Use `getIncomingLinks(target,
    from_attribute=None)` semantics; a menu relation uses `isReferencing`, so
    the default filtered query also finds it.
16. Link integrity disabled: set
    `plone.registry` `plone.enable_link_integrity_checks = False`, modify the
    owner, and assert no relation is created; the delete view returns no
    breach. Re-enable, modify, and assert the relation appears.
17. External URLs: a menu with only `external_url` produces no incoming
    relations and no delete warning.
18. Site-root target: if the spec keeps the current core filter, assert that a
    menu link to `/` is not tracked (documented limitation). If the spec
    requires it, this test is the failing test that motivates a fallback.

### Soft-dependency tests

19. Import isolation: in a subprocess, block `plone.app.linkintegrity` (or run
    in an environment without it) and import `collective.megamenu`; assert it
    imports and `iter_menu_link_uids` can be used. The `linkintegrity.py`
    module and its imports must not be reachable from the package root.
20. ZCML: assert the addon's `configure.zcml` uses
    `zcml:condition="installed plone.app.linkintegrity"` around the adapter
    include. A full "package absent" ZCML run is best done in CI with the
    package removed from the environment; a unit test cannot easily unload
    already-imported ZCML.
21. Menu editing/rendering with linkintegrity absent: the profile installs, the
    edit form saves, and the viewlet renders. No relation or warning is
    expected.

### Robot / acceptance

22. Editor creates a target page, configures a menu link to it, and saves.
23. Editor tries to delete the target from `folder_contents`; the standard
    "Potential link breakage" confirmation appears and names the object that
    stores the menu (site root, folder or LRF). "Delete anyway" completes the
    deletion through Plone's normal flow.
24. Remove the menu link, save, then delete the target; no warning appears.
25. Inherited case: configure the menu on the site root, navigate to a
    descendant folder, and delete a target referenced by the root menu; the
    warning names the site root.

## Recommendation for the spec

- Mechanism: one `IRetriever` adapter, `@implementer(IRetriever)` +
  `@adapter(IEditableMenu)`, subclassing `DXGeneral`, unioning
  `super().retrieveLinks()` with `resolveuid/<uid>` for all nested link items.
- Registration: conditional ZCML include (`installed plone.app.linkintegrity`)
  pointing to an isolated module; no import of linkintegrity anywhere else.
- No fallback event subscriber: Folder, LRF and Plone Site root are all
  Dexterity content and already covered by the core `IDexterityHasRelations`
  subscribers.
- Scope: track only the menu stored on the object itself; doing so naturally
  attributes inherited-menu references to the ancestor that owns the menu.
- Known limitation to state explicitly: a menu link whose target is the Plone
  Site root itself is not tracked because `getObjectsFromLinks` skips
  `IPloneSiteRoot` targets.
- Backfill: none, as decided in the map; references appear on the next
  `IObjectModifiedEvent` (or add/copy event) for each menu owner.

## Sources

Primary source files (installed versions in this repo):

- `.venv/lib/python3.10/site-packages/plone/app/linkintegrity/retriever.py`
  (`DXGeneral`, lines 15–39).
- `.venv/lib/python3.10/site-packages/plone/app/linkintegrity/handlers.py`
  (`findObject` resolveuid branch lines 42–56; `getObjectsFromLinks` lines
  79–102; `modifiedContent` lines 105–113; `removedContent` lines 116–130).
- `.venv/lib/python3.10/site-packages/plone/app/linkintegrity/configure.zcml`
  (adapter line 16; `IDexterityHasRelations` subscribers lines 18–42).
- `.venv/lib/python3.10/site-packages/plone/app/linkintegrity/browser/info.py`
  (`getIncomingLinks(obj, from_attribute=None)` line 129; source title/URL lines
  145–155; site-root target skip lines 33–38).
- `.venv/lib/python3.10/site-packages/plone/app/linkintegrity/utils.py`
  (`referencedRelationship = "isReferencing"` line 8; `getIncomingLinks` lines
  11–20).
- `.venv/lib/python3.10/site-packages/plone/behavior/metaconfigure.py`
  (schema-only behavior sets `marker = provides`, lines 117–122; registration
  lines 140–148).
- `.venv/lib/python3.10/site-packages/plone/dexterity/content.py`
  (`FTIAwareSpecification` adds behavior markers, lines 121–199; `DexterityContent`
  class lines 302–314).
- `.venv/lib/python3.10/site-packages/plone/app/relationfield/configure.zcml`
  (`IDexterityHasRelations` class directive lines 39–41).
- `.venv/lib/python3.10/site-packages/plone/restapi/blocks_linkintegrity.py`
  (`BlocksRetriever` lines 13–29; no `super()` call).
- `.venv/lib/python3.10/site-packages/plone/restapi/configure.zcml`
  (adapter registration line 140).
- `.venv/lib/python3.10/site-packages/zope/configuration/xmlconfig.py`
  (`installed` condition uses `__import__`, lines 398–413).
- `Products/CMFPlone/Portal.py` (installed 6.2.2: `PloneSite(Container, ...)`,
  lines 15–44).
- `.venv/lib/python3.10/site-packages/z3c/relationfield/event.py`
  (`_setRelation` lines 129–148; `breakRelations` lines 90–113).

Upstream references:

- <https://github.com/plone/plone.app.linkintegrity/blob/5.0.0/src/plone/app/linkintegrity/retriever.py>
- <https://github.com/plone/plone.app.linkintegrity/blob/5.0.0/src/plone/app/linkintegrity/handlers.py>
- <https://github.com/plone/plone.app.linkintegrity/blob/5.0.0/src/plone/app/linkintegrity/configure.zcml>
- <https://github.com/plone/plone.app.linkintegrity/blob/5.0.0/README.rst>
  ("Customization": custom `IRetriever` adapters are the intended extension
  point).
- <https://github.com/plone/plone.app.linkintegrity/blob/4.0.6/plone/app/linkintegrity/handlers.py>
  (4.0.6 used by Plone 6.0.15/6.1.x).
- <https://github.com/plone/plone.app.linkintegrity/blob/3.6.1/plone/app/linkintegrity/retriever.py>
  (3.6.1 used by Plone 6.0.0–6.0.2).
- <https://github.com/plone/plone.restapi/blob/10.0.4/src/plone/restapi/blocks_linkintegrity.py>
  (prior art; note the missing `super()`).
- <https://github.com/plone/Products.CMFPlone/blob/6.2.2/src/Products/CMFPlone/Portal.py>
- <https://github.com/plone/plone.app.relationfield/blob/5.0.0/src/plone/app/relationfield/configure.zcml>
- <https://github.com/zopefoundation/zope.configuration/blob/master/src/zope/configuration/xmlconfig.py>
  (`installed` / `not-installed` conditions).
- Plone release constraints used to map versions:
  <https://dist.plone.org/release/6.0.0/constraints.txt>,
  <https://dist.plone.org/release/6.0.2/constraints.txt>,
  <https://dist.plone.org/release/6.0.15/constraints.txt>,
  <https://dist.plone.org/release/6.1.3/constraints.txt>,
  <https://dist.plone.org/release/6.2.2/constraints.txt>.

## Runtime verification notes

Probes were run with the addon's `INTEGRATION_TESTING` layer on the installed
Plone 6.2.2 stack. A temporary test registered the proposed `MenuRetriever`,
set menus on a Folder and on the Plone Site root, called
`zope.lifecycleevent.modified()`, and observed:

- `getAdapter(folder, IRetriever)` and `getAdapter(portal, IRetriever)` returned
  `MenuRetriever` (not `DXGeneral`).
- `retrieveLinks()` returned `{'resolveuid/<target-uid>'}`.
- `getOutgoingLinks(owner)` contained a `RelationValue` to the target.
- `getIncomingLinks(target)` returned the Folder and, after the second probe,
  the Plone Site.
- `getObjectsFromLinks(owner, {'resolveuid/<target-uid>'})` produced a
  `RelationValue`.

The temporary test was removed; no application code was changed.

# Conditional `LRF` behavior registration for `cs.megamenu`

Research for [ticket 02](../issues/02-conditional-lrf-registration.md). Baseline: Plone 6.2.2, `plone.app.multilingual` 9.0.2, `Products.GenericSetup` 5.2, `Products.CMFCore` 3.8, `plone.dexterity` 4.0.0, `plone.behavior` 3.0.1. Version pins: <https://dist.plone.org/release/6.2.2/constraints.txt>.

Sources are linked at the end of each section.

## 1. Recommendation

Use the **FTI behavior list**, shipped as a per-type GenericSetup XML file in the addon's default profile, and close the "PAM installed after this addon" gap with a `ProfileImportedEvent` subscriber.

The mechanism is:

1. Add `profiles/default/types/LRF.xml` containing only the `behaviors` property with `purge="false"`. **Do not add `LRF` to `profiles/default/types.xml`.**
2. Keep the `<plone:behavior>` registration unconditional. The addon must not import `plone.app.multilingual` anywhere.
3. Register a subscriber for `Products.GenericSetup.interfaces.IProfileImportedEvent`. When PAM's `default` profile is imported and this addon is already installed, look up the `LRF` FTI and append the behavior if it is missing. This covers PAM installed after the addon, PAM reinstalled, and site creation where the addon profile runs before PAM.
4. Add `profiles/uninstall/types/LRF.xml` that removes only this behavior with `<element value="..." remove="true"/>` and `purge="false"`.
5. If LRF support is added in a later addon version, add an upgrade step with `<genericsetup:upgradeDepends import_steps="types"/>`.

Do **not** use a profile dependency or conditional ZCML for the assignment. Do **not** use an object-level `IBehaviorAssignable` adapter for a type-wide policy.

The core reason this works is that GenericSetup does not attempt to import `types/<type>.xml` for a type that does not exist. It silently skips the file. That is the conditional mechanism; the subscriber only handles ordering.

Sources:

- <https://github.com/zopefoundation/Products.CMFCore/blob/3.8/src/Products/CMFCore/exportimport/typeinfo.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/utils.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/events.py>
- <https://github.com/plone/plone.app.multilingual/blob/9.0.2/src/plone/app/multilingual/configure.zcml>

## 2. Why `types/LRF.xml` is conditional

`TypesToolXMLAdapter` and `TypeInformationXMLAdapter` drive the `types` import step. `importTypesTool()` calls `importObjects(portal_types, '', context)`.

`importObjects()` does two things:

1. It imports the tool-level body (`types.xml`) through the `types` adapter. `TypesToolXMLAdapter._initObjects()` creates an FTI only for each `<object>` listed in `types.xml`.
2. It then recurses over `portal_types.objectValues()` — that is, **only the FTIs that already exist** — and for each one reads `types/<fti_id>.xml` (spaces in the FTI id become underscores, so the site root is `types/Plone_Site.xml`).

Consequences:

- PAM installed before the addon: the `LRF` FTI exists, so `types/LRF.xml` is read and the behavior is merged into its `behaviors` property.
- PAM not installed (or installed later): there is no `LRF` FTI. The recursion never reaches an `LRF` object, so `types/LRF.xml` is never opened. There is **no exception, no warning, and no GenericSetup log entry**. It is silently skipped.
- If the addon puts `<object name="LRF" meta_type="Dexterity FTI"/>` in its own `types.xml`, the behavior is different: `_initObjects()` finds `Dexterity FTI` in `Products.meta_types` and **creates a bare `DexterityFTI("LRF")` even without PAM**. That produces a bogus LRF type with default class, factory, add permission, and schema. Never list `LRF` in the addon's `types.xml`.

The per-type file does not need a corresponding entry in `types.xml`; an empty `types.xml` wrapper is enough. This is a GenericSetup implementation detail, not an explicitly documented contract, so cover it with a test.

Sources:

- <https://github.com/zopefoundation/Products.CMFCore/blob/3.8/src/Products/CMFCore/exportimport/typeinfo.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/utils.py>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/configure.zcml>
- <https://6.docs.plone.org/backend/behaviors.html#using-a-genericsetup-profile>

## 3. Mechanism comparison

| Mechanism | Conditional on PAM? | Handles PAM installed later? | Result when LRF is absent | Verdict |
| --- | --- | --- | --- | --- |
| `types/LRF.xml` in default profile | Yes, by FTI existence | No, not by itself | Silently skipped | Recommended core |
| Optional separate profile | Yes, by FTI existence | No | Silently skipped; profile still marked installed | Only for explicit opt-in |
| Setuphandler / import step | Yes, explicit `portal_types.get("LRF")` check | No, unless combined with an event/subscriber | No-op; can log | Acceptable fallback |
| Profile dependency on PAM | Yes, by installing PAM | Yes, because PAM is installed | Not applicable | Rejected: hard dependency |
| Conditional ZCML | Only module importability | No | ZCML block not loaded | Rejected |

### 3.1 Optional GenericSetup profile

A second profile (for example `profiles/lrf`) with the same `types/LRF.xml` works technically, but adds a manual step for the site manager. If PAM is absent, applying it succeeds silently and the profile is recorded as installed, which is misleading. It also does not solve the late-install ordering problem. Choose it only if LRF support must be opt-in per site.

```xml
<genericsetup:registerProfile
    name="lrf"
    title="cs.megamenu: Language Root Folder support"
    description="Adds the editable menu behavior to plone.app.multilingual language root folders."
    provides="Products.GenericSetup.interfaces.EXTENSION"
    directory="profiles/lrf"
    />
```

### 3.2 Setuphandler / import step

A Python step is defensible if you want an explicit log line and a single code path:

```python
from Products.CMFCore.utils import getToolByName

BEHAVIOR = "cs.megamenu.behavior"


def add_behavior_to_lrf(context):
    if context.readDataFile("cs.megamenu_default.txt") is None:
        return
    portal = context.getSite()
    fti = getToolByName(portal, "portal_types").get("LRF")
    if fti is None or not hasattr(fti, "behaviors"):
        return
    behaviors = list(fti.behaviors)
    if BEHAVIOR not in behaviors:
        behaviors.append(BEHAVIOR)
        fti._updateProperty("behaviors", tuple(behaviors))
```

Register it as a `<genericsetup:importStep>`:

```xml
<genericsetup:importStep
    name="cs.megamenu.lrf"
    title="cs.megamenu: enable the behavior on LRF"
    handler="cs.megamenu.setuphandlers.add_behavior_to_lrf"
    />
```

The marker-file guard is required if you use an import step: every registered import step runs on every profile import, so without the guard the step would run during unrelated profile imports. The snippet above is the import-step form. A `post_handler` receives the setup tool instead of an import context, so it has no `readDataFile()` and must resolve the site with `aq_parent(tool)`; it runs only for the addon's own profile, after all import steps, but still before PAM is installed if PAM comes later. Both variants duplicate what GenericSetup already does declaratively. The same logic can be called from the `ProfileImportedEvent` subscriber described below.

### 3.3 Profile dependency

Adding this to `profiles/default/metadata.xml` makes PAM mandatory:

```xml
<dependencies>
  <dependency>profile-plone.app.multilingual:default</dependency>
</dependencies>
```

`getDependenciesForProfile()` raises `KeyError` if the dependency profile is not registered (PAM not installed), and `_runImportStepsFromContext()` applies the dependency chain, which installs PAM. That both breaks the "optional" requirement and silently enables multilingual support on monolingual sites. Reject.

### 3.4 Conditional ZCML

ZCML `zcml:condition="installed plone.app.multilingual"` tests only whether a Python module can be imported at ZCML processing time. It does not know whether the PAM profile is installed in a particular Plone site, and ZCML is loaded once per process. More importantly, behavior assignment is site data in the FTI, not a ZCML registration, so conditional ZCML cannot express it. Register the behavior unconditionally; an unassigned behavior utility is inert. Reject conditional ZCML for this purpose.

Sources:

- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/tool.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/zcml.py>
- <https://zopeconfiguration.readthedocs.io/en/latest/narr.html#making-specific-directives-conditional>
- <https://github.com/plone/plone.app.multilingual/blob/9.0.2/src/plone/app/multilingual/configure.zcml>

## 4. Reinstall, upgrade, and uninstall

### Reapplying the profile

GenericSetup re-runs the `types` step. With `purge="false"` on the `behaviors` property, `_initProperties()` merges the existing tuple with the new elements and filters duplicates. Reapplying is idempotent.

`purge` defaults to **true per property**, even when the profile is an EXTENSION profile and `shouldPurge()` is false for the whole object. Without `purge="false"`, the install XML would replace PAM's entire behavior list with only `cs.megamenu.behavior`.

### Reinstall

Plone 6 has no supported "reinstall" operation; the old `reinstallProducts` API was removed. In practice reinstall means uninstall followed by install. The uninstall profile removes this behavior from the `LRF` FTI; the install profile merges it back. If PAM is absent during either half, the corresponding `types/LRF.xml` is silently skipped.

### Upgrade

If LRF support is introduced after the addon has already shipped, bump the profile version and add:

```xml
<genericsetup:upgradeSteps
    profile="cs.megamenu:default"
    source="1000"
    destination="1001"
    >
  <genericsetup:upgradeDepends
      title="Enable the editable menu behavior on LRF"
      import_steps="types"
      />
</genericsetup:upgradeSteps>
```

`UpgradeDepends` calls `runImportStepFromProfile()` with `purge=False` by default. The `types` step re-reads `types/LRF.xml`; if LRF is absent it is a no-op. This covers addon upgrades, not PAM installed later.

### PAM installed after the addon

This is the important gap. When PAM is installed, its profile creates the `LRF` FTI during the `types` step and then runs `post_handler=".setuphandlers.init_pam"`. GenericSetup notifies `ProfileImportedEvent` after the post handler. A subscriber can add the behavior at that point:

```python
from Acquisition import aq_parent

PAM_PROFILE = "plone.app.multilingual:default"
OWN_PROFILE = "cs.megamenu:default"
BEHAVIOR = "cs.megamenu.behavior"


def _normalize(profile_id):
    if profile_id and profile_id.startswith("profile-"):
        return profile_id[len("profile-") :]
    return profile_id


def add_behavior_when_pam_is_installed(event):
    if _normalize(event.profile_id) != PAM_PROFILE:
        return
    setup = event.tool
    if setup.getLastVersionForProfile(OWN_PROFILE) == "unknown":
        return
    portal = aq_parent(setup)
    portal_types = getattr(portal, "portal_types", None)
    if portal_types is None:
        return
    fti = portal_types.get("LRF")
    if fti is None or not hasattr(fti, "behaviors"):
        return
    behaviors = list(fti.behaviors)
    if BEHAVIOR not in behaviors:
        behaviors.append(BEHAVIOR)
        fti._updateProperty("behaviors", tuple(behaviors))
```

```xml
<subscriber
    for="Products.GenericSetup.interfaces.IProfileImportedEvent"
    handler=".subscribers.add_behavior_when_pam_is_installed"
    />
```

Details that matter:

- `ProfileImportedEvent.profile_id` may be `plone.app.multilingual:default` or `profile-plone.app.multilingual:default`; the quickinstaller uses the prefixed form. Normalize before comparing.
- `getLastVersionForProfile()` returns `"unknown"` when this addon is not installed and strips a `profile-` prefix itself. Use it to avoid adding the behavior on sites that merely have the addon package in the Python path.
- `event.tool` is `portal_setup`; it has no public `getSite()`. `aq_parent(setup)` returns the Plone site because `portal_setup` lives in the site root.
- Do not use an `IObjectAddedEvent` subscriber on the `LRF` FTI as a late-install hook. PAM's `types/LRF.xml` imports its `behaviors` property without `purge="false"` and would overwrite a behavior added on FTI creation. `ProfileImportedEvent` fires after PAM's `types` step and post handler, so it is safe.
- Site creation applies `extension_ids` in order. `cs.megamenu` can run before `plone.app.multilingual`, so the profile XML is skipped; the subscriber fixes this case.

### PAM uninstall and reinstall

PAM's uninstall profile removes the `LRF` FTI entirely:

```xml
<object meta_type="Plone Types Tool" name="portal_types">
  <object meta_type="Dexterity FTI" name="LRF" remove="True" />
</object>
```

So when PAM is uninstalled, the behavior assignment disappears with the FTI. Uninstalling `cs.megamenu` afterwards is a silent no-op for LRF. If PAM is later reinstalled, a fresh `LRF` FTI is created with PAM's default behaviors; the `ProfileImportedEvent` subscriber re-adds the addon behavior, otherwise the site manager must reapply the addon profile.

### Uninstall behavior

Ship a separate file in the uninstall profile:

```xml
<?xml version="1.0" encoding="utf-8"?>
<object name="LRF" meta_type="Dexterity FTI">
  <property name="behaviors" purge="false">
    <element value="cs.megamenu.behavior" remove="true" />
  </property>
</object>
```

- `remove="true"` on `<element>` is supported by `PropertyManagerHelpers._initProperties()`.
- `purge="false"` is mandatory. With the default `purge="true"`, a remove-only property would set `behaviors` to `()` and wipe PAM's behaviors. Do not use `<property name="behaviors" remove="true"/>` either; that deletes the property from the FTI.
- If LRF is absent, the uninstall file is silently skipped.
- Uninstalling the addon does not unregister its `plone:behavior` ZCML utility from the running process; ZCML is process-wide and is only reloaded on restart. The leftover utility is inert once no FTI lists it.
- Removing the behavior from the FTI stops exposing the fields. Previously stored values remain on the objects (as attributes or annotations, depending on the behavior storage), so reinstalling the behavior brings the menu data back.

Sources:

- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/utils.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/context.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/upgrade.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/events.py>
- <https://github.com/plone/plone.app.multilingual/blob/9.0.2/src/plone/app/multilingual/profiles/default/types/LRF.xml>
- <https://github.com/plone/plone.app.multilingual/blob/9.0.2/src/plone/app/multilingual/profiles/uninstall/types.xml>
- <https://github.com/plone/Products.CMFPlone/blob/6.2.2/src/Products/CMFPlone/factory.py>
- <https://github.com/plone/Products.CMFPlone/blob/6.2.2/src/Products/CMFPlone/controlpanel/browser/quickinstaller.py>
- <https://6.docs.plone.org/backend/upgrading/version-specific-migration/upgrade-addons-to-51.html#uninstall>

## 5. FTI behavior list vs. object-level assignable adapter

The FTI is the right place.

`plone.dexterity` registers `DexterityBehaviorAssignable` as an adapter for `IDexterityContent`. Its `enumerateBehaviors()` yields from `SCHEMA_CACHE.behavior_registrations(self.context.portal_type)`, and `SchemaCache.behavior_registrations()` iterates `fti.behaviors` and looks up the named `IBehavior` utilities. In other words, the FTI's `behaviors` property is the canonical assignment mechanism for Dexterity.

This also means the assignment is evaluated at runtime: adding the behavior to the FTI applies to LRF objects that already exist, with no content migration. `DexterityFTI._updateProperty()` fires a modification event, which invalidates the schema cache.

An object-level `IBehaviorAssignable` adapter is not appropriate here:

- `plone.behavior.interfaces.IBehaviorAssignable` explicitly says there is no default implementation; assignment is application-specific.
- `plone.behavior`'s own documentation says `plone.dexterity` provides the suitable adapter for Dexterity content.
- A custom adapter would have to import PAM (or adapt a PAM-provided interface), reintroducing the dependency.
- It would bypass the Content Types control panel, so site managers could not see or disable the behavior per type.
- It would apply to every object of the adapted interface rather than to the `LRF` type as a configurable policy. Object-level assignment is for per-object exceptions, not type-wide behavior.

Do not confuse assignment with storage. The assignment lives on the FTI; the behavior's field values live on each object. That is why removing the behavior does not delete the stored menu.

Sources:

- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/behavior.py>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/schema.py>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/fti.py>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/configure.zcml>
- <https://github.com/plone/plone.behavior/blob/3.0.1/src/plone/behavior/interfaces.py>
- <https://github.com/plone/plone.behavior/blob/3.0.1/src/plone/behavior/behaviors.rst>
- <https://github.com/plone/plone.behavior/blob/3.0.1/src/plone/behavior/annotation.py>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/content.py>

## 6. Concrete files for `cs.megamenu`

`profiles/default/types/LRF.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<object name="LRF" meta_type="Dexterity FTI"
        xmlns:i18n="http://xml.zope.org/namespaces/i18n">
  <property name="behaviors" purge="false">
    <element value="cs.megamenu.behavior" />
  </property>
</object>
```

`profiles/default/types.xml` stays as the existing wrapper; do not add `LRF`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<object meta_type="Plone Types Tool" name="portal_types">
</object>
```

`configure.zcml` (unconditional; no PAM import):

```xml
<plone:behavior
    name="cs.megamenu.behavior"
    title="Editable menu"
    description="A configurable menu tree"
    provides=".behaviors.menu.IEditableMenu"
    />
```

`profiles/uninstall/types/LRF.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<object name="LRF" meta_type="Dexterity FTI">
  <property name="behaviors" purge="false">
    <element value="cs.megamenu.behavior" remove="true" />
  </property>
</object>
```

Test matrix for the implementation:

1. Install the addon on a site without PAM: install succeeds; no `LRF` FTI is created; no error.
2. Install PAM first, then the addon: `LRF` gains the behavior; existing LRFs expose the fields.
3. Install the addon first, then PAM: the `ProfileImportedEvent` subscriber adds the behavior to the new `LRF` FTI.
4. Reapply the addon profile: no duplicate behavior entries.
5. Uninstall the addon with PAM present: only this behavior is removed; PAM's behaviors remain.
6. Uninstall PAM, then the addon: both uninstalls succeed; LRF is gone.
7. Reinstall PAM: the subscriber re-adds the behavior.
8. Create a site with both addons selected: behavior is present regardless of extension order.

## 7. Gotchas

- `purge="false"` is required on both install and uninstall. Without it, install replaces PAM's behavior list, and uninstall wipes it.
- `shouldPurge()` being false for EXTENSION profiles does not make per-property `purge` default to false. The per-property default remains true.
- Never list `LRF` in the addon's `types.xml`; GenericSetup will create a bare FTI when PAM is absent.
- PAM's own `types/LRF.xml` writes `behaviors` without `purge="false"`; a behavior added before PAM's `types` step (for example from an FTI-added subscriber) is overwritten. Use `ProfileImportedEvent`, which fires after PAM's post handler.
- `ProfileImportedEvent.profile_id` can carry the `profile-` prefix. Normalize it.
- The `LRF` FTI has a `behaviors` property; if a custom non-Dexterity type named `LRF` exists without one, `_initProperties()` raises `ValueError: undefined property 'behaviors'`. Guard with `hasattr(fti, "behaviors")` in Python; the XML path cannot.
- Ensure the string in the FTI matches the registered behavior name. `plone.dexterity` 4.0.0 still has a deprecated fallback that resolves the dotted interface name and logs a warning if the named behavior is not found, but relying on it is fragile.
- The addon's behavior module and subscriber must not import `plone.app.multilingual`. Compare profile ids and type names as strings.
- `types/LRF.xml` being conditional on FTI existence is a GenericSetup implementation detail. Pin the behavior with an integration test so a future GenericSetup change is caught.

Sources:

- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/utils.py>
- <https://github.com/zopefoundation/Products.GenericSetup/blob/5.2/src/Products/GenericSetup/context.py>
- <https://github.com/plone/plone.app.multilingual/blob/9.0.2/src/plone/app/multilingual/profiles/default/types/LRF.xml>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/schema.py>
- <https://github.com/plone/plone.dexterity/blob/4.0.0/src/plone/dexterity/fti.py>
- <https://github.com/plone/plone.behavior/blob/3.0.1/src/plone/behavior/metaconfigure.py>

## 8. Open verification items

1. Confirm on a real Plone 6.2.2 instance that the `ProfileImportedEvent` subscriber runs after PAM's `post_handler` and that `portal_types["LRF"]` is present. The source order says yes; verify with a test.
2. Confirm that site creation with both addons selected applies `cs.megamenu` before `plone.app.multilingual` in the actual Classic UI form. The subscriber makes the order irrelevant, but the test should assert it.
3. Confirm that the behavior fields are exposed on LRF's `@@edit` form once the FTI behavior is added, and that existing LRFs created by `init_pam` pick it up without migration.

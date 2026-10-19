# Conditional LRF behavior registration

Type: research
Status: resolved
Blocked by: none

## Question

`LRF` is the Language Root Folder type from `plone.app.multilingual`, not a core Plone type. How should `collective.megamenu` enable its behavior on `LRF` only when `plone.app.multilingual` is installed, without making multilingual a hard dependency?

Compare the realistic mechanisms:

- an optional GenericSetup profile the site manager applies when PAM is present;
- a setuphandler/import step that checks whether the `LRF` FTI exists and adds the behavior only then;
- a profile dependency or conditional ZCML.

Recommend one, with the exact GenericSetup/ZCML/Python mechanics. Cover failure modes when `LRF` is absent, what happens on reinstall/upgrade, how uninstall behaves, and whether the behavior list should be updated through the FTI or through an object-level assignable adapter.

## Answer

Resolved by a research subagent. Full findings: [research/conditional-lrf-registration.md](../research/conditional-lrf-registration.md).

Recommendation: keep `profiles/default/types/LRF.xml` with `<property name="behaviors" purge="false">` but do **not** list `LRF` in `types.xml`. GenericSetup only imports FTIs that already exist; when `LRF` is absent the file is silently skipped, with no error or warning. Register `<plone:behavior>` unconditionally and never import PAM. For uninstall, use `profiles/uninstall/types/LRF.xml` with `<element value="collective.megamenu.menu" remove="true"/>` and `purge="false"`; omitting `purge="false"` would wipe PAM's behaviors. For upgrades, use `<genericsetup:upgradeDepends import_steps="types"/>`.

Final implementation decision (supersedes the research recommendation): keep `profiles/default/types/LRF.xml` for PAM installed before the addon, and use the addon profile's `post_handler` (`setuphandlers.add_behavior_to_lrf`) as a profile-level fallback instead of a `ProfileImportedEvent` subscriber. The post_handler checks the `LRF` FTI and appends the behavior idempotently. It covers site creation with both addons. If PAM is installed after the addon, reapply the addon profile; do not subscribe to PAM's profile import. Rejected: a PAM profile dependency, conditional ZCML, an object-level `IBehaviorAssignable` adapter, and the PAM-profile event subscriber.

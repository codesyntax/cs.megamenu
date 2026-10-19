---
myst:
  html_meta:
    "description": "collective.megamenu how-to guides"
    "property=og:description": "collective.megamenu how-to guides"
    "property=og:title": "collective.megamenu how-to guides"
    "keywords": "Plone, collective.megamenu, how-to, menu, navigation"
---

# How-to guides 🛠️

## Configure the site-wide menu 🛠️

1. Log in as a user who can edit the Plone Site root.
2. Open `/Plone/@@edit` and switch to the **Mega menu** fieldset.
3. In the **Menu** field, use **Add folder** and **Add link**.
4. Save.

The site root menu is used by all descendants that do not configure their own
menu.

## Override the menu in a section 📁

1. Open the section Folder’s edit form and switch to the **Mega menu**
   fieldset.
2. Configure its **Menu** field.
3. Save.

The nearest configured ancestor wins. Leave the field unset to inherit.

## Opt out of the inherited menu 🚫

Configure a menu on the Folder and delete all its items, leaving an explicitly
saved empty menu. The viewlet renders no main navigation for that Folder and
its descendants.

To go back to inheritance, use **Use inherited menu** in the editor instead of
deleting the last item.

## Add an internal link 🔗

1. Add a **link** item.
2. Open the **Internal** tab.
3. Click **Select** and pick an object with the content browser.
4. Save.

The target is stored as a UID and resolved with the current user’s `View`
permission at render time. Internal menu links also participate in Plone’s
linkintegrity checks.

## Delete content referenced by a menu 🗑️

When you delete a content item that an internal menu link points to, Plone shows
the standard “Potential link breakage” warning. The warning names the object
that stores the menu (the site root, a folder, or an LRF). Choose **Delete
anyway** to continue, or cancel and update the menu first.

Existing menus are registered with linkintegrity on their next save. External
URLs and links to the Plone Site root itself are not tracked.

## Add an external link 🌐

1. Add a **link** item.
2. Open the **External** tab.
3. Enter an `http`, `https`, `mailto`, or `tel` URL.
4. Save.

Enable **Open in a new tab** if needed; the viewlet adds
`rel="noopener noreferrer"`.

## Style an item 🎨

- **CSS class** is added to the item’s `<li>`.
- **Plone icon name** is resolved through `@@iconresolver` and rendered as an
  inline SVG before the label. Use names such as `alarm` or
  `contenttype/document`.

## Enable LRF support 🌍

Install `plone.app.multilingual` before or after `collective.megamenu`.

- If PAM is installed before the add-on, the add-on profile enables the
  behavior on `LRF`.
- If PAM is installed after the add-on, reapply the
  `collective.megamenu:default` profile.

## Build the editor assets 🧱

```shell
npm install
npm run build
```

The remote bundle and chunks are written to
`src/collective/megamenu/browser/static/bundles/`.

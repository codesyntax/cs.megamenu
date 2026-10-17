---
myst:
  html_meta:
    "description": "collective.megamenu tutorial"
    "property=og:description": "collective.megamenu tutorial"
    "property=og:title": "collective.megamenu tutorial"
    "keywords": "Plone, collective.megamenu, tutorial"
---

# Tutorial: create your first site menu 🚀

## Install the add-on 🚀

```shell
pip install collective.megamenu
```

Then install **collective.megamenu** from **Site Setup → Add-ons**.

## Open the site root edit form ✏️

Log in as an administrator, open `/Plone/@@edit`, and switch to the
**Mega menu** fieldset.

## Add a folder 📁

1. In the **Menu** field, click **Add folder**.
2. Set the title, for example `Products`.
3. Optionally set a CSS class and a Plone icon name (for example `alarm`).

## Add a link 🔗

1. Select the folder, then click **Add link**.
2. Set the title, for example `Product A`.
3. Keep the **Internal** tab selected and use the content browser to
   choose a page.
4. Save the form.

The menu is now stored on the site root and rendered in place of the main
navigation.

## Try an override 🧭

1. Create or open a Folder in the site.
2. Configure its **Menu** field with different items.
3. Visit the Folder. It uses its own menu; its descendants inherit it.

## Try an opt-out 🚫

1. Configure a menu on a Folder and delete all items.
2. Save. The main navigation renders nothing for that Folder and its
   descendants.
3. To restore inheritance, edit the Folder and click **Use inherited menu**.

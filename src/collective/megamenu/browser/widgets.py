"""Custom edit widget for the editable menu field."""

from .. import _
from plone import api
from plone.app.z3cform.interfaces import ITextAreaWidget
from plone.app.z3cform.widgets.contentbrowser import get_contentbrowser_options
from plone.app.z3cform.widgets.text import TextAreaWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import implementer_only

import json


class IMegaMenuWidget(ITextAreaWidget):
    """Marker for the master-detail menu widget template."""


@implementer_only(IMegaMenuWidget)
class MegaMenuWidget(TextAreaWidget):
    klass = "megamenu-widget"

    def contentbrowser_options_json(self):
        options = get_contentbrowser_options(
            self.context,
            "",
            ";",
            "plone.app.vocabularies.Catalog",
            "@@getVocabulary",
        )
        options["maximumSelectionSize"] = 1
        options["mode"] = "browse"
        portal = api.portal.get()
        if portal is not None:
            options["basePath"] = "/".join(portal.getPhysicalPath())
        return json.dumps(options)

    def translations_json(self):
        messages = {
            "menuTree": _("Menu tree"),
            "addFolderShort": _("+ Folder"),
            "addLinkShort": _("+ Link"),
            "useInherited": _("Use inherited menu"),
            "noMenu": _("No menu configured"),
            "intentionalEmpty": _("This menu is intentionally empty"),
            "inherited": _("The nearest ancestor menu is inherited."),
            "noNavigation": _("The viewlet will render no navigation here."),
            "inheritedHere": _(
                "No menu is configured here. The nearest ancestor menu is inherited."
            ),
            "addFolder": _("Add folder"),
            "addLink": _("Add link"),
            "selectItem": _("Select a menu item to edit it."),
            "folderDetails": _("Folder details"),
            "linkDetails": _("Link details"),
            "folder": _("Folder"),
            "link": _("Link"),
            "title": _("Title"),
            "cssClass": _("CSS class"),
            "iconClass": _("Icon CSS class"),
            "requiredSuffix": _(" (required)"),
            "cssPlaceholder": _("e.g. nav-products"),
            "iconPlaceholder": _("e.g. bi bi-house"),
            "iconPreview": _("Icon preview:"),
            "folderHelp": _(
                "Folders are placeholders. They group children and are not clickable."
            ),
            "emptyFolderHelp": _(
                "This folder has no children and will not appear in the menu."
            ),
            "target": _("Target"),
            "internalTab": _("Internal"),
            "externalTab": _("External"),
            "externalUrl": _("External URL"),
            "openInNewTab": _("Open in a new tab"),
            "moveUp": _("Move up"),
            "moveDown": _("Move down"),
            "delete": _("Delete"),
            "collapse": _("Collapse"),
            "expand": _("Expand"),
            "addFolderInside": _("Add folder inside"),
            "addLinkInside": _("Add link inside"),
            "validationErrors": _("{count} validation error(s)"),
            "untitled": _("(untitled)"),
            "untitledFolder": _("Untitled folder"),
            "untitledLink": _("Untitled link"),
            "internalTarget": _("Internal target"),
            "noTarget": _("No target"),
            "child": _("child"),
            "children": _("children"),
            "internalTargetSelected": _("Internal target selected."),
            "confirmDelete": _(
                'Delete "{title}" and its {count} direct child item(s)?'
            ),
            "titleRequired": _("Title is required."),
            "tooLong": _("Use at most 200 characters."),
            "cssError": _(
                "Use only letters, numbers, hyphens, and underscores, "
                "separated by single spaces."
            ),
            "urlError": _("Use an http(s), mailto, or tel URL."),
            "internalTargetError": _(
                "The selected internal target no longer exists or is not "
                "visible to you."
            ),
            "uniqueIds": _("Menu item IDs must be unique and valid UUIDs."),
            "folderTarget": _("A folder cannot have a target."),
            "folderChildren": _("A folder must have children."),
            "linkChildren": _("A link cannot have children."),
            "oneTarget": _("Choose exactly one target: internal or external."),
            "itemType": _("A menu item must be a folder or a link."),
            "versionError": _("Unsupported menu version. Expected version 1."),
        }
        return json.dumps({
            key: translate(message, context=self.request)
            for key, message in messages.items()
        })


@implementer(IFieldWidget)
def MegaMenuFieldWidget(field, request):
    return FieldWidget(field, MegaMenuWidget(request))

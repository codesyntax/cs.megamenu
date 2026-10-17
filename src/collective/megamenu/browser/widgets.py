"""Custom edit widget for the editable menu field."""

from plone import api
from plone.app.z3cform.interfaces import ITextAreaWidget
from plone.app.z3cform.widgets.contentbrowser import get_contentbrowser_options
from plone.app.z3cform.widgets.text import TextAreaWidget
from z3c.form.interfaces import IFieldWidget
from z3c.form.widget import FieldWidget
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


@implementer(IFieldWidget)
def MegaMenuFieldWidget(field, request):
    return FieldWidget(field, MegaMenuWidget(request))

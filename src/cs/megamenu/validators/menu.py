"""z3c.form validators for the editable menu field."""

from ..behaviors.menu import IEditableMenu
from .validation import validate_menu
from z3c.form import validator
from z3c.form.interfaces import NOT_CHANGED
from zope.interface import Invalid


class MenuValidator(validator.SimpleFieldValidator):
    """Run the JSON Schema and the context-aware menu rules together."""

    def validate(self, value, force=False):
        if value is NOT_CHANGED:
            return super().validate(value, force)
        errors = validate_menu(value)
        if errors:
            raise Invalid("\n".join(errors))
        return super().validate(value, force)


validator.WidgetValidatorDiscriminators(MenuValidator, field=IEditableMenu["menu"])

"""JSON Schema for the editable menu value.

This is the schema embedded in the behavior field. Keep it in sync with
``.scratch/collective-megamenu/research/menu-schema.json`` and the validation
table in the implementation spec.
"""

MENU_JSON_SCHEMA = r"""
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Editable menu",
  "type": "object",
  "additionalProperties": false,
  "required": ["version", "items"],
  "properties": {
    "version": {
      "const": 1
    },
    "items": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/menuItem"
      }
    }
  },
  "definitions": {
    "uuid": {
      "type": "string",
      "pattern": "^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200,
      "pattern": "\\S"
    },
    "cssClass": {
      "type": "string",
      "maxLength": 200,
      "pattern": "^$|^[A-Za-z_-][A-Za-z0-9_-]*( [A-Za-z_-][A-Za-z0-9_-]*)*$"
    },
    "icon": {
      "type": "string",
      "maxLength": 200,
      "pattern": "^$|^[A-Za-z_-][A-Za-z0-9_-]*( [A-Za-z_-][A-Za-z0-9_-]*)*$"
    },
    "internalUid": {
      "type": "string",
      "maxLength": 64,
      "pattern": "^$|^\\S+$"
    },
    "externalUrl": {
      "type": "string",
      "maxLength": 2048,
      "pattern": "^$|^(?:[Hh][Tt][Tt][Pp][Ss]?://|[Mm][Aa][Ii][Ll][Tt][Oo]:|[Tt][Ee][Ll]:)"
    },
    "openInNewTab": {
      "type": "boolean"
    },
    "menuItem": {
      "oneOf": [
        {
          "$ref": "#/definitions/folderItem"
        },
        {
          "$ref": "#/definitions/linkItem"
        }
      ]
    },
    "folderItem": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "type", "title", "css_class", "icon", "children"],
      "properties": {
        "id": {
          "$ref": "#/definitions/uuid"
        },
        "type": {
          "const": "folder"
        },
        "title": {
          "$ref": "#/definitions/title"
        },
        "css_class": {
          "$ref": "#/definitions/cssClass"
        },
        "icon": {
          "$ref": "#/definitions/icon"
        },
        "children": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/menuItem"
          }
        }
      }
    },
    "linkItem": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "id",
        "type",
        "title",
        "css_class",
        "icon",
        "internal_uid",
        "external_url",
        "open_in_new_tab"
      ],
      "properties": {
        "id": {
          "$ref": "#/definitions/uuid"
        },
        "type": {
          "const": "link"
        },
        "title": {
          "$ref": "#/definitions/title"
        },
        "css_class": {
          "$ref": "#/definitions/cssClass"
        },
        "icon": {
          "$ref": "#/definitions/icon"
        },
        "internal_uid": {
          "$ref": "#/definitions/internalUid"
        },
        "external_url": {
          "$ref": "#/definitions/externalUrl"
        },
        "open_in_new_tab": {
          "$ref": "#/definitions/openInNewTab"
        }
      },
      "oneOf": [
        {
          "properties": {
            "internal_uid": {
              "minLength": 1
            },
            "external_url": {
              "const": ""
            }
          }
        },
        {
          "properties": {
            "internal_uid": {
              "const": ""
            },
            "external_url": {
              "minLength": 1
            }
          }
        }
      ]
    }
  }
}
"""

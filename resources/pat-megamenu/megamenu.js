import { BasePattern } from "@patternslib/patternslib/src/core/basepattern";
import registry from "@patternslib/patternslib/src/core/registry";
import { unmount } from "svelte";

const UUID_RE =
  /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
const CSS_RE =
  /^$|^[A-Za-z_-][A-Za-z0-9_-]*( [A-Za-z_-][A-Za-z0-9_-]*)*$/;
const HOST_RE =
  /^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)*$/;
const TARGET_KEYS = ["internal_uid", "external_url", "open_in_new_tab"];

const CSS_ERROR =
  "Use only letters, numbers, hyphens, and underscores, separated by single spaces.";
const URL_ERROR = "Use an http(s), mailto, or tel URL.";
const INTERNAL_TARGET_ERROR =
  "The selected internal target no longer exists or is not visible to you.";

class MegaMenuPattern extends BasePattern {
  static name = "megamenu";
  static trigger = ".pat-megamenu";

  async init() {
    import("./megamenu.scss");

    const widget = this.el.closest(".megamenu-widget");
    this.textarea = widget.querySelector(".megamenu-json");
    this.contentbrowserOptions = JSON.parse(
      widget.querySelector(".megamenu-options").textContent || "{}"
    );
    this.model = this.readModel();
    this.selectedId = null;
    this.expanded = new Set();
    this.errors = {};
    this.focusId = null;
    this.renderToken = 0;

    if (this.model?.items?.length) {
      this.selectedId = this.model.items[0].id;
    }

    this.el.addEventListener("click", (event) => this.onClick(event));
    this.el.addEventListener("input", (event) => this.onInput(event));
    this.el.addEventListener("change", (event) => this.onChange(event));
    const form = this.el.closest("form");
    if (form) {
      form.addEventListener("submit", (event) => this.onSubmit(event));
    }

    await this.render();
  }

  async destroy() {
    await this.destroyPickers();
    if (super.destroy) {
      super.destroy();
    }
  }

  newId() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
      const random = (Math.random() * 16) | 0;
      const value = char === "x" ? random : (random & 0x3) | 0x8;
      return value.toString(16);
    });
  }

  escape(value) {
    return String(value == null ? "" : value).replace(
      /[&<>"']/g,
      (char) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[char]
    );
  }

  escapeAttr(value) {
    return this.escape(value);
  }

  readModel() {
    const raw = (this.textarea.value || "").trim();
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  serialize() {
    this.textarea.value = this.model ? JSON.stringify(this.model) : "";
  }

  walk(items, callback) {
    for (const item of items || []) {
      callback(item);
      if (item.children) {
        this.walk(item.children, callback);
      }
    }
  }

  findItem(id) {
    let found = null;
    this.walk(this.model?.items || [], (item) => {
      if (item.id === id) {
        found = item;
      }
    });
    return found;
  }

  findSiblings(id, items = null) {
    const list = items || this.model?.items || [];
    for (let index = 0; index < list.length; index += 1) {
      if (list[index].id === id) {
        return { array: list, index, parent: null };
      }
      if (list[index].children) {
        const result = this.findSiblings(id, list[index].children);
        if (result) {
          return { ...result, parent: list[index] };
        }
      }
    }
    return null;
  }

  childrenOf(parentId) {
    if (!parentId) {
      return this.model.items;
    }
    const parent = this.findItem(parentId);
    return parent && parent.children ? parent.children : this.model.items;
  }

  pathTo(id, items = null, trail = []) {
    const list = items || this.model?.items || [];
    for (const item of list) {
      if (item.id === id) {
        return trail;
      }
      if (item.children) {
        const result = this.pathTo(id, item.children, [...trail, item.id]);
        if (result) {
          return result;
        }
      }
    }
    return null;
  }

  errorCountFor(id) {
    return Object.keys(this.errors).filter((key) => key.startsWith(`${id}:`))
      .length;
  }

  targetSummary(item) {
    if (item.type === "folder") {
      const count = (item.children || []).length;
      return `${count} ${count === 1 ? "child" : "children"}`;
    }
    if (item.internal_uid) {
      return "Internal target";
    }
    if (item.external_url) {
      return item.external_url;
    }
    return "No target";
  }

  async render() {
    this.renderToken += 1;
    const token = this.renderToken;
    await this.destroyPickers();
    if (token !== this.renderToken) {
      return;
    }

    this.el.innerHTML = this.renderLayout();

    const selected = this.selectedId ? this.findItem(this.selectedId) : null;
    if (selected && selected.type === "link" && !selected.external_url) {
      await this.initPicker(selected);
    }

    if (this.focusId) {
      const focusId = this.focusId;
      this.focusId = null;
      const input = this.el.querySelector(
        `[data-focus-id="${this.escapeAttr(focusId)}"]`
      );
      if (input) {
        input.focus();
        input.select();
      }
    }
  }

  renderLayout() {
    if (this.model === null) {
      return this.renderInheritedState();
    }
    const items = this.model.items || [];
    const selected = this.selectedId ? this.findItem(this.selectedId) : null;
    return `
      <div class="megamenu-editor">
        <div class="megamenu-live" aria-live="polite"></div>
        <div class="megamenu-tree-pane">
          <div class="megamenu-toolbar">
            <strong>Menu tree</strong>
            <span class="megamenu-spacer"></span>
            <button type="button" data-action="add-folder">+ Folder</button>
            <button type="button" data-action="add-link">+ Link</button>
            <button type="button" data-action="use-inherited">Use inherited menu</button>
          </div>
          ${items.length ? this.renderTree(items, 0) : this.renderEmptyState()}
        </div>
        <div class="megamenu-inspector">${this.renderInspector(selected)}</div>
      </div>`;
  }

  renderInheritedState() {
    return `
      <div class="megamenu-editor megamenu-inherited">
        <div class="megamenu-live" aria-live="polite"></div>
        <div class="megamenu-tree-pane">${this.renderEmptyState()}</div>
        <div class="megamenu-inspector">
          <p class="megamenu-muted">
            No menu is configured here. The nearest ancestor menu is inherited.
          </p>
        </div>
      </div>`;
  }

  renderEmptyState() {
    const inherited = this.model === null;
    return `
      <div class="megamenu-empty">
        <h3>${inherited ? "No menu configured" : "This menu is intentionally empty"}</h3>
        <p>${
          inherited
            ? "The nearest ancestor menu is inherited."
            : "The viewlet will render no navigation here."
        }</p>
        <div>
          <button type="button" data-action="add-folder">Add folder</button>
          <button type="button" data-action="add-link">Add link</button>
        </div>
      </div>`;
  }

  renderTree(items, depth) {
    return `<ul class="megamenu-tree">${items
      .map((item) => this.renderTreeRow(item, depth))
      .join("")}</ul>`;
  }

  renderTreeRow(item, depth) {
    const isFolder = item.type === "folder";
    const expanded = this.expanded.has(item.id);
    const selected = this.selectedId === item.id;
    const errorCount = this.errorCountFor(item.id);
    const title = this.escape(item.title || "(untitled)");
    const icon = this.escapeAttr(item.icon || "bi bi-circle");
    return `
      <li>
        <div class="megamenu-tree-row${selected ? " is-selected" : ""}${
          errorCount ? " has-error" : ""
        }" data-select data-id="${this.escapeAttr(item.id)}" style="--depth:${depth}">
          ${
            isFolder
              ? `<button type="button" class="megamenu-icon-btn" data-action="toggle" data-id="${this.escapeAttr(
                  item.id
                )}" aria-expanded="${expanded}" aria-label="${
                  expanded ? "Collapse" : "Expand"
                } ${title}">${expanded ? "▾" : "▸"}</button>`
              : '<span class="megamenu-toggle-spacer"></span>'
          }
          <i class="${icon}" aria-hidden="true"></i>
          <span class="megamenu-node-title">${title}</span>
          <span class="megamenu-badge megamenu-badge-${item.type}">${
            isFolder ? "Folder" : "Link"
          }</span>
          <span class="megamenu-target-summary">${this.escape(
            this.targetSummary(item)
          )}</span>
          ${
            errorCount
              ? `<span class="megamenu-error-dot" title="${errorCount} validation error(s)">!</span>`
              : ""
          }
          <span class="megamenu-row-actions">
            ${
              isFolder
                ? `<button type="button" data-action="add-folder-child" data-id="${this.escapeAttr(
                    item.id
                  )}" title="Add folder inside">+F</button>
                   <button type="button" data-action="add-link-child" data-id="${this.escapeAttr(
                     item.id
                   )}" title="Add link inside">+L</button>`
                : ""
            }
            <button type="button" data-action="move-up" data-id="${this.escapeAttr(
              item.id
            )}" title="Move up">↑</button>
            <button type="button" data-action="move-down" data-id="${this.escapeAttr(
              item.id
            )}" title="Move down">↓</button>
            <button type="button" class="megamenu-danger" data-action="delete" data-id="${this.escapeAttr(
              item.id
            )}" title="Delete">✕</button>
          </span>
        </div>
        ${
          isFolder && expanded
            ? this.renderTree(item.children || [], depth + 1)
            : ""
        }
      </li>`;
  }

  fieldText(id, field, label, value, options = {}) {
    const error = this.errors[`${id}:${field}`];
    const focus =
      field === "title" && this.focusId === id
        ? ` data-focus-id="${this.escapeAttr(id)}"`
        : "";
    return `
      <label class="megamenu-field${error ? " has-error" : ""}">
        <span class="megamenu-field-label">${this.escape(label)}${
          options.required ? " (required)" : ""
        }</span>
        <input type="text" data-id="${this.escapeAttr(id)}" data-field="${this.escapeAttr(
          field
        )}" value="${this.escapeAttr(value || "")}"${focus}${
          options.placeholder
            ? ` placeholder="${this.escapeAttr(options.placeholder)}"`
            : ""
        }>
        ${
          error
            ? `<span class="megamenu-field-error">${this.escape(error)}</span>`
            : ""
        }
      </label>`;
  }

  targetEditor(item) {
    const isExternal = !!item.external_url;
    const targetError = this.errors[`${item.id}:target`];
    return `
      <fieldset class="megamenu-target-editor">
        <legend>Target</legend>
        <label><input type="radio" name="target-${this.escapeAttr(
          item.id
        )}" data-id="${this.escapeAttr(
          item.id
        )}" data-field="target_type" value="internal" ${
          !isExternal ? "checked" : ""
        }> Internal Plone content</label>
        <label><input type="radio" name="target-${this.escapeAttr(
          item.id
        )}" data-id="${this.escapeAttr(
          item.id
        )}" data-field="target_type" value="external" ${
          isExternal ? "checked" : ""
        }> External URL</label>
        ${
          !isExternal
            ? `<div class="megamenu-picker" data-picker-node="${this.escapeAttr(
                item.id
              )}"></div>`
            : `<div class="megamenu-field${targetError ? " has-error" : ""}">
                 <span class="megamenu-field-label">External URL</span>
                 <input type="text" data-id="${this.escapeAttr(
                   item.id
                 )}" data-field="external_url" value="${this.escapeAttr(
                   item.external_url || ""
                 )}" placeholder="https://example.com">
                 ${
                   targetError
                     ? `<span class="megamenu-field-error">${this.escape(
                         targetError
                       )}</span>`
                     : ""
                 }
               </div>`
        }
        ${
          !isExternal && targetError
            ? `<span class="megamenu-field-error">${this.escape(
                targetError
              )}</span>`
            : ""
        }
        <label class="megamenu-check"><input type="checkbox" data-id="${this.escapeAttr(
          item.id
        )}" data-field="open_in_new_tab" ${
          item.open_in_new_tab ? "checked" : ""
        }> Open in a new tab</label>
      </fieldset>`;
  }

  renderInspector(item) {
    if (!item) {
      return '<p class="megamenu-muted">Select a menu item to edit it.</p>';
    }
    const isFolder = item.type === "folder";
    const errorCount = this.errorCountFor(item.id);
    const shownFields = ["title", "css_class", "icon", "target", "external_url"];
    const generalErrors = Object.entries(this.errors)
      .filter(([key]) => {
        const [errorId, field] = key.split(":");
        return errorId === item.id && !shownFields.includes(field);
      })
      .map(([, message]) => `<li>${this.escape(message)}</li>`)
      .join("");
    return `
      <div class="megamenu-inspector-header">
        <h3>${isFolder ? "Folder" : "Link"} details</h3>
        <span class="megamenu-badge megamenu-badge-${item.type}">${
          isFolder ? "Folder" : "Link"
        }</span>
        ${errorCount ? '<span class="megamenu-error-dot">!</span>' : ""}
      </div>
      ${this.fieldText(item.id, "title", "Title", item.title, { required: true })}
      ${this.fieldText(item.id, "css_class", "CSS class", item.css_class, {
        placeholder: "e.g. nav-products",
      })}
      ${this.fieldText(item.id, "icon", "Icon CSS class", item.icon, {
        placeholder: "e.g. bi bi-house",
      })}
      <div class="megamenu-icon-preview">
        Icon preview:
        <i class="${this.escapeAttr(
          item.icon || "bi bi-circle"
        )}" aria-hidden="true"></i>
      </div>
      ${
        isFolder
          ? '<p class="megamenu-help">Folders are placeholders. They group children and are not clickable.</p>'
          : this.targetEditor(item)
      }
      ${
        isFolder && (!item.children || item.children.length === 0)
          ? '<p class="megamenu-help">This folder has no children and will not appear in the menu.</p>'
          : ""
      }
      ${
        generalErrors
          ? `<ul class="megamenu-error-list">${generalErrors}</ul>`
          : ""
      }
      <div class="megamenu-inspector-actions">
        ${
          isFolder
            ? `<button type="button" data-action="add-folder-child" data-id="${this.escapeAttr(
                item.id
              )}">Add folder</button>
               <button type="button" data-action="add-link-child" data-id="${this.escapeAttr(
                 item.id
               )}">Add link</button>`
            : ""
        }
        <button type="button" data-action="move-up" data-id="${this.escapeAttr(
          item.id
        )}">Move up</button>
        <button type="button" data-action="move-down" data-id="${this.escapeAttr(
          item.id
        )}">Move down</button>
        <button type="button" class="megamenu-danger" data-action="delete" data-id="${this.escapeAttr(
          item.id
        )}">Delete</button>
      </div>`;
  }

  async destroyPickers() {
    const inputs = this.el.querySelectorAll(".pat-contentbrowser");
    for (const input of inputs) {
      const pattern = input["pattern-contentbrowser"];
      if (!pattern) {
        continue;
      }
      if (pattern.component_content_browser) {
        try {
          await unmount(pattern.component_content_browser);
        } catch {
          // The component may already be unmounted.
        }
      }
      pattern.destroy();
    }
  }

  async initPicker(item) {
    const container = this.el.querySelector(
      `.megamenu-picker[data-picker-node="${this.escapeAttr(item.id)}"]`
    );
    if (!container) {
      return;
    }
    const input = document.createElement("input");
    input.type = "text";
    input.className = "pat-contentbrowser";
    input.id = `megamenu-picker-${item.id}`;
    input.value = item.internal_uid || "";
    input.setAttribute(
      "data-pat-contentbrowser",
      JSON.stringify(this.contentbrowserOptions)
    );
    container.appendChild(input);

    let initialized = false;
    input.addEventListener("change", () => {
      const uid = (input.value || "").split(";")[0] || "";
      if (!initialized) {
        initialized = true;
        if (!uid) {
          return;
        }
      }
      if (uid !== item.internal_uid) {
        item.internal_uid = uid;
        item.external_url = "";
        delete this.errors[`${item.id}:target`];
        this.serialize();
        this.updateTreeSummary(item.id);
        const live = this.el.querySelector(".megamenu-live");
        if (live) {
          live.textContent = "Internal target selected.";
        }
        setTimeout(() => {
          const link = container.querySelector(
            ".content-browser-selected-items-wrapper a"
          );
          if (link) {
            link.focus();
          }
        }, 0);
      }
    });

    registry.scan(container, ["contentbrowser"]);
  }

  updateTreeSummary(id) {
    const item = this.findItem(id);
    if (!item) {
      return;
    }
    const element = this.el.querySelector(
      `.megamenu-tree-row[data-id="${this.escapeAttr(
        id
      )}"] .megamenu-target-summary`
    );
    if (element) {
      element.textContent = this.targetSummary(item);
    }
  }

  addItem(type, parentId) {
    if (this.model === null) {
      this.model = { version: 1, items: [] };
    }
    const siblings = this.childrenOf(parentId);
    const item =
      type === "folder"
        ? {
            id: this.newId(),
            type: "folder",
            title: "Untitled folder",
            css_class: "",
            icon: "bi bi-folder",
            children: [],
          }
        : {
            id: this.newId(),
            type: "link",
            title: "Untitled link",
            css_class: "",
            icon: "bi bi-link-45deg",
            internal_uid: "",
            external_url: "",
            open_in_new_tab: false,
          };
    siblings.push(item);
    if (parentId) {
      this.expanded.add(parentId);
    }
    this.expanded.add(item.id);
    this.selectedId = item.id;
    this.focusId = item.id;
    this.errors = {};
    this.serialize();
    this.render();
  }

  deleteItem(id) {
    const item = this.findItem(id);
    if (!item) {
      return;
    }
    if (item.children && item.children.length) {
      const confirmed = window.confirm(
        `Delete "${item.title || "Untitled folder"}" and its ${
          item.children.length
        } direct child item(s)?`
      );
      if (!confirmed) {
        return;
      }
    }
    const siblings = this.findSiblings(id);
    if (!siblings) {
      return;
    }
    siblings.array.splice(siblings.index, 1);
    if (this.selectedId === id) {
      const next =
        siblings.array[Math.min(siblings.index, siblings.array.length - 1)] ||
        siblings.parent;
      this.selectedId = next ? next.id : null;
    }
    this.expanded.delete(id);
    this.errors = {};
    this.serialize();
    this.render();
  }

  moveItem(id, delta) {
    const siblings = this.findSiblings(id);
    if (!siblings) {
      return;
    }
    const nextIndex = siblings.index + delta;
    if (nextIndex < 0 || nextIndex >= siblings.array.length) {
      return;
    }
    const [item] = siblings.array.splice(siblings.index, 1);
    siblings.array.splice(nextIndex, 0, item);
    this.serialize();
    this.render();
  }

  toggleItem(id) {
    if (this.expanded.has(id)) {
      this.expanded.delete(id);
    } else {
      this.expanded.add(id);
    }
    this.render();
  }

  selectItem(id) {
    const item = this.findItem(id);
    if (!item) {
      return;
    }
    this.selectedId = id;
    if (item.type === "folder") {
      this.expanded.add(id);
    }
    this.render();
  }

  revealItem(id) {
    const item = this.findItem(id);
    if (!item) {
      this.render();
      return;
    }
    for (const parentId of this.pathTo(id) || []) {
      this.expanded.add(parentId);
    }
    this.selectedId = id;
    this.render();
  }

  useInherited() {
    this.model = null;
    this.selectedId = null;
    this.expanded = new Set();
    this.errors = {};
    this.serialize();
    this.render();
  }

  onClick(event) {
    const actionElement = event.target.closest("[data-action]");
    if (actionElement) {
      event.preventDefault();
      event.stopPropagation();
      const action = actionElement.dataset.action;
      const id = actionElement.dataset.id;
      const parent = actionElement.dataset.parent || null;
      if (action === "add-folder") this.addItem("folder", parent);
      else if (action === "add-link") this.addItem("link", parent);
      else if (action === "add-folder-child") this.addItem("folder", id);
      else if (action === "add-link-child") this.addItem("link", id);
      else if (action === "delete") this.deleteItem(id);
      else if (action === "move-up") this.moveItem(id, -1);
      else if (action === "move-down") this.moveItem(id, 1);
      else if (action === "toggle") this.toggleItem(id);
      else if (action === "use-inherited") this.useInherited();
      return;
    }
    const selectElement = event.target.closest("[data-select]");
    if (selectElement) {
      this.selectItem(selectElement.dataset.id);
    }
  }

  onInput(event) {
    const element = event.target.closest("[data-field]");
    if (!element || element.type === "radio" || element.type === "checkbox") {
      return;
    }
    const id = element.dataset.id;
    const field = element.dataset.field;
    const item = this.findItem(id);
    if (!item) {
      return;
    }
    item[field] = element.value;
    delete this.errors[`${id}:${field}`];
    if (field === "external_url") {
      delete this.errors[`${id}:target`];
    }
    this.serialize();
  }

  onChange(event) {
    const element = event.target.closest("[data-field]");
    if (!element) {
      return;
    }
    const id = element.dataset.id;
    const field = element.dataset.field;
    const item = this.findItem(id);
    if (!item) {
      return;
    }

    if (field === "target_type") {
      if (element.value === "internal") {
        item.internal_uid = item.internal_uid || "";
        item.external_url = "";
      } else {
        item.internal_uid = "";
        item.external_url = item.external_url || "";
      }
      delete this.errors[`${id}:target`];
      this.serialize();
      this.render();
      return;
    }

    if (field === "open_in_new_tab") {
      item.open_in_new_tab = element.checked;
      this.serialize();
      return;
    }

    let value = element.value;
    if (field === "title" || field === "external_url") {
      value = value.trim();
    }
    if (field === "external_url") {
      value = value.replace(/^([A-Za-z][A-Za-z0-9+.-]*:)/, (match) =>
        match.toLowerCase()
      );
    }
    item[field] = value;
    delete this.errors[`${id}:${field}`];
    if (field === "external_url") {
      delete this.errors[`${id}:target`];
    }
    this.serialize();
    this.render();
  }

  onSubmit(event) {
    this.errors = this.validate();
    if (Object.keys(this.errors).length) {
      event.preventDefault();
      const firstId = Object.keys(this.errors)[0].split(":")[0];
      this.focusId = firstId;
      this.revealItem(firstId);
      return;
    }
    this.serialize();
  }

  validExternalUrl(url) {
    if (typeof url !== "string" || !url.trim() || /\s/.test(url)) {
      return false;
    }
    try {
      const parsed = new URL(url);
      const scheme = parsed.protocol.replace(":", "").toLowerCase();
      if (!["http", "https", "mailto", "tel"].includes(scheme)) {
        return false;
      }
      if (
        (scheme === "http" || scheme === "https") &&
        !HOST_RE.test(parsed.hostname)
      ) {
        return false;
      }
      if (
        (scheme === "mailto" || scheme === "tel") &&
        !parsed.pathname
      ) {
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }

  validate() {
    const errors = {};
    if (this.model === null) {
      return errors;
    }
    if (!this.model || this.model.version !== 1) {
      errors["model:version"] =
        "Unsupported menu version. Expected version 1.";
      return errors;
    }
    const seen = new Set();
    const walk = (items) => {
      for (const item of items) {
        const id = item.id || "";
        if (!UUID_RE.test(id) || seen.has(id)) {
          errors[`${id}:id`] =
            "Menu item IDs must be unique and valid UUIDs.";
        } else {
          seen.add(id);
        }
        const title = typeof item.title === "string" ? item.title : "";
        if (!title.trim()) {
          errors[`${id}:title`] = "Title is required.";
        } else if (title.length > 200) {
          errors[`${id}:title`] = "Use at most 200 characters.";
        }
        if (
          typeof item.css_class !== "string" ||
          !CSS_RE.test(item.css_class)
        ) {
          errors[`${id}:css_class`] = CSS_ERROR;
        } else if (item.css_class.length > 200) {
          errors[`${id}:css_class`] = "Use at most 200 characters.";
        }
        if (typeof item.icon !== "string" || !CSS_RE.test(item.icon)) {
          errors[`${id}:icon`] = CSS_ERROR;
        } else if (item.icon.length > 200) {
          errors[`${id}:icon`] = "Use at most 200 characters.";
        }

        if (item.type === "folder") {
          if (TARGET_KEYS.some((key) => key in item)) {
            errors[`${id}:target`] = "A folder cannot have a target.";
          }
          if (!Array.isArray(item.children)) {
            errors[`${id}:children`] = "A folder must have children.";
          } else {
            walk(item.children);
          }
        } else if (item.type === "link") {
          if ("children" in item) {
            errors[`${id}:children`] = "A link cannot have children.";
          }
          const hasInternal =
            typeof item.internal_uid === "string" &&
            item.internal_uid.trim() !== "";
          const hasExternal =
            typeof item.external_url === "string" &&
            item.external_url.trim() !== "";
          if (hasInternal === hasExternal) {
            errors[`${id}:target`] =
              "Choose exactly one target: internal or external.";
          } else if (hasExternal && !this.validExternalUrl(item.external_url)) {
            errors[`${id}:target`] = URL_ERROR;
          } else if (hasInternal && anyWhitespace(item.internal_uid)) {
            errors[`${id}:target`] = INTERNAL_TARGET_ERROR;
          }
        } else {
          errors[`${id}:type`] = "A menu item must be a folder or a link.";
        }
      }
    };
    walk(Array.isArray(this.model.items) ? this.model.items : []);
    return errors;
  }
}

function anyWhitespace(value) {
  return /\s/.test(value);
}

registry.register(MegaMenuPattern);

export default MegaMenuPattern;
export { MegaMenuPattern };

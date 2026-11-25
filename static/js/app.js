// Small Alpine.js components shared by every page.
// Loaded before Alpine, so components are registered on "alpine:init".

document.addEventListener("alpine:init", () => {
  const STORAGE_KEY = "walleto.sidebarCollapsed";

  function readCollapsed() {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch {
      return false; // storage blocked (private mode): fall back to expanded
    }
  }

  // Sidebar collapse, remembered per browser.
  Alpine.data("shell", () => ({
    collapsed: readCollapsed(),
    toggle() {
      this.collapsed = !this.collapsed;
      try {
        localStorage.setItem(STORAGE_KEY, this.collapsed ? "1" : "0");
      } catch {
        /* ignore */
      }
    },
  }));

  // Rupiah typed the way people write it ("2.500.000", "Rp 1,250,000"); 0 when not a whole number.
  // The server's AmountField is the real check; this only drives the live previews.
  function parseRupiah(text) {
    const digits = String(text || "").replace(/^\s*rp\.?\s*/i, "").replace(/[.,\s]/g, "");
    return /^\d{1,15}$/.test(digits) ? Number(digits) : 0;
  }
  function rupiah(value) {
    const sign = value < 0 ? "−" : "";
    return `${sign}Rp${Math.abs(value).toLocaleString("id-ID")}`;
  }
  function field(root, name) {
    return root.querySelector(`[name="${name}"]`);
  }

  // Add/edit wallet modal: the preview card follows the name and type fields.
  Alpine.data("walletPreview", () => ({
    name: "",
    type: "",
    init() {
      this.sync();
    },
    sync() {
      const name = field(this.$root, "name");
      const type = field(this.$root, "type");
      this.name = name ? name.value.trim() : "";
      this.type = type && type.selectedOptions[0] ? type.selectedOptions[0].text : "";
    },
  }));

  // Transfer modal (transfers spec, "Transfer preview"). Balances come from a
  // json_script tag rendered by the view: {id: {name, balance}}.
  Alpine.data("transferForm", () => ({
    wallets: {},
    from: "",
    to: "",
    amount: 0,
    init() {
      const data = this.$root.querySelector("#transfer-wallets");
      this.wallets = data ? JSON.parse(data.textContent) : {};
      this.sync();
    },
    sync() {
      const from = field(this.$root, "from_wallet");
      const to = field(this.$root, "to_wallet");
      this.from = from ? from.value : "";
      this.to = to ? to.value : "";
      this.amount = parseRupiah(field(this.$root, "amount")?.value);
    },
    swap() {
      const from = field(this.$root, "from_wallet");
      const to = field(this.$root, "to_wallet");
      [from.value, to.value] = [to.value, from.value];
      // Let the styled menus (enhanceSelect) show the swapped values.
      from.dispatchEvent(new Event("change", { bubbles: true }));
      to.dispatchEvent(new Event("change", { bubbles: true }));
      this.sync();
    },
    get source() {
      return this.wallets[this.from];
    },
    get target() {
      return this.wallets[this.to];
    },
    get insufficient() {
      return !!this.source && this.amount > this.source.balance;
    },
    money(value) {
      return rupiah(value);
    },
    get submitLabel() {
      return this.amount > 0 ? `Transfer ${rupiah(this.amount)}` : "Record transfer";
    },
  }));

  // Goal detail chart (savings-goals spec, "Goal detail page"): saved per day as a
  // stepline, and the straight plan line when the goal has a deadline. Data comes
  // from a json_script tag; ApexCharts is loaded only on that page.
  Alpine.data("goalChart", () => ({
    init() {
      const data = JSON.parse(document.getElementById("goal-chart-data").textContent);
      const draw = () => {
        const points = (rows) => rows.map(([day, value]) => ({ x: new Date(`${day}T00:00:00`).getTime(), y: value }));
        const series = [{ name: "Saved", type: "line", data: points(data.saved) }];
        if (data.plan) series.push({ name: "Plan", type: "line", data: points(data.plan) });
        const chart = new window.ApexCharts(this.$refs.chart, {
          chart: { height: 260, type: "line", fontFamily: "inherit", toolbar: { show: false }, zoom: { enabled: false }, animations: { enabled: false } },
          series,
          colors: ["#1f5c4a", "#99aa99"],
          stroke: { width: [2.5, 1.5], curve: ["stepline", "straight"], dashArray: [0, 5] },
          markers: { size: 0, hover: { size: 4 } },
          grid: { borderColor: "#eaece3", strokeDashArray: 3, padding: { left: 8, right: 8 } },
          xaxis: { type: "datetime", labels: { style: { colors: "#92918a", fontSize: "11px" }, datetimeUTC: false }, axisBorder: { show: false }, axisTicks: { show: false } },
          yaxis: { min: 0, max: Math.max(data.target, ...data.saved.map(([, v]) => v)), tickAmount: 4, labels: { style: { colors: "#92918a", fontSize: "11px" }, formatter: (v) => rupiah(Math.round(v)) } },
          tooltip: { x: { format: "d MMM yyyy" }, y: { formatter: (v) => rupiah(Math.round(v)) } },
          legend: { show: false },
          dataLabels: { enabled: false },
        });
        chart.render();
      };
      if (window.ApexCharts) draw();
      else window.addEventListener("load", draw, { once: true });
    },
  }));

  // Savings goals order (savings-goals spec, "Main goal"): drag the grip handle, or
  // focus it and press the up/down arrow keys. The order is saved right away; when
  // a different goal ends up first, the page reloads so it gets the big card.
  Alpine.data("goalOrder", () => ({
    first: null,
    init() {
      this.first = this.ids()[0];
      const start = () =>
        window.Sortable.create(this.$el, {
          handle: ".drag-handle",
          draggable: "[data-goal-id]",
          animation: 150,
          ghostClass: "opacity-40",
          onEnd: () => this.save(),
        });
      if (window.Sortable) start();
      else window.addEventListener("load", start, { once: true });
    },
    ids() {
      return [...this.$el.querySelectorAll(":scope > [data-goal-id]")].map((el) => el.dataset.goalId);
    },
    move(handle, step) {
      const item = handle.closest("[data-goal-id]");
      const sibling = step < 0 ? item.previousElementSibling : item.nextElementSibling;
      if (!sibling || !sibling.matches("[data-goal-id]")) return;
      if (step < 0) sibling.before(item);
      else sibling.after(item);
      handle.focus();
      this.save();
    },
    async save() {
      const body = new FormData();
      this.ids().forEach((id) => body.append("order", id));
      const headers = JSON.parse(document.body.getAttribute("hx-headers") || "{}");
      const response = await fetch(this.$el.dataset.orderUrl, { method: "POST", body, headers });
      if (response.ok && this.ids()[0] !== this.first) window.location.reload();
    },
  }));

  // Date range popover (period-picker spec, add-date-range design decision 6).
  // Draws a Monday-first month grid; the first click is the start, the second the
  // end, which fills the From/To fields and submits the form (HTMX swaps the page).
  // The server applies every rule (no future days, 92 days at most, whole month).
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December"];
  const SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const isoDate = (y, m, d) => `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;

  Alpine.data("periodPicker", () => ({
    ready: false,
    open: false,
    start: "",
    end: "",
    today: "",
    anchor: null, // first click, waiting for the second
    hover: null,
    viewYear: 0,
    viewMonth: 0, // 0-11
    init() {
      const data = this.$el.dataset;
      this.start = data.start;
      this.end = data.end;
      this.today = data.today;
      const [year, month] = this.end.split("-").map(Number);
      this.viewYear = year;
      this.viewMonth = month - 1;
      this.ready = true;
    },
    get title() {
      return `${MONTHS[this.viewMonth]} ${this.viewYear}`;
    },
    get canStepForward() {
      return isoDate(this.viewYear, this.viewMonth, 1) < this.today.slice(0, 8) + "01";
    },
    get hint() {
      return this.anchor ? "Now choose the last day." : "Choose the first day.";
    },
    get cells() {
      const first = new Date(Date.UTC(this.viewYear, this.viewMonth, 1));
      const blanks = (first.getUTCDay() + 6) % 7; // Monday first
      const days = new Date(Date.UTC(this.viewYear, this.viewMonth + 1, 0)).getUTCDate();
      const cells = [];
      for (let i = 0; i < blanks; i++) cells.push({ key: `b${i}`, iso: "", day: "", disabled: true, label: "" });
      for (let d = 1; d <= days; d++) {
        const iso = isoDate(this.viewYear, this.viewMonth, d);
        cells.push({ key: iso, iso, day: d, disabled: iso > this.today, label: `${d} ${SHORT[this.viewMonth]} ${this.viewYear}` });
      }
      return cells;
    },
    // The range to highlight: the chosen one, or the one being picked.
    range() {
      if (this.anchor) {
        const other = this.hover || this.anchor;
        return other < this.anchor ? [other, this.anchor] : [this.anchor, other];
      }
      // The current month runs to its last day; only highlight up to today.
      return [this.start, this.end > this.today ? this.today : this.end];
    },
    isSelected(cell) {
      const [from, to] = this.range();
      return Boolean(cell.iso) && (cell.iso === from || cell.iso === to);
    },
    dayClass(cell) {
      if (!cell.iso) return "is-blank";
      const [from, to] = this.range();
      return {
        "is-edge": cell.iso === from || cell.iso === to,
        "is-between": cell.iso > from && cell.iso < to,
        "is-today": cell.iso === this.today,
      };
    },
    step(delta) {
      if (delta > 0 && !this.canStepForward) return;
      const index = this.viewYear * 12 + this.viewMonth + delta;
      this.viewYear = Math.floor(index / 12);
      this.viewMonth = index % 12;
    },
    pick(iso) {
      if (!iso || iso > this.today) return;
      if (!this.anchor) {
        this.anchor = iso;
        this.hover = iso;
        return;
      }
      const [from, to] = iso < this.anchor ? [iso, this.anchor] : [this.anchor, iso];
      this.anchor = null;
      this.$refs.from.value = from;
      this.$refs.to.value = to;
      this.close();
      this.$refs.form.requestSubmit();
    },
    close() {
      this.anchor = null;
      this.hover = null;
      if (this.$refs.details) this.$refs.details.open = false;
    },
  }));

  // A styled menu over a native <select> (Transactions filters). The select keeps the value and
  // the form's change event, so HTMX filtering and the no-JavaScript form are unchanged.
  Alpine.data("selectMenu", () => ({
    ready: false,
    open: false,
    groups: [],
    current: { value: "", label: "", color: "" },
    init() {
      const select = this.$refs.select;
      const item = (option) => ({ value: option.value, label: option.textContent.trim(), color: option.dataset.color || "" });
      const groups = [{ key: "top", label: "", items: [] }];
      for (const child of select.children) {
        if (child.tagName === "OPTGROUP") {
          groups.push({ key: child.label, label: child.label, items: [...child.children].map(item) });
        } else {
          groups[0].items.push(item(child));
        }
      }
      this.groups = groups.filter((g) => g.items.length);
      const selected = select.selectedOptions[0];
      this.current = selected ? item(selected) : this.groups[0].items[0];
      this.ready = true;
    },
    toggle() {
      this.open = !this.open;
    },
    close() {
      this.open = false;
    },
    choose(item) {
      this.current = item;
      this.open = false;
      const select = this.$refs.select;
      if (select.value !== item.value) {
        select.value = item.value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
    },
  }));

  // Assistant plan card (add-assistant-planning design decision 4): Edit unlocks the amounts, and the
  // per-day values and the total follow as the user types. The server checks everything again on Apply.
  Alpine.data("planCard", () => ({
    editing: false,
    left: 0,
    days: 1,
    diff: 0,
    totalText: "",
    init() {
      this.left = Number(this.$root.dataset.left) || 0;
      this.days = Math.max(Number(this.$root.dataset.days) || 1, 1);
      this.recount();
    },
    edit() {
      this.editing = true;
      this.$nextTick(() => this.$root.querySelector("input[data-amount]")?.focus());
    },
    // Show the typed amount with thousands dots again (70000 -> 70.000) once the box is left.
    tidy(input) {
      const value = Number(String(input.value).replace(/[^0-9]/g, "")) || 0;
      input.value = rupiah(value).replace(/^.*Rp/, "");
    },
    recount() {
      let total = 0;
      this.$root.querySelectorAll("input[data-amount]").forEach((input) => {
        const value = Number(String(input.value).replace(/[^0-9]/g, "")) || 0;
        total += value;
        const cell = input.closest("tr")?.querySelector("[data-per-day]");
        if (cell) cell.textContent = rupiah(Math.floor(value / this.days));
      });
      this.diff = total - this.left;
      if (this.diff === 0) {
        this.totalText = `Adds up to ${rupiah(total)} of ${rupiah(this.left)} left.`;
      } else {
        const side = this.diff > 0 ? "over" : "under";
        this.totalText = `${rupiah(total)}: ${rupiah(Math.abs(this.diff))} ${side} the ${rupiah(this.left)} left.`;
      }
    },
  }));

  // Toast that closes itself after about four seconds.
  Alpine.data("toast", () => ({
    visible: true,
    init() {
      setTimeout(() => (this.visible = false), 4000);
    },
  }));
});

// Money inputs (AmountField, `data-money`): add dot separators while typing,
// 2000000 -> 2.000.000, keeping the caret after the same digit. Runs in the
// capture phase, so Alpine previews listening on the form read the formatted value.
// The server parses "2.000.000" either way, so without JavaScript nothing breaks.
document.addEventListener(
  "input",
  (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.hasAttribute("data-money")) return;
    const caret = input.selectionStart ?? input.value.length;
    const digitsBeforeCaret = input.value.slice(0, caret).replace(/\D/g, "").replace(/^0+(?=\d)/, "").length;
    const digits = input.value.replace(/\D/g, "").replace(/^0+(?=\d)/, "").slice(0, 15);
    const formatted = digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    if (formatted === input.value) return;
    input.value = formatted;
    // Put the caret back after the same number of digits.
    let position = 0;
    for (let seen = 0; position < formatted.length && seen < digitsBeforeCaret; position++) {
      if (/\d/.test(formatted[position])) seen++;
    }
    input.setSelectionRange(position, position);
  },
  true,
);

// Assistant chat (add-assistant design decision 5): on send, show the question as a bubble and a
// "thinking" bubble at once; the server's turn (question + answer) replaces them when it arrives.
window.walletoChat = {
  send(form) {
    const field = form.querySelector("[name=question]");
    const text = (field && field.value || "").trim();
    const list = document.getElementById("conversation");
    if (!text || !list) return;
    document.getElementById("suggestions")?.remove();
    const pending = document.createElement("div");
    pending.id = "pending-turn";
    pending.className = "contents";
    const bubble = document.createElement("div");
    bubble.className = "assistant-message is-user";
    const p = document.createElement("p");
    p.textContent = text; // text, never HTML
    bubble.append(p);
    const thinking = document.createElement("div");
    thinking.className = "assistant-thinking";
    thinking.setAttribute("role", "status");
    thinking.innerHTML = '<span></span><span></span><span></span><span class="sr-only">Thinking…</span>';
    pending.append(bubble, thinking);
    list.append(pending);
    thinking.scrollIntoView({ block: "nearest" });
    if (field.tagName === "TEXTAREA") {
      field.value = ""; // the request already holds the text
      field.style.height = "";
    }
  },
  // htmx fires beforeSwap on the swap target (#conversation), not on the form, so this listens there.
  settle(event) {
    if (event.detail.target?.id === "conversation") document.getElementById("pending-turn")?.remove();
  },
  done(form, event) {
    if (!event.detail.successful) {
      // No answer came back (network or server error): keep the question visible with a note.
      const thinking = document.querySelector("#pending-turn .assistant-thinking");
      if (thinking) {
        thinking.className = "assistant-message text-clay";
        thinking.textContent = "The assistant couldn't answer right now. Try again.";
      }
      document.getElementById("pending-turn")?.removeAttribute("id");
    }
    form.querySelector("textarea")?.focus();
  },
};

document.addEventListener("htmx:beforeSwap", (event) => window.walletoChat.settle(event));

// Styled dropdowns for every form <select class="input"> (modals, form pages, the style guide).
// The native select stays in the form, hidden, and keeps the value, the label link, validation and
// the change event; this only draws a button and a menu over it. Without JavaScript nothing changes.
(function () {
  const CHEVRON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
  const CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>';

  function closeAll(except) {
    document.querySelectorAll(".select-wrap.is-open").forEach((wrap) => {
      if (wrap !== except) wrap._close(false);
    });
  }

  function enhance(select) {
    if (select.dataset.enhanced || select.multiple || select.hasAttribute("x-ref")) return;
    select.dataset.enhanced = "1";

    const wrap = document.createElement("div");
    wrap.className = "select-wrap";
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);
    select.classList.add("sr-only");
    select.tabIndex = -1;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "input select-trigger";
    button.setAttribute("aria-haspopup", "listbox");
    button.setAttribute("aria-expanded", "false");
    const label = document.createElement("span");
    label.className = "truncate";
    button.append(label);
    button.insertAdjacentHTML("beforeend", '<span class="select-chevron">' + CHEVRON + "</span>");
    const menu = document.createElement("div");
    menu.className = "select-menu popover";
    menu.setAttribute("role", "listbox");
    menu.hidden = true;
    wrap.append(button, menu);

    const fieldLabel = select.id ? document.querySelector('label[for="' + select.id + '"]') : null;
    const name = fieldLabel ? fieldLabel.textContent.trim() : "";
    if (name) menu.setAttribute("aria-label", name);

    function render() {
      menu.innerHTML = "";
      const addOption = (option) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "select-menu-item";
        item.setAttribute("role", "option");
        item.disabled = option.disabled;
        const selected = option.value === select.value;
        item.setAttribute("aria-selected", String(selected));
        if (selected) item.classList.add("is-selected");
        const text = document.createElement("span");
        text.className = "flex-1 truncate";
        text.textContent = option.textContent.trim();
        item.append(text);
        if (selected) item.insertAdjacentHTML("beforeend", '<span class="text-forest">' + CHECK + "</span>");
        item.addEventListener("click", () => choose(option.value));
        menu.append(item);
      };
      for (const child of select.children) {
        if (child.tagName === "OPTGROUP") {
          const heading = document.createElement("p");
          heading.className = "select-menu-group";
          heading.textContent = child.label;
          menu.append(heading);
          [...child.children].forEach(addOption);
        } else {
          addOption(child);
        }
      }
    }

    function sync() {
      const option = select.selectedOptions[0];
      label.textContent = option ? option.textContent.trim() : "";
      label.classList.toggle("text-placeholder", !option || option.value === "");
      button.disabled = select.disabled;
      button.setAttribute("aria-label", (name ? name + ": " : "") + label.textContent);
    }

    // Fixed to the screen so a scrolling modal cannot clip it; opens upward when there is no room below.
    function place() {
      const rect = button.getBoundingClientRect();
      const below = window.innerHeight - rect.bottom - 8;
      const above = rect.top - 8;
      const height = Math.min(menu.scrollHeight, 300);
      const up = below < Math.min(height, 200) && above > below;
      menu.style.position = "fixed";
      menu.style.left = rect.left + "px";
      menu.style.width = rect.width + "px";
      menu.style.maxHeight = Math.max(Math.min(300, up ? above : below), 120) + "px";
      menu.style.top = up ? "" : rect.bottom + 4 + "px";
      menu.style.bottom = up ? window.innerHeight - rect.top + 4 + "px" : "";
    }

    function open() {
      closeAll(wrap);
      render();
      menu.hidden = false;
      place();
      wrap.classList.add("is-open");
      button.setAttribute("aria-expanded", "true");
      const target = menu.querySelector(".is-selected") || menu.querySelector(".select-menu-item:not(:disabled)");
      if (target) target.focus();
    }

    wrap._close = (focusButton) => {
      menu.hidden = true;
      wrap.classList.remove("is-open");
      button.setAttribute("aria-expanded", "false");
      if (focusButton) button.focus();
    };

    function choose(value) {
      wrap._close(true);
      if (select.value !== value) {
        select.value = value;
        select.dispatchEvent(new Event("input", { bubbles: true }));
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      sync();
    }

    button.addEventListener("click", () => (wrap.classList.contains("is-open") ? wrap._close(false) : open()));
    button.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        open();
      }
    });
    menu.addEventListener("keydown", (event) => {
      const items = [...menu.querySelectorAll(".select-menu-item:not(:disabled)")];
      const index = items.indexOf(document.activeElement);
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        const next = event.key === "ArrowDown" ? Math.min(index + 1, items.length - 1) : Math.max(index - 1, 0);
        if (items[next]) items[next].focus();
      } else if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation(); // keep a surrounding modal open
        wrap._close(true);
      } else if (event.key === "Tab") {
        wrap._close(false);
      }
    });
    // The field label points at the hidden select: send its focus to the button.
    select.addEventListener("focus", () => button.focus());
    select.addEventListener("change", sync);
    sync();
  }

  function enhanceAll(root) {
    const scope = root && root.querySelectorAll ? root : document;
    if (scope.matches && scope.matches("select.input")) enhance(scope);
    scope.querySelectorAll("select.input").forEach(enhance);
  }

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".select-wrap")) closeAll(null);
  });
  // A fixed menu would float away from its field: close it when anything scrolls or resizes.
  window.addEventListener("resize", () => closeAll(null));
  document.addEventListener("scroll", (event) => {
    if (!(event.target.closest && event.target.closest(".select-menu"))) closeAll(null);
  }, true);
  document.addEventListener("DOMContentLoaded", () => enhanceAll(document));
  document.addEventListener("htmx:load", (event) => enhanceAll(event.target));
})();

// Failed and slow requests (polish-and-deploy design decision 6, app-shell spec).
// HTMX does not swap 4xx/5xx responses, so the page (and a modal with what was typed) stays as it was;
// this only tells the user. Same look as the server toasts in components/toasts.html.
(function () {
  const INFO = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg>';
  const CLOSE = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>';

  function stack() {
    let box = document.getElementById("client-toasts");
    if (!box) {
      box = document.createElement("div");
      box.id = "client-toasts";
      box.className = "pointer-events-none fixed right-4 bottom-24 z-50 flex flex-col gap-2 md:right-6 md:bottom-6";
      box.setAttribute("aria-live", "assertive");
      // A popover sits in the top layer, so the toast shows above an open <dialog> modal too.
      box.setAttribute("popover", "manual");
      box.style.cssText = "top:auto;left:auto;margin:0;border:0;padding:0;background:transparent;overflow:visible";
      document.body.append(box);
    }
    if (box.showPopover) {
      if (box.matches(":popover-open")) box.hidePopover();
      box.showPopover(); // re-open so it is the newest top-layer element, above any modal
    }
    return box;
  }

  window.walletoToast = function (text) {
    const box = stack();
    if ([...box.querySelectorAll("[data-toast-text]")].some((p) => p.textContent === text)) return; // no duplicates
    const toast = document.createElement("div");
    toast.className = "toast toast-error pointer-events-auto";
    toast.setAttribute("role", "alert");
    toast.innerHTML = `<span class="toast-icon">${INFO}</span><div class="flex-1 pt-0.5"><p class="text-control text-ink" data-toast-text></p></div>` +
      `<button type="button" class="btn-icon -my-1.5 size-7" aria-label="Dismiss">${CLOSE}</button>`;
    toast.querySelector("[data-toast-text]").textContent = text; // text, never HTML
    const close = () => toast.remove();
    toast.querySelector("button").addEventListener("click", close);
    setTimeout(close, 4000);
    box.append(toast);
  };

  document.addEventListener("htmx:responseError", () => window.walletoToast("Something went wrong. Try again."));
  document.addEventListener("htmx:sendError", () => window.walletoToast("You're offline. Check your connection and try again."));

  // Thin bar at the top while any request runs; CSS delays it ~300ms so fast requests never flash it.
  let running = 0;
  const root = document.documentElement;
  document.addEventListener("htmx:beforeRequest", () => { running += 1; root.classList.add("is-loading"); });
  const done = () => { running = Math.max(0, running - 1); if (!running) root.classList.remove("is-loading"); };
  document.addEventListener("htmx:afterRequest", done);
})();

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
  settle() {
    document.getElementById("pending-turn")?.remove();
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

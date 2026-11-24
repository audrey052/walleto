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


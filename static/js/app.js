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

  // Toast that closes itself after about four seconds.
  Alpine.data("toast", () => ({
    visible: true,
    init() {
      setTimeout(() => (this.visible = false), 4000);
    },
  }));
});

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

  // Toast that closes itself after about four seconds.
  Alpine.data("toast", () => ({
    visible: true,
    init() {
      setTimeout(() => (this.visible = false), 4000);
    },
  }));
});

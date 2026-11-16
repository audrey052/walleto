import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Amount, Icon, Modal, Progress, money, type IconName } from "./components/ui";
import DesignSystem from "./DesignSystem";
import { categories, formatDate, initialTransactions, wallets, type Transaction } from "./data";

type Page =
  | "Dashboard"
  | "Transactions"
  | "Wallets"
  | "Budget"
  | "Savings goals"
  | "Assistant"
  | "Design system";
const navigation: { label: Page; icon: IconName }[] = [
  { label: "Dashboard", icon: "dashboard" },
  { label: "Transactions", icon: "transactions" },
  { label: "Wallets", icon: "wallet" },
  { label: "Budget", icon: "budget" },
  { label: "Savings goals", icon: "goal" },
  { label: "Assistant", icon: "assistant" },
];

function MiniTrend({ expense = false }: { expense?: boolean }) {
  return (
    <svg width="89" height="30" viewBox="0 0 89 30" fill="none" aria-hidden="true">
      <path
        d={
          expense
            ? "M1 24 9 20 17 23 25 13 33 16 41 10 49 15 57 8 65 11 73 4 81 7 88 2"
            : "M1 25 9 25 17 25 25 25 33 25 41 25 49 17 57 17 65 17 73 17 81 5 88 5"
        }
        stroke={expense ? "#A8ADA3" : "#6C9380"}
        strokeWidth="1.5"
      />
    </svg>
  );
}

function SpendingChart({
  data,
  monthLabel,
  monthIndex,
  year,
  currentMonth,
  budget,
}: {
  data: number[];
  monthLabel: string;
  monthIndex: number;
  year: number;
  currentMonth: boolean;
  budget: number;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(800000, ...data);
  const days = new Date(year, monthIndex + 1, 0).getDate();
  const limit = Math.round(budget / days);
  return (
    <section className="panel chart-panel">
      <div className="section-heading">
        <div>
          <h2>Daily spending</h2>
          <p>Your spending, one day at a time.</p>
        </div>
        <span className="chart-legend">
          <i />
          Daily budget
        </span>
      </div>
      <div className="chart-container">
        <div className="y-labels">
          {[max, max * 0.75, max * 0.5, max * 0.25, 0].map((n, i) => (
            <span key={i}>{n === 0 ? "0" : `${Math.round(n / 1000)}k`}</span>
          ))}
        </div>
        <div className="chart-plot">
          <div className="chart-grid">
            {[0, 1, 2, 3, 4].map((i) => (
              <i key={i} />
            ))}
          </div>
          <div className="budget-line" style={{ bottom: `${(limit / max) * 100}%` }}>
            <span>{money(limit)}</span>
          </div>
          <div className="bars">
            {Array.from({ length: days }, (_, i) => (
              <div key={i} className={`bar-cell ${currentMonth && i === 13 ? "today" : ""}`}>
                {data[i] !== undefined ? (
                  <button
                    aria-label={`${i + 1} ${monthLabel}: ${money(data[i])}`}
                    className={`chart-bar ${currentMonth && i === 13 ? "current" : ""}`}
                    style={{ height: `${(data[i] / max) * 100}%` }}
                    onMouseEnter={() => setHover(i)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(i)}
                    onBlur={() => setHover(null)}
                  >
                    {hover === i && (
                      <span className="chart-tooltip">
                        <small>
                          {i + 1} {monthLabel}
                        </small>
                        {money(data[i])}
                      </span>
                    )}
                  </button>
                ) : (
                  <span className="future-bar" />
                )}
              </div>
            ))}
          </div>
          <div className="x-labels">
            {Array.from({ length: days }, (_, i) => (
              <span className={currentMonth && i === 13 ? "current-label" : ""} key={i}>
                {[0, 4, 9, 13, 19, 24, days - 1].includes(i) ? String(i + 1).padStart(2, "0") : ""}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="chart-footer">
        <span>
          <i className="legend-square" />
          Daily expenses
        </span>
        <span>
          {currentMonth ? "01–14" : `01–${days}`} {monthLabel} {year}
        </span>
      </div>
    </section>
  );
}

function TransactionTable({
  transactions,
  compact = false,
}: {
  transactions: Transaction[];
  compact?: boolean;
}) {
  return (
    <div className="table-scroll">
      <table className="transaction-table">
        <thead>
          <tr>
            <th>Transaction</th>
            <th>Category</th>
            <th>Wallet</th>
            <th>Date</th>
            <th className="text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => {
            const category = categories.find((c) => c.name === t.category);
            return (
              <tr key={t.id}>
                <td>
                  <div className="merchant-cell">
                    <span
                      className={`merchant-icon ${t.merchant === "GoFood" || t.merchant === "Grab" ? "green-merchant" : ""}`}
                    >
                      <Icon name={t.income ? "arrow-down" : category?.icon || "other"} size={18} />
                    </span>
                    <div>
                      <strong>{t.merchant}</strong>
                      <p>{t.note}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`category-tag ${category?.tag || "food-tag"}`}>
                    <i />
                    {t.category}
                  </span>
                </td>
                <td>
                  <span className="wallet-cell">
                    <i className={t.wallet.toLowerCase()} />
                    {t.wallet}
                  </span>
                </td>
                <td className="date-cell">{formatDate(t.date)}</td>
                <td className={`transaction-amount ${t.income ? "positive" : ""}`}>
                  {t.income ? "+" : "−"}
                  {money(t.amount)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {transactions.length === 0 && (
        <div className="empty-state">
          <span className="empty-icon">
            <Icon name="transactions" size={24} />
          </span>
          <h3>No transactions here yet.</h3>
          <p>
            {compact
              ? "A little space for a fresh month."
              : "Try another search or add a new transaction."}
          </p>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>("Dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [monthOffset, setMonthOffset] = useState(0);
  const [transactions, setTransactions] = useState(initialTransactions);
  const [wallet, setWallet] = useState("All wallets");
  const [modal, setModal] = useState<
    "transaction" | "budget" | "goal" | "goal-settings" | "help" | null
  >(null);
  const [toast, setToast] = useState("");
  const [notifications, setNotifications] = useState(false);
  const [profile, setProfile] = useState(false);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All categories");
  const [monthlyBudgets, setMonthlyBudgets] = useState<Record<string, number>>({});
  const [goal, setGoal] = useState({
    name: "A little room to breathe",
    target: 30000000,
    saved: 18750000,
    monthly: 1250000,
  });
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState<{ role: string; text: string }[]>([]);
  const month = new Date(2026, 10 + monthOffset, 1);
  const monthLabel = month.toLocaleDateString("en-GB", { month: "long", year: "numeric" });
  const shortMonth = month.toLocaleDateString("en-GB", { month: "short" });
  const currentMonth = monthOffset === 0;
  const prefix = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`;
  const budget = monthlyBudgets[prefix] ?? 8000000;
  const monthTransactions = useMemo(
    () =>
      transactions.filter(
        (t) => t.date.startsWith(prefix) && (wallet === "All wallets" || t.wallet === wallet),
      ),
    [transactions, prefix, wallet],
  );
  const expense = monthTransactions.filter((t) => !t.income).reduce((sum, t) => sum + t.amount, 0);
  const income = monthTransactions.filter((t) => t.income).reduce((sum, t) => sum + t.amount, 0);
  const remaining = budget - expense;
  const comparisonAvailable = currentMonth && wallet === "All wallets";
  const expenseChange = (expense / 5414352 - 1) * 100;
  const incomeChange = (income / 12000000 - 1) * 100;
  const filteredTransactions = monthTransactions
    .filter(
      (t) =>
        (categoryFilter === "All categories" || t.category === categoryFilter) &&
        `${t.merchant} ${t.note}`.toLowerCase().includes(search.toLowerCase()),
    )
    .sort((a, b) => b.date.localeCompare(a.date) || b.id - a.id);
  const displayedCategories = categories
    .map((c) => ({
      ...c,
      amount: monthTransactions
        .filter((t) => !t.income && t.category === c.name)
        .reduce((sum, t) => sum + t.amount, 0),
      budget: (c.budget * budget) / 8000000,
    }))
    .sort((a, b) => b.amount - a.amount);
  const chartData = useMemo(() => {
    const data: number[] = currentMonth ? Array(14).fill(0) : [];
    for (const t of monthTransactions.filter((t) => !t.income)) {
      const day = Number(t.date.slice(8, 10)) - 1;
      while (data.length <= day) data.push(0);
      data[day] += t.amount;
    }
    return data;
  }, [currentMonth, monthTransactions]);
  const recentDailyPace = chartData.slice(-3).reduce((sum, amount) => sum + amount, 0) / 3;
  const largestCategory = displayedCategories[0];
  const shoppingCategory = displayedCategories.find((c) => c.name === "Shopping")!;
  const shoppingPercent = Math.round((shoppingCategory.amount / shoppingCategory.budget) * 100);
  const notify = (text: string) => setToast(text);
  useEffect(() => {
    document.title = `${page} — Walleto`;
  }, [page]);
  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 4500);
    return () => clearTimeout(id);
  }, [toast]);
  useEffect(() => {
    const close = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setNotifications(false);
        setProfile(false);
      }
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  function navigate(next: Page) {
    setPage(next);
    if (next !== "Dashboard" && next !== "Transactions") setWallet("All wallets");
    setSearch("");
    setCategoryFilter("All categories");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function addTransaction(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const amount = Number(form.get("amount"));
    if (!Number.isFinite(amount) || amount <= 0) return;
    const transaction: Transaction = {
      id: Date.now(),
      merchant: String(form.get("merchant")).trim(),
      note: String(form.get("note")).trim() || "Personal transaction",
      amount,
      category: String(form.get("category")),
      wallet: String(form.get("wallet")),
      date: String(form.get("date")),
      income: form.get("type") === "Income",
    };
    setTransactions((prev) => [transaction, ...prev]);
    const date = new Date(`${transaction.date}T12:00:00`);
    setMonthOffset((date.getFullYear() - 2026) * 12 + date.getMonth() - 10);
    setWallet("All wallets");
    setModal(null);
    notify("Transaction added. Your numbers are up to date.");
  }
  function exportTransactions() {
    const rows = [
      ["Date", "Merchant", "Category", "Wallet", "Amount"],
      ...monthTransactions.map((t) => [
        formatDate(t.date),
        t.merchant,
        t.category,
        t.wallet,
        String(t.income ? t.amount : -t.amount),
      ]),
    ];
    const csv = rows
      .map((row) => row.map((v) => `"${v.replace(/"/g, '""')}"`).join(","))
      .join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `walleto-${prefix}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    notify("Your monthly statement has been downloaded.");
  }
  function askAssistant(text: string) {
    if (!text.trim()) return;
    let response = `For ${monthLabel}, you have spent ${money(expense)} against a ${money(budget)} plan, leaving ${money(remaining)}. Try a weekly check-in and keep a little room for unexpected expenses.`;
    if (/food|eating|lunch/i.test(text))
      response = `You have spent ${money(displayedCategories.find((c) => c.name === "Food & drinks")?.amount || 0)} on Food & drinks this month. A few small changes can add up: bringing lunch twice a week could leave around Rp320.000 more in your monthly budget. That is an illustrative estimate, so adjust it to your routine.`;
    if (/save|saving|goal/i.test(text))
      response = `You have ${money(goal.saved)} saved toward your ${money(goal.target)} goal. ${goal.saved >= goal.target ? "You have reached your target. Take a moment to appreciate how far you have come." : `Setting aside ${money(goal.monthly)} each month would close the ${money(goal.target - goal.saved)} gap in about ${Math.ceil((goal.target - goal.saved) / goal.monthly)} months.`}`;
    if (/plan|next|december/i.test(text))
      response = `Here is a starting point for your next month: keep your spending plan at ${money(budget)}, set aside ${money(goal.monthly)} for savings, and reserve Rp500.000 for unexpected costs. Review Food & drinks first — it is the best place to create a little more breathing room.`;
    setConversation((prev) => [
      ...prev,
      { role: "You", text },
      { role: "Walleto", text: response },
    ]);
    setQuestion("");
  }

  const monthlyControl = (
    <div className="month-picker">
      <button aria-label="Previous month" onClick={() => setMonthOffset((n) => n - 1)}>
        <Icon name="chevron-left" size={16} />
      </button>
      <span>
        <Icon name="calendar" size={15} />
        {monthLabel}
      </span>
      <button aria-label="Next month" onClick={() => setMonthOffset((n) => n + 1)}>
        <Icon name="chevron-right" size={16} />
      </button>
    </div>
  );

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate("Dashboard");
          }}
          aria-label="Walleto dashboard"
        >
          <span className="brand-mark">
            <svg width="27" height="25" viewBox="0 0 27 25" fill="none">
              <path
                d="m3 5 5 15h5l3-9 3 9h4l4-15"
                transform="translate(-2 0)"
                stroke="currentColor"
                strokeWidth="3.5"
                strokeLinejoin="round"
              />
              <path
                d="m8 5 3 9 3-9"
                stroke="currentColor"
                strokeWidth="3.5"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <span>
            walleto<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="sidebar-section-label">YOUR WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <button
              key={item.label}
              aria-label={item.label}
              aria-current={page === item.label ? "page" : undefined}
              className={`nav-item ${page === item.label ? "active" : ""}`}
              onClick={() => navigate(item.label)}
              title={collapsed ? item.label : undefined}
            >
              <Icon name={item.icon} size={19} />
              <span>{item.label}</span>
              {item.label === "Assistant" && <span className="nav-new">NEW</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-mark">
              <Icon name="goal" size={18} />
            </span>
            <h3>
              A little today.
              <br />A lot more tomorrow.
            </h3>
            <p>Your future self will thank you.</p>
            <button onClick={() => navigate("Savings goals")}>
              Set a savings goal <Icon name="arrow-right" size={14} />
            </button>
          </div>
          <button
            className={`nav-item utility ${page === "Design system" ? "active" : ""}`}
            onClick={() => navigate("Design system")}
            title="Design system"
          >
            <Icon name="grid" size={18} />
            <span>Design system</span>
            <span className="ds-mini">01</span>
          </button>
          <button
            className="nav-item utility help-link"
            onClick={() => setModal("help")}
            title="Help & getting started"
          >
            <Icon name="help" size={18} />
            <span>Help & getting started</span>
          </button>
          <div className="profile-wrap">
            <button
              className="profile"
              aria-label="Aditya Ramadhan, personal account"
              onClick={() => setProfile((v) => !v)}
              aria-expanded={profile}
            >
              <span className="avatar">AR</span>
              <span className="profile-copy">
                <strong>Aditya Ramadhan</strong>
                <small>Personal account</small>
              </span>
              <Icon name="chevron-down" size={15} />
            </button>
            {profile && (
              <div className="profile-popover popover">
                <strong>Aditya Ramadhan</strong>
                <p>aditya.ramadhan@email.com</p>
                <div className="profile-divider" />
                <span className="demo-label">Personal workspace · Demo</span>
                <p>Your changes stay in this preview session.</p>
              </div>
            )}
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button collapse-button"
              onClick={() => setCollapsed((v) => !v)}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <Icon name="collapse" size={18} />
            </button>
            <span className="topbar-divider" />
            <span className="breadcrumb">
              My workspace <Icon name="chevron-right" size={12} />
              <span>{page}</span>
            </span>
          </div>
          <div className="topbar-right">
            <span className="local-date">Saturday, 14 Nov 2026</span>
            <span className="topbar-divider" />
            <div className="notification-wrap">
              <button
                className={`icon-button notification-button ${notifications ? "selected" : ""}`}
                aria-label="Notifications"
                aria-expanded={notifications}
                onClick={() => setNotifications((v) => !v)}
              >
                <Icon name="bell" size={19} />
                <i />
              </button>
              {notifications && (
                <div className="notification-popover popover">
                  <div className="popover-title">
                    <strong>A quick heads-up</strong>
                    <span className="tiny-dot" />
                  </div>
                  <p>
                    You’ve used {shoppingPercent}% of your shopping budget for {monthLabel}.
                  </p>
                  <small>14 Nov 2026 · Budget update</small>
                  <button
                    className="text-button"
                    onClick={() => {
                      navigate("Budget");
                      setNotifications(false);
                    }}
                  >
                    Review your budget <Icon name="arrow-right" size={14} />
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="main-content">
          {page === "Design system" ? (
            <DesignSystem notify={notify} addTransaction={() => setModal("transaction")} />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    {page === "Dashboard"
                      ? "A LITTLE CLARITY, EVERY DAY"
                      : "YOUR MONEY, WITH INTENTION"}
                  </div>
                  <h1>{page}</h1>
                  <p>
                    {page === "Dashboard"
                      ? "A clear view of where you are, and where you’re headed."
                      : page === "Transactions"
                        ? "The everyday details that make up the bigger picture."
                        : page === "Wallets"
                          ? "Different places. One clear picture."
                          : page === "Budget"
                            ? "A plan for your money. Room for your life."
                            : page === "Savings goals"
                              ? "Make a little room for the things that matter."
                              : "A thoughtful second look at your finances."}
                  </p>
                </div>
                <div className="page-actions">
                  {monthlyControl}
                  {page === "Dashboard" || page === "Transactions" ? (
                    <button className="button primary" onClick={() => setModal("transaction")}>
                      <Icon name="plus" size={16} />
                      <span>Add transaction</span>
                    </button>
                  ) : page === "Budget" ? (
                    <button className="button primary" onClick={() => setModal("budget")}>
                      Edit monthly plan
                    </button>
                  ) : page === "Savings goals" ? (
                    <button className="button primary" onClick={() => setModal("goal")}>
                      <Icon name="plus" size={16} />
                      Add to savings
                    </button>
                  ) : null}
                </div>
              </div>

              {page === "Dashboard" && (
                <>
                  <div className="overview-toolbar">
                    <span className="section-overline">YOUR MONTH AT A GLANCE</span>
                    <label className="wallet-select">
                      <Icon name="wallet" size={15} />
                      <select
                        aria-label="Filter by wallet"
                        value={wallet}
                        onChange={(e) => setWallet(e.target.value)}
                      >
                        <option>All wallets</option>
                        {wallets.map((w) => (
                          <option key={w.name}>{w.name}</option>
                        ))}
                      </select>
                      <Icon name="chevron-down" size={13} />
                    </label>
                  </div>
                  <section className="balance-overview">
                    <div className="remaining-block">
                      <div className="metric-label">
                        Remaining this month{" "}
                        <span
                          className="info-hint"
                          tabIndex={0}
                          aria-label="Monthly spending plan minus expenses"
                        >
                          <Icon name="info" size={14} />
                          <span>Your monthly spending plan minus expenses.</span>
                        </span>
                      </div>
                      <div className={`main-amount ${remaining < 0 ? "negative" : ""}`}>
                        <Amount value={remaining} />
                      </div>
                      <div className="projection">
                        <span className={`status-dot ${remaining < 0 ? "red" : ""}`} />
                        {expense
                          ? remaining >= 0
                            ? recentDailyPace > 0
                              ? `Enough for ~${Math.max(0, Math.round(remaining / recentDailyPace))} days at your current pace`
                              : "A little room to breathe in your monthly plan"
                            : "Time to take a second look at your plan"
                          : "A fresh month. A little room to plan."}
                      </div>
                      <div className="remaining-progress">
                        <Progress value={(expense / budget) * 100} />
                        <span>
                          <strong>{money(expense)}</strong> of {money(budget)} planned
                        </span>
                      </div>
                    </div>
                    <div className="secondary-metric">
                      <span className="metric-icon income-icon">
                        <Icon name="arrow-down" size={17} />
                      </span>
                      <div className="metric-label">Total income</div>
                      <div className="secondary-amount">
                        <Amount value={income} />
                      </div>
                      <div className="metric-bottom">
                        <span className={incomeChange >= 0 ? "positive" : "negative"}>
                          <Icon name={incomeChange >= 0 ? "arrow-up" : "arrow-down"} size={13} />
                          {comparisonAvailable ? `${Math.abs(incomeChange).toFixed(1)}%` : "—"}{" "}
                          <span>vs. last month</span>
                        </span>
                        <MiniTrend />
                      </div>
                    </div>
                    <div className="secondary-metric expense-metric">
                      <span className="metric-icon expense-icon">
                        <Icon name="arrow-up" size={17} />
                      </span>
                      <div className="metric-label">Total expenses</div>
                      <div className="secondary-amount">
                        <Amount value={expense} />
                      </div>
                      <div className="metric-bottom">
                        <span className={expenseChange >= 0 ? "negative" : "positive"}>
                          <Icon name={expenseChange >= 0 ? "arrow-up" : "arrow-down"} size={13} />
                          {comparisonAvailable
                            ? `${Math.abs(expenseChange).toFixed(1)}%`
                            : "—"}{" "}
                          <span>vs. last month</span>
                        </span>
                        <MiniTrend expense />
                      </div>
                    </div>
                  </section>
                  <div className="chart-category-grid">
                    <SpendingChart
                      data={chartData}
                      monthLabel={shortMonth}
                      monthIndex={month.getMonth()}
                      year={month.getFullYear()}
                      currentMonth={currentMonth}
                      budget={budget}
                    />
                    <section className="panel category-panel">
                      <div className="section-heading">
                        <div>
                          <h2>Where it goes</h2>
                          <p>Spending by category</p>
                        </div>
                        <button
                          className="icon-button"
                          aria-label="View all budgets"
                          onClick={() => navigate("Budget")}
                        >
                          <Icon name="arrow-right" size={17} />
                        </button>
                      </div>
                      <div className="category-list">
                        {displayedCategories.map((c) => (
                          <button
                            className="category-row"
                            key={c.name}
                            onClick={() => {
                              navigate("Transactions");
                              setCategoryFilter(c.name);
                            }}
                          >
                            <div className="category-row-top">
                              <span>
                                <i style={{ background: c.color }} />
                                {c.name}
                              </span>
                              <strong>{money(c.amount)}</strong>
                            </div>
                            <div className="category-progress-row">
                              <Progress value={(c.amount / c.budget) * 100} color={c.color} />
                              <span>{Math.round((c.amount / c.budget) * 100)}%</span>
                            </div>
                          </button>
                        ))}
                      </div>
                      <div className="category-footnote">Percentage of each category’s budget</div>
                    </section>
                  </div>
                  <div className="insight-row">
                    <span className="insight-icon">
                      <Icon name="assistant" size={19} />
                    </span>
                    <p>
                      {expense > 0 ? (
                        <>
                          A small observation:{" "}
                          <strong>
                            {largestCategory.name} accounts for{" "}
                            {Math.round((largestCategory.amount / expense) * 100)}%
                          </strong>{" "}
                          of your spending this month.
                        </>
                      ) : (
                        <>A fresh perspective starts with your first transaction this month.</>
                      )}
                    </p>
                    <button
                      className="text-button"
                      onClick={() => {
                        navigate("Assistant");
                        if (currentMonth) askAssistant("Help me understand my food spending.");
                      }}
                    >
                      Let’s take a look <Icon name="arrow-right" size={15} />
                    </button>
                  </div>
                  <section className="panel recent-panel">
                    <div className="section-heading">
                      <div>
                        <h2>
                          Recent transactions{" "}
                          <span className="count-label">{monthTransactions.length}</span>
                        </h2>
                        <p>The little things, all accounted for.</p>
                      </div>
                      <button className="text-button" onClick={() => navigate("Transactions")}>
                        View all transactions <Icon name="arrow-right" size={15} />
                      </button>
                    </div>
                    <TransactionTable
                      transactions={[...monthTransactions]
                        .sort((a, b) => b.date.localeCompare(a.date))
                        .slice(0, 6)}
                      compact
                    />
                  </section>
                </>
              )}

              {page === "Transactions" && (
                <section className="panel transactions-page">
                  <div className="transactions-toolbar">
                    <label className="search-input">
                      <Icon name="search" size={17} />
                      <input
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search transactions…"
                        aria-label="Search transactions"
                      />
                    </label>
                    <select
                      className="filter-select"
                      aria-label="Filter by wallet"
                      value={wallet}
                      onChange={(e) => setWallet(e.target.value)}
                    >
                      <option>All wallets</option>
                      {wallets.map((w) => (
                        <option key={w.name}>{w.name}</option>
                      ))}
                    </select>
                    <select
                      className="filter-select"
                      aria-label="Filter by category"
                      value={categoryFilter}
                      onChange={(e) => setCategoryFilter(e.target.value)}
                    >
                      <option>All categories</option>
                      {categories.map((c) => (
                        <option key={c.name}>{c.name}</option>
                      ))}
                    </select>
                    <button className="button" onClick={exportTransactions}>
                      <Icon name="download" size={15} />
                      Export CSV
                    </button>
                  </div>
                  <div className="transaction-summary">
                    <span>
                      {filteredTransactions.length} transactions in {monthLabel}
                    </span>
                    <span>
                      Monthly expenses <strong>{money(expense)}</strong>
                    </span>
                  </div>
                  <TransactionTable transactions={filteredTransactions} />
                </section>
              )}
              {page === "Wallets" && (
                <>
                  <section className="wallet-total">
                    <span className="eyebrow">ACROSS ALL YOUR WALLETS</span>
                    <div className="main-amount">
                      <Amount
                        value={
                          wallets.reduce((s, w) => s + w.balance, 0) +
                          transactions
                            .filter((t) => t.id > 100)
                            .reduce((s, t) => s + (t.income ? t.amount : -t.amount), 0)
                        }
                      />
                    </div>
                    <p>
                      Your balances at a glance ·{" "}
                      {currentMonth ? "14 Nov 2026" : `Snapshot for ${monthLabel}`}
                    </p>
                  </section>
                  <div className="wallet-grid">
                    {wallets.map((w) => (
                      <button
                        className="panel wallet-card"
                        key={w.name}
                        onClick={() => {
                          setWallet(w.name);
                          navigate("Dashboard");
                        }}
                      >
                        <span className="bank-logo" style={{ color: w.color }}>
                          {w.short}
                        </span>
                        <div className="wallet-card-heading">
                          <h2>{w.name}</h2>
                          <span>{w.type}</span>
                        </div>
                        <div className="secondary-amount">
                          <Amount
                            value={
                              w.balance +
                              transactions
                                .filter((t) => t.id > 100 && t.wallet === w.name)
                                .reduce((s, t) => s + (t.income ? t.amount : -t.amount), 0)
                            }
                          />
                        </div>
                        <div className="wallet-card-footer">
                          <span>{w.detail}</span>
                          <span>
                            View activity <Icon name="arrow-right" size={15} />
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="plain-note">
                    <Icon name="info" size={17} />
                    <span>
                      These are sample wallets. Balances update with the transactions you add in
                      this preview.
                    </span>
                  </div>
                </>
              )}
              {page === "Budget" && (
                <>
                  <section className="budget-overview panel">
                    <div>
                      <span className="eyebrow">YOUR MONTHLY SPENDING PLAN</span>
                      <div className="main-amount">
                        <Amount value={budget} />
                      </div>
                      <p>
                        {money(remaining)} left to spend in {monthLabel}
                      </p>
                    </div>
                    <div className="budget-overview-progress">
                      <div>
                        <span>Spent so far</span>
                        <strong>{Math.round((expense / budget) * 100)}%</strong>
                      </div>
                      <Progress value={(expense / budget) * 100} />
                      <p>
                        {money(expense)} of {money(budget)}
                      </p>
                    </div>
                  </section>
                  <section className="panel budget-list">
                    <div className="section-heading">
                      <div>
                        <h2>A place for every Rupiah</h2>
                        <p>Your category budgets add up to your monthly plan.</p>
                      </div>
                    </div>
                    {displayedCategories.map((c) => (
                      <div className="budget-detail-row" key={c.name}>
                        <span className="merchant-icon">
                          <Icon name={c.icon} />
                        </span>
                        <div className="budget-name">
                          <strong>{c.name}</strong>
                          <span>
                            {Math.round((c.amount / c.budget) * 100) >= 85
                              ? "Getting close to your limit"
                              : "A little breathing room"}
                          </span>
                        </div>
                        <div className="budget-detail-progress">
                          <Progress
                            value={(c.amount / c.budget) * 100}
                            color={c.amount / c.budget >= 0.85 ? "#B7791F" : c.color}
                          />
                        </div>
                        <div className="budget-values">
                          <strong>{money(c.amount)}</strong>
                          <span>of {money(c.budget)}</span>
                        </div>
                        <span
                          className={`budget-percent ${c.amount / c.budget >= 0.85 ? "warning" : ""}`}
                        >
                          {Math.round((c.amount / c.budget) * 100)}%
                        </span>
                      </div>
                    ))}
                  </section>
                </>
              )}
              {page === "Savings goals" && (
                <>
                  <section className="panel savings-feature">
                    <div className="savings-feature-copy">
                      <span className="eyebrow">YOUR SAVINGS GOAL</span>
                      <h2>{goal.name}</h2>
                      <p>A little intention today. More room for what matters tomorrow.</p>
                      <div className="main-amount">
                        <Amount value={goal.saved} />
                        <span className="goal-target">of {money(goal.target)}</span>
                      </div>
                      <Progress value={(goal.saved / goal.target) * 100} />
                      <div className="goal-meta">
                        <span>
                          {goal.saved >= goal.target
                            ? "Your goal, reached."
                            : `${Math.round((goal.saved / goal.target) * 100)}% of the way there`}
                        </span>
                        <span>{money(Math.max(0, goal.target - goal.saved))} to go</span>
                      </div>
                      <div className="savings-actions">
                        <button className="button primary" onClick={() => setModal("goal")}>
                          <Icon name="plus" size={16} />
                          Add to this goal
                        </button>
                        <button className="text-button" onClick={() => setModal("goal-settings")}>
                          Edit goal <Icon name="arrow-right" size={15} />
                        </button>
                      </div>
                    </div>
                    <div className="savings-illustration" aria-hidden="true">
                      <div className="ledger-number">01</div>
                      <div className="savings-lines">
                        {Array.from({ length: 9 }, (_, i) => (
                          <div
                            key={i}
                            className={
                              i < Math.round(Math.min(1, goal.saved / goal.target) * 9)
                                ? "filled"
                                : ""
                            }
                          />
                        ))}
                      </div>
                      <span>
                        SMALL STEPS.
                        <br />
                        REAL PROGRESS.
                      </span>
                    </div>
                  </section>
                  <div className="insight-row">
                    <Icon name="info" size={18} />
                    <p>
                      {goal.saved >= goal.target ? (
                        <>
                          You did it. <strong>A little consistency brought you here.</strong> Set a
                          new target whenever you’re ready.
                        </>
                      ) : (
                        <>
                          Put aside <strong>{money(goal.monthly)} a month</strong> to reach your
                          target in about {Math.ceil((goal.target - goal.saved) / goal.monthly)}{" "}
                          months.
                        </>
                      )}
                    </p>
                  </div>
                </>
              )}
              {page === "Assistant" && (
                <div className="assistant-page">
                  <section className="assistant-intro">
                    <span className="assistant-symbol">
                      <Icon name="assistant" size={27} />
                    </span>
                    <span className="eyebrow">A LITTLE PERSPECTIVE</span>
                    <h2>
                      Good decisions start
                      <br />
                      with a clearer picture.
                    </h2>
                    <p>
                      Look closer at your habits, find a little breathing room,
                      <br className="desktop-break" /> or make a thoughtful plan for next month.
                    </p>
                  </section>
                  <div className="assistant-prompts">
                    {[
                      "Where can I spend a little less?",
                      "Help me plan for next month.",
                      "How can I reach my savings goal?",
                    ].map((q, i) => (
                      <button key={q} onClick={() => askAssistant(q)}>
                        <span className="prompt-number">0{i + 1}</span>
                        {q}
                        <Icon name="arrow-right" size={16} />
                      </button>
                    ))}
                  </div>
                  <div className="conversation" aria-live="polite">
                    {conversation.map((message, i) => (
                      <div
                        className={`message ${message.role === "You" ? "user-message" : ""}`}
                        key={i}
                      >
                        <span>{message.role}</span>
                        <p>{message.text}</p>
                      </div>
                    ))}
                  </div>
                  <form
                    className="assistant-input"
                    onSubmit={(e) => {
                      e.preventDefault();
                      askAssistant(question);
                    }}
                  >
                    <input
                      placeholder="What’s on your mind about money?"
                      aria-label="Ask Walleto a question"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      required
                    />
                    <button
                      className="button primary icon-only"
                      aria-label="Send question"
                      disabled={!question.trim()}
                    >
                      <Icon name="arrow-right" size={19} />
                    </button>
                  </form>
                  <p className="assistant-disclaimer">
                    An interactive preview with sample insights, not live AI or financial advice.
                  </p>
                </div>
              )}
            </>
          )}
          <footer className="page-footer">
            <span>A little more clarity. A little more possibility.</span>
            <span>Made for your everyday.</span>
          </footer>
        </main>
      </div>
      {modal === "transaction" && (
        <Modal
          title="A little detail. A clearer picture."
          description="Add a transaction to keep your month in view."
          onClose={() => setModal(null)}
        >
          <form onSubmit={addTransaction} className="form-stack">
            <div className="form-two-col">
              <label className="field">
                Type
                <select name="type">
                  <option>Expense</option>
                  <option>Income</option>
                </select>
              </label>
              <label className="field">
                Amount (Rp)
                <input
                  name="amount"
                  type="number"
                  min="1"
                  step="1"
                  placeholder="67500"
                  required
                  autoFocus
                />
              </label>
            </div>
            <label className="field">
              Merchant or description
              <input name="merchant" placeholder="e.g. GoFood" required maxLength={80} />
            </label>
            <div className="form-two-col">
              <label className="field">
                Category
                <select name="category">
                  {categories.map((c) => (
                    <option key={c.name}>{c.name}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                Wallet
                <select name="wallet">
                  {wallets.map((w) => (
                    <option key={w.name}>{w.name}</option>
                  ))}
                </select>
              </label>
            </div>
            <label className="field">
              Date
              <input name="date" type="date" defaultValue={`${prefix}-14`} required />
            </label>
            <label className="field">
              Note <span className="optional">(optional)</span>
              <input name="note" placeholder="A little context for later" maxLength={120} />
            </label>
            <p className="form-note">Preview only. Your changes last for this session.</p>
            <div className="modal-actions">
              <button type="button" className="button" onClick={() => setModal(null)}>
                Cancel
              </button>
              <button className="button primary">
                Add transaction <Icon name="arrow-right" size={15} />
              </button>
            </div>
          </form>
        </Modal>
      )}
      {modal === "budget" && (
        <Modal
          title="Give your month a plan."
          description="Your category limits will adjust proportionally."
          onClose={() => setModal(null)}
        >
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              const value = Number(new FormData(e.currentTarget).get("budget"));
              if (value > 0) {
                setMonthlyBudgets((plans) => ({ ...plans, [prefix]: value }));
                setModal(null);
                notify("Your monthly spending plan has been updated.");
              }
            }}
          >
            <label className="field">
              Monthly spending budget (Rp)
              <input
                type="number"
                name="budget"
                defaultValue={budget}
                min="100000"
                step="1"
                required
                autoFocus
              />
            </label>
            <div className="modal-actions">
              <button type="button" className="button" onClick={() => setModal(null)}>
                Cancel
              </button>
              <button className="button primary">Save monthly plan</button>
            </div>
          </form>
        </Modal>
      )}
      {modal === "goal" && (
        <Modal
          title="A step closer to your goal."
          description="Record money you’ve set aside for what matters to you."
          onClose={() => setModal(null)}
        >
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              const amount = Number(new FormData(e.currentTarget).get("amount"));
              if (amount > 0) {
                setGoal((g) => ({ ...g, saved: g.saved + amount }));
                setModal(null);
                notify("Savings added. Your future self says thank you.");
              }
            }}
          >
            <div className="goal-modal-summary">
              <span>{goal.name}</span>
              <strong>
                {money(goal.saved)} <small>of {money(goal.target)}</small>
              </strong>
              <Progress value={(goal.saved / goal.target) * 100} />
            </div>
            <label className="field">
              Amount to set aside (Rp)
              <input
                name="amount"
                type="number"
                min="1"
                step="1"
                placeholder="1250000"
                required
                autoFocus
              />
            </label>
            <p className="form-note">
              This records your goal progress; it doesn’t move money between wallets.
            </p>
            <div className="modal-actions">
              <button type="button" className="button" onClick={() => setModal(null)}>
                Cancel
              </button>
              <button className="button primary">Add to savings</button>
            </div>
          </form>
        </Modal>
      )}
      {modal === "goal-settings" && (
        <Modal
          title="Give your goal a little direction."
          description="Make a plan that feels right for your everyday life."
          onClose={() => setModal(null)}
        >
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              const form = new FormData(e.currentTarget);
              const name = String(form.get("name")).trim();
              const target = Number(form.get("target"));
              const monthly = Number(form.get("monthly"));
              if (
                !name ||
                !Number.isFinite(target) ||
                target <= 0 ||
                !Number.isFinite(monthly) ||
                monthly <= 0
              )
                return;
              setGoal((g) => ({ ...g, name, target, monthly }));
              setModal(null);
              notify("Your savings goal has a fresh plan.");
            }}
          >
            <label className="field">
              Goal name
              <input
                name="name"
                defaultValue={goal.name}
                maxLength={60}
                pattern=".*\S.*"
                required
                autoFocus
              />
            </label>
            <label className="field">
              Target amount (Rp)
              <input
                name="target"
                type="number"
                min="1"
                step="1"
                defaultValue={goal.target}
                required
              />
            </label>
            <label className="field">
              Monthly contribution plan (Rp)
              <input
                name="monthly"
                type="number"
                min="1"
                step="1"
                defaultValue={goal.monthly}
                required
              />
            </label>
            <p className="form-note">
              Your existing {money(goal.saved)} in savings stays untouched. A contribution plan is a
              reminder, not an automatic transfer.
            </p>
            <div className="modal-actions">
              <button type="button" className="button" onClick={() => setModal(null)}>
                Cancel
              </button>
              <button className="button primary">Save goal</button>
            </div>
          </form>
        </Modal>
      )}
      {modal === "help" && (
        <Modal
          title="A good place to start."
          description="A little clarity about your Walleto preview."
          onClose={() => setModal(null)}
        >
          <div className="help-content">
            <div>
              <span>01</span>
              <p>
                <strong>Get a feel for your month.</strong> Your dashboard brings sample
                transactions, wallets, and budgets into one view.
              </p>
            </div>
            <div>
              <span>02</span>
              <p>
                <strong>Try a little of everything.</strong> Add a transaction, adjust your budget,
                or record progress toward a savings goal.
              </p>
            </div>
            <div>
              <span>03</span>
              <p>
                <strong>This is an interactive design preview.</strong> No bank accounts are
                connected. Changes last until you refresh, and assistant insights are illustrative.
              </p>
            </div>
          </div>
          <div className="modal-actions">
            <button className="button primary" onClick={() => setModal(null)}>
              That makes sense <Icon name="check" size={15} />
            </button>
          </div>
        </Modal>
      )}
      {toast && (
        <div className="toast" role="status">
          <span className="toast-check">
            <Icon name="check" size={15} />
          </span>
          <span>{toast}</span>
          <button
            className="icon-button"
            onClick={() => setToast("")}
            aria-label="Dismiss notification"
          >
            <Icon name="close" size={15} />
          </button>
        </div>
      )}
    </div>
  );
}

import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Options = {
  departments: string[];
  technologies: string[];
  priorities: string[];
};

type DashboardData = {
  updated_at: string;
  filters: { technologies: string[] };
  metrics: {
    total: number;
    solved: number;
    in_progress: number;
    unresolved: number;
    solved_percent: number;
    avg_response: number | null;
    avg_repair: number | null;
    sla: number;
  };
  charts: Record<string, { name: string; count: number }[]>;
  rows: TableRow[];
  in_progress_rows: TableRow[];
  unresolved_rows: TableRow[];
};

type TableRow = {
  reported_at: string;
  technology: string;
  location: string;
  priority: string;
  description: string;
  reported_by: string;
  status: string;
  reacted_at: string;
  solved_at: string;
  solution: string;
};

const emptyOptions: Options = { departments: [], technologies: [], priorities: ["Low", "Medium", "High"] };

function App() {
  const [page, setPage] = useState<"form" | "dashboard">("form");
  const [options, setOptions] = useState<Options>(emptyOptions);

  useEffect(() => {
    fetch("/api/options").then((response) => response.json()).then(setOptions).catch(() => setOptions(emptyOptions));
  }, []);

  return (
    <main className="app-shell">
      <nav className="top-nav">
        <button className={page === "form" ? "active" : ""} onClick={() => setPage("form")}>Formular</button>
        <button className={page === "dashboard" ? "active" : ""} onClick={() => setPage("dashboard")}>Power BI Dashboard</button>
      </nav>
      {page === "form" ? <TicketForm options={options} /> : <Dashboard />}
    </main>
  );
}

function TicketForm({ options }: { options: Options }) {
  const [form, setForm] = useState({
    reported_by: "",
    department: "",
    department_custom: "",
    technology: "",
    technology_custom: "",
    location: "",
    priority: "Medium",
    description: "",
    note: ""
  });
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<string>("");
  const [isSending, setIsSending] = useState(false);

  const update = (name: string, value: string) => setForm((current) => ({ ...current, [name]: value }));

  async function toBase64(file: File) {
    const buffer = await file.arrayBuffer();
    let binary = "";
    const bytes = new Uint8Array(buffer);
    bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
    return btoa(binary);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const department = form.department === "Jine / Other" ? form.department_custom : form.department;
    const technology = form.technology === "Jine / Other" ? form.technology_custom : form.technology;
    if (!form.reported_by || !department || !technology || !form.location || !form.description) {
      setStatus("Vyplnte prosim vsechna povinna pole.");
      return;
    }
    setIsSending(true);
    setStatus("");
    const attachments = await Promise.all(files.map(async (file) => ({ name: file.name, data: await toBase64(file) })));
    const response = await fetch("/api/tickets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reported_by: form.reported_by,
        department,
        technology,
        location: form.location,
        priority: form.priority,
        description: form.description,
        note: form.note,
        attachments
      })
    });
    setIsSending(false);
    if (response.ok) {
      setStatus("Ticket byl odeslan do Teams.");
      setForm({ reported_by: "", department: "", department_custom: "", technology: "", technology_custom: "", location: "", priority: "Medium", description: "", note: "" });
      setFiles([]);
    } else {
      const detail = await response.json().catch(() => ({}));
      setStatus(detail.detail || "Nepodarilo se odeslat. Zkontrolujte VPN.");
    }
  }

  return (
    <section className="panel form-panel">
      <h1>Technical Fault Report</h1>
      <p className="lead">Please fill in the technical details of the issue. The information will be immediately sent for resolution.</p>
      <form onSubmit={submit}>
        <label>Reported by *<input value={form.reported_by} onChange={(e) => update("reported_by", e.target.value)} /></label>
        <div className="grid-two">
          <label>1. Department *<select value={form.department} onChange={(e) => update("department", e.target.value)}><option value=""></option>{options.departments.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>2. Technology *<select value={form.technology} onChange={(e) => update("technology", e.target.value)}><option value=""></option>{options.technologies.map((item) => <option key={item}>{item}</option>)}</select></label>
        </div>
        {(form.department === "Jine / Other" || form.technology === "Jine / Other") && (
          <div className="grid-two">
            {form.department === "Jine / Other" && <label>Enter department / Zadejte oddeleni<input value={form.department_custom} onChange={(e) => update("department_custom", e.target.value)} /></label>}
            {form.technology === "Jine / Other" && <label>Enter technology / Zadejte technologii<input value={form.technology_custom} onChange={(e) => update("technology_custom", e.target.value)} /></label>}
          </div>
        )}
        <div className="grid-two">
          <label>3. Location *<input value={form.location} onChange={(e) => update("location", e.target.value)} /></label>
          <label>4. Priority<select value={form.priority} onChange={(e) => update("priority", e.target.value)}>{options.priorities.map((item) => <option key={item}>{item}</option>)}</select></label>
        </div>
        <label>Detailed fault description *<textarea rows={7} value={form.description} onChange={(e) => update("description", e.target.value)} /></label>
        <label>Additional note<textarea rows={3} value={form.note} onChange={(e) => update("note", e.target.value)} /></label>
        <label>Attachments<input type="file" multiple accept=".jpg,.jpeg,.png,.pdf" onChange={(e) => setFiles(Array.from(e.target.files || []))} /></label>
        <button type="submit" className="primary-action" disabled={isSending}>{isSending ? "Odesilam..." : "SUBMIT REPORT"}</button>
      </form>
      {status && <p className="status-text">{status}</p>}
    </section>
  );
}

function Dashboard() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [password, setPassword] = useState("");
  const [days, setDays] = useState("30");
  const [technology, setTechnology] = useState("Vse");
  const [priority, setPriority] = useState("Vse");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  async function login(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/dashboard/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password })
    });
    if (response.ok) {
      setIsLoggedIn(true);
    } else {
      setError("Nespravne heslo nebo chybi konfigurace hesla.");
    }
  }

  useEffect(() => {
    if (!isLoggedIn) return;
    const query = new URLSearchParams({ days, technology, priority });
    fetch(`/api/dashboard?${query.toString()}`)
      .then((response) => response.ok ? response.json() : Promise.reject(response))
      .then((payload) => { setData(payload); setError(""); })
      .catch(() => setError("Data se nepodarilo nacist."));
  }, [isLoggedIn, days, technology, priority]);

  const maxDaily = useMemo(() => Math.max(1, ...(data?.charts.daily.map((item) => item.count) || [1])), [data]);

  if (!isLoggedIn) {
    return (
      <section className="panel login-panel">
        <h2>Pristup do dashboardu</h2>
        <p>Dashboard je dostupny pouze opravnenym uzivatelum.</p>
        <form onSubmit={login}>
          <label>Zadejte heslo<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
          <button className="primary-action">Prihlasit se</button>
        </form>
        {error && <p className="status-text">{error}</p>}
      </section>
    );
  }

  return (
    <section className="dashboard">
      <header className="dashboard-header">
        <div><h1>Power BI Dashboard - CZLC4</h1><p>Aktualizovano {data?.updated_at || "-"}</p></div>
        <button onClick={() => setIsLoggedIn(false)}>Odhlasit</button>
      </header>
      <div className="filters">
        <select value={days} onChange={(e) => setDays(e.target.value)}><option value="7">7 dni</option><option value="30">30 dni</option><option value="all">Vse</option></select>
        <select value={technology} onChange={(e) => setTechnology(e.target.value)}><option value="Vse">Vse technologie</option>{data?.filters.technologies.map((item) => <option key={item}>{item}</option>)}</select>
        <select value={priority} onChange={(e) => setPriority(e.target.value)}><option value="Vse">Vse priority</option><option>High</option><option>Medium</option><option>Low</option></select>
      </div>
      {error && <p className="status-text">{error}</p>}
      {data && (
        <>
          <div className="metrics">
            <Metric label="Celkem zavad" value={data.metrics.total} />
            <Metric label={`Vyreseno (${data.metrics.solved_percent} %)`} value={data.metrics.solved} />
            <Metric label="Nevyreseno" value={data.metrics.unresolved} alert />
            <Metric label="V reseni" value={data.metrics.in_progress} />
            <Metric label="Prum. reakce" value={data.metrics.avg_response === null ? "-" : `${data.metrics.avg_response} min`} />
            <Metric label="Prum. oprava" value={data.metrics.avg_repair === null ? "-" : `${data.metrics.avg_repair} min`} />
            <Metric label="SLA <30 min" value={`${data.metrics.sla} %`} />
          </div>
          <div className="chart-grid">
            <Card title="Zavady za den"><BarList items={data.charts.daily} max={maxDaily} /></Card>
            <Card title="Top technologie"><BarList items={data.charts.technology} /></Card>
            <Card title="Podle priority"><BarList items={data.charts.priority} /></Card>
            <Card title="Podle oddeleni"><BarList items={data.charts.department} /></Card>
            <Card title="Nejproblematictejsi mista"><BarList items={data.charts.location} /></Card>
            <Card title="Zavady dle dne v tydnu"><BarList items={data.charts.weekday} /></Card>
          </div>
          <Card title="Nevyresene zavady a zavady V reseni"><DataTable rows={data.unresolved_rows} /></Card>
          <Card title="Vsechna data"><DataTable rows={data.rows} /></Card>
        </>
      )}
    </section>
  );
}

function Metric({ label, value, alert = false }: { label: string; value: string | number; alert?: boolean }) {
  return <div className={`metric ${alert ? "alert" : ""}`}><strong>{value}</strong><span>{label}</span></div>;
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="card"><h3>{title}</h3>{children}</section>;
}

function BarList({ items, max }: { items: { name: string; count: number }[]; max?: number }) {
  const localMax = max || Math.max(1, ...items.map((item) => item.count));
  return <div className="bar-list">{items.map((item) => <div className="bar-row" key={item.name}><span>{item.name}</span><div><i style={{ width: `${Math.max(6, item.count / localMax * 100)}%` }} /></div><b>{item.count}</b></div>)}</div>;
}

function DataTable({ rows }: { rows: TableRow[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Cas</th><th>Technologie</th><th>Misto</th><th>Priorita</th><th>Popis</th><th>Nahlasil</th><th>Stav</th></tr></thead>
        <tbody>{rows.slice(0, 100).map((row, index) => <tr key={`${row.reported_at}-${index}`}><td>{row.reported_at}</td><td>{row.technology}</td><td>{row.location}</td><td>{row.priority}</td><td>{row.description}</td><td>{row.reported_by}</td><td>{row.status}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

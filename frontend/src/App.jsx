import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const money = (paise) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format((paise || 0) / 100);

export default function App() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [mode, setMode] = useState("login");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function request(path, options = {}, auth = true) {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(auth && token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  }

  async function loadDashboard(accessToken = token) {
    const headers = { Authorization: `Bearer ${accessToken}` };
    const [meRes, accountRes, txRes] = await Promise.all([
      fetch(`${API}/api/me`, { headers }),
      fetch(`${API}/api/account`, { headers }),
      fetch(`${API}/api/transactions`, { headers }),
    ]);
    if (![meRes, accountRes, txRes].every(r => r.ok)) throw new Error("Could not load your account");
    setUser(await meRes.json());
    setAccount(await accountRes.json());
    setTransactions(await txRes.json());
  }

  async function submitAuth(e) {
    e.preventDefault(); setBusy(true); setMessage("");
    const form = new FormData(e.currentTarget);
    try {
      if (mode === "register") {
        await request("/api/auth/register", { method: "POST", body: JSON.stringify({
          full_name: form.get("full_name"), email: form.get("email"), password: form.get("password")
        }) }, false);
        setMessage("Registration successful. Please sign in.");
        setMode("login");
      } else {
        const data = await request("/api/auth/login", { method: "POST", body: JSON.stringify({
          email: form.get("email"), password: form.get("password")
        }) }, false);
        setToken(data.access_token);
        await loadDashboard(data.access_token);
      }
    } catch (err) { setMessage(err.message); }
    finally { setBusy(false); }
  }

  async function submitTransfer(e) {
    e.preventDefault(); setBusy(true); setMessage("");
    const form = new FormData(e.currentTarget);
    try {
      await request("/api/transfers", { method: "POST", body: JSON.stringify({
        recipient_account: form.get("recipient"),
        amount_paise: Math.round(Number(form.get("amount")) * 100),
        description: form.get("description") || "Transfer"
      }) });
      setMessage("Transfer completed successfully.");
      e.currentTarget.reset();
      await loadDashboard();
    } catch (err) { setMessage(err.message); }
    finally { setBusy(false); }
  }

  function logout() { setToken(""); setUser(null); setAccount(null); setTransactions([]); setMessage(""); }

  if (!user) return <main className="auth-shell">
    <section className="auth-card">
      <div className="brand-mark">M</div>
      <p className="eyebrow">MKU FINANCIAL</p>
      <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
      <p className="muted">A secure, simulated banking experience.</p>
      <form onSubmit={submitAuth}>
        {mode === "register" && <label>Full name<input name="full_name" minLength="2" maxLength="120" required placeholder="Your name" /></label>}
        <label>Email address<input name="email" type="email" required placeholder="you@example.com" /></label>
        <label>Password<input name="password" type="password" minLength={mode === "register" ? 10 : 1} required placeholder={mode === "register" ? "At least 10 characters" : "Your password"} /></label>
        <button disabled={busy}>{busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}</button>
      </form>
      {message && <p className="notice">{message}</p>}
      <p className="switch">{mode === "login" ? "New here?" : "Already registered?"} <button className="link" onClick={() => {setMode(mode === "login" ? "register" : "login"); setMessage("");}}>{mode === "login" ? "Create an account" : "Sign in"}</button></p>
      <p className="tiny">Demo application · No real money or bank connection</p>
    </section>
  </main>;

  return <main className="app-shell">
    <header className="topbar"><div className="brand"><span className="brand-mark small">M</span><strong>MKU Banking</strong></div><div className="profile"><span>{user.full_name}</span><button className="secondary compact" onClick={logout}>Sign out</button></div></header>
    <section className="welcome"><div><p className="eyebrow">PERSONAL BANKING</p><h1>Good to see you, {user.full_name.split(" ")[0]}</h1><p className="muted">Here is your account overview.</p></div><span className="status">● Account active</span></section>
    {message && <p className="notice">{message}</p>}
    <section className="balance-card"><div><p className="balance-label">Available balance</p><h2>{money(account?.balance_paise)}</h2><p className="account-number">Account · {account?.account_number}</p></div><div className="balance-icon">₹</div></section>
    <section className="content-grid">
      <div className="panel"><div className="panel-heading"><div><p className="eyebrow">PAYMENTS</p><h3>Send money</h3></div></div>
        <form onSubmit={submitTransfer}>
          <label>Recipient account number<input name="recipient" required placeholder="MKU000000000000" /></label>
          <label>Amount (INR)<input name="amount" type="number" min="0.01" step="0.01" max="500000" required placeholder="100.00" /></label>
          <label>Description<input name="description" maxLength="240" placeholder="Rent, bills, etc." /></label>
          <button disabled={busy}>{busy ? "Processing..." : "Transfer money"}</button>
        </form>
        <p className="tiny">Transfers are simulated and cannot be reversed in this demo.</p>
      </div>
      <div className="panel"><div className="panel-heading"><div><p className="eyebrow">ACTIVITY</p><h3>Recent transactions</h3></div></div>
        {transactions.length === 0 ? <div className="empty">No transactions yet. Your activity will appear here.</div> :
          <div className="transactions">{transactions.map(tx => <div className="transaction" key={tx.reference}><div className={`tx-icon ${tx.direction.toLowerCase()}`}>{tx.direction === "CREDIT" ? "↓" : "↑"}</div><div className="tx-info"><strong>{tx.description}</strong><span>{new Date(tx.created_at).toLocaleString()}</span><small>{tx.reference.slice(0, 8)} · {tx.status}</small></div><strong className={tx.direction === "CREDIT" ? "credit" : ""}>{tx.direction === "CREDIT" ? "+" : "-"}{money(tx.amount_paise)}</strong></div>)}</div>}
      </div>
    </section>
    <footer>MKU Banking · Educational demo · Never use real financial information</footer>
  </main>;
}

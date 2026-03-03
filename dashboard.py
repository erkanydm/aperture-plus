"""
dashboard.py — Aperture+ Admin Dashboard
Run: python3 dashboard.py
Then open: http://localhost:5001
"""

from flask import Flask, jsonify, render_template_string, request
import sqlite3
import os
import subprocess
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/aperture/.env"))

app = Flask(__name__)
DB_PATH = os.path.expanduser("~/aperture/aperture.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            plan TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS send_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            score INTEGER,
            recipients INTEGER,
            status TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            plan TEXT,
            amount REAL,
            currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aperture+ Admin</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0a;
    --surface: #111111;
    --surface2: #181818;
    --border: #222222;
    --gold: #C9A84C;
    --gold-dim: rgba(201,168,76,0.15);
    --green: #3DD68C;
    --red: #FF5F57;
    --text: #E8E8E8;
    --muted: #666666;
    --accent: #C9A84C;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Mono', monospace;
    min-height: 100vh;
  }
  /* TOP BAR */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 32px;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 100;
  }
  .logo {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
  }
  .logo span { color: var(--gold); }
  .topbar-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .live-dot {
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  .time-display {
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 1px;
  }
  /* LAYOUT */
  .main { padding: 32px; max-width: 1400px; margin: 0 auto; }
  .grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
  }
  .grid-3 {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
  }
  /* CARDS */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
  }
  .card-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
  }
  .card-value {
    font-family: 'Syne', sans-serif;
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
  }
  .card-sub {
    font-size: 11px;
    color: var(--muted);
    margin-top: 8px;
  }
  .card-gold { border-color: rgba(201,168,76,0.3); }
  .card-gold .card-value { color: var(--gold); }
  .card-green { border-color: rgba(61,214,140,0.2); }
  .card-green .card-value { color: var(--green); }
  /* SECTION HEADERS */
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  .section-title {
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
  }
  /* SCORE DISPLAY */
  .score-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
  }
  .score-big {
    font-family: 'Syne', sans-serif;
    font-size: 80px;
    font-weight: 800;
    line-height: 1;
    color: var(--gold);
  }
  .score-denom {
    font-size: 24px;
    color: var(--muted);
  }
  .score-label {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 12px;
  }
  .label-low { background: rgba(61,214,140,0.15); color: var(--green); }
  .label-mid { background: rgba(201,168,76,0.15); color: var(--gold); }
  .label-high { background: rgba(255,95,87,0.15); color: var(--red); }
  /* TABLE */
  table { width: 100%; border-collapse: collapse; }
  th {
    text-align: left;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 12px 12px;
    font-size: 13px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    vertical-align: middle;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--surface2); }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  .badge-active { background: rgba(61,214,140,0.15); color: var(--green); }
  .badge-free { background: rgba(255,255,255,0.06); color: var(--muted); }
  .badge-paid { background: var(--gold-dim); color: var(--gold); }
  .badge-sent { background: rgba(61,214,140,0.15); color: var(--green); }
  .badge-failed { background: rgba(255,95,87,0.15); color: var(--red); }
  /* BUTTONS */
  .btn {
    padding: 10px 20px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: all 0.2s;
  }
  .btn-gold {
    background: var(--gold);
    color: #000;
    font-weight: 600;
  }
  .btn-gold:hover { background: #e0b94f; transform: translateY(-1px); }
  .btn-ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
  }
  .btn-ghost:hover { border-color: var(--gold); color: var(--gold); }
  .btn-danger {
    background: transparent;
    color: var(--red);
    border: 1px solid rgba(255,95,87,0.3);
    padding: 6px 12px;
    font-size: 11px;
  }
  .btn-danger:hover { background: rgba(255,95,87,0.1); }
  /* SEND PANEL */
  .send-panel {
    background: var(--surface);
    border: 1px solid rgba(201,168,76,0.3);
    border-radius: 12px;
    padding: 32px;
  }
  .send-actions { display: flex; flex-direction: column; gap: 12px; margin-top: 24px; }
  .send-btn-row { display: flex; gap: 12px; }
  /* FORM */
  .input-row { display: flex; gap: 12px; margin-bottom: 16px; }
  input[type="email"], input[type="text"], select {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 14px;
    color: var(--text);
    font-family: 'DM Mono', monospace;
    font-size: 13px;
    flex: 1;
    outline: none;
    transition: border-color 0.2s;
  }
  input:focus, select:focus { border-color: var(--gold); }
  /* TOAST */
  .toast {
    position: fixed;
    bottom: 32px;
    right: 32px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 20px;
    font-size: 13px;
    display: none;
    z-index: 999;
    animation: slideUp 0.3s ease;
  }
  .toast.show { display: block; }
  .toast-success { border-color: rgba(61,214,140,0.4); color: var(--green); }
  .toast-error { border-color: rgba(255,95,87,0.4); color: var(--red); }
  @keyframes slideUp {
    from { transform: translateY(10px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
  /* STATUS LINE */
  .status-line {
    font-size: 11px;
    color: var(--muted);
    padding: 12px 0;
    border-top: 1px solid var(--border);
    margin-top: 12px;
  }
  .text-green { color: var(--green); }
  .text-gold { color: var(--gold); }
  .text-red { color: var(--red); }
  .text-muted { color: var(--muted); }
  /* SCROLLABLE TABLE WRAPPER */
  .table-wrap { overflow-x: auto; }
  /* RESPONSIVE */
  @media (max-width: 900px) {
    .grid-4 { grid-template-columns: repeat(2, 1fr); }
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="logo">Aperture<span>+</span> <span style="color:var(--muted);font-size:12px;font-weight:400;margin-left:8px">ADMIN</span></div>
  <div class="topbar-right">
    <div class="live-dot"></div>
    <div class="time-display" id="clock"></div>
  </div>
</div>

<div class="main">

  <!-- STAT CARDS -->
  <div class="grid-4" id="stat-cards">
    <div class="card card-gold">
      <div class="card-label">Total Subscribers</div>
      <div class="card-value" id="total-subs">—</div>
      <div class="card-sub" id="active-subs">— active</div>
    </div>
    <div class="card card-green">
      <div class="card-label">Revenue This Month</div>
      <div class="card-value" id="rev-month">$0</div>
      <div class="card-sub" id="rev-week">$0 this week</div>
    </div>
    <div class="card">
      <div class="card-label">New Today</div>
      <div class="card-value" id="new-today">0</div>
      <div class="card-sub" id="new-week">0 this week</div>
    </div>
    <div class="card">
      <div class="card-label">Emails Sent</div>
      <div class="card-value" id="emails-sent">—</div>
      <div class="card-sub" id="last-sent">Last send: —</div>
    </div>
  </div>

  <!-- SCORE + SEND -->
  <div class="grid-2" style="margin-bottom:24px">

    <!-- TODAY'S SCORE -->
    <div class="score-card">
      <div class="section-header">
        <div class="section-title">Today's Market Score</div>
        <button class="btn btn-ghost" onclick="refreshScore()">↻ Refresh</button>
      </div>
      <div style="display:flex;align-items:baseline;gap:8px">
        <div class="score-big" id="score-num">—</div>
        <div class="score-denom">/16</div>
      </div>
      <div id="score-badge" class="score-label label-low">Loading...</div>
      <div class="score-sub" style="margin-top:16px;font-size:12px;color:var(--muted)" id="score-subject">—</div>
      <div class="status-line" id="score-meta">Fetching latest data...</div>
    </div>

    <!-- SEND CONTROLS -->
    <div class="send-panel">
      <div class="section-title" style="margin-bottom:8px">Send Controls</div>
      <p style="color:var(--muted);font-size:12px;margin-bottom:20px">Trigger newsletter sends manually.</p>
      <div class="send-actions">
        <div>
          <div style="font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px;text-transform:uppercase">Test Send</div>
          <div class="send-btn-row">
            <button class="btn btn-ghost" onclick="triggerSend('dry-run')" style="flex:1">⊙ Dry Run</button>
            <button class="btn btn-ghost" onclick="triggerSend('test')" style="flex:1">✉ Test Email</button>
          </div>
        </div>
        <div>
          <div style="font-size:11px;color:var(--muted);margin-bottom:8px;letter-spacing:1px;text-transform:uppercase">Live Send</div>
          <button class="btn btn-gold" onclick="confirmSend()" style="width:100%">▶ Send to All Subscribers</button>
        </div>
      </div>
      <div class="status-line" id="send-status">Ready.</div>
    </div>
  </div>

  <!-- SUBSCRIBERS + ADD -->
  <div class="grid-3" style="margin-bottom:24px">
    <div class="card">
      <div class="section-header">
        <div class="section-title">Subscribers</div>
        <span id="sub-count" style="font-size:12px;color:var(--muted)">0 total</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Name</th>
              <th>Plan</th>
              <th>Joined</th>
              <th></th>
            </tr>
          </thead>
          <tbody id="sub-table">
            <tr><td colspan="5" style="color:var(--muted);text-align:center;padding:32px">No subscribers yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="section-title" style="margin-bottom:16px">Add Subscriber</div>
      <div class="input-row" style="flex-direction:column;gap:10px">
        <input type="email" id="new-email" placeholder="email@example.com">
        <input type="text" id="new-name" placeholder="Name (optional)">
        <select id="new-plan">
          <option value="free">Free</option>
          <option value="paid">Pro ($19/mo)</option>
        </select>
        <button class="btn btn-gold" onclick="addSubscriber()" style="width:100%">+ Add Subscriber</button>
      </div>

      <div class="section-title" style="margin-top:32px;margin-bottom:16px">Add Payment</div>
      <div style="flex-direction:column;gap:10px;display:flex">
        <input type="email" id="pay-email" placeholder="email@example.com">
        <input type="text" id="pay-amount" placeholder="Amount (e.g. 9)">
        <select id="pay-plan">
          <option value="monthly">Monthly $19</option>
          <option value="annual">Annual $179</option>
        </select>
        <button class="btn btn-ghost" onclick="addPayment()" style="width:100%">+ Log Payment</button>
      </div>
    </div>
  </div>

  <!-- SEND LOG + FINANCES -->
  <div class="grid-2">
    <div class="card">
      <div class="section-header">
        <div class="section-title">Send History</div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Date</th><th>Subject</th><th>Score</th><th>Recipients</th><th>Status</th></tr>
          </thead>
          <tbody id="send-log">
            <tr><td colspan="5" style="color:var(--muted);text-align:center;padding:32px">No sends yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="section-header">
        <div class="section-title">Finance Log</div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Date</th><th>Email</th><th>Plan</th><th>Amount</th></tr>
          </thead>
          <tbody id="pay-log">
            <tr><td colspan="4" style="color:var(--muted);text-align:center;padding:32px">No payments yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
// Clock
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleTimeString('en-US', {hour12: false});
}
setInterval(updateClock, 1000);
updateClock();

// Toast
function toast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast show toast-${type}`;
  setTimeout(() => t.classList.remove('show'), 3500);
}

// Load stats
async function loadStats() {
  const r = await fetch('/api/stats');
  const d = await r.json();

  document.getElementById('total-subs').textContent = d.total_subscribers;
  document.getElementById('active-subs').textContent = d.active_subscribers + ' active';
  document.getElementById('rev-month').textContent = '$' + d.revenue_month.toFixed(0);
  document.getElementById('rev-week').textContent = '$' + d.revenue_week.toFixed(0) + ' this week';
  document.getElementById('new-today').textContent = d.new_today;
  document.getElementById('new-week').textContent = d.new_week + ' this week';
  document.getElementById('emails-sent').textContent = d.total_sends;
  document.getElementById('last-sent').textContent = d.last_sent ? 'Last: ' + d.last_sent : 'Never sent';
  document.getElementById('sub-count').textContent = d.total_subscribers + ' total';
}

// Load score
async function refreshScore() {
  document.getElementById('score-num').textContent = '…';
  try {
    const r = await fetch('/api/score');
    const d = await r.json();
    document.getElementById('score-num').textContent = d.score ?? '—';
    document.getElementById('score-subject').textContent = d.subject ?? '';
    document.getElementById('score-meta').textContent = `IWM: $${d.iwm ?? '—'} | VIX: ${d.vix ?? '—'} | Updated: ${new Date().toLocaleTimeString()}`;
    const badge = document.getElementById('score-badge');
    if (d.score <= 5) { badge.textContent = 'LOW RISK'; badge.className = 'score-label label-low'; }
    else if (d.score <= 10) { badge.textContent = 'MODERATE RISK'; badge.className = 'score-label label-mid'; }
    else { badge.textContent = 'HIGH RISK'; badge.className = 'score-label label-high'; }
  } catch(e) {
    document.getElementById('score-num').textContent = '—';
    document.getElementById('score-meta').textContent = 'Could not load score. Run scheduler first.';
  }
}

// Load subscribers
async function loadSubscribers() {
  const r = await fetch('/api/subscribers');
  const d = await r.json();
  const tbody = document.getElementById('sub-table');
  if (!d.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:32px">No subscribers yet</td></tr>';
    return;
  }
  tbody.innerHTML = d.map(s => `
    <tr>
      <td>${s.email}</td>
      <td style="color:var(--muted)">${s.name || '—'}</td>
      <td><span class="badge badge-${s.plan}">${s.plan}</span></td>
      <td style="color:var(--muted);font-size:11px">${s.created_at?.split('T')[0] || s.created_at?.split(' ')[0]}</td>
      <td><button class="btn btn-danger" onclick="removeSubscriber(${s.id})">✕</button></td>
    </tr>
  `).join('');
}

// Load send log
async function loadSendLog() {
  const r = await fetch('/api/send-log');
  const d = await r.json();
  const tbody = document.getElementById('send-log');
  if (!d.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:32px">No sends yet</td></tr>';
    return;
  }
  tbody.innerHTML = d.map(s => `
    <tr>
      <td style="font-size:11px;color:var(--muted)">${s.sent_at?.split('T')[0] || s.sent_at?.split(' ')[0]}</td>
      <td style="font-size:12px">${s.subject}</td>
      <td style="color:var(--gold)">${s.score}/16</td>
      <td>${s.recipients}</td>
      <td><span class="badge badge-${s.status}">${s.status}</span></td>
    </tr>
  `).join('');
}

// Load payments
async function loadPayments() {
  const r = await fetch('/api/payments');
  const d = await r.json();
  const tbody = document.getElementById('pay-log');
  if (!d.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--muted);text-align:center;padding:32px">No payments yet</td></tr>';
    return;
  }
  tbody.innerHTML = d.map(p => `
    <tr>
      <td style="font-size:11px;color:var(--muted)">${p.created_at?.split('T')[0] || p.created_at?.split(' ')[0]}</td>
      <td style="font-size:12px">${p.email}</td>
      <td><span class="badge badge-paid">${p.plan}</span></td>
      <td style="color:var(--green)">$${p.amount}</td>
    </tr>
  `).join('');
}

// Add subscriber
async function addSubscriber() {
  const email = document.getElementById('new-email').value.trim();
  const name = document.getElementById('new-name').value.trim();
  const plan = document.getElementById('new-plan').value;
  if (!email) { toast('Enter an email address', 'error'); return; }
  const r = await fetch('/api/subscribers', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email, name, plan})
  });
  const d = await r.json();
  if (d.success) {
    toast('Subscriber added ✓');
    document.getElementById('new-email').value = '';
    document.getElementById('new-name').value = '';
    loadSubscribers(); loadStats();
  } else {
    toast(d.error || 'Failed to add', 'error');
  }
}

// Remove subscriber
async function removeSubscriber(id) {
  if (!confirm('Remove this subscriber?')) return;
  const r = await fetch(`/api/subscribers/${id}`, {method: 'DELETE'});
  const d = await r.json();
  if (d.success) { toast('Removed'); loadSubscribers(); loadStats(); }
}

// Add payment
async function addPayment() {
  const email = document.getElementById('pay-email').value.trim();
  const amount = parseFloat(document.getElementById('pay-amount').value);
  const plan = document.getElementById('pay-plan').value;
  if (!email || !amount) { toast('Fill in email and amount', 'error'); return; }
  const r = await fetch('/api/payments', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({email, amount, plan})
  });
  const d = await r.json();
  if (d.success) {
    toast('Payment logged ✓');
    document.getElementById('pay-email').value = '';
    document.getElementById('pay-amount').value = '';
    loadPayments(); loadStats();
  } else {
    toast(d.error || 'Failed', 'error');
  }
}

// Trigger send
async function triggerSend(mode) {
  document.getElementById('send-status').textContent = `Running ${mode}...`;
  const r = await fetch('/api/send', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({mode})
  });
  const d = await r.json();
  document.getElementById('send-status').textContent = d.message;
  if (d.success) { toast(d.message); loadSendLog(); loadStats(); }
  else toast(d.message, 'error');
}

function confirmSend() {
  if (confirm('Send to ALL subscribers now?')) triggerSend('send');
}

// Init
loadStats();
refreshScore();
loadSubscribers();
loadSendLog();
loadPayments();
setInterval(loadStats, 30000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/stats")
def stats():
    conn = get_db()
    c = conn.cursor()
    now = datetime.now()
    today = now.date().isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    total = c.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
    active = c.execute("SELECT COUNT(*) FROM subscribers WHERE status='active'").fetchone()[0]
    new_today = c.execute("SELECT COUNT(*) FROM subscribers WHERE DATE(created_at)=?", (today,)).fetchone()[0]
    new_week = c.execute("SELECT COUNT(*) FROM subscribers WHERE created_at >= ?", (week_ago,)).fetchone()[0]
    rev_month = c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE created_at >= ? AND status='completed'", (month_ago,)).fetchone()[0]
    rev_week = c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE created_at >= ? AND status='completed'", (week_ago,)).fetchone()[0]
    total_sends = c.execute("SELECT COUNT(*) FROM send_log").fetchone()[0]
    last_row = c.execute("SELECT sent_at FROM send_log ORDER BY sent_at DESC LIMIT 1").fetchone()
    last_sent = last_row[0] if last_row else None
    conn.close()

    return jsonify({
        "total_subscribers": total,
        "active_subscribers": active,
        "new_today": new_today,
        "new_week": new_week,
        "revenue_month": float(rev_month),
        "revenue_week": float(rev_week),
        "total_sends": total_sends,
        "last_sent": last_sent
    })

@app.route("/api/score")
def score():
    # Try to read from last run log
    log_dir = os.path.expanduser("~/aperture/logs")
    try:
        import glob
        files = sorted(glob.glob(f"{log_dir}/*.log"), reverse=True)
        if files:
            with open(files[0]) as f:
                content = f.read()
            import re
            score_match = re.search(r'Score[:\s]+(\d+)/16', content)
            subject_match = re.search(r'Subject[:\s]+"([^"]+)"', content)
            iwm_match = re.search(r'IWM[:\s]+\$?([\d.]+)', content)
            vix_match = re.search(r'VIX[:\s]+([\d.]+)', content)
            return jsonify({
                "score": int(score_match.group(1)) if score_match else None,
                "subject": subject_match.group(1) if subject_match else "Run scheduler to generate",
                "iwm": iwm_match.group(1) if iwm_match else None,
                "vix": vix_match.group(1) if vix_match else None,
            })
    except:
        pass
    return jsonify({"score": None, "subject": "Run scheduler to generate today's issue", "iwm": None, "vix": None})

@app.route("/api/subscribers", methods=["GET"])
def get_subscribers():
    conn = get_db()
    rows = conn.execute("SELECT * FROM subscribers ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/subscribers", methods=["POST"])
def add_subscriber():
    data = request.json
    try:
        conn = get_db()
        conn.execute("INSERT INTO subscribers (email, name, plan) VALUES (?,?,?)",
                     (data["email"], data.get("name",""), data.get("plan","free")))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "Email already exists"})

@app.route("/api/subscribers/<int:sub_id>", methods=["DELETE"])
def remove_subscriber(sub_id):
    conn = get_db()
    conn.execute("DELETE FROM subscribers WHERE id=?", (sub_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/send-log")
def send_log():
    conn = get_db()
    rows = conn.execute("SELECT * FROM send_log ORDER BY sent_at DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/payments", methods=["GET"])
def get_payments():
    conn = get_db()
    rows = conn.execute("SELECT * FROM payments ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/payments", methods=["POST"])
def add_payment():
    data = request.json
    try:
        conn = get_db()
        conn.execute("INSERT INTO payments (email, plan, amount) VALUES (?,?,?)",
                     (data["email"], data["plan"], data["amount"]))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/send", methods=["POST"])
def trigger_send():
    data = request.json
    mode = data.get("mode", "dry-run")
    aperture_dir = os.path.expanduser("~/aperture")
    venv_python = os.path.join(aperture_dir, "venv/bin/python3")

    flag_map = {"dry-run": "--dry-run", "test": "--test", "send": "--send"}
    flag = flag_map.get(mode, "--dry-run")

    try:
        result = subprocess.run(
            [venv_python, "scheduler.py", flag],
            cwd=aperture_dir,
            capture_output=True, text=True, timeout=120
        )
        success = result.returncode == 0
        msg = "Completed successfully" if success else f"Error: {result.stderr[-200:]}"

        if success and mode == "send":
            conn = get_db()
            sub_count = conn.execute("SELECT COUNT(*) FROM subscribers WHERE status='active'").fetchone()[0]
            conn.execute("INSERT INTO send_log (subject, score, recipients, status) VALUES (?,?,?,?)",
                         ("Manual send", 0, sub_count, "sent"))
            conn.commit()
            conn.close()

        return jsonify({"success": success, "message": msg})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "Timed out after 2 minutes"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == "__main__":
    init_db()
    print("\n" + "="*50)
    print("  Aperture+ Admin Dashboard")
    print("  http://localhost:5001")
    print("="*50 + "\n")
    app.run(debug=False, port=5001)

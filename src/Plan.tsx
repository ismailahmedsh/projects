import React, { useState, useMemo, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";

const INK = "#1c1b17";
const CREAM = "#f6f2ea";
const CARD = "#fffdf8";
const GREEN = "#1f4d3a";
const AMBER = "#b4671f";
const BLUE = "#2f5d7c";
const RED = "#9c3b2e";
const MUTE = "#7c766b";
const LINE = "#e4ddcf";

const fmt = (n) => (isFinite(n) ? Math.round(n).toLocaleString("en-US") : "—");
const fmtK = (n) => (Math.abs(n) >= 1000 ? Math.round(n / 1000) + "k" : Math.round(n));
const MO = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Local-only persistence: real figures live in the browser, never in the bundle.
const LS_KEY = "portfolio-plan-v1";
const loadSaved = () => {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || "{}") || {}; }
  catch { return {}; }
};

// Generic example defaults — replace them in the app; your entries persist locally.
const CF_DEFAULTS = {
  salary: 30000, rentIncome: 5000, myRent: 4000, serviceCharge: 1000,
  living: 10000, currentCash: 100000, floor: 50000, eqRate: 8.0,
  rate: 4.0, bal0: 500000, installment: 4000,
};

// total interest paid on the original schedule with no extra payments
function baselineInterest(bal0, rate, installment) {
  let bal = bal0, i = rate / 100 / 12, interest = 0;
  for (let m = 0; m < 1200 && bal > 0.5; m++) {
    const intr = bal * i; interest += intr;
    let pr = installment - intr;
    if (pr <= 0) return interest; // installment never amortizes the loan
    if (pr > bal) pr = bal;
    bal -= pr;
  }
  return interest;
}

// instant-access (eSaver-style) tiered rates, % p.a. by balance
function flexRate(bal) {
  if (bal >= 5000000) return 3.0;
  if (bal >= 1000000) return 1.75;
  if (bal >= 500000) return 1.0;
  if (bal >= 100000) return 0.5;
  return 0.3;
}

const PRESETS = {
  Aggressive: { m: 70, e: 60 },
  Balanced: { m: 40, e: 65 },
  Relaxed: { m: 15, e: 80 },
};

function simulate(p) {
  const { surplus, spare, mPct, ePct, eqRate, flexShare, ladderRate, horizonYear, rate, bal0, installment } = p;
  const HORIZON = (horizonYear - 2026) * 12; // lands on June of the selected year
  const i = rate / 100 / 12, de = eqRate / 100 / 12, dl = ladderRate / 100 / 12;
  const mFrac = mPct / 100, eRatio = ePct / 100, fShare = flexShare / 100;
  let bal = bal0, sleeve = 0, flex = 0, ladder = 0, equity = 0;
  let interest = 0, fees = 0, paid = false, payoffLabel = null;

  // deploy spare now
  equity += spare * eRatio;
  flex += spare * (1 - eRatio) * fShare;
  ladder += spare * (1 - eRatio) * (1 - fShare);

  const schedule = [], series = [];
  let y = 2026, mo = 6;

  for (let m = 1; m <= HORIZON; m++) {
    mo++; if (mo > 12) { mo = 1; y++; }
    if (bal > 0) {
      const intr = bal * i; interest += intr;
      let pr = installment - intr; if (pr > bal) pr = bal; bal -= pr;
    }
    const savIn = paid
      ? (surplus * mFrac + installment) * (1 - eRatio)
      : surplus * (1 - mFrac) * (1 - eRatio);
    const eqIn = paid
      ? (surplus * mFrac + installment) * eRatio
      : surplus * (1 - mFrac) * eRatio;
    if (!paid) sleeve += surplus * mFrac;
    flex += savIn * fShare;
    ladder += savIn * (1 - fShare);
    equity += eqIn;

    sleeve *= 1 + flexRate(sleeve) / 100 / 12;
    flex *= 1 + flexRate(flex) / 100 / 12;
    ladder *= 1 + dl;
    equity *= 1 + de;

    if (!paid && mo === 6 && y >= 2027 && bal > 0) {
      const pay = Math.min(sleeve, bal);
      fees += pay * 0.01; bal -= pay; sleeve -= pay;
      schedule.push({ label: `${MO[mo]} ${y}`, amt: pay, bal: Math.max(0, bal) });
    }
    if (!paid && bal <= 0.5) {
      bal = 0; paid = true; payoffLabel = `${MO[mo]} ${y}`;
      equity += sleeve * eRatio;
      flex += sleeve * (1 - eRatio) * fShare;
      ladder += sleeve * (1 - eRatio) * (1 - fShare);
      sleeve = 0;
      schedule.push({ label: payoffLabel, amt: 0, bal: 0, cleared: true });
    }
    if (m % 3 === 0 || m === 1) {
      series.push({
        t: +(m / 12).toFixed(2), mortgage: Math.round(bal),
        savings: Math.round(flex + ladder), equity: Math.round(equity),
      });
    }
  }
  return {
    schedule, series, interest: Math.round(interest), fees: Math.round(fees),
    payoffLabel, endFlex: Math.round(flex), endLadder: Math.round(ladder),
    endEq: Math.round(equity), warchest: Math.round(flex + ladder + equity),
  };
}

export default function Plan() {
  const saved0 = loadSaved();
  const [cf, setCf] = useState({ ...CF_DEFAULTS, ...(saved0.cf || {}) });
  const [active, setActive] = useState("");
  const [mPct, setMPct] = useState(saved0.mPct ?? PRESETS.Balanced.m);
  const [ePct, setEPct] = useState(saved0.ePct ?? 10);
  // savings sleeve detail
  const [flexShare, setFlexShare] = useState(saved0.flexShare ?? 40);
  const [horizonYear, setHorizonYear] = useState(saved0.horizonYear ?? 2037);
  const [showSav, setShowSav] = useState(true);
  const [docTitle, setDocTitle] = useState(saved0.docTitle ?? 'Payoff + Portfolio Plan');

  const [showCharts, setShowCharts] = useState(true);
  const [showTable, setShowTable] = useState(true);
  const [w12, setW12] = useState(saved0.w12 ?? 50), [w24, setW24] = useState(saved0.w24 ?? 25), [w36, setW36] = useState(saved0.w36 ?? 25);
  const [r12, setR12] = useState(saved0.r12 ?? 3.95), [r24, setR24] = useState(saved0.r24 ?? 4.1), [r36, setR36] = useState(saved0.r36 ?? 4.4);

  // persist everything the user tweaks to their browser only
  useEffect(() => {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify({
        cf, mPct, ePct, flexShare, horizonYear, docTitle, w12, w24, w36, r12, r24, r36,
      }));
    } catch { /* storage unavailable — ignore */ }
  }, [cf, mPct, ePct, flexShare, horizonYear, docTitle, w12, w24, w36, r12, r24, r36]);

  const pick = (k) => { setActive(k); setMPct(PRESETS[k].m); setEPct(PRESETS[k].e); };
  const setF = (k) => (e) => { const v = parseFloat(e.target.value); setCf((s) => ({ ...s, [k]: isNaN(v) ? 0 : v })); };

  const income = cf.salary + cf.rentIncome;
  const outgo = cf.myRent + cf.installment + cf.serviceCharge + cf.living;
  const surplus = income - outgo;
  const spare = Math.max(0, cf.currentCash - cf.floor);

  const wSum = w12 + w24 + w36 || 1;
  const ladderRate = (w12 * r12 + w24 * r24 + w36 * r36) / wSum;

  const sim = useMemo(() => simulate({
    surplus: Math.max(0, surplus), spare, mPct, ePct,
    eqRate: cf.eqRate, flexShare, ladderRate, horizonYear,
    rate: cf.rate, bal0: cf.bal0, installment: cf.installment,
  }), [surplus, spare, mPct, ePct, cf.eqRate, flexShare, ladderRate, horizonYear, cf.rate, cf.bal0, cf.installment]);

  const baseline = useMemo(() => baselineInterest(cf.bal0, cf.rate, cf.installment), [cf.bal0, cf.rate, cf.installment]);
  const saved = baseline - sim.interest;
  const Hm = (horizonYear - 2026) * 12;
  const spareSav = spare * Math.pow(1 + ladderRate / 100 / 12, Hm);
  const spareEq = spare * Math.pow(1 + cf.eqRate / 100 / 12, Hm);
  const mAed = Math.round(surplus * (mPct / 100));
  const eAed = Math.round(surplus * (1 - mPct / 100) * (ePct / 100));
  const sAed = Math.round(surplus * (1 - mPct / 100) * (1 - ePct / 100));
  const blended = ((flexShare / 100) * 0.5 + (1 - flexShare / 100) * ladderRate).toFixed(2);

  const rows = [
    ["Salary", cf.salary, "in", "salary"],
    ["Property rent", cf.rentIncome, "in", "rentIncome"],
    ["Your rent", cf.myRent, "out", "myRent"],
    ["Mortgage installment", cf.installment, "out", "installment"],
    ["Service charge", cf.serviceCharge, "out", "serviceCharge"],
    ["Living expenses", cf.living, "out", "living"],
  ];
  const allocBars = [["Mortgage", mAed, INK], ["Equity", eAed, AMBER], ["Savings", sAed, BLUE]];
  const allocTotal = mAed + eAed + sAed || 1;
  const num = (v, set, w = 58) => (
    <input type="number" step="0.05" value={v} onChange={(e) => set(parseFloat(e.target.value) || 0)}
      style={{ width: w, textAlign: "right", padding: "3px 6px", border: `1px solid ${LINE}`, borderRadius: 6, background: CREAM, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12, color: INK }} />
  );



  return (
    <div style={{ background: CREAM, padding: "26px 18px", color: INK }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap'); .pp *{box-sizing:border-box}
@media(max-width:640px){
  .pp .grid-top{grid-template-columns:1fr!important}
  .pp .grid-sav{grid-template-columns:1fr!important}
  .pp .grid-charts{grid-template-columns:1fr!important}
  .pp .grid-metrics{grid-template-columns:repeat(2,1fr)!important}
  .pp .save-slots{flex-direction:column}
  .pp .save-slot{flex:1 1 100%!important}
  .pp .alloc-legend{flex-wrap:wrap;gap:4px}
  .pp .deploy-boxes{flex-direction:column}
  .pp .cash-fields{flex-direction:column}
}
`}</style>
      <div className="pp" style={{ maxWidth: 980, margin: "0 auto", fontFamily: "'Hanken Grotesk',sans-serif" }}>

        <div style={{ borderBottom: `2px solid ${INK}`, paddingBottom: 12, marginBottom: 18 }}>
          <input
            value={docTitle} onChange={(e) => setDocTitle(e.target.value)}
            style={{ fontFamily: "'Fraunces',serif", fontSize: 27, fontWeight: 600, letterSpacing: -0.4, border: "none", background: "transparent", color: INK, width: "100%", outline: "none", margin: 0, padding: 0 }}
          />

        </div>

                <div className="grid-top" style={{ display: "grid", gridTemplateColumns: "1.05fr 1fr", gap: 18, alignItems: "start" }}>
          <div>
            <h3 style={{ fontFamily: "'Fraunces',serif", fontSize: 15, margin: "0 0 9px" }}>Monthly cash flow</h3>
            <div style={{ background: CARD, border: `1px solid ${LINE}`, borderRadius: 12, padding: "13px 15px" }}>
              {rows.map(([l, v, d, k]) => (
                <div key={l} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 3 }}>
                    <span style={{ fontSize: 12.5, color: d === "in" ? GREEN : INK }}>{d === "in" ? "+ " : "− "}{l}</span>
                    {k ? <input type="number" value={v} onChange={setF(k)} style={{ width: 90, textAlign: "right", padding: "3px 7px", border: `1px solid ${LINE}`, borderRadius: 6, background: CREAM, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5, color: INK }} />
                      : <span style={{ width: 90, textAlign: "right", fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5, color: MUTE }}>{fmt(v)}</span>}
                  </div>
                  <div style={{ height: 4, borderRadius: 3, background: LINE, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${Math.min(100, (v / income) * 100)}%`, background: d === "in" ? GREEN : AMBER, opacity: d === "in" ? 1 : 0.5 }} />
                  </div>
                </div>
              ))}
              <div style={{ borderTop: `1.5px solid ${INK}`, marginTop: 10, paddingTop: 9, display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Net surplus to deploy</span>
                <span style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 18, fontWeight: 600, color: surplus >= 0 ? GREEN : RED }}>{fmt(surplus)}</span>
              </div>
              <div className="cash-fields" style={{ display: "flex", gap: 8, marginTop: 12 }}>
                <label style={{ flex: 1 }}>
                  <span style={{ fontSize: 10.5, color: MUTE, display: "block", marginBottom: 3 }}>Current cash balance</span>
                  <input type="number" value={cf.currentCash} onChange={setF("currentCash")} style={{ width: "100%", padding: "5px 8px", border: `1px solid ${LINE}`, borderRadius: 6, background: CREAM, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5, color: INK }} />
                </label>
                <label style={{ flex: 1 }}>
                  <span style={{ fontSize: 10.5, color: MUTE, display: "block", marginBottom: 3 }}>Emergency fund (kept liquid)</span>
                  <input type="number" value={cf.floor} onChange={setF("floor")} style={{ width: "100%", padding: "5px 8px", border: `1px solid ${LINE}`, borderRadius: 6, background: CREAM, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5, color: INK }} />
                </label>
              </div>
              <div className="cash-fields" style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <label style={{ flex: 1 }}>
                  <span style={{ fontSize: 10.5, color: MUTE, display: "block", marginBottom: 3 }}>Mortgage balance</span>
                  <input type="number" value={cf.bal0} onChange={setF("bal0")} style={{ width: "100%", padding: "5px 8px", border: `1px solid ${LINE}`, borderRadius: 6, background: CREAM, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5, color: INK }} />
                </label>
                <label style={{ flex: 1 }}>
                  <span style={{ fontSize: 10.5, color: MUTE, display: "block", marginBottom: 3 }}>Mortgage rate (% p.a.)</span>
                  <input type="number" step="0.05" value={cf.rate} onChange={setF("rate")} style={{ width: "100%", padding: "5px 8px", border: `1px solid ${LINE}`, borderRadius: 6, background: CREAM, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5, color: INK }} />
                </label>
              </div>
              <div style={{ fontSize: 11, color: MUTE, marginTop: 8 }}>{fmt(spare)} deployable now (cash minus emergency fund). If it all went to one place, by June {horizonYear}:</div>
              <div className="deploy-boxes" style={{ display: "flex", gap: 8, marginTop: 6 }}>
                <div style={{ flex: 1, background: CREAM, border: `1px solid ${LINE}`, borderRadius: 8, padding: "7px 10px" }}>
                  <div style={{ fontSize: 10, color: BLUE, marginBottom: 2 }}>all in deposit ladder ({ladderRate.toFixed(2)}%)</div>
                  <div style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 14, fontWeight: 600, color: BLUE }}>{fmt(spareSav)}</div>
                </div>
                <div style={{ flex: 1, background: CREAM, border: `1px solid ${LINE}`, borderRadius: 8, padding: "7px 10px" }}>
                  <div style={{ fontSize: 10, color: AMBER, marginBottom: 2 }}>all in equity ({cf.eqRate}% expected)</div>
                  <div style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 14, fontWeight: 600, color: AMBER }}>{fmt(spareEq)}</div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 style={{ fontFamily: "'Fraunces',serif", fontSize: 15, margin: "0 0 9px" }}>Where the surplus goes</h3>
            <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
              {Object.keys(PRESETS).map((k) => {
                const on = k === active;
                return <button key={k} onClick={() => pick(k)} style={{ flex: 1, padding: "8px 6px", borderRadius: 9, cursor: "pointer", border: `1px solid ${on ? INK : LINE}`, background: on ? INK : CARD, color: on ? CREAM : INK, fontFamily: "'Hanken Grotesk',sans-serif", fontSize: 12.5, fontWeight: 500 }}>{k}</button>;
              })}
            </div>
            <div style={{ background: CARD, border: `1px solid ${LINE}`, borderRadius: 12, padding: "13px 15px" }}>
              <label style={{ display: "block", marginBottom: 11 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: MUTE, marginBottom: 3 }}><span>To mortgage</span><span style={{ fontFamily: "'IBM Plex Mono',monospace", color: INK }}>{mPct}%</span></div>
                <input type="range" min={0} max={100} step={5} value={mPct} onChange={(e) => { setMPct(+e.target.value); setActive(""); }} style={{ width: "100%", accentColor: INK }} />
              </label>
              <label style={{ display: "block", marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: MUTE, marginBottom: 3 }}><span>Of the rest, to equity</span><span style={{ fontFamily: "'IBM Plex Mono',monospace", color: INK }}>{ePct}%</span></div>
                <input type="range" min={0} max={100} step={5} value={ePct} onChange={(e) => { setEPct(+e.target.value); setActive(""); }} style={{ width: "100%", accentColor: AMBER }} />
              </label>
              <div style={{ display: "flex", height: 22, borderRadius: 6, overflow: "hidden", border: `1px solid ${LINE}` }}>
                {allocBars.map(([l, v, c]) => (
                  <div key={l} title={`${l} ${fmt(v)}`} style={{ width: `${(v / allocTotal) * 100}%`, background: c }} />
                ))}
              </div>
              <div className="alloc-legend" style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginTop: 6, fontFamily: "'IBM Plex Mono',monospace" }}>
                <span style={{ color: INK }}>■ mortgage {fmt(mAed)}</span>
                <span style={{ color: AMBER }}>■ equity {fmt(eAed)}</span>
                <span style={{ color: BLUE }}>■ savings {fmt(sAed)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* SAVINGS SLEEVE DETAIL */}
        <button onClick={() => setShowSav(!showSav)} style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", cursor: "pointer", padding: 0, margin: "18px 0 9px", fontFamily: "'Fraunces',serif", fontSize: 15, color: INK, fontWeight: 600 }}>
          <span style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 13 }}>{showSav ? "▾" : "▸"}</span>
          Inside the savings bucket — {fmt(sAed)}/mo
        </button>
        {showSav && (
        <div className="grid-sav" style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 18, alignItems: "start" }}>
          <div style={{ background: CARD, border: `1px solid ${LINE}`, borderRadius: 12, padding: "13px 15px" }}>
            <label style={{ display: "block", marginBottom: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: MUTE, marginBottom: 3 }}>
                <span>Instant-access saver share</span>
                <span style={{ fontFamily: "'IBM Plex Mono',monospace", color: INK }}>{flexShare}%</span>
              </div>
              <input type="range" min={0} max={100} step={5} value={flexShare} onChange={(e) => setFlexShare(+e.target.value)} style={{ width: "100%", accentColor: BLUE }} />
              <div style={{ fontSize: 11, color: MUTE, marginTop: 3 }}>
                {fmt(sAed * flexShare / 100)}/mo flexible · {fmt(sAed * (1 - flexShare / 100))}/mo into deposit ladder
              </div>
            </label>
            <div style={{ fontSize: 11.5, color: MUTE, marginBottom: 6 }}>Instant-access tiers (eSaver-style, % p.a.)</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5, fontFamily: "'IBM Plex Mono',monospace" }}>
              <tbody>
                {[["below 100k", "0.30"], ["100k – 500k", "0.50"], ["500k – 1M", "1.00"], ["1M – 5M", "1.75"]].map(([t, r]) => (
                  <tr key={t} style={{ borderBottom: `1px solid ${LINE}` }}>
                    <td style={{ padding: "5px 6px", color: INK }}>{t}</td>
                    <td style={{ padding: "5px 6px", textAlign: "right", color: RED }}>{r}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ fontSize: 11, color: MUTE, marginTop: 7, lineHeight: 1.5 }}>
              Withdraw anytime, no minimum, but the rate is poor below 500k. Use only for the emergency fund and cash awaiting deployment.
            </div>
          </div>

          <div style={{ background: CARD, border: `1px solid ${LINE}`, borderRadius: 12, padding: "13px 15px" }}>
            <div style={{ fontSize: 11.5, color: MUTE, marginBottom: 6 }}>Term-deposit ladder (rates editable, weights = % of ladder)</div>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: `1.5px solid ${INK}`, color: MUTE }}>
                  <th style={{ textAlign: "left", padding: "5px 6px", fontWeight: 500 }}>Tenor</th>
                  <th style={{ textAlign: "right", padding: "5px 6px", fontWeight: 500 }}>Rate %</th>
                  <th style={{ textAlign: "right", padding: "5px 6px", fontWeight: 500 }}>Weight %</th>
                  <th style={{ textAlign: "right", padding: "5px 6px", fontWeight: 500 }}>Typical min</th>
                </tr>
              </thead>
              <tbody style={{ fontFamily: "'IBM Plex Mono',monospace" }}>
                <tr style={{ borderBottom: `1px solid ${LINE}` }}>
                  <td style={{ padding: "6px" }}>12 mo</td>
                  <td style={{ padding: "6px", textAlign: "right" }}>{num(r12, setR12)}</td>
                  <td style={{ padding: "6px", textAlign: "right" }}>{num(w12, setW12, 50)}</td>
                  <td style={{ padding: "6px", textAlign: "right", color: MUTE }}>10k</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${LINE}` }}>
                  <td style={{ padding: "6px" }}>24 mo</td>
                  <td style={{ padding: "6px", textAlign: "right" }}>{num(r24, setR24)}</td>
                  <td style={{ padding: "6px", textAlign: "right" }}>{num(w24, setW24, 50)}</td>
                  <td style={{ padding: "6px", textAlign: "right", color: MUTE }}>10–25k</td>
                </tr>
                <tr>
                  <td style={{ padding: "6px" }}>36 mo</td>
                  <td style={{ padding: "6px", textAlign: "right" }}>{num(r36, setR36)}</td>
                  <td style={{ padding: "6px", textAlign: "right" }}>{num(w36, setW36, 50)}</td>
                  <td style={{ padding: "6px", textAlign: "right", color: MUTE }}>25k+</td>
                </tr>
              </tbody>
            </table>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10, padding: "8px 10px", background: CREAM, borderRadius: 8, fontFamily: "'IBM Plex Mono',monospace", fontSize: 12.5 }}>
              <span style={{ color: MUTE }}>ladder rate {ladderRate.toFixed(2)}%</span>
              <span style={{ color: INK, fontWeight: 600 }}>blended savings ≈ {blended}%</span>
            </div>
            <div style={{ fontSize: 11, color: MUTE, marginTop: 7, lineHeight: 1.5 }}>
              Breaking a deposit early typically costs ~2% off the rate, so match tenors to when you need the cash. Longer tenor pays more but locks longer.
            </div>
          </div>
        </div>
        )}


        <button onClick={() => setShowCharts(!showCharts)} style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", cursor: "pointer", padding: 0, margin: "4px 0 9px", fontFamily: "'Fraunces',serif", fontSize: 15, color: INK, fontWeight: 600 }}>
          <span style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 13 }}>{showCharts ? "\u25be" : "\u25b8"}</span>
          Charts
        </button>
        {showCharts && (
        <div className="grid-charts" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <h4 style={{ fontFamily: "'Fraunces',serif", fontSize: 14, margin: "0 0 4px" }}>Mortgage balance</h4>
            <div style={{ height: 175 }}>
              <ResponsiveContainer>
                <LineChart data={sim.series} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke={LINE} vertical={false} />
                  <XAxis dataKey="t" tick={{ fontSize: 10, fill: MUTE }} unit="y" />
                  <YAxis tickFormatter={fmtK} tick={{ fontSize: 10, fill: MUTE }} width={36} />
                  <Tooltip formatter={(v) => fmt(v)} labelFormatter={(l) => `Year ${l}`} />
                  <Line type="monotone" dataKey="mortgage" stroke={INK} strokeWidth={2.5} dot={false} name="Mortgage" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div>
            <h4 style={{ fontFamily: "'Fraunces',serif", fontSize: 14, margin: "0 0 4px" }}>Savings + equity build-up</h4>
            <div style={{ height: 175 }}>
              <ResponsiveContainer>
                <LineChart data={sim.series} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke={LINE} vertical={false} />
                  <XAxis dataKey="t" tick={{ fontSize: 10, fill: MUTE }} unit="y" />
                  <YAxis tickFormatter={fmtK} tick={{ fontSize: 10, fill: MUTE }} width={36} />
                  <Tooltip formatter={(v) => fmt(v)} labelFormatter={(l) => `Year ${l}`} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="equity" stroke={AMBER} strokeWidth={2.5} dot={false} name="Equity" />
                  <Line type="monotone" dataKey="savings" stroke={BLUE} strokeWidth={2.5} dot={false} name="Savings (all)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        )}

        <button onClick={() => setShowTable(!showTable)} style={{ display: "flex", alignItems: "center", gap: 8, background: "none", border: "none", cursor: "pointer", padding: 0, margin: "16px 0 7px", fontFamily: "'Fraunces',serif", fontSize: 15, color: INK, fontWeight: 600 }}>
          <span style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 13 }}>{showTable ? "\u25be" : "\u25b8"}</span>
          Mortgage lump schedule (each June, from saved surplus)
        </button>
        {showTable && (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
            <thead><tr style={{ borderBottom: `1.5px solid ${INK}`, color: MUTE }}>
              <th style={{ textAlign: "left", padding: "6px 10px", fontWeight: 500 }}>Date</th>
              <th style={{ textAlign: "right", padding: "6px 10px", fontWeight: 500 }}>Lump (AED)</th>
              <th style={{ textAlign: "right", padding: "6px 10px", fontWeight: 500 }}>Balance after</th>
            </tr></thead>
            <tbody>
              {sim.schedule.length === 0 && <tr><td colSpan={3} style={{ padding: 10, color: MUTE }}>No lumps under this split.</td></tr>}
              {sim.schedule.map((r, idx) => (
                <tr key={idx} style={{ borderBottom: `1px solid ${LINE}`, background: r.cleared ? "#e7efe7" : "transparent" }}>
                  <td style={{ padding: "7px 10px", fontFamily: "'IBM Plex Mono',monospace" }}>{r.label}</td>
                  <td style={{ padding: "7px 10px", textAlign: "right", fontFamily: "'IBM Plex Mono',monospace" }}>{r.cleared ? "cleared" : fmt(r.amt)}</td>
                  <td style={{ padding: "7px 10px", textAlign: "right", fontFamily: "'IBM Plex Mono',monospace", fontWeight: 600, color: r.cleared ? GREEN : INK }}>{fmt(r.bal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}

        {/* HEADLINE */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "18px 0 8px" }}>
          <h3 style={{ fontFamily: "'Fraunces',serif", fontSize: 15, margin: 0 }}>Results by June</h3>
          <select value={horizonYear} onChange={(e) => setHorizonYear(+e.target.value)}
            style={{ padding: "5px 10px", border: `1px solid ${LINE}`, borderRadius: 7, background: CARD, fontFamily: "'IBM Plex Mono',monospace", fontSize: 13, color: INK, cursor: "pointer" }}>
            {Array.from({ length: 18 }, (_, k) => 2028 + k).map((yy) => <option key={yy} value={yy}>{yy}</option>)}
          </select>
        </div>
        <div className="grid-metrics" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(135px,1fr))", gap: 10, margin: "0 0 6px" }}>
          {[
            ["Loan cleared", sim.payoffLabel || `after ${horizonYear}`, GREEN],
            ["Interest saved", fmt(saved), GREEN],
            [`Equity by ${horizonYear}`, fmt(sim.endEq), AMBER],
            [`Deposits by ${horizonYear}`, fmt(sim.endLadder), BLUE],
            [`Flexi cash by ${horizonYear}`, fmt(sim.endFlex), BLUE],
            [`Total pot by ${horizonYear}`, fmt(sim.warchest), INK],
          ].map(([l, v, c]) => (
            <div key={l} style={{ background: CARD, border: `1px solid ${LINE}`, borderRadius: 10, padding: "11px 13px" }}>
              <div style={{ fontSize: 10.5, color: MUTE, marginBottom: 5, lineHeight: 1.3 }}>{l}</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: c, fontFamily: "'IBM Plex Mono',monospace" }}>{v}</div>
            </div>
          ))}
        </div>
        <div style={{ fontSize: 10.5, color: MUTE, marginBottom: 14 }}>AED. Total pot = flexi cash + deposits + equity at the selected year. This is the pool a future down payment would come from.</div>


      </div>
    </div>
  );
}

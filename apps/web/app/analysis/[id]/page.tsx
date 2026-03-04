"use client";

import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import { getAnalysis, downloadReport } from "@/lib/api";
import type { AnalysisResult, InterpretationResult, MatchedPattern } from "@/lib/types";

/* ═══════════════════════════════════════════════════════════════════
   Panel styles & display names
   ═══════════════════════════════════════════════════════════════════ */

const PS: Record<string, { color: string; accent: string }> = {
  "Complete Blood Count": { color: "#FEF2F2", accent: "#EF4444" },
  "Iron Studies": { color: "#FEF2F2", accent: "#EF4444" },
  Vitamins: { color: "#FFFBEB", accent: "#F59E0B" },
  "Renal Function": { color: "#F5F3FF", accent: "#8B5CF6" },
  Diabetes: { color: "#FFFBEB", accent: "#D97706" },
  Thyroid: { color: "#FDF2F8", accent: "#EC4899" },
  "Liver Function": { color: "#ECFDF5", accent: "#10B981" },
  "Lipid Profile": { color: "#EFF6FF", accent: "#3B82F6" },
  Electrolytes: { color: "#ECFEFF", accent: "#06B6D4" },
  "Urine Analysis": { color: "#F5F3FF", accent: "#8B5CF6" },
  "Tumor Markers": { color: "#FAF5FF", accent: "#9333EA" },
  Other: { color: "#F1F5F9", accent: "#64748B" },
};

const DN: Record<string, string> = {
  hemoglobin: "Hemoglobin", hematocrit: "Hematocrit", mcv: "MCV", mch: "MCH", mchc: "MCHC",
  rdw: "RDW-CV", rdw_sd: "RDW-SD", wbc: "Total WBC", neutrophils: "Neutrophils", lymphocytes: "Lymphocytes",
  platelets: "Platelets", rbc: "RBC Count", neutrophils_pct: "Neutrophils %", lymphocytes_pct: "Lymphocytes %",
  monocytes_pct: "Monocytes %", eosinophils_pct: "Eosinophils %", basophils_pct: "Basophils %",
  aec: "AEC (Abs. Eosinophil Count)", anc: "ANC (Abs. Neutrophil Count)", alc: "ALC (Abs. Lymphocyte Count)",
  amc: "AMC (Abs. Monocyte Count)", abc: "ABC (Abs. Basophil Count)",
  ferritin: "Ferritin", serum_iron: "Serum Iron", tibc: "TIBC", transferrin_saturation: "Transferrin Sat",
  vitamin_b12: "Vitamin B12", folate: "Folate", vitamin_d: "Vitamin D (25-OH)",
  creatinine: "Creatinine", bun: "BUN", urea: "Urea", egfr: "eGFR", uric_acid: "Uric Acid",
  fasting_glucose: "Fasting Glucose", hba1c: "HbA1c", avg_blood_glucose: "Est. Avg. Glucose",
  fasting_insulin: "Fasting Insulin", pp_glucose: "PP Glucose (2h)",
  tsh: "TSH", free_t4: "Free T4", free_t3: "Free T3", total_t3: "Total T3", total_t4: "Total T4", anti_tpo: "Anti-TPO Ab",
  alt: "ALT (SGPT)", ast: "AST (SGOT)", alp: "ALP", ggt: "GGT (Gamma-GT)", total_bilirubin: "Total Bilirubin",
  direct_bilirubin: "Direct Bilirubin", indirect_bilirubin: "Indirect Bilirubin",
  albumin: "Albumin", total_protein: "Total Protein", globulin: "Globulin", ag_ratio: "A/G Ratio",
  total_cholesterol: "Total Cholesterol", ldl: "LDL", hdl: "HDL Cholesterol", triglycerides: "Triglycerides",
  vldl: "VLDL", non_hdl_cholesterol: "Non-HDL Cholesterol",
  sodium: "Sodium", potassium: "Potassium", chloride: "Chloride", calcium: "Calcium",
  phosphate: "Phosphate", magnesium: "Magnesium",
  afp: "AFP", cea: "CEA", ca19_9: "CA 19-9", ca15_3: "CA 15-3", psa: "PSA", ca125: "CA-125",
};

const PANEL_ORDER: [string, string[]][] = [
  ["Complete Blood Count", ["hemoglobin","hematocrit","mcv","mch","mchc","rdw","rdw_sd","wbc","neutrophils","lymphocytes","platelets","rbc","neutrophils_pct","lymphocytes_pct","monocytes_pct","eosinophils_pct","basophils_pct","aec","anc","alc","amc","abc"]],
  ["Iron Studies", ["ferritin","serum_iron","tibc","transferrin_saturation"]],
  ["Vitamins", ["vitamin_b12","folate","vitamin_d"]],
  ["Renal Function", ["creatinine","bun","egfr","uric_acid","urea"]],
  ["Diabetes", ["fasting_glucose","hba1c","avg_blood_glucose","fasting_insulin","pp_glucose"]],
  ["Thyroid", ["tsh","free_t4","free_t3","total_t3","total_t4","anti_tpo"]],
  ["Liver Function", ["alt","ast","alp","ggt","total_bilirubin","direct_bilirubin","indirect_bilirubin","albumin","total_protein","globulin","ag_ratio"]],
  ["Lipid Profile", ["total_cholesterol","ldl","hdl","triglycerides","vldl","non_hdl_cholesterol"]],
  ["Electrolytes", ["sodium","potassium","chloride","calcium","phosphate","magnesium"]],
  ["Urine Analysis", ["urine_protein","urine_glucose","urine_ketones","urine_specific_gravity","urine_ph"]],
  ["Tumor Markers", ["afp","cea","ca19_9","ca15_3","psa","ca125"]],
];

const SEV: Record<string, number> = { critical: 0, high: 1, moderate: 2, low: 3 };

function getName(k: string) { return DN[k] || k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()); }

function sevColor(s: string) {
  if (s === "critical") return "#DC2626";
  if (s === "high") return "#EA580C";
  if (s === "moderate") return "#D97706";
  return "#2563EB";
}

function statusDot(s: string) {
  if (s === "critical_low" || s === "critical_high") return "#DC2626";
  if (s === "high") return "#EA580C";
  if (s === "low") return "#2563EB";
  return "#D97706";
}

function statusLabel(s: string) {
  if (s === "critical_low" || s === "critical_high") return "Critical";
  if (s === "high") return "High";
  if (s === "low") return "Low";
  return "Normal";
}

function refStr(r: InterpretationResult) {
  if (!r.reference_range) return null;
  const { low, high } = r.reference_range;
  if (low !== null && high !== null) return `${low}–${high} ${r.unit}`;
  if (low !== null) return `≥${low} ${r.unit}`;
  if (high !== null) return `≤${high} ${r.unit}`;
  return null;
}

/* Cluster patterns by category */
function clusterPatterns(patterns: MatchedPattern[]) {
  const clusters: { category: string; patterns: MatchedPattern[] }[] = [];
  const catMap = new Map<string, MatchedPattern[]>();
  for (const p of patterns) {
    const cat = p.category || "Other";
    if (!catMap.has(cat)) catMap.set(cat, []);
    catMap.get(cat)!.push(p);
  }
  Array.from(catMap.entries()).forEach(([cat, pats]) => {
    pats.sort((a, b) => (SEV[a.severity] ?? 9) - (SEV[b.severity] ?? 9));
    clusters.push({ category: cat, patterns: pats });
  });
  clusters.sort((a, b) => (SEV[a.patterns[0]?.severity] ?? 9) - (SEV[b.patterns[0]?.severity] ?? 9));
  return clusters;
}

/* Auto-generate summary narrative from patterns */
function generateNarrative(data: AnalysisResult) {
  if (data.rag_narrative?.narrative) return data.rag_narrative.narrative;
  const patterns = data.tier2.patterns;
  if (patterns.length === 0) return "All test results are within normal limits. No concerning clinical patterns detected.";
  const critical = patterns.filter(p => p.severity === "critical" || p.severity === "high");
  const top = critical.slice(0, 3).map(p => p.name).join(", ");
  const interps = critical.slice(0, 2).map(p => p.interpretation).join(" ");
  return `${top}. ${interps}`;
}

function generatePriorities(data: AnalysisResult) {
  const refs = data.tier3.referrals.slice(0, 3);
  const tests = data.tier3.further_tests.flatMap(g => g.tests).slice(0, 3);
  const items: string[] = [];
  refs.forEach(r => items.push(`${r.urgency === "urgent" ? "URGENT" : r.urgency === "soon" ? "SOON" : "ROUTINE"}: ${r.specialist} — ${r.reason}`));
  if (items.length < 3) tests.forEach(t => { if (items.length < 3) items.push(t.test_name); });
  return items;
}

/* ═══════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════ */

export default function AnalysisResultPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("summary");
  const [expandedPanels, setExpandedPanels] = useState<string[]>(["critical"]);
  const [expandedPatterns, setExpandedPatterns] = useState<string[]>([]);
  const [showAllResults, setShowAllResults] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    async function load() {
      setLoading(true); setError(null);
      let localData: AnalysisResult | null = null;
      try { const raw = localStorage.getItem(`analysis_${id}`); if (raw) { localData = JSON.parse(raw); if (!cancelled) setData(localData); } } catch {}
      try {
        const apiData = await getAnalysis(id);
        if (!cancelled) { if (localData?.patient?.name && !apiData.patient?.name) apiData.patient.name = localData.patient.name; setData(apiData); try { localStorage.setItem(`analysis_${id}`, JSON.stringify(apiData)); } catch {} }
      } catch (err: unknown) { if (!localData && !cancelled) setError(err instanceof Error ? err.message : "Failed to load."); }
      finally { if (!cancelled) setLoading(false); }
    }
    load();
    return () => { cancelled = true; };
  }, [id]);

  // Auto-expand most severe pattern per cluster
  useEffect(() => {
    if (!data) return;
    const clusters = clusterPatterns(data.tier2.patterns);
    setExpandedPatterns(clusters.map(c => c.patterns[0]?.id).filter(Boolean));
  }, [data]);

  const filteredTier1 = useMemo(() => {
    if (!data) return {};
    const f: Record<string, InterpretationResult> = {};
    for (const [k, v] of Object.entries(data.tier1)) { if (v.status !== "unknown") f[k] = v; }
    return f;
  }, [data]);

  const stats = useMemo(() => {
    const e = Object.values(filteredTier1);
    return {
      total: e.length,
      abnormal: e.filter(r => r.status !== "normal").length,
      critical: e.filter(r => r.status === "critical_low" || r.status === "critical_high").length,
      patterns: data?.tier2.patterns.length ?? 0,
    };
  }, [filteredTier1, data]);

  const criticalResults = useMemo(() => Object.entries(filteredTier1).filter(([, v]) => v.status === "critical_low" || v.status === "critical_high"), [filteredTier1]);

  const abnormalGrouped = useMemo(() => {
    const groups: { panel: string; tests: [string, InterpretationResult][] }[] = [];
    const assigned = new Set<string>();
    for (const [pn, tids] of PANEL_ORDER) {
      const tests: [string, InterpretationResult][] = [];
      for (const tid of tids) {
        if (filteredTier1[tid] && filteredTier1[tid].status !== "normal" && filteredTier1[tid].status !== "critical_low" && filteredTier1[tid].status !== "critical_high") {
          tests.push([tid, filteredTier1[tid]]); assigned.add(tid);
        }
      }
      if (tests.length > 0) groups.push({ panel: pn, tests });
    }
    const other: [string, InterpretationResult][] = [];
    for (const [tid, r] of Object.entries(filteredTier1)) { if (!assigned.has(tid) && r.status !== "normal" && r.status !== "critical_low" && r.status !== "critical_high") other.push([tid, r]); }
    if (other.length > 0) groups.push({ panel: "Other", tests: other });
    return groups;
  }, [filteredTier1]);

  const allGrouped = useMemo(() => {
    const groups: { panel: string; tests: [string, InterpretationResult][] }[] = [];
    const assigned = new Set<string>();
    for (const [pn, tids] of PANEL_ORDER) {
      const tests: [string, InterpretationResult][] = [];
      for (const tid of tids) { if (filteredTier1[tid]) { tests.push([tid, filteredTier1[tid]]); assigned.add(tid); } }
      if (tests.length > 0) groups.push({ panel: pn, tests });
    }
    const other: [string, InterpretationResult][] = [];
    for (const tid of Object.keys(filteredTier1)) { if (!assigned.has(tid)) other.push([tid, filteredTier1[tid]]); }
    if (other.length > 0) groups.push({ panel: "Other", tests: other });
    return groups;
  }, [filteredTier1]);

  const clusters = useMemo(() => data ? clusterPatterns(data.tier2.patterns) : [], [data]);
  const visibleStaging = useMemo(() => data ? Object.entries(data.tier2.staging ?? {}).filter(([, s]) => s.show !== false) : [], [data]);

  const categorizedTests = useMemo(() => {
    if (!data) return { blood: [] as { name: string; rationale: string }[], urine: [] as { name: string; rationale: string }[], imaging: [] as { name: string; rationale: string }[] };
    const blood = new Map<string, string>(), urine = new Map<string, string>(), imaging = new Map<string, string>();
    for (const g of data.tier3.further_tests) for (const t of g.tests) {
      const n = t.test_name.toLowerCase();
      if (n.includes("urine") || n.includes("uacr")) urine.set(t.test_name, t.rationale);
      else if (n.includes("ultrasound") || n.includes("imaging") || n.includes("x-ray") || n.includes("ct ") || n.includes("mri") || n.includes("scan") || n.includes("echo") || n.includes("fundoscopy") || n.includes("dexa") || n.includes("ecg") || n.includes("fibroscan")) imaging.set(t.test_name, t.rationale);
      else blood.set(t.test_name, t.rationale);
    }
    const toArr = (m: Map<string, string>) => Array.from(m, ([name, rationale]) => ({ name, rationale }));
    return { blood: toArr(blood), urine: toArr(urine), imaging: toArr(imaging) };
  }, [data]);

  // Summary: group related abnormals into condensed alerts
  const summaryAlerts = useMemo(() => {
    if (!data) return [];
    const alerts: { dot: string; title: string; value: string; note: string; panel: string }[] = [];
    // Critical first
    for (const [key, r] of criticalResults) {
      alerts.push({ dot: "#DC2626", title: getName(key), value: `${r.value} ${r.unit}`, note: r.plain_text, panel: "critical" });
    }
    // Then group abnormals by panel
    for (const { panel, tests } of abnormalGrouped) {
      if (tests.length >= 3) {
        const names = tests.map(([k, r]) => `${getName(k)} ${r.value}`).join(" · ");
        const note = tests[0][1].plain_text;
        alerts.push({ dot: statusDot(tests[0][1].status), title: panel, value: names, note, panel });
      } else {
        for (const [key, r] of tests) {
          alerts.push({ dot: statusDot(r.status), title: getName(key), value: `${r.value} ${r.unit}`, note: r.plain_text, panel });
        }
      }
    }
    return alerts.slice(0, 12);
  }, [data, criticalResults, abnormalGrouped]);

  const handleDownload = useCallback(async () => {
    if (!id) return; setDownloading(true);
    try { const blob = await downloadReport(id); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `vitalytics-report-${id}.pdf`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); }
    catch { alert("Failed to download report."); } finally { setDownloading(false); }
  }, [id]);

  const togglePanel = (panel: string) => {
    setExpandedPanels(prev => prev.includes(panel) ? prev.filter(p => p !== panel) : [...prev, panel]);
  };

  const togglePattern = (pid: string) => {
    setExpandedPatterns(prev => prev.includes(pid) ? prev.filter(p => p !== pid) : [...prev, pid]);
  };

  /* ── Loading / Error ── */
  if (loading) return (
    <div style={{ maxWidth: 920, margin: "0 auto" }}>
      <div style={{ height: 120, borderRadius: 16, background: "linear-gradient(135deg, #6366F1, #8B5CF6)", marginBottom: 16 }} />
      {[0, 1, 2].map(i => <div key={i} style={{ height: 80, background: "#FFF", border: "1px solid #E2E8F0", borderRadius: 14, marginBottom: 12 }} />)}
    </div>
  );

  if (error && !data) return (
    <div style={{ maxWidth: 920, margin: "0 auto", textAlign: "center", paddingTop: 80 }}>
      <p style={{ fontSize: 16, fontWeight: 700, color: "#DC2626", marginBottom: 8 }}>Unable to load analysis</p>
      <p style={{ fontSize: 13, color: "#64748B" }}>{error}</p>
      <button onClick={() => window.location.reload()} className="btn-primary" style={{ marginTop: 16 }}>Retry</button>
    </div>
  );

  if (!data) return null;
  const patientName = data.patient?.name;
  const narrative = generateNarrative(data);
  const priorities = generatePriorities(data);
  const TABS = [
    { key: "summary", label: "Summary" },
    { key: "findings", label: "Findings" },
    { key: "patterns", label: "Patterns" },
    { key: "actions", label: "Actions" },
  ];

  return (
    <div style={{ maxWidth: 920, margin: "0 auto" }}>
      {/* ═══ HERO ═══ */}
      <div className="animate-up" style={{ borderRadius: 16, padding: "24px 28px", marginBottom: 16, background: "linear-gradient(135deg, #6366F1 0%, #8B5CF6 40%, #A78BFA 100%)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: "#FFFFFF", letterSpacing: "-0.02em" }}>
              {patientName || "Analysis Results"}
            </h1>
            <p style={{ fontSize: 13, color: "rgba(255,255,255,0.7)", marginTop: 4 }}>
              {data.patient.age} years, {data.patient.sex === "male" ? "Male" : "Female"} · {new Date(data.timestamp).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
            </p>
          </div>
          <button onClick={handleDownload} disabled={downloading} style={{ background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)", borderRadius: 10, padding: "8px 16px", color: "white", fontSize: 12, fontWeight: 600, cursor: "pointer", backdropFilter: "blur(8px)", transition: "all 0.2s" }}>
            {downloading ? "..." : "Download PDF"}
          </button>
        </div>
        {/* Stat cards */}
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          {[
            { label: "Abnormal", value: stats.abnormal, bg: "rgba(251,191,36,0.2)", color: "#FCD34D", tab: "findings" },
            { label: "Critical", value: stats.critical, bg: "rgba(248,113,113,0.2)", color: "#FCA5A5", tab: "findings" },
            { label: "Patterns", value: stats.patterns, bg: "rgba(196,181,253,0.2)", color: "#C4B5FD", tab: "patterns" },
            { label: "Tests", value: stats.total, bg: "rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.9)", tab: "findings" },
          ].map(s => (
            <button key={s.label} onClick={() => setActiveTab(s.tab)} style={{ flex: 1, background: s.bg, border: "1px solid rgba(255,255,255,0.1)", borderRadius: 10, padding: "10px 8px", textAlign: "center", cursor: "pointer", backdropFilter: "blur(8px)", transition: "all 0.2s" }}>
              <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</p>
              <p style={{ fontSize: 10, color: "rgba(255,255,255,0.6)", fontWeight: 500, marginTop: 2 }}>{s.label}</p>
            </button>
          ))}
        </div>
      </div>

      {/* ═══ TAB BAR ═══ */}
      <div className="animate-up" style={{ animationDelay: "0.06s", display: "flex", gap: 0, marginBottom: 20, background: "#FFFFFF", borderRadius: 12, border: "1px solid #E2E8F0", padding: 4, position: "sticky", top: 0, zIndex: 10 }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)} style={{
            flex: 1, padding: "10px 0", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer", border: "none",
            background: activeTab === t.key ? "#F1F5F9" : "transparent",
            color: activeTab === t.key ? "#6366F1" : "#94A3B8",
            transition: "all 0.2s",
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ═══ TAB CONTENT ═══ */}
      <div className="animate-fadeIn" key={activeTab} style={{ minHeight: 400 }}>

        {/* ──── SUMMARY TAB ──── */}
        {activeTab === "summary" && (
          <div>
            {/* Staging */}
            {visibleStaging.length > 0 && (
              <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
                {visibleStaging.map(([key, staging]) => {
                  const sc = staging.color === "amber" || staging.color === "yellow" ? "#D97706" : staging.color === "orange" ? "#EA580C" : staging.color === "red" || staging.color === "darkred" ? "#DC2626" : "#059669";
                  return (
                    <div key={key} className="card-sm" style={{ flex: "1 1 200px", borderLeft: `3px solid ${sc}`, padding: "12px 16px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                        <span style={{ fontSize: 11, fontWeight: 600, color: "#64748B" }}>{getName(key)}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, color: sc, background: `${sc}15`, padding: "2px 8px", borderRadius: 6 }}>{staging.stage}</span>
                      </div>
                      <p style={{ fontSize: 13, fontWeight: 600, color: "#0F172A" }}>{staging.label}</p>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Two-column layout */}
            <div style={{ display: "grid", gridTemplateColumns: "58% 42%", gap: 16, marginBottom: 16 }}>
              {/* LEFT: Key Alerts */}
              <div className="card" style={{ padding: 20 }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>Key Alerts</p>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {summaryAlerts.map((alert, i) => (
                    <div key={i} onClick={() => { setActiveTab("findings"); if (alert.panel !== "critical") togglePanel(alert.panel); }} style={{ cursor: "pointer", display: "flex", gap: 10, padding: "8px 10px", borderRadius: 10, transition: "background 0.15s" }} onMouseEnter={e => e.currentTarget.style.background = "#F8FAFC"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: alert.dot, marginTop: 5, flexShrink: 0 }} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
                          <span style={{ fontSize: 13, fontWeight: 600, color: "#0F172A" }}>{alert.title}:</span>
                          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13, fontWeight: 700, color: alert.dot }}>{alert.value}</span>
                        </div>
                        <p style={{ fontSize: 12, color: "#94A3B8", marginTop: 2, lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{alert.note}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* RIGHT: Clinical Impression */}
              <div className="card" style={{ padding: 20, borderLeft: "3px solid #6366F1" }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Clinical Impression</p>
                <p style={{ fontSize: 13, color: "#334155", lineHeight: 1.65, marginBottom: 16 }}>{narrative}</p>
                {priorities.length > 0 && (
                  <>
                    <p style={{ fontSize: 11, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Priorities</p>
                    {priorities.map((p, i) => (
                      <p key={i} style={{ fontSize: 12, color: "#475569", marginBottom: 4 }}>{i + 1}. {p}</p>
                    ))}
                  </>
                )}
              </div>
            </div>

            {/* Pattern chips row */}
            {data.tier2.patterns.length > 0 && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.tier2.patterns.map(p => (
                  <button key={p.id} onClick={() => { setActiveTab("patterns"); if (!expandedPatterns.includes(p.id)) togglePattern(p.id); }} style={{ fontSize: 11, fontWeight: 600, color: sevColor(p.severity), background: `${sevColor(p.severity)}10`, border: `1px solid ${sevColor(p.severity)}30`, padding: "4px 12px", borderRadius: 8, cursor: "pointer", transition: "all 0.15s" }}>
                    {p.name} · {p.severity}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ──── FINDINGS TAB ──── */}
        {activeTab === "findings" && (
          <div>
            {/* Critical — always open */}
            {criticalResults.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#DC2626", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Critical ({criticalResults.length})</p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {criticalResults.map(([key, r]) => (
                    <div key={key} className="card-sm" style={{ borderLeft: "4px solid #DC2626", padding: 16 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: "#64748B" }}>{getName(key)}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, background: "#FEF2F2", color: "#991B1B", padding: "2px 8px", borderRadius: 6 }}>Critical</span>
                      </div>
                      <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 28, fontWeight: 700, color: "#DC2626", lineHeight: 1.1 }}>
                        {r.value} <span style={{ fontSize: 12, fontWeight: 500, color: "#94A3B8" }}>{r.unit}</span>
                      </p>
                      {refStr(r) && <p style={{ fontSize: 11, color: "#94A3B8", marginTop: 4 }}>Ref: {refStr(r)}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Accordion panels */}
            {abnormalGrouped.map(({ panel, tests }) => {
              const ps = PS[panel] || PS.Other;
              const isOpen = expandedPanels.includes(panel);
              return (
                <div key={panel} style={{ marginBottom: 8 }}>
                  <button onClick={() => togglePanel(panel)} style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: isOpen ? "12px 12px 0 0" : 12, cursor: "pointer", transition: "all 0.2s" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: ps.accent }} />
                      <span style={{ fontSize: 13, fontWeight: 600, color: "#0F172A" }}>{panel}</span>
                      <span style={{ fontSize: 11, fontWeight: 600, color: ps.accent, background: ps.color, padding: "2px 8px", borderRadius: 6 }}>{tests.length} abnormal</span>
                    </div>
                    <span style={{ fontSize: 14, color: "#94A3B8", transform: isOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>▼</span>
                  </button>
                  {isOpen && (
                    <div style={{ border: "1px solid #E2E8F0", borderTop: "none", borderRadius: "0 0 12px 12px", padding: 12, background: "#FFFFFF" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        {tests.map(([key, r]) => (
                          <div key={key} style={{ borderLeft: `3px solid ${ps.accent}`, padding: "10px 14px", borderRadius: 10, background: ps.color }}>
                            <span style={{ fontSize: 11, fontWeight: 600, color: "#64748B" }}>{getName(key)}</span>
                            <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 22, fontWeight: 700, color: ps.accent, marginTop: 2 }}>
                              {r.value} <span style={{ fontSize: 11, fontWeight: 500, color: "#94A3B8" }}>{r.unit}</span>
                            </p>
                            {refStr(r) && <p style={{ fontSize: 10, color: "#94A3B8", marginTop: 2 }}>Ref: {refStr(r)}</p>}
                            <span style={{ fontSize: 10, fontWeight: 600, color: statusDot(r.status), background: `${statusDot(r.status)}15`, padding: "1px 6px", borderRadius: 4, marginTop: 4, display: "inline-block" }}>{statusLabel(r.status)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* View all results */}
            <button onClick={() => setShowAllResults(!showAllResults)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600, color: "#6366F1", padding: "12px 0" }}>
              {showAllResults ? "Hide all results ↑" : `View all ${stats.total} results →`}
            </button>
            {showAllResults && (
              <div style={{ borderRadius: 12, border: "1px solid #E2E8F0", overflow: "hidden", marginTop: 4 }}>
                {allGrouped.map(({ panel, tests }) => (
                  <div key={panel}>
                    <div style={{ padding: "8px 16px", background: "#F1F5F9", fontWeight: 700, fontSize: 11, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.05em" }}>{panel}</div>
                    {tests.map(([key, r], i) => {
                      const badge = r.status === "normal" ? { bg: "#ECFDF5", color: "#059669" } : r.status === "critical_low" || r.status === "critical_high" ? { bg: "#FEF2F2", color: "#DC2626" } : { bg: "#FFFBEB", color: "#D97706" };
                      return (
                        <div key={key} style={{ display: "flex", alignItems: "center", padding: "8px 16px", background: i % 2 === 0 ? "#FFFFFF" : "#F8FAFC", borderBottom: "1px solid #F1F5F9", fontSize: 12 }}>
                          <span style={{ flex: 2, fontWeight: 500, color: "#0F172A" }}>{getName(key)}</span>
                          <span style={{ flex: 1, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, color: "#0F172A" }}>{r.value}</span>
                          <span style={{ flex: 1, color: "#94A3B8" }}>{r.unit}</span>
                          <span style={{ flex: 1, color: "#94A3B8" }}>{refStr(r) || "–"}</span>
                          <span style={{ fontWeight: 700, background: badge.bg, color: badge.color, padding: "2px 8px", borderRadius: 6, fontSize: 10 }}>{statusLabel(r.status)}</span>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ──── PATTERNS TAB ──── */}
        {activeTab === "patterns" && (
          <div>
            {clusters.length === 0 ? (
              <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
                <p style={{ fontSize: 15, fontWeight: 700, color: "#059669" }}>No concerning patterns detected</p>
              </div>
            ) : (
              clusters.map(cluster => (
                <div key={cluster.category} style={{ marginBottom: 20 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>{cluster.category}</p>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {cluster.patterns.map(p => {
                      const isOpen = expandedPatterns.includes(p.id);
                      const sc = sevColor(p.severity);
                      return (
                        <div key={p.id}>
                          <button onClick={() => togglePattern(p.id)} style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: isOpen ? "12px 12px 0 0" : 12, cursor: "pointer", transition: "all 0.15s" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <span style={{ fontSize: 13, fontWeight: 600, color: "#0F172A" }}>{p.name}</span>
                            </div>
                            <span style={{ fontSize: 10, fontWeight: 700, color: sc, background: `${sc}12`, padding: "3px 10px", borderRadius: 6 }}>{p.severity}</span>
                          </button>
                          {isOpen && (
                            <div style={{ border: "1px solid #E2E8F0", borderTop: "none", borderRadius: "0 0 12px 12px", padding: "14px 18px", background: "#FFFFFF", borderLeft: `3px solid ${sc}` }}>
                              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
                                {p.matched_criteria.split(",").map((c, i) => (
                                  <span key={i} style={{ fontSize: 10, fontWeight: 600, color: "#6366F1", background: "#EEF2FF", padding: "2px 8px", borderRadius: 6 }}>{c.trim()}</span>
                                ))}
                              </div>
                              <p style={{ fontSize: 13, color: "#475569", lineHeight: 1.6 }}>{p.interpretation}</p>
                              {p.harrison_ref && <p style={{ fontSize: 11, fontStyle: "italic", color: "#94A3B8", marginTop: 8 }}>{p.harrison_ref}</p>}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* ──── ACTIONS TAB ──── */}
        {activeTab === "actions" && (
          <div>
            {/* Referrals — horizontal scroll */}
            {data.tier3.referrals.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Specialist Referrals</p>
                <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 4 }}>
                  {data.tier3.referrals.map((ref, i) => {
                    const uc = ref.urgency === "urgent" ? "#DC2626" : ref.urgency === "soon" ? "#D97706" : "#059669";
                    return (
                      <div key={i} style={{ minWidth: 160, flex: "0 0 auto", background: "#FFFFFF", border: "1px solid #E2E8F0", borderTop: `3px solid ${uc}`, borderRadius: 12, padding: "14px 16px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                          <span style={{ fontSize: 13, fontWeight: 700, color: "#0F172A" }}>{ref.specialist}</span>
                        </div>
                        <span style={{ fontSize: 10, fontWeight: 600, color: uc, background: `${uc}12`, padding: "2px 8px", borderRadius: 6 }}>{ref.urgency}</span>
                        <p style={{ fontSize: 11, color: "#64748B", marginTop: 6 }}>{ref.reason}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Tests — 3-column */}
            {(categorizedTests.blood.length > 0 || categorizedTests.urine.length > 0 || categorizedTests.imaging.length > 0) && (
              <div style={{ marginBottom: 20 }}>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Recommended Tests</p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                  {categorizedTests.blood.length > 0 && (
                    <div className="card-sm" style={{ borderLeft: "3px solid #EF4444", padding: 16 }}>
                      <p style={{ fontSize: 12, fontWeight: 700, color: "#EF4444", marginBottom: 10 }}>Blood Tests</p>
                      {categorizedTests.blood.map(t => <p key={t.name} style={{ fontSize: 12, color: "#475569", marginBottom: 5 }}>○ {t.name}</p>)}
                    </div>
                  )}
                  {categorizedTests.urine.length > 0 && (
                    <div className="card-sm" style={{ borderLeft: "3px solid #8B5CF6", padding: 16 }}>
                      <p style={{ fontSize: 12, fontWeight: 700, color: "#8B5CF6", marginBottom: 10 }}>Urine Tests</p>
                      {categorizedTests.urine.map(t => <p key={t.name} style={{ fontSize: 12, color: "#475569", marginBottom: 5 }}>○ {t.name}</p>)}
                    </div>
                  )}
                  {categorizedTests.imaging.length > 0 && (
                    <div className="card-sm" style={{ borderLeft: "3px solid #3B82F6", padding: 16 }}>
                      <p style={{ fontSize: 12, fontWeight: 700, color: "#3B82F6", marginBottom: 10 }}>Imaging & Other</p>
                      {categorizedTests.imaging.map(t => <p key={t.name} style={{ fontSize: 12, color: "#475569", marginBottom: 5 }}>○ {t.name}</p>)}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Lifestyle — 3-column */}
            {data.tier3.lifestyle && (
              <div>
                <p style={{ fontSize: 12, fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10 }}>Lifestyle Plan</p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                  <div className="card-sm" style={{ padding: 16 }}>
                    <p style={{ fontSize: 12, fontWeight: 700, color: "#10B981", marginBottom: 8 }}>Diet</p>
                    {data.tier3.lifestyle.diet.map((d, i) => <p key={i} style={{ fontSize: 12, color: "#475569", marginBottom: 4, lineHeight: 1.4 }}>• {d}</p>)}
                  </div>
                  <div className="card-sm" style={{ padding: 16 }}>
                    <p style={{ fontSize: 12, fontWeight: 700, color: "#D97706", marginBottom: 8 }}>Exercise</p>
                    {data.tier3.lifestyle.exercise.map((e, i) => <p key={i} style={{ fontSize: 12, color: "#475569", marginBottom: 4, lineHeight: 1.4 }}>• <strong>{e.type}</strong> — {e.duration}, {e.frequency}</p>)}
                  </div>
                  <div className="card-sm" style={{ padding: 16 }}>
                    <p style={{ fontSize: 12, fontWeight: 700, color: "#6366F1", marginBottom: 8 }}>Lifestyle</p>
                    {[...data.tier3.lifestyle.sleep, ...data.tier3.lifestyle.stress, ...(data.tier3.lifestyle.weight || [])].map((s, i) => <p key={i} style={{ fontSize: 12, color: "#475569", marginBottom: 4, lineHeight: 1.4 }}>• {s}</p>)}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <div style={{ padding: "16px 20px", borderRadius: 12, background: "#F1F5F9", border: "1px solid #E2E8F0", marginTop: 24, marginBottom: 32 }}>
        <p style={{ fontSize: 11, fontWeight: 600, color: "#94A3B8" }}>Clinical Decision Support Disclaimer</p>
        <p style={{ fontSize: 11, color: "#94A3B8", lineHeight: 1.5, marginTop: 2 }}>
          This analysis is for informational purposes only and does not constitute medical advice. All interpretations must be reviewed by a qualified healthcare professional.
        </p>
      </div>
    </div>
  );
}

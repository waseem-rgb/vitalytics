"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { runAnalysis, uploadLabReport } from "@/lib/api";
import type { UploadResponse } from "@/lib/types";

const PANELS = [
  { id: "cbc", label: "Blood Count", color: "#FEF2F2", accent: "#EF4444" },
  { id: "diabetes", label: "Diabetes", color: "#FFFBEB", accent: "#D97706" },
  { id: "lipid", label: "Lipid Profile", color: "#EFF6FF", accent: "#3B82F6" },
  { id: "lft", label: "Liver", color: "#ECFDF5", accent: "#10B981" },
  { id: "rft", label: "Kidney", color: "#F5F3FF", accent: "#8B5CF6" },
  { id: "thyroid", label: "Thyroid", color: "#FDF2F8", accent: "#EC4899" },
  { id: "vitamins", label: "Vitamins", color: "#FFFBEB", accent: "#F59E0B" },
  { id: "iron", label: "Iron Studies", color: "#FEF2F2", accent: "#EF4444" },
  { id: "electrolytes", label: "Electrolytes", color: "#ECFEFF", accent: "#06B6D4" },
  { id: "urine", label: "Urine", color: "#F5F3FF", accent: "#8B5CF6" },
  { id: "tumor", label: "Tumor Markers", color: "#FAF5FF", accent: "#9333EA" },
] as const;

type PanelId = (typeof PANELS)[number]["id"];

const TESTS: Record<PanelId, { id: string; name: string; unit?: string; placeholder: string }[]> = {
  cbc: [
    { id: "hemoglobin", name: "Hemoglobin", unit: "g/dL", placeholder: "13.5–17.5" },
    { id: "hematocrit", name: "Hematocrit", unit: "%", placeholder: "40–50" },
    { id: "rbc", name: "RBC", unit: "M/µL", placeholder: "4.5–5.5" },
    { id: "wbc", name: "WBC", unit: "×10³/µL", placeholder: "4.5–11" },
    { id: "platelets", name: "Platelets", unit: "×10³/µL", placeholder: "150–450" },
    { id: "mcv", name: "MCV", unit: "fL", placeholder: "80–100" },
    { id: "mch", name: "MCH", unit: "pg", placeholder: "27–33" },
    { id: "mchc", name: "MCHC", unit: "g/dL", placeholder: "32–36" },
    { id: "rdw", name: "RDW", unit: "%", placeholder: "11.5–14.5" },
    { id: "aec", name: "AEC", unit: "cells/µL", placeholder: "40–400" },
  ],
  diabetes: [
    { id: "fasting_glucose", name: "Fasting Glucose", unit: "mg/dL", placeholder: "≤100" },
    { id: "hba1c", name: "HbA1c", unit: "%", placeholder: "<6.0" },
    { id: "pp_glucose", name: "PP Glucose", unit: "mg/dL", placeholder: "<140" },
    { id: "fasting_insulin", name: "Fasting Insulin", unit: "µIU/mL", placeholder: "2.6–24.9" },
  ],
  lipid: [
    { id: "total_cholesterol", name: "Total Cholesterol", unit: "mg/dL", placeholder: "<200" },
    { id: "triglycerides", name: "Triglycerides", unit: "mg/dL", placeholder: "<150" },
    { id: "hdl", name: "HDL", unit: "mg/dL", placeholder: "≥40" },
    { id: "ldl", name: "LDL", unit: "mg/dL", placeholder: "≤100" },
    { id: "vldl", name: "VLDL", unit: "mg/dL", placeholder: "<30" },
    { id: "non_hdl_cholesterol", name: "Non-HDL Chol", unit: "mg/dL", placeholder: "<130" },
  ],
  lft: [
    { id: "alt", name: "ALT (SGPT)", unit: "U/L", placeholder: "7–56" },
    { id: "ast", name: "AST (SGOT)", unit: "U/L", placeholder: "10–40" },
    { id: "alp", name: "ALP", unit: "U/L", placeholder: "44–147" },
    { id: "ggt", name: "GGT", unit: "U/L", placeholder: "9–48" },
    { id: "total_bilirubin", name: "Bilirubin", unit: "mg/dL", placeholder: "0.1–1.2" },
    { id: "albumin", name: "Albumin", unit: "g/dL", placeholder: "3.5–5.5" },
    { id: "total_protein", name: "Total Protein", unit: "g/dL", placeholder: "6.0–8.0" },
    { id: "globulin", name: "Globulin", unit: "g/dL", placeholder: "2.0–3.5" },
  ],
  rft: [
    { id: "creatinine", name: "Creatinine", unit: "mg/dL", placeholder: "0.7–1.3" },
    { id: "bun", name: "BUN", unit: "mg/dL", placeholder: "7–20" },
    { id: "urea", name: "Urea", unit: "mg/dL", placeholder: "15–45" },
    { id: "egfr", name: "eGFR", unit: "mL/min", placeholder: ">90" },
    { id: "uric_acid", name: "Uric Acid", unit: "mg/dL", placeholder: "3.5–7.2" },
  ],
  thyroid: [
    { id: "tsh", name: "TSH", unit: "mIU/L", placeholder: "0.4–4.0" },
    { id: "free_t4", name: "Free T4", unit: "ng/dL", placeholder: "0.8–1.8" },
    { id: "free_t3", name: "Free T3", unit: "pg/mL", placeholder: "2.3–4.2" },
    { id: "total_t3", name: "Total T3", unit: "ng/mL", placeholder: "0.76–2.21" },
    { id: "total_t4", name: "Total T4", unit: "µg/dL", placeholder: "4.5–13.0" },
    { id: "anti_tpo", name: "Anti-TPO Ab", unit: "IU/mL", placeholder: "<35" },
  ],
  vitamins: [
    { id: "vitamin_b12", name: "Vitamin B12", unit: "pg/mL", placeholder: "200–900" },
    { id: "folate", name: "Folate", unit: "ng/mL", placeholder: "2.7–17" },
    { id: "vitamin_d", name: "Vitamin D", unit: "ng/mL", placeholder: "30–100" },
  ],
  iron: [
    { id: "serum_iron", name: "Serum Iron", unit: "µg/dL", placeholder: "60–170" },
    { id: "ferritin", name: "Ferritin", unit: "ng/mL", placeholder: "12–300" },
    { id: "tibc", name: "TIBC", unit: "µg/dL", placeholder: "250–370" },
    { id: "transferrin_saturation", name: "Transferrin Sat", unit: "%", placeholder: "20–50" },
  ],
  electrolytes: [
    { id: "sodium", name: "Sodium", unit: "mEq/L", placeholder: "136–145" },
    { id: "potassium", name: "Potassium", unit: "mEq/L", placeholder: "3.5–5.0" },
    { id: "chloride", name: "Chloride", unit: "mEq/L", placeholder: "98–106" },
    { id: "calcium", name: "Calcium", unit: "mg/dL", placeholder: "8.5–10.5" },
    { id: "phosphate", name: "Phosphate", unit: "mg/dL", placeholder: "2.5–4.5" },
    { id: "magnesium", name: "Magnesium", unit: "mg/dL", placeholder: "1.7–2.2" },
  ],
  urine: [
    { id: "urine_protein", name: "Urine Protein", placeholder: "0 = negative" },
    { id: "urine_glucose", name: "Urine Glucose", placeholder: "0 = negative" },
    { id: "urine_ketones", name: "Urine Ketones", placeholder: "0 = negative" },
    { id: "urine_specific_gravity", name: "Specific Gravity", placeholder: "1.005–1.030" },
    { id: "urine_ph", name: "Urine pH", placeholder: "5.0–8.0" },
  ],
  tumor: [
    { id: "psa", name: "PSA", unit: "ng/mL", placeholder: "0–4" },
    { id: "cea", name: "CEA", unit: "ng/mL", placeholder: "≤5" },
    { id: "afp", name: "AFP", unit: "IU/mL", placeholder: "≤6.5" },
    { id: "ca125", name: "CA-125", unit: "U/mL", placeholder: "<35" },
    { id: "ca19_9", name: "CA 19-9", unit: "U/mL", placeholder: "<37" },
  ],
};

const PANEL_LABEL_MAP: Record<string, { label: string; color: string; accent: string }> = {};
for (const p of PANELS) {
  for (const t of TESTS[p.id]) {
    PANEL_LABEL_MAP[t.id] = { label: p.label, color: p.color, accent: p.accent };
  }
}

function getParsedPanelChips(parsed: Record<string, number>) {
  const map = new Map<string, { label: string; color: string; accent: string; count: number }>();
  for (const key of Object.keys(parsed)) {
    const info = PANEL_LABEL_MAP[key];
    if (info) {
      const existing = map.get(info.label);
      if (existing) existing.count++;
      else map.set(info.label, { ...info, count: 1 });
    }
  }
  return Array.from(map.values());
}

export default function NewAnalysisPage() {
  const router = useRouter();
  const [patientName, setPatientName] = useState("");
  const [age, setAge] = useState("");
  const [sex, setSex] = useState<"male" | "female">("male");
  const [labResults, setLabResults] = useState<Record<string, string>>({});
  const [activePanel, setActivePanel] = useState<PanelId>("cbc");
  const [editOpen, setEditOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const totalFilled = Object.values(labResults).filter((v) => v && v.trim() !== "").length;
  const panelHasValues = (pid: PanelId) => TESTS[pid].some((t) => labResults[t.id]?.trim());
  const curPanel = PANELS.find((p) => p.id === activePanel)!;

  const handleFileUpload = useCallback(async (file: File) => {
    const validTypes = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!validTypes.includes(file.type)) { setError("Unsupported file type."); return; }
    setIsUploading(true); setError(null); setUploadResult(null);
    try {
      const result = await uploadLabReport(file);
      setUploadResult(result);
      const merged: Record<string, string> = {};
      for (const [key, val] of Object.entries(result.parsed_results)) merged[key] = String(val);
      setLabResults(merged);
      if (result.patient) {
        if (result.patient.name) setPatientName(result.patient.name);
        if (result.patient.age) { const m = String(result.patient.age).match(/\d+/); if (m) setAge(m[0]); }
        if (result.patient.sex) { const s = String(result.patient.sex).toLowerCase(); if (s === "male" || s === "m") setSex("male"); else if (s === "female" || s === "f") setSex("female"); }
      }
    } catch (err: any) { setError(err?.response?.data?.detail || err?.message || "Failed to parse."); }
    finally { setIsUploading(false); }
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragOver(false); const f = e.dataTransfer.files?.[0]; if (f) handleFileUpload(f); }, [handleFileUpload]);
  const resetUpload = () => { setUploadResult(null); setLabResults({}); setPatientName(""); setAge(""); setEditOpen(false); };

  const handleRunAnalysis = async () => {
    setError(null);
    const parsedAge = parseInt(age, 10);
    if (!age || isNaN(parsedAge) || parsedAge < 0 || parsedAge > 150) { setError("Please enter a valid age (0-150)."); return; }
    const currentResults: Record<string, number> = {};
    for (const [key, val] of Object.entries(labResults)) { const t = val.trim(); if (t) { const n = parseFloat(t); if (!isNaN(n)) currentResults[key] = n; } }
    if (Object.keys(currentResults).length === 0) { setError("Enter at least one lab result or upload a report."); return; }
    setIsSubmitting(true);
    try {
      const result = await runAnalysis({ patient: { age: parsedAge, sex, name: patientName || undefined }, lab_results: currentResults, use_rag: true });
      const storable = { ...result }; if (patientName) storable.patient = { ...storable.patient, name: patientName };
      localStorage.setItem(`analysis_${result.id}`, JSON.stringify(storable));
      router.push(`/analysis/${result.id}`);
    } catch (err: any) { setError(err?.response?.data?.detail || err?.message || "Analysis failed."); setIsSubmitting(false); }
  };

  const stage = isUploading ? "loading" : uploadResult ? "done" : "idle";
  const panelChips = uploadResult ? getParsedPanelChips(uploadResult.parsed_results) : [];

  return (
    <div style={{ maxWidth: 860, margin: "0 auto" }}>
      {/* Hero */}
      <div className="animate-up" style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 30, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.02em" }}>
          Analyze your lab report
        </h1>
        <p style={{ fontSize: 15, color: "#64748B", marginTop: 8, lineHeight: 1.6, maxWidth: 480 }}>
          Upload a report or enter values to get evidence-based clinical insights.
        </p>
      </div>

      {/* Upload */}
      <div className="animate-up" style={{ animationDelay: "0.08s", marginBottom: 24 }}>
        {stage === "idle" ? (
          <div
            onDrop={onDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onClick={() => fileInputRef.current?.click()}
            style={{
              padding: "56px 40px", display: "flex", flexDirection: "column", alignItems: "center",
              cursor: "pointer", background: isDragOver ? "#F8FAFC" : "#FFFFFF",
              border: isDragOver ? "2px dashed rgba(99,102,241,0.5)" : "2px dashed #E2E8F0",
              borderRadius: 16, transition: "all 0.2s ease",
            }}
          >
            <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileUpload(f); }} style={{ display: "none" }} />
            <div style={{ width: 56, height: 56, borderRadius: 14, background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 5v14" stroke="#6366F1" strokeWidth="2.5" strokeLinecap="round" /><path d="M7 10l5-5 5 5" stroke="#6366F1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            <p style={{ marginTop: 16, fontSize: 17, fontWeight: 700, color: "#0F172A" }}>Drop your report here</p>
            <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>or click to browse · PDF, JPG, PNG</p>
          </div>
        ) : stage === "loading" ? (
          <div className="animate-fadeIn" style={{ padding: "60px 40px", textAlign: "center", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: 16 }}>
            <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 24 }}>
              {[0, 1, 2].map((i) => (<div key={i} style={{ width: 10, height: 10, borderRadius: "50%", background: "#6366F1", animation: `dotBounce 1.4s ease-in-out ${i * 0.16}s infinite` }} />))}
            </div>
            <p style={{ fontSize: 18, fontWeight: 700, color: "#0F172A" }}>Reading your report</p>
            <p style={{ fontSize: 14, color: "#94A3B8", marginTop: 6 }}>Extracting values and identifying test panels</p>
          </div>
        ) : (
          <div className="animate-scaleIn" style={{ padding: "24px 28px", background: "#FFFFFF", border: "1px solid #E2E8F0", borderRadius: 16 }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: "#ECFDF5", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M5 11l4 4L17 7" stroke="#059669" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 16, fontWeight: 700, color: "#059669" }}>Report parsed successfully</p>
                <p style={{ fontSize: 13, color: "#64748B", marginTop: 3, marginBottom: 12 }}>
                  {patientName && <strong>{patientName}</strong>}{patientName && age && " · "}{age && `${age} years`}{age && sex && `, ${sex === "male" ? "Male" : "Female"}`}
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {panelChips.map((c, i) => (
                    <span key={c.label} className="animate-slideUp" style={{ animationDelay: `${i * 0.04}s`, fontSize: 12, fontWeight: 600, color: c.accent, background: c.color, padding: "4px 12px", borderRadius: 8 }}>{c.label}</span>
                  ))}
                  <span className="animate-slideUp" style={{ animationDelay: `${panelChips.length * 0.04}s`, fontSize: 12, fontWeight: 700, color: "#059669", background: "#ECFDF5", padding: "4px 12px", borderRadius: 8 }}>{totalFilled} tests</span>
                </div>
              </div>
              <button onClick={resetUpload} className="btn-secondary" style={{ flexShrink: 0, padding: "6px 16px", fontSize: 12 }}>Change</button>
            </div>
          </div>
        )}
      </div>

      {/* Patient info */}
      {stage === "done" && (
        <div className="animate-up" style={{ animationDelay: "0.12s", display: "grid", gridTemplateColumns: "2fr 1fr 1.5fr", gap: 12, marginBottom: 24 }}>
          <div className="card-sm">
            <label style={{ fontSize: 10, fontWeight: 600, color: "#94A3B8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6, display: "block" }}>Patient</label>
            <input type="text" value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="Patient name" style={{ width: "100%", fontSize: 15, fontWeight: 700, color: "#0F172A", background: "transparent", border: "none", outline: "none", padding: 0 }} />
          </div>
          <div className="card-sm">
            <label style={{ fontSize: 10, fontWeight: 600, color: "#94A3B8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6, display: "block" }}>Age</label>
            <input type="number" value={age} onChange={(e) => setAge(e.target.value)} placeholder="e.g. 45" style={{ width: "100%", fontSize: 15, fontWeight: 700, color: "#0F172A", background: "transparent", border: "none", outline: "none", padding: 0, fontFamily: "'JetBrains Mono', monospace" }} />
          </div>
          <div className="card-sm">
            <label style={{ fontSize: 10, fontWeight: 600, color: "#94A3B8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6, display: "block" }}>Sex</label>
            <div style={{ display: "flex", gap: 6 }}>
              {(["male", "female"] as const).map((s) => (
                <button key={s} onClick={() => setSex(s)} style={{ flex: 1, padding: 8, borderRadius: 10, textAlign: "center", fontSize: 13, fontWeight: 600, cursor: "pointer", border: "none", background: sex === s ? "#0F172A" : "#F1F5F9", color: sex === s ? "white" : "#94A3B8", transition: "all 0.15s ease" }}>{s === "male" ? "Male" : "Female"}</button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Edit trigger */}
      {stage === "done" && !editOpen && (
        <div onClick={() => setEditOpen(true)} className="animate-up card-hover" style={{ animationDelay: "0.16s", padding: "14px 20px", marginBottom: 24, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: "#64748B" }}>Review & edit extracted values</span>
          <span style={{ fontSize: 16, color: "#94A3B8" }}>↓</span>
        </div>
      )}

      {/* Lab values editor */}
      {(stage !== "done" || editOpen) && (
        <div className="animate-up" style={{ background: "#FFFFFF", borderRadius: 16, border: "1px solid #E2E8F0", marginBottom: 24, overflow: "hidden" }}>
          <div style={{ padding: "16px 20px 0", borderBottom: "1px solid #E2E8F0" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
              <span style={{ fontSize: 15, fontWeight: 700, color: "#0F172A" }}>
                Lab Values
                {totalFilled > 0 && <span style={{ fontSize: 11, fontWeight: 700, color: "#059669", background: "#ECFDF5", padding: "2px 8px", borderRadius: 8, marginLeft: 10 }}>{totalFilled}</span>}
              </span>
              {stage === "done" && <button onClick={() => setEditOpen(false)} style={{ background: "none", border: "none", fontSize: 12, color: "#94A3B8", cursor: "pointer", fontWeight: 600 }}>Close ↑</button>}
            </div>
            <div style={{ display: "flex", gap: 2, overflowX: "auto", paddingBottom: 0 }}>
              {PANELS.map((p) => {
                const active = activePanel === p.id;
                const hasFill = panelHasValues(p.id);
                return (
                  <button key={p.id} onClick={() => setActivePanel(p.id)} style={{ padding: "8px 14px", paddingBottom: 12, borderRadius: "10px 10px 0 0", border: "none", fontSize: 12, fontWeight: active ? 700 : 500, cursor: "pointer", whiteSpace: "nowrap", background: active ? p.color : "transparent", color: active ? p.accent : hasFill ? "#0F172A" : "#94A3B8", borderBottom: active ? `2.5px solid ${p.accent}` : "2.5px solid transparent", marginBottom: -1, transition: "all 0.2s ease" }}>
                    {p.label}
                    {hasFill && !active && <span style={{ width: 4, height: 4, borderRadius: "50%", background: p.accent, display: "inline-block", marginLeft: 5, verticalAlign: "middle" }} />}
                  </button>
                );
              })}
            </div>
          </div>
          <div style={{ padding: 24, background: `${curPanel.color}88` }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
              {TESTS[activePanel].map((test, i) => {
                const filled = labResults[test.id]?.trim();
                return (
                  <div key={test.id} className="animate-slideUp" style={{ animationDelay: `${i * 0.03}s` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                      <label style={{ fontSize: 12, fontWeight: 600, color: filled ? "#0F172A" : "#64748B" }}>{test.name}</label>
                      {test.unit && <span style={{ fontSize: 10, color: "#94A3B8", fontWeight: 500 }}>{test.unit}</span>}
                    </div>
                    <input type="text" value={labResults[test.id] || ""} onChange={(e) => setLabResults((prev) => ({ ...prev, [test.id]: e.target.value }))} placeholder={test.placeholder} className="input-field" style={{ background: filled ? curPanel.color : undefined, borderColor: filled ? `${curPanel.accent}40` : undefined, fontWeight: filled ? 700 : undefined }} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="animate-fadeIn" style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24, padding: "14px 20px", borderRadius: 12, background: "#FEF2F2", border: "1px solid #FECACA" }}>
          <span style={{ color: "#DC2626", fontWeight: 600, fontSize: 13 }}>{error}</span>
          <button onClick={() => setError(null)} style={{ marginLeft: "auto", background: "none", border: "none", color: "#DC2626", cursor: "pointer", fontSize: 16 }}>×</button>
        </div>
      )}

      {/* Run Analysis */}
      <div className="animate-up" style={{ animationDelay: "0.2s", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 13, color: "#94A3B8" }}>{totalFilled > 0 ? `${totalFilled} values ready` : "Upload or enter values to begin"}</span>
        <button onClick={handleRunAnalysis} disabled={isSubmitting || totalFilled === 0} className="btn-primary" style={{ fontSize: 14, fontWeight: 700, padding: "14px 32px", display: "flex", alignItems: "center", gap: 8 }}>
          {isSubmitting ? "Running..." : "Run Analysis"}
          {!isSubmitting && <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>}
        </button>
      </div>
    </div>
  );
}

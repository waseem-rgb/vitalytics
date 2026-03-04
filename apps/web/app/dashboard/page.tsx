"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { AnalysisResult } from "@/lib/types";

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);

  useEffect(() => {
    const stored: AnalysisResult[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith("analysis_")) {
        try { stored.push(JSON.parse(localStorage.getItem(key)!)); } catch {}
      }
    }
    stored.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    setAnalyses(stored);
  }, []);

  const totalAnalyses = analyses.length;
  const totalAbnormal = analyses.reduce((sum, a) => {
    const t1 = a.tier1 || {};
    return sum + Object.values(t1).filter(v => v.status !== "normal").length;
  }, 0);
  const totalCritical = analyses.reduce((sum, a) => {
    const t1 = a.tier1 || {};
    return sum + Object.values(t1).filter(v => v.status === "critical_low" || v.status === "critical_high").length;
  }, 0);

  return (
    <div style={{ maxWidth: 920, margin: "0 auto" }}>
      {/* Hero */}
      <div className="animate-up" style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.02em" }}>
          Your Health Intelligence
        </h1>
        <p style={{ fontSize: 15, color: "#64748B", marginTop: 6, marginBottom: 20 }}>
          Upload lab reports and get evidence-based clinical insights instantly.
        </p>
        <Link href="/analysis/new" className="btn-primary" style={{ fontSize: 14, padding: "12px 28px" }}>
          New Analysis →
        </Link>
      </div>

      {/* Stats */}
      <div className="animate-up" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 32, animationDelay: "0.06s" }}>
        {[
          { label: "Total Analyses", value: totalAnalyses, accent: "#6366F1" },
          { label: "Abnormal Findings", value: totalAbnormal, accent: "#D97706" },
          { label: "Critical Alerts", value: totalCritical, accent: "#DC2626" },
        ].map(s => (
          <div key={s.label} className="card" style={{ textAlign: "center", padding: "24px 16px", borderTop: `3px solid ${s.accent}` }}>
            <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 32, fontWeight: 700, color: s.accent, lineHeight: 1 }}>{s.value}</p>
            <p style={{ fontSize: 12, color: "#94A3B8", fontWeight: 500, marginTop: 4 }}>{s.label}</p>
          </div>
        ))}
      </div>

      {/* Recent */}
      <div className="animate-up" style={{ animationDelay: "0.12s" }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: "#0F172A", marginBottom: 14 }}>Recent Analyses</h2>
        {analyses.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "48px 20px" }}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: "#EEF2FF", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M2 14l4-7 3 4 4-9 5 12" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            <p style={{ fontSize: 14, color: "#94A3B8", marginBottom: 12 }}>No analyses yet. Upload a lab report to get started.</p>
            <Link href="/analysis/new" className="btn-primary" style={{ fontSize: 13 }}>Upload Lab Report</Link>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {analyses.slice(0, 10).map((a, idx) => {
              const t1 = a.tier1 || {};
              const abnormal = Object.values(t1).filter(v => v.status !== "normal").length;
              const critical = Object.values(t1).filter(v => v.status === "critical_low" || v.status === "critical_high").length;
              const patterns = a.tier2?.patterns?.length || 0;
              const name = a.patient?.name;
              return (
                <Link key={a.id} href={`/analysis/${a.id}`} className="card-hover animate-up" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px", animationDelay: `${0.14 + idx * 0.03}s` }}>
                  <div>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "#0F172A", marginBottom: 3 }}>
                      {name || `${a.patient.sex === "female" ? "Female" : "Male"}, Age ${a.patient.age}`}
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                      {name && <span style={{ fontSize: 11, color: "#94A3B8" }}>{a.patient.age}y {a.patient.sex}</span>}
                      <span style={{ fontSize: 11, color: "#94A3B8" }}>{new Date(a.timestamp).toLocaleDateString()}</span>
                      <span style={{ fontSize: 11, color: "#94A3B8" }}>{Object.keys(t1).length} tests</span>
                      {abnormal > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#D97706", background: "#FFFBEB", padding: "1px 8px", borderRadius: 6 }}>{abnormal} abnormal</span>}
                      {critical > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#DC2626", background: "#FEF2F2", padding: "1px 8px", borderRadius: 6 }}>{critical} critical</span>}
                      {patterns > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#6366F1", background: "#EEF2FF", padding: "1px 8px", borderRadius: 6 }}>{patterns} patterns</span>}
                    </div>
                  </div>
                  <span style={{ fontSize: 12, color: "#94A3B8", fontWeight: 500 }}>→</span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

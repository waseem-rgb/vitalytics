"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import type { AnalysisResult } from "@/lib/types";

interface PatientRecord {
  name: string;
  age: number;
  sex: "male" | "female";
  analyses: AnalysisResult[];
  latestTimestamp: string;
  totalTests: number;
  totalAbnormal: number;
  totalPatterns: number;
}

export default function PatientsPage() {
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([]);
  const [search, setSearch] = useState("");

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

  const patients = useMemo(() => {
    const map = new Map<string, PatientRecord>();
    for (const a of analyses) {
      const name = a.patient?.name || `Patient (${a.patient.age}y ${a.patient.sex})`;
      const key = name.toLowerCase();
      if (!map.has(key)) {
        map.set(key, { name, age: a.patient.age, sex: a.patient.sex, analyses: [], latestTimestamp: a.timestamp, totalTests: 0, totalAbnormal: 0, totalPatterns: 0 });
      }
      const rec = map.get(key)!;
      rec.analyses.push(a);
      const t1 = a.tier1 || {};
      rec.totalTests += Object.keys(t1).length;
      rec.totalAbnormal += Object.values(t1).filter(v => v.status !== "normal" && v.status !== "unknown").length;
      rec.totalPatterns += a.tier2?.patterns?.length || 0;
      if (new Date(a.timestamp) > new Date(rec.latestTimestamp)) rec.latestTimestamp = a.timestamp;
    }
    return Array.from(map.values()).sort((a, b) => new Date(b.latestTimestamp).getTime() - new Date(a.latestTimestamp).getTime());
  }, [analyses]);

  const filtered = useMemo(() => {
    if (!search.trim()) return patients;
    const q = search.toLowerCase();
    return patients.filter(p => p.name.toLowerCase().includes(q));
  }, [patients, search]);

  return (
    <div style={{ maxWidth: 920, margin: "0 auto" }}>
      {/* Header */}
      <div className="animate-up" style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: "#0F172A", letterSpacing: "-0.02em" }}>Patient History</h1>
        <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>
          {patients.length} patient{patients.length !== 1 ? "s" : ""} · {analyses.length} total analyses
        </p>
      </div>

      {/* Search */}
      {patients.length > 0 && (
        <div className="animate-up" style={{ marginBottom: 20, animationDelay: "0.06s" }}>
          <input
            type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search patients..."
            className="input-text" style={{ width: "100%", borderRadius: 12 }}
          />
        </div>
      )}

      {/* List */}
      {filtered.length === 0 ? (
        <div className="card animate-up" style={{ textAlign: "center", padding: "48px 20px", animationDelay: "0.1s" }}>
          <p style={{ fontSize: 14, color: "#94A3B8" }}>
            {search ? "No patients match your search" : "No patient records yet"}
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {filtered.map((patient, idx) => (
            <div key={patient.name} className="card animate-up" style={{ padding: 0, overflow: "hidden", animationDelay: `${0.08 + idx * 0.04}s` }}>
              {/* Patient header */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: "linear-gradient(135deg, #EEF2FF, #E0E7FF)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: "#6366F1" }}>
                    {patient.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p style={{ fontSize: 14, fontWeight: 600, color: "#0F172A" }}>{patient.name}</p>
                    <p style={{ fontSize: 11, color: "#94A3B8" }}>{patient.age}y {patient.sex} · {patient.analyses.length} report{patient.analyses.length !== 1 ? "s" : ""}</p>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  {patient.totalAbnormal > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#D97706", background: "#FFFBEB", padding: "2px 8px", borderRadius: 6 }}>{patient.totalAbnormal} abnormal</span>}
                  {patient.totalPatterns > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#6366F1", background: "#EEF2FF", padding: "2px 8px", borderRadius: 6 }}>{patient.totalPatterns} patterns</span>}
                </div>
              </div>
              {/* Analysis list */}
              <div style={{ borderTop: "1px solid #E2E8F0", padding: "6px 12px" }}>
                {patient.analyses.map(a => {
                  const t1 = a.tier1 || {};
                  const abnormal = Object.values(t1).filter(v => v.status !== "normal" && v.status !== "unknown").length;
                  const patterns = a.tier2?.patterns?.length || 0;
                  return (
                    <Link key={a.id} href={`/analysis/${a.id}`} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 10px", borderRadius: 8, transition: "background 0.15s" }} onMouseEnter={e => e.currentTarget.style.background = "#F8FAFC"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 11, color: "#94A3B8" }}>{new Date(a.timestamp).toLocaleDateString()}</span>
                        <span style={{ fontSize: 11, color: "#CBD5E1" }}>{Object.keys(t1).length} tests</span>
                        {abnormal > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#D97706", background: "#FFFBEB", padding: "1px 6px", borderRadius: 4 }}>{abnormal} abnormal</span>}
                        {patterns > 0 && <span style={{ fontSize: 10, fontWeight: 600, color: "#DC2626", background: "#FEF2F2", padding: "1px 6px", borderRadius: 4 }}>{patterns} patterns</span>}
                      </div>
                      <span style={{ fontSize: 11, color: "#94A3B8" }}>→</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

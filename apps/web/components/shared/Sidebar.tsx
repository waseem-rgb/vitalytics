"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analysis/new", label: "New Analysis" },
  { href: "/patients", label: "Patients" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="flex flex-col shrink-0"
      style={{
        width: 240,
        background: "linear-gradient(180deg, #0F172A, #1E293B)",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3" style={{ padding: "24px 20px 32px" }}>
        <div
          className="flex items-center justify-center shrink-0"
          style={{
            width: 34,
            height: 34,
            borderRadius: 10,
            background: "linear-gradient(135deg, #6366F1, #8B5CF6)",
          }}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M2 11l3-5.5 2.5 3.5L11 2l3 9"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div>
          <p style={{ fontSize: 16, fontWeight: 700, color: "#FFFFFF", letterSpacing: "-0.02em" }}>
            Vitalytics
          </p>
          <p style={{ fontSize: 9, fontWeight: 600, color: "#64748B", letterSpacing: "0.12em", textTransform: "uppercase" }}>
            Lab Intelligence
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1" style={{ padding: "0 12px" }}>
        {nav.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className="block"
              style={{
                padding: "10px 14px",
                margin: "2px 0",
                borderRadius: 10,
                fontSize: 13,
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "#FFFFFF" : "#94A3B8",
                background: isActive ? "rgba(99, 102, 241, 0.15)" : "transparent",
                transition: "all 0.15s ease",
              }}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: "16px 20px", borderTop: "1px solid rgba(148, 163, 184, 0.15)" }}>
        <p style={{ fontSize: 10, color: "#64748B", textAlign: "center", fontWeight: 500 }}>
          Clinical Decision Support Only
        </p>
      </div>
    </aside>
  );
}

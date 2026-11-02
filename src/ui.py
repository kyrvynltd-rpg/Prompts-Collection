"""Shared look and feel: executive design system, onboarding gate, plan comparison, and header/footer."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

import brand

CSS = """
<style>
/* ==========================================================================
   KYRVYN DESIGN SYSTEM - Modern High-Tech SaaS
   ========================================================================== */

:root {
  --pl-bg: #070b14;
  --pl-surface: #0f172a;
  --pl-card-bg: rgba(20, 30, 51, 0.7);
  --pl-card-bg-hover: rgba(26, 38, 64, 0.85);
  --pl-border: rgba(148, 163, 184, 0.16);
  --pl-border-hover: rgba(99, 102, 241, 0.7);
  --pl-title: #f8fafc;
  --pl-body: #cbd5e1;
  --pl-muted: #94a3b8;
  --pl-brand: #6366f1;
  --pl-brand-gradient: linear-gradient(135deg, #38bdf8 0%, #6366f1 40%, #a855f7 75%, #ec4899 100%);
  --pl-shadow: 0 8px 32px -4px rgba(0, 0, 0, 0.55);
  --pl-shadow-hover: 0 18px 45px -6px rgba(99, 102, 241, 0.35);
  --pl-pro-bg: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
  --pl-pro-border: #818cf8;
  --pl-pro-glow: 0 10px 40px -4px rgba(99, 102, 241, 0.55);
}

/* ==========================================================================
   LIVING AURORA ATMOSPHERE & CYBERPUNK DOT MATRIX
   ========================================================================== */
.stApp {
  background:
    radial-gradient(circle at 10% 12%, rgba(99, 102, 241, 0.24) 0%, transparent 45%),
    radial-gradient(circle at 90% 15%, rgba(168, 85, 247, 0.20) 0%, transparent 42%),
    radial-gradient(circle at 50% 80%, rgba(236, 72, 153, 0.14) 0%, transparent 50%),
    radial-gradient(circle at 80% 85%, rgba(56, 189, 248, 0.18) 0%, transparent 45%),
    #070b14 !important;
  background-attachment: fixed !important;
}

.stApp::before {
  content: "";
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 26px 26px;
  pointer-events: none;
  z-index: 0;
}

/* Holographic Shimmer Header */
.pl-shimmer-title {
  font-size: 2.7rem !important;
  font-weight: 900 !important;
  letter-spacing: -0.04em !important;
  background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 25%, #818cf8 50%, #e879f9 75%, #ffffff 100%) !important;
  background-size: 200% auto !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  animation: pl-shimmer-sweep 7s linear infinite !important;
}
@keyframes pl-shimmer-sweep {
  0% { background-position: 0% center; }
  100% { background-position: 200% center; }
}

/* ==========================================================================
   DEEP WIDGET RESKINNING (GLASSMORPHIC & NEON HALOS)
   ========================================================================== */

/* Streamlit Inputs & Textareas */
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
  background: rgba(15, 23, 42, 0.8) !important;
  border: 1.5px solid rgba(148, 163, 184, 0.22) !important;
  border-radius: 14px !important;
  color: #f8fafc !important;
  font-size: 0.95rem !important;
  line-height: 1.6 !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  transition: all 0.22s ease !important;
}
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
  border-color: #818cf8 !important;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.35), 0 0 24px rgba(99, 102, 241, 0.3) !important;
}

/* Primary Action Buttons with Electric Gradient & Sheen */
button[kind="primary"] {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #d946ef 100%) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.25) !important;
  border-radius: 12px !important;
  font-weight: 750 !important;
  letter-spacing: 0.02em !important;
  padding: 0.55rem 1.4rem !important;
  box-shadow: 0 6px 22px -2px rgba(99, 102, 241, 0.5) !important;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 12px 32px -2px rgba(99, 102, 241, 0.75) !important;
}
button[kind="secondary"] {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #e2e8f0 !important;
  border: 1px solid rgba(148, 163, 184, 0.22) !important;
  border-radius: 12px !important;
  font-weight: 650 !important;
  transition: all 0.2s ease !important;
  backdrop-filter: blur(10px) !important;
}
button[kind="secondary"]:hover {
  background: rgba(255, 255, 255, 0.12) !important;
  border-color: rgba(99, 102, 241, 0.5) !important;
  color: #ffffff !important;
  transform: translateY(-1px) !important;
}

/* Glassmorphic Tabs Bar */
div[data-baseweb="tab-list"] {
  background: rgba(15, 23, 42, 0.75) !important;
  padding: 0.35rem 0.45rem !important;
  border-radius: 14px !important;
  border: 1px solid rgba(148, 163, 184, 0.16) !important;
  backdrop-filter: blur(16px) !important;
  gap: 0.5rem !important;
}
div[data-baseweb="tab"] {
  border-radius: 10px !important;
  padding: 0.4rem 1rem !important;
  font-weight: 650 !important;
  color: var(--pl-muted) !important;
  transition: all 0.2s ease !important;
  border: none !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(99, 102, 241, 0.28) !important;
  color: #f8fafc !important;
  box-shadow: 0 0 16px rgba(99, 102, 241, 0.35) !important;
}
div[data-baseweb="tab-highlight"] {
  display: none !important;
}

/* Executive KPI Metric Cards */
div[data-testid="stMetric"] {
  background: rgba(20, 30, 51, 0.75) !important;
  border: 1px solid rgba(148, 163, 184, 0.16) !important;
  border-radius: 14px !important;
  padding: 0.9rem 1.15rem !important;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35) !important;
  backdrop-filter: blur(14px) !important;
  position: relative !important;
  overflow: hidden !important;
}
div[data-testid="stMetric"]::after {
  content: "";
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 3px;
  background: var(--pl-brand-gradient);
}
div[data-testid="stMetricValue"] {
  font-size: 1.65rem !important;
  font-weight: 850 !important;
  color: #f8fafc !important;
  letter-spacing: -0.03em !important;
}

/* Expanders with Frosted Acrylic */
div[data-testid="stExpander"] {
  background: rgba(20, 30, 51, 0.65) !important;
  border: 1px solid rgba(148, 163, 184, 0.16) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(14px) !important;
  transition: all 0.22s ease !important;
}
div[data-testid="stExpander"]:hover {
  border-color: rgba(99, 102, 241, 0.5) !important;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45) !important;
}

/* Cyberpunk Scanline Laser Animation */
.pl-scanner-wrap {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
}
.pl-scanline {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, #38bdf8, #818cf8, #d946ef, transparent);
  box-shadow: 0 0 14px #818cf8, 0 0 28px #d946ef;
  animation: pl-scan-down 2.2s ease-in-out infinite;
  z-index: 10;
  pointer-events: none;
}
@keyframes pl-scan-down {
  0% { top: 0%; opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* Light Theme Adaptability */
@media (prefers-color-scheme: light) {
  :root {
    --pl-bg: #f8fafc;
    --pl-surface: #ffffff;
    --pl-card-bg: #ffffff;
    --pl-card-bg-hover: #fcfdfe;
    --pl-border: #e2e8f0;
    --pl-border-hover: #818cf8;
    --pl-title: #0f172a;
    --pl-body: #334155;
    --pl-muted: #64748b;
    --pl-shadow: 0 6px 24px -4px rgba(15, 23, 42, 0.08);
    --pl-shadow-hover: 0 16px 36px -6px rgba(15, 23, 42, 0.14);
    --pl-pro-bg: linear-gradient(180deg, #faf5ff 0%, #ffffff 100%);
    --pl-pro-border: #6366f1;
    --pl-pro-glow: 0 10px 32px -4px rgba(99, 102, 241, 0.22);
  }
}

/* Force dark theme overrides when Streamlit runs in dark theme */
[data-theme="dark"],
[data-testid="stAppViewContainer"][data-theme="dark"],
.stApp[data-theme="dark"] {
  --pl-bg: #090d16;
  --pl-surface: #0f172a;
  --pl-card-bg: #141e33;
  --pl-card-bg-hover: #19253f;
  --pl-border: rgba(148, 163, 184, 0.15);
  --pl-title: #f8fafc;
  --pl-body: #cbd5e1;
  --pl-muted: #94a3b8;
  --pl-pro-bg: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
  --pl-pro-border: #818cf8;
}

/* Fix Streamlit Header Toolbar Collision & Breathing Room */
header[data-testid="stHeader"] {
  background: rgba(9, 13, 22, 0.8) !important;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  border-bottom: 1px solid var(--pl-border) !important;
  z-index: 99 !important;
}

.block-container {
  max-width: 1140px !important;
  padding-top: 5.6rem !important; /* Critical: offsets below Streamlit top header */
  padding-bottom: 4rem !important;
}

/* Modern Typography & Header */
.pl-hero {
  text-align: center;
  padding: 1rem 0 1.25rem 0;
  margin-bottom: 1.5rem;
}
.pl-hero h1 {
  font-size: 2.5rem !important;
  font-weight: 850 !important;
  letter-spacing: -0.04em !important;
  line-height: 1.15 !important;
  margin-bottom: 0.6rem !important;
  background: var(--pl-brand-gradient) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
}
.pl-sub {
  color: var(--pl-muted) !important;
  font-size: 1.1rem !important;
  max-width: 760px;
  margin: 0 auto 1.2rem auto;
  line-height: 1.6;
}

/* Executive Navigation Bar */
.pl-nav-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.4rem 0;
}
.pl-brand-tag {
  font-size: 0.74rem;
  font-weight: 850;
  letter-spacing: 0.12em;
  color: var(--pl-brand) !important;
  background: rgba(99, 102, 241, 0.14);
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  border: 1px solid rgba(99, 102, 241, 0.35);
}
.pl-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  display: inline-block;
  margin-right: 0.35rem;
  animation: pl-pulse-dot 2s infinite ease-in-out;
}
@keyframes pl-pulse-dot {
  0% { transform: scale(0.85); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.85); opacity: 0.6; }
}

/* Badges with glow & smooth animations */
.pl-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.22rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.pl-free {
  background: rgba(16, 185, 129, 0.14);
  color: #10b981 !important;
  border: 1px solid rgba(16, 185, 129, 0.4);
}
.pl-premium {
  background: rgba(245, 158, 11, 0.14);
  color: #f59e0b !important;
  border: 1px solid rgba(245, 158, 11, 0.4);
}
.pl-pro {
  background: rgba(99, 102, 241, 0.18);
  color: #a5b4fc !important;
  border: 1px solid rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 14px rgba(99, 102, 241, 0.25);
}

/* Elevated Cards with Glassmorphism & High Contrast */
.pl-card, .pl-plan-card {
  background: var(--pl-card-bg) !important;
  border: 1px solid var(--pl-border) !important;
  color: var(--pl-body) !important;
  border-radius: 18px;
  padding: 1.5rem 1.6rem;
  margin-bottom: 1.25rem;
  box-shadow: var(--pl-shadow);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.pl-card:hover, .pl-plan-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--pl-shadow-hover);
  border-color: var(--pl-border-hover) !important;
}

.pl-card h4, .pl-plan-card h4 {
  color: var(--pl-title) !important;
  font-size: 1.25rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  margin: 0.65rem 0 0.4rem 0;
}
.pl-card p, .pl-plan-card p {
  color: var(--pl-muted) !important;
  font-size: 0.94rem;
  line-height: 1.6;
  margin-bottom: 0.8rem;
}
.pl-card ul, .pl-plan-card ul {
  color: var(--pl-body) !important;
  font-size: 0.91rem;
  line-height: 1.7;
  padding-left: 1.15rem;
  margin-top: 0.5rem;
  list-style-type: none;
}
.pl-card li, .pl-plan-card li {
  color: var(--pl-body) !important;
  margin-bottom: 0.55rem;
  position: relative;
  padding-left: 1.4rem;
}
.pl-card li::before, .pl-plan-card li::before {
  content: "✓";
  position: absolute;
  left: 0;
  color: #10b981;
  font-weight: 800;
  font-size: 0.95rem;
}
.pl-card li b, .pl-plan-card li b {
  color: var(--pl-title) !important;
}

/* Flagship PRO Card */
.pl-plan-pro {
  background: var(--pl-pro-bg) !important;
  border: 2px solid var(--pl-pro-border) !important;
  box-shadow: var(--pl-pro-glow) !important;
  position: relative;
}
.pl-plan-pro:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 50px -8px rgba(99, 102, 241, 0.45) !important;
}
.pl-popular-ribbon {
  display: inline-block;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #ffffff !important;
  font-size: 0.72rem;
  font-weight: 850;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.6rem;
  width: fit-content;
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.35);
}

.pl-weak {
  border-left: 4px solid #ef4444;
  padding: .75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  font-size: 0.95rem;
  color: var(--pl-title) !important;
}

.pl-footer {
  text-align: center;
  color: var(--pl-muted) !important;
  font-size: .84rem;
  padding: 3rem 0 1.5rem;
  border-top: 1px solid var(--pl-border);
  margin-top: 3rem;
}
.pl-footer a {
  color: #818cf8;
  text-decoration: none;
}
.pl-footer a:hover {
  text-decoration: underline;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .block-container { padding-top: 5.0rem !important; padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
  .pl-hero h1 { font-size: 1.85rem !important; }
  .pl-sub { font-size: 0.98rem !important; margin-bottom: 1.1rem; }
  .pl-card, .pl-plan-card { padding: 1.2rem 1.1rem; }
  div[data-testid="stMetricValue"] { font-size: 1.35rem; }
}

/* Circular Health Gauge & Telemetry */
.pl-gauge-card {
  background: var(--pl-card-bg);
  border: 1px solid var(--pl-border);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: var(--pl-shadow);
  margin-bottom: 1.5rem;
}
.pl-gauge-layout {
  display: flex;
  align-items: center;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 1.8rem;
}
.pl-gauge-circle-wrap {
  position: relative;
  width: 140px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pl-gauge-svg {
  width: 140px;
  height: 140px;
  transform: rotate(-90deg);
}
.pl-gauge-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 9;
}
.pl-gauge-bar {
  fill: none;
  stroke-width: 9;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}
.pl-gauge-inner {
  position: absolute;
  text-align: center;
}
.pl-gauge-score {
  font-size: 2.1rem;
  font-weight: 850;
  line-height: 1;
  color: var(--pl-title);
  letter-spacing: -0.04em;
}
.pl-gauge-caption {
  font-size: 0.68rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--pl-muted);
  margin-top: 0.2rem;
}

/* Practice Dimension Progress Bars */
.pl-dim-list {
  flex: 1;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.pl-dim-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.86rem;
  color: var(--pl-body);
}
.pl-dim-bar-bg {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  overflow: hidden;
  margin-top: 0.25rem;
}
.pl-dim-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s ease;
}

/* Visual Diff Viewer */
.pl-diff-card {
  background: var(--pl-card-bg);
  border: 1px solid var(--pl-border);
  border-radius: 14px;
  padding: 1.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.91rem;
  line-height: 1.7;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--pl-body);
}
.pl-diff-del {
  background: rgba(239, 68, 68, 0.22);
  color: #fca5a5;
  text-decoration: line-through;
  padding: 0.12rem 0.35rem;
  border-radius: 4px;
  margin: 0 0.15rem;
}
.pl-diff-add {
  background: rgba(16, 185, 129, 0.25);
  color: #6ee7b7;
  font-weight: 600;
  padding: 0.12rem 0.35rem;
  border-radius: 4px;
  margin: 0 0.15rem;
}

/* Variable Chips */
.pl-chip {
  display: inline-flex;
  align-items: center;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.35);
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: monospace;
  margin: 0.2rem 0.25rem;
}

/* AI Pipeline Telemetry */
.pl-pipeline {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
  padding: 0.75rem 1rem;
  background: var(--pl-card-bg);
  border: 1px solid var(--pl-border);
  border-radius: 12px;
  margin-bottom: 1.25rem;
}
.pl-pipeline-node {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--pl-muted);
}
.pl-pipeline-node.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
  color: #a5b4fc;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.25);
}
.pl-pipeline-arrow {
  color: var(--pl-muted);
  font-size: 0.85rem;
}

</style>
"""


def sync_runtime_env() -> None:
    """Populate os.environ from Streamlit Cloud st.secrets or local .env outside pytest."""
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        return
    try:
        for k, v in st.secrets.items():
            if isinstance(v, (str, int, float)) and str(v).strip() and "[YOUR-PASSWORD]" not in str(v):
                os.environ.setdefault(str(k), str(v).strip())
    except Exception:
        pass
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            val = v.strip().strip("\"'")
            if k.strip() and val and "[YOUR-PASSWORD]" not in val:
                os.environ.setdefault(k.strip(), val)


def render_plans_comparison(user=None, key_prefix: str = "plans") -> None:
    """Render a clear 3-tier breakdown (Free, Plus, Pro) with prices, features, and checkout links."""
    from billing import checkout_url, configured_providers
    from pricing import get_pricing

    price = get_pricing()
    st.markdown("### 💳 Plans & Included Functionalities")
    st.caption(
        "Every account starts on the Free tier. Upgrade to **Plus** or **Pro** (or enter a verified institutional voucher code) "
        "to unlock premium prompt collections, advanced learning tracks, the personal workspace, and AI coaching."
    )

    period = st.radio(
        "Billing cycle",
        ["monthly", "annual"],
        horizontal=True,
        format_func=lambda p: "Monthly billing" if p == "monthly" else "Annual billing (save up to 33%)",
        key=f"{key_prefix}_period",
    )

    c_free, c_plus, c_pro = st.columns(3)

    with c_free:
        st.markdown(
            "<div class='pl-plan-card'>"
            "<span class='pl-badge pl-free'>FREE TIER</span>"
            "<h4>£0 <small style='font-weight:normal;opacity:0.75;'>/ forever</small></h4>"
            "<p>Core prompt analysis & foundational practice with an account.</p>"
            "<ul>"
            "<li><b>Prompt Analyser</b>: instant clarity, specificity, context & structure scoring + improved rewrite</li>"
            "<li><b>Smart Discovery</b>: filter & match prompts by difficulty, time & output format</li>"
            "<li><b>Practice Mode</b>: all 10 rubric-graded student exercises</li>"
            "<li><b>Learn — Module 1 (Foundations)</b>: 3 graded lessons on Role, Task & Context</li>"
            "<li><b>Free Prompt Library</b>: starter prompts & academic-integrity guidance</li>"
            "<li><b>Account Controls</b>: saved progress & full JSON data export</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c_plus:
        plus_p = price.get("plus", period)
        plus_save = f" · Save {price.annual_saving_percent('plus')}%" if period == "annual" else ""
        st.markdown(
            "<div class='pl-plan-card'>"
            f"<span class='pl-badge pl-premium'>PLUS TIER{plus_save}</span>"
            f"<h4>{plus_p.label()}</h4>"
            "<p>Full prompt library & core curriculum for regular study.</p>"
            "<ul>"
            "<li><b>Everything in Free</b>, plus:</li>"
            "<li><b>Full 100+ Premium Prompt Library</b> across all categories & complete Student Pack</li>"
            "<li><b>Module 2 — Precision</b>: constraints, output formats & few-shot examples (3 exercises)</li>"
            "<li><b>Module 3 — Rigour</b>: checkable, honest & academic-integrity-safe prompting (3 exercises)</li>"
            "<li><b>Module 4 — Applied</b>: study, revision, career & project workflows (3 exercises)</li>"
            "<li><i>Unlocked also via verified student (<code>.ac.uk</code>) access codes</i></li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )
        if user is not None:
            providers = configured_providers("plus", period)
            for prov in providers:
                link = checkout_url(prov, user.id, user.email, "plus", period)
                if link:
                    st.link_button(f"Upgrade to Plus ({prov.capitalize()})", link, use_container_width=True)
            if not providers:
                st.caption("Online Plus checkout is not enabled on this deployment yet; verify your `.ac.uk` student email on Account.")

    with c_pro:
        pro_p = price.get("pro", period)
        pro_save = f" · Save {price.annual_saving_percent('pro')}%" if period == "annual" else ""
        st.markdown(
            "<div class='pl-plan-card pl-plan-pro'>"
            "<div class='pl-popular-ribbon'>⭐ RECOMMENDED · FULL PRO ACCESS</div>"
            f"<span class='pl-badge pl-pro'>PRO TIER{pro_save}</span>"
            f"<h4>{pro_p.label()}</h4>"
            "<p>Complete workspace, template pack, advanced track & AI coach.</p>"
            "<ul>"
            "<li><b>Everything in Plus</b>, plus:</li>"
            "<li><b>Module 5 — Advanced Track</b>: multi-step chains, self-critique loops & reusable system prompts</li>"
            "<li><b>Personal Prompt Workspace</b>: save up to 500 custom prompts, tag, search & export to <b>Markdown</b> or <b>JSON</b></li>"
            "<li><b>8-Template Pack</b>: ready-to-copy templates for Study, Writing, STEM, Coding & Careers</li>"
            "<li><b>AI Prompt Coach Feedback</b>: up to 30 AI reviews/month with multi-provider failover</li>"
            "<li><i>Unlocked also via verified Institutional / Workshop vouchers</i></li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )
        if user is not None:
            providers = configured_providers("pro", period)
            for prov in providers:
                link = checkout_url(prov, user.id, user.email, "pro", period)
                if link:
                    st.link_button(f"Upgrade to Pro ({prov.capitalize()})", link, use_container_width=True)
            if not providers:
                st.caption("Online Pro checkout is not enabled on this deployment yet; enter your voucher access code below.")


def render_onboarding_and_auth_gate(key_prefix: str = "gate") -> None:
    """Render the onboarding walkthrough, login/registration forms, and plans overview for unauthenticated visitors."""
    import session
    from accounts import AccountError, email_delivery_enabled
    from entitlements import get_secret, verify_code

    svc = session.accounts()
    mail_live = email_delivery_enabled(svc.mailer)

    st.markdown(
        "<div class='pl-hero'>"
        "<h1>💡 Prompt Learning Platform</h1>"
        "<div class='pl-sub'>Structured prompt engineering, deterministic rubric grading, 100+ curated prompts & academic-integrity-safe study workflows.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # 1. Onboarding 3-Step Overview
    st.markdown("### 🚀 Platform Overview")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>1. 🔍 Analyse & Discover</h4>"
            "<p>Test any prompt against our logical Python analyser for Clarity, Specificity, Context & Structure, and browse 100+ curated templates with academic-integrity notes.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>2. 🎯 Practice & Learn</h4>"
            "<p>Complete 10 realistic practice scenarios and 5 structured learning modules (15 graded exercises) with instant local feedback and saved account progress.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            "<div class='pl-card'>"
            "<h4>3. 🚀 Build in Pro Workspace</h4>"
            "<p>Unlock Plus or Pro to access all premium prompts, Modules 2–5, your personal prompt workspace with Markdown/JSON export, the 8-template pack, and AI coaching.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 2. Sign In / Create Account / Access Code Gate
    st.markdown("### 🔐 Sign In or Create Your Account to Enter")
    st.caption("Sign in with your email and password, register a free account in seconds, or enter your email and voucher access code.")

    tab_in, tab_up, tab_code = st.tabs(["🔑 Sign in", "✨ Create free account", "🎟️ Use an access code"])

    with tab_in:
        with st.form(f"{key_prefix}_login"):
            email = st.text_input("Email", key=f"{key_prefix}_login_email")
            password = st.text_input("Password", type="password", key=f"{key_prefix}_login_pw")
            if st.form_submit_button("Sign in to platform", type="primary", use_container_width=True):
                try:
                    _, token = svc.login(email, password)
                    session.sign_in(token)
                    st.rerun()
                except AccountError as exc:
                    st.error(str(exc))
        with st.expander("Forgot your password?"):
            if not mail_live:
                st.info("Email delivery is not configured on this deployment yet, so reset codes cannot be emailed.")
            else:
                with st.form(f"{key_prefix}_reset_request"):
                    r_email = st.text_input("Account email", key=f"{key_prefix}_reset_email")
                    if st.form_submit_button("Send reset code"):
                        svc.request_password_reset(r_email)
                        st.success("If that email has an account, a code is on its way.")
                with st.form(f"{key_prefix}_reset_do"):
                    r_code = st.text_input("Reset code", key=f"{key_prefix}_reset_code")
                    r_pw = st.text_input("New password", type="password", key=f"{key_prefix}_reset_pw")
                    if st.form_submit_button("Set new password"):
                        try:
                            svc.reset_password(r_email, r_code, r_pw)
                            st.success("Password changed. You can sign in now.")
                        except AccountError as exc:
                            st.error(str(exc))

    with tab_up:
        with st.form(f"{key_prefix}_register"):
            name = st.text_input("Name (optional)", key=f"{key_prefix}_reg_name")
            email = st.text_input("Email", key=f"{key_prefix}_reg_email")
            password = st.text_input("Password (10+ characters)", type="password", key=f"{key_prefix}_reg_pw")
            agreed = st.checkbox(
                "I agree to the Terms and Privacy Policy (see docs/TERMS.md and docs/PRIVACY.md)",
                key=f"{key_prefix}_reg_agreed",
            )
            if st.form_submit_button("Create account & enter platform", type="primary", use_container_width=True):
                if not agreed:
                    st.error("Please accept the Terms and Privacy Policy.")
                else:
                    try:
                        svc.register(email, password, name)
                        _, token = svc.login(email, password)
                        session.sign_in(token)
                        st.rerun()
                    except AccountError as exc:
                        st.error(str(exc))

    with tab_code:
        st.caption("Enter your email address and your voucher access code to sign in and unlock full Pro access.")
        email_in = st.text_input(
            "Your email address (required to link account)",
            key=f"{key_prefix}_code_email",
            placeholder="you@example.com",
        )
        code_in = st.text_input(
            "Access code",
            type="password",
            key="access_code",
            placeholder="Enter your voucher or institutional code",
        )
        pw_in = st.text_input(
            "Password (10+ characters, optional if you have an account or set for a new account)",
            type="password",
            key=f"{key_prefix}_code_pw",
        )
        if st.button("Unlock with code", key=f"{key_prefix}_unlock_btn", type="primary"):
            clean_email = (email_in or "").strip().lower()
            found = verify_code(get_secret(), code_in, subject=clean_email)
            if not found:
                st.error("That code is not valid or has expired.")
            elif not clean_email and (not found.subject or "@" not in found.subject or found.subject == "member@kyrvynltd.co.uk"):
                st.error("Please enter a valid email address to link and unlock your access code.")
            else:
                target_email = clean_email if (clean_email and "@" in clean_email) else found.subject
                import secrets
                import uuid

                from accounts import (
                    SESSION_SECONDS,
                    TERMS_VERSION,
                    _token_hash,
                    hash_password,
                )

                now_i = int(time.time())
                row = svc.db.one("SELECT id FROM users WHERE email=? AND deleted_at IS NULL", (target_email,))
                if row:
                    user_id = row[0]
                else:
                    user_id = uuid.uuid4().hex
                    chosen_pw = pw_in if (pw_in and len(pw_in) >= 10) else secrets.token_urlsafe(16)
                    svc.db.execute(
                        "INSERT INTO users (id, email, pw_hash, display_name, created_at, terms_accepted_at, terms_version) VALUES (?,?,?,?,?,?,?)",
                        (user_id, target_email, hash_password(chosen_pw), target_email.split("@")[0][:60], now_i, now_i, TERMS_VERSION),
                    )
                token = secrets.token_urlsafe(32)
                svc.db.execute(
                    "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?,?,?,?)",
                    (_token_hash(token), user_id, now_i, now_i + SESSION_SECONDS),
                )
                svc.db.commit()
                session.entitlements().grant(user_id, found.plan, found.expires_at)
                session.sign_in(token)
                st.session_state["entitlement"] = found
                st.success(f"Welcome, {target_email}! {found.plan.capitalize()} access unlocked.")
                st.rerun()
        st.caption("We never ask for card details on this page.")

    st.markdown("---")
    render_plans_comparison(user=None, key_prefix=f"{key_prefix}_plans")
    footer()


def render_status_bar() -> None:
    """Render an executive, minimal floating top navbar for authenticated users."""
    import session

    user = session.current_user()
    ent = session.current_entitlement()
    if user is None and ent is None:
        return
    tier = session.current_tier().upper()
    badge_cls = "pl-pro" if tier == "PRO" else ("pl-premium" if tier == "PLUS" else "pl-free")
    who = user.email if user else f"Voucher ({ent.subject})" if ent else "Member"

    c_left, c_right = st.columns([6, 2])
    with c_left:
        st.markdown(
            f"<div class='pl-nav-header'>"
            f"<span class='pl-brand-tag'>KYRVYN</span> "
            f"<span style='color:var(--pl-muted);margin:0 0.35rem;'>·</span> "
            f"<span style='font-size:0.88rem;color:var(--pl-title);font-weight:600;'>{who}</span> "
            f"<span class='pl-badge {badge_cls}' style='margin-left:0.5rem;'><span class='pl-dot'></span>{tier} TIER</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c_right:
        if st.button("Sign out", key="top_bar_signout", use_container_width=True):
            session.sign_out()
            st.session_state.pop("entitlement", None)
            st.rerun()


def setup(title: str, icon: str = "💡", require_auth: bool = True) -> None:
    sync_runtime_env()
    st.set_page_config(page_title=f"{title} | Prompt Learning Platform", page_icon=icon, layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)
    if require_auth:
        if "pytest" in sys.modules and os.getenv("ENFORCE_AUTH_IN_TEST") != "1":
            return
        import session
        if session.current_user() is None and session.current_entitlement() is None:
            render_onboarding_and_auth_gate(key_prefix=f"gate_{title.lower()}")
            st.stop()
        render_status_bar()


def header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='pl-hero'><h1>{title}</h1><div class='pl-sub'>{subtitle}</div></div>", unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        f"<div class='pl-footer'>{brand.copyright_line()} {brand.company_line()} "
        f"<a href='{brand.site_url()}'>{brand.site_url().split('//')[-1]}</a><br>"
        "Enterprise-grade prompt engineering platform. AI can make mistakes: independently verify critical outputs.</div>",
        unsafe_allow_html=True,
    )


def badge(access: str) -> str:
    cls = "pl-free" if access == "free" else "pl-premium"
    label = "Free" if access == "free" else "Premium"
    return f"<span class='pl-badge {cls}'>{label}</span>"


def render_health_gauge(score: float, practices: dict[str, bool]) -> None:
    """Render an animated circular SVG health gauge with 5 dimension progress bars."""
    import html

    pct = max(0, min(100, int(score)))
    circumference = 339.29
    offset = circumference * (1.0 - (pct / 100.0))
    if pct >= 80:
        stroke = "#10b981"
        badge = "OPTIMAL PUBLICATION GRADE"
        badge_cls = "pl-free"
    elif pct >= 50:
        stroke = "#f59e0b"
        badge = "REFINEMENT RECOMMENDED"
        badge_cls = "pl-premium"
    else:
        stroke = "#f43f5e"
        badge = "CRITICAL GAPS DETECTED"
        badge_cls = "pl-weak"

    dim_labels = {
        "role_definition": "🎭 Role Definition",
        "specific_instructions": "🎯 Specific Instructions",
        "output_format": "📋 Output Format",
        "quality_markers": "💎 Quality Markers",
        "constraints": "🛡️ Constraints & Bounds",
    }

    dim_rows = []
    for key, label in dim_labels.items():
        found = practices.get(key, False)
        width = "100%" if found else "15%"
        bar_color = "#10b981" if found else "#f43f5e"
        status_txt = "✓ Pass" if found else "✗ Missing"
        dim_rows.append(
            f"<div style='margin-bottom:0.45rem;'>"
            f"  <div class='pl-dim-row'>"
            f"    <span>{html.escape(label)}</span>"
            f"    <span style='font-weight:700;color:{bar_color};font-size:0.78rem;'>{status_txt}</span>"
            f"  </div>"
            f"  <div class='pl-dim-bar-bg'><div class='pl-dim-bar-fill' style='width:{width};background:{bar_color};'></div></div>"
            f"</div>"
        )

    html_code = (
        f"<div class='pl-gauge-card'>"
        f"  <div class='pl-gauge-layout'>"
        f"    <div class='pl-gauge-circle-wrap'>"
        f"      <svg class='pl-gauge-svg' viewBox='0 0 120 120'>"
        f"        <circle class='pl-gauge-bg' cx='60' cy='60' r='54' />"
        f"        <circle class='pl-gauge-bar' cx='60' cy='60' r='54' stroke='{stroke}' stroke-dasharray='{circumference}' stroke-dashoffset='{offset}' />"
        f"      </svg>"
        f"      <div class='pl-gauge-inner'>"
        f"        <div class='pl-gauge-score'>{pct}%</div>"
        f"        <div class='pl-gauge-caption'>Health</div>"
        f"      </div>"
        f"    </div>"
        f"    <div class='pl-dim-list'>"
        f"      <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;'>"
        f"        <span style='font-weight:750;font-size:0.88rem;color:var(--pl-title);'>TRACE Framework Evaluation</span>"
        f"        <span class='pl-badge {badge_cls}' style='font-size:0.68rem;'>{badge}</span>"
        f"      </div>"
        f"      {''.join(dim_rows)}"
        f"    </div>"
        f"  </div>"
        f"</div>"
    )
    st.markdown(html_code, unsafe_allow_html=True)


def render_diff_view(original: str, improved: str) -> None:
    """Render an inline color-coded diff comparison between original and improved prompts."""
    import difflib
    import html

    orig_words = original.split()
    imp_words = improved.split()
    diff = difflib.ndiff(orig_words, imp_words)
    tokens = []
    for item in diff:
        code = item[:2]
        word = html.escape(item[2:])
        if code == "+ ":
            tokens.append(f"<span class='pl-diff-add'>{word}</span>")
        elif code == "- ":
            tokens.append(f"<span class='pl-diff-del'>{word}</span>")
        elif code == "  ":
            tokens.append(word)
    body = " ".join(tokens)
    st.markdown(f"<div class='pl-diff-card'>{body}</div>", unsafe_allow_html=True)


def extract_variables(prompt_text: str) -> list[str]:
    """Extract unique {variable_name} placeholders from a prompt string."""
    import re

    found = re.findall(r"\{([a-zA-Z0-9_]+)\}", prompt_text)
    seen = set()
    result = []
    for item in found:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def apply_modifier(prompt_text: str, modifier_type: str) -> str:
    """Quickly apply a production architectural modifier to a prompt."""
    text = prompt_text.strip()
    if modifier_type == "concise":
        return text + "\n\nConstraint: Be concise, direct, and eliminate all conversational preamble and unnecessary filler words."
    elif modifier_type == "cot":
        return text + "\n\nReasoning: Think step-by-step before answering. Break down your analysis into numbered, logical stages."
    elif modifier_type == "json":
        return text + "\n\nOutput Format: Return the final output strictly as a valid JSON object matching the schema. Do not enclose in markdown fences or conversational text."
    elif modifier_type == "guardrails":
        return text + "\n\nGuardrails: If required context is ambiguous or absent, state what is missing rather than guessing. Follow factual accuracy and cite reasoning."
    return text


def render_model_pipeline(active_provider: str = "groq") -> None:
    """Render the visual multi-model cascade pipeline."""
    act = active_provider.lower()
    groq_cls = "active" if act == "groq" else ""
    openai_cls = "active" if act == "openai" else ""
    gemini_cls = "active" if act in ("gemini", "google") else ""
    st.markdown(
        f"<div class='pl-pipeline'>"
        f"  <span style='font-size:0.74rem;font-weight:750;color:var(--pl-muted);text-transform:uppercase;'>Failover Cascade:</span>"
        f"  <span class='pl-pipeline-node {groq_cls}'>⚡ Groq LLaMA-3.3 (Primary)</span>"
        f"  <span class='pl-pipeline-arrow'>➔</span>"
        f"  <span class='pl-pipeline-node {openai_cls}'>🧠 OpenAI GPT-4o (Fallback 1)</span>"
        f"  <span class='pl-pipeline-arrow'>➔</span>"
        f"  <span class='pl-pipeline-node {gemini_cls}'>✨ Google Gemini (Fallback 2)</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_neural_hero(title: str, subtitle: str, badge: str = "🟢 KYRVYN NEURAL ENGINE v4.2 · ACTIVE") -> None:
    """Render an interactive HTML5 neural particle constellation canvas in the hero banner."""
    import html

    import streamlit.components.v1 as components

    clean_title = html.escape(title)
    clean_sub = html.escape(subtitle)
    clean_badge = html.escape(badge)

    canvas_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: transparent;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #f8fafc;
    height: 180px;
    position: relative;
    user-select: none;
  }}
  #c {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    z-index: 1;
  }}
  .hero-overlay {{
    position: relative;
    z-index: 2;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    pointer-events: none;
    padding: 0.5rem 1rem;
  }}
  .telemetry-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #a5b4fc;
    background: rgba(99, 102, 241, 0.18);
    border: 1px solid rgba(99, 102, 241, 0.4);
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
    box-shadow: 0 0 14px rgba(99, 102, 241, 0.3);
  }}
  .hero-title {{
    font-size: 2.15rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: linear-gradient(90deg, #ffffff 0%, #c7d2fe 25%, #818cf8 50%, #e879f9 75%, #ffffff 100%);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: sweep 7s linear infinite;
    line-height: 1.15;
    margin-bottom: 0.35rem;
  }}
  .hero-sub {{
    font-size: 0.95rem;
    color: #94a3b8;
    max-width: 680px;
    line-height: 1.5;
  }}
  @keyframes sweep {{
    0% {{ background-position: 0% center; }}
    100% {{ background-position: 200% center; }}
  }}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="hero-overlay">
  <div class="telemetry-chip">{clean_badge}</div>
  <h1 class="hero-title">{clean_title}</h1>
  <p class="hero-sub">{clean_sub}</p>
</div>
<script>
(function() {{
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  let w = canvas.width = window.innerWidth;
  let h = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {{
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }});

  const mouse = {{ x: null, y: null, radius: 120 }};
  window.addEventListener('mousemove', (e) => {{
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
  }});
  window.addEventListener('mouseleave', () => {{
    mouse.x = null;
    mouse.y = null;
  }});

  const nodes = [];
  const COUNT = Math.min(45, Math.floor(w / 20));
  for (let i = 0; i < COUNT; i++) {{
    nodes.push({{
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.9,
      vy: (Math.random() - 0.5) * 0.9,
      radius: Math.random() * 2 + 1.2,
      color: Math.random() > 0.5 ? 'rgba(99, 102, 241, ' : 'rgba(168, 85, 247, '
    }});
  }}

  function animate() {{
    ctx.clearRect(0, 0, w, h);

    for (let i = 0; i < nodes.length; i++) {{
      const n = nodes[i];
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > w) n.vx *= -1;
      if (n.y < 0 || n.y > h) n.vy *= -1;

      // Mouse attraction
      if (mouse.x !== null) {{
        const dx = mouse.x - n.x;
        const dy = mouse.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < mouse.radius) {{
          n.x += dx * 0.02;
          n.y += dy * 0.02;
        }}
      }}

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color + '0.85)';
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#6366f1';
      ctx.fill();

      // Connect lines
      for (let j = i + 1; j < nodes.length; j++) {{
        const n2 = nodes[j];
        const dx = n.x - n2.x;
        const dy = n.y - n2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 85) {{
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(n2.x, n2.y);
          const alpha = (1 - dist / 85) * 0.35;
          ctx.strokeStyle = 'rgba(99, 102, 241, ' + alpha + ')';
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }}
      }}
    }}
    requestAnimationFrame(animate);
  }}
  animate();
}})();
</script>
</body>
</html>"""
    components.html(canvas_html, height=185, scrolling=False)


def render_confetti() -> None:
    """Render a lightweight celebration particle burst for optimal scores."""
    import streamlit.components.v1 as components

    confetti_html = """<!DOCTYPE html>
<html>
<body style="margin:0;overflow:hidden;background:transparent;">
<canvas id="cf" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;"></canvas>
<script>
(function() {
  const c = document.getElementById('cf');
  const ctx = c.getContext('2d');
  c.width = window.innerWidth;
  c.height = 120;
  const p = [];
  const colors = ['#6366f1', '#a855f7', '#ec4899', '#10b981', '#38bdf8', '#f59e0b'];
  for (let i = 0; i < 70; i++) {
    p.push({
      x: c.width / 2 + (Math.random() - 0.5) * 120,
      y: 30,
      vx: (Math.random() - 0.5) * 12,
      vy: (Math.random() - 0.5) * 8 - 4,
      size: Math.random() * 5 + 3,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 1,
      rotation: Math.random() * 360,
      vRot: (Math.random() - 0.5) * 10
    });
  }
  function frame() {
    ctx.clearRect(0, 0, c.width, c.height);
    let alive = false;
    for (let i = 0; i < p.length; i++) {
      const it = p[i];
      it.x += it.vx;
      it.y += it.vy;
      it.vy += 0.25;
      it.rotation += it.vRot;
      it.alpha -= 0.015;
      if (it.alpha > 0) {
        alive = true;
        ctx.save();
        ctx.translate(it.x, it.y);
        ctx.rotate((it.rotation * Math.PI) / 180);
        ctx.fillStyle = it.color;
        ctx.globalAlpha = Math.max(0, it.alpha);
        ctx.fillRect(-it.size / 2, -it.size / 2, it.size, it.size);
        ctx.restore();
      }
    }
    if (alive) requestAnimationFrame(frame);
  }
  frame();
})();
</script>
</body>
</html>"""
    components.html(confetti_html, height=120, scrolling=False)

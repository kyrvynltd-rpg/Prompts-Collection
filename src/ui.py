"""Shared look and feel: responsive CSS, header and footer for all pages."""
import os
import sys
from pathlib import Path

import streamlit as st

import brand

CSS = """
<style>
.block-container { max-width: 1000px; padding-top: 1.5rem; }
.pl-hero h1 { margin-bottom: .2rem; }
.pl-sub { color: #6b7280; margin-bottom: 1.2rem; }
.pl-badge { display:inline-block; padding: .1rem .55rem; border-radius: 999px; font-size: .75rem; font-weight: 600; }
.pl-free { background:#e8f5ec; color:#146c2e; }
.pl-premium { background:#fff3d6; color:#8a5a00; }
.pl-card { border:1px solid rgba(128,128,128,.25); border-radius:12px; padding:1rem 1.1rem; margin-bottom:.8rem; }
.pl-weak { border-left: 4px solid #d9534f; padding:.5rem .8rem; background: rgba(217,83,79,.08); border-radius:6px; }
.pl-footer { text-align:center; color:#6b7280; font-size:.8rem; padding:1.5rem 0 .5rem; }
@media (max-width: 640px) {
  .block-container { padding: 1rem .8rem; }
  .pl-hero h1 { font-size: 1.5rem; }
  div[data-testid="stMetricValue"] { font-size: 1.4rem; }
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


def setup(title: str, icon: str = "💡") -> None:
    sync_runtime_env()
    st.set_page_config(page_title=f"{title} | Prompt Learning Platform", page_icon=icon, layout="wide",
                       initial_sidebar_state="collapsed")
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='pl-hero'><h1>{title}</h1><div class='pl-sub'>{subtitle}</div></div>", unsafe_allow_html=True)


def footer() -> None:
    st.markdown(
        f"<div class='pl-footer'>{brand.copyright_line()} {brand.company_line()} "
        f"<a href='{brand.site_url()}'>{brand.site_url().split('//')[-1]}</a><br>"
        "AI can be wrong: verify facts and follow your institution's AI policy.</div>",
        unsafe_allow_html=True,
    )


def badge(access: str) -> str:
    cls = "pl-free" if access == "free" else "pl-premium"
    label = "Free" if access == "free" else "Premium"
    return f"<span class='pl-badge {cls}'>{label}</span>"

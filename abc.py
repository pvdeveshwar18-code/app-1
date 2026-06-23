import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataScope – Distribution Analyser",
    page_icon="📊",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0f1117;
    color: #e8eaf0;
}

.main-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7c6ef8 0%, #48c7f0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.1rem;
}

.sub-title {
    color: #8891aa;
    font-size: 1rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: #1a1d2e;
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.5rem;
}

.metric-card h4 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.75rem;
    color: #8891aa;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 0.3rem 0;
}

.metric-card p {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: #e8eaf0;
}

.verdict-yes {
    background: linear-gradient(135deg, #0d2e1a 0%, #0d2a25 100%);
    border: 1px solid #1a5c38;
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    font-size: 0.95rem;
    color: #4ade80;
    font-weight: 600;
}

.verdict-no {
    background: linear-gradient(135deg, #2e0d0d 0%, #2a0d1a 100%);
    border: 1px solid #7f1d1d;
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    font-size: 0.95rem;
    color: #f87171;
    font-weight: 600;
}

.col-header {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #c4b5fd;
    border-bottom: 2px solid #2a2d3e;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}

.stFileUploader > label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem !important;
    font-weight: 600;
}

.section-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #8891aa;
    margin-bottom: 0.3rem;
}

div[data-testid="stMetric"] {
    background: #1a1d2e;
    border: 1px solid #2a2d3e;
    border-radius: 10px;
    padding: 0.8rem 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">📊 DataScope</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Upload an Excel file · get histograms · know if your data is forecast-ready</p>', unsafe_allow_html=True)

# ── Threshold slider ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    threshold = st.slider(
        "Mean–Median closeness threshold (%)",
        min_value=1, max_value=30, value=10,
        help="If |(mean − median) / mean| × 100 ≤ this %, data is flagged as forecast-ready."
    )
    bins = st.slider("Histogram bins", min_value=5, max_value=80, value=20)
    st.markdown("---")
    st.markdown("**What does 'forecast-ready' mean?**")
    st.caption(
        "When mean ≈ median the distribution is roughly symmetric (low skew). "
        "Many forecasting models assume this. A large gap usually signals outliers or heavy skew "
        "that need treatment before modelling."
    )

# ── File upload ───────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Drop your Excel file here (.xlsx / .xls)", type=["xlsx", "xls"])

if uploaded is None:
    st.info("⬆️  Upload an Excel file to begin analysis.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if not numeric_cols:
    st.warning("No numeric columns found in the uploaded file.")
    st.stop()

st.success(f"✅  Loaded **{len(df):,} rows × {len(df.columns)} columns** — {len(numeric_cols)} numeric column(s) detected.")

# ── Summary table ─────────────────────────────────────────────────────────────
with st.expander("🗂  Raw data preview", expanded=False):
    st.dataframe(df.head(50), use_container_width=True)

# ── Analysis ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## Column Analysis")

plt.style.use("dark_background")

for col in numeric_cols:
    series = df[col].dropna()
    if len(series) == 0:
        continue

    mean_val  = series.mean()
    median_val = series.median()
    std_val   = series.std()
    skew_val  = series.skew()

    # Pct difference relative to mean (handle zero mean)
    if mean_val != 0:
        pct_diff = abs((mean_val - median_val) / mean_val) * 100
    else:
        pct_diff = abs(mean_val - median_val) * 100

    forecast_ready = pct_diff <= threshold

    # ── Layout: metrics left, histogram right ──
    st.markdown(f'<p class="col-header">📈 {col}</p>', unsafe_allow_html=True)
    m_col, h_col = st.columns([1, 2.8])

    with m_col:
        st.metric("Mean",   f"{mean_val:,.4g}")
        st.metric("Median", f"{median_val:,.4g}")
        st.metric("Std Dev", f"{std_val:,.4g}")
        st.metric("Skewness", f"{skew_val:.3f}")
        st.metric("Mean–Median gap", f"{pct_diff:.2f}%")

        if forecast_ready:
            st.markdown(
                f'<div class="verdict-yes">✅ &nbsp;Forecast-ready<br>'
                f'<span style="font-weight:400;font-size:0.82rem;">Mean & median within {pct_diff:.1f}% — distribution is roughly symmetric.</span></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="verdict-no">⚠️ &nbsp;Skewed — review before forecasting<br>'
                f'<span style="font-weight:400;font-size:0.82rem;">Gap is {pct_diff:.1f}% (threshold {threshold}%). Consider log-transform or outlier removal.</span></div>',
                unsafe_allow_html=True
            )

    with h_col:
        fig, ax = plt.subplots(figsize=(7, 3.4))
        fig.patch.set_facecolor("#1a1d2e")
        ax.set_facecolor("#1a1d2e")

        counts, edges, patches = ax.hist(
            series, bins=bins,
            color="#7c6ef8", edgecolor="#0f1117", linewidth=0.4, alpha=0.88
        )

        # Mean & median lines
        ax.axvline(mean_val,   color="#48c7f0", linewidth=1.8, linestyle="--", label=f"Mean {mean_val:,.4g}")
        ax.axvline(median_val, color="#f472b6", linewidth=1.8, linestyle=":",  label=f"Median {median_val:,.4g}")

        ax.legend(fontsize=8, framealpha=0.25, loc="upper right")
        ax.set_xlabel(col, color="#8891aa", fontsize=9)
        ax.set_ylabel("Frequency", color="#8891aa", fontsize=9)
        ax.tick_params(colors="#8891aa", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2a2d3e")

        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
        buf.seek(0)
        st.image(buf, use_container_width=True)
        plt.close(fig)

    st.markdown("<br>", unsafe_allow_html=True)

# ── Overall summary ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🗒  Summary")

summary_rows = []
for col in numeric_cols:
    series = df[col].dropna()
    if len(series) == 0:
        continue
    mean_val   = series.mean()
    median_val = series.median()
    pct_diff   = abs((mean_val - median_val) / mean_val * 100) if mean_val != 0 else abs(mean_val - median_val) * 100
    summary_rows.append({
        "Column": col,
        "Mean": round(mean_val, 4),
        "Median": round(median_val, 4),
        "Skewness": round(series.skew(), 4),
        "Mean-Median Gap (%)": round(pct_diff, 2),
        "Forecast Ready": "✅ Yes" if pct_diff <= threshold else "⚠️ No"
    })

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ── Download summary ──────────────────────────────────────────────────────────
csv = summary_df.to_csv(index=False).encode()
st.download_button("⬇️  Download summary CSV", csv, "datascope_summary.csv", "text/csv")

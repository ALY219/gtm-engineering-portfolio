"""
Day 44 — GrowthFlow AI: Outbound Attribution Dashboard

A live Streamlit dashboard tracking:
- Lead enrichment funnel (Raw → Enriched → Hot → CRM)
- ICP score distribution
- Token usage & unit economics
- AI reasoning audit feed

Deployment fix: Uses Path(__file__).parent to anchor CSV path,
making it CWD-independent (works on local terminal AND Streamlit Cloud).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(page_title="GrowthFlow GTM Dashboard", layout="wide", page_icon="📊")

# ─── Load Data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    # Anchor path to this file's directory (fixes Streamlit Cloud CWD issue)
    csv_path = Path(__file__).parent / "enriched_leads.csv"
    df = pd.read_csv(csv_path)
    
    # Calculate paid-equivalent cost (Gemini 2.5 Flash pricing: $0.30/1M in, $2.50/1M out)
    df['cost_usd'] = (df['input_tokens'] / 1_000_000 * 0.30) + (df['output_tokens'] / 1_000_000 * 2.50)
    return df

df = load_data()

# ─── Header ────────────────────────────────────────────────────
st.title("📊 GrowthFlow AI: Outbound Attribution Dashboard")
st.markdown("*Real-time visibility into AI-scored lead enrichment and CRM routing.*")

# ─── Top Level KPIs (The "Executive View") ─────────────────────
col1, col2, col3, col4 = st.columns(4)

total_leads = len(df)
hot_leads = len(df[df['icp_score'] >= 70])
warm_leads = len(df[(df['icp_score'] >= 40) & (df['icp_score'] < 70)])
total_cost = df['cost_usd'].sum()

col1.metric("Total Leads Enriched", total_leads)
col2.metric("🔥 Hot Leads (SQLs)", hot_leads, f"{(hot_leads/total_leads)*100:.1f}% conversion")
col3.metric("🟡 Warm Leads (Nurture)", warm_leads)
col4.metric("AI Enrichment Cost", f"${total_cost:.4f}", help="Paid-equivalent token cost")

st.divider()

# ─── The Funnel Visualization ──────────────────────────────────
st.subheader("Lead Qualification Funnel")

funnel_data = pd.DataFrame({
    "Stage": ["Raw Domains", "Enriched (Context Found)", "Hot (Score ≥ 70)", "Pushed to HubSpot CRM"],
    "Count": [
        total_leads, 
        len(df[df['raw_context'] != "No recent news found."]), 
        hot_leads, 
        hot_leads  # Assuming 100% of hot leads were routed via Day 42 script
    ]
})

fig_funnel = go.Figure(go.Funnel(
    y=funnel_data["Stage"],
    x=funnel_data["Count"],
    textinfo="value+percent initial",
    marker=dict(color=["#808080", "#A9A9A9", "#FF4B4B", "#00A86B"])
))
fig_funnel.update_layout(margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig_funnel, use_container_width=True)

st.divider()

# ─── Lead Scoring Distribution ─────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("ICP Score Distribution")
    fig_hist = px.histogram(
        df, x="icp_score", nbins=10, color_discrete_sequence=["#4B0082"],
        title="Distribution of AI ICP Fit Scores (0-100)"
    )
    fig_hist.update_layout(xaxis_title="ICP Score", yaxis_title="Number of Leads")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_right:
    st.subheader("Token Usage vs. Score")
    fig_scatter = px.scatter(
        df, x="icp_score", y="output_tokens", size="input_tokens", color="icp_score",
        hover_name="domain", title="Does higher context yield higher scores?"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ─── The Data Table (Actionable Intel) ─────────────────────────
st.subheader("Lead Intelligence Feed")
st.markdown("*Click column headers to sort. Use this feed to manually verify AI reasoning before launching full-scale outbound.*")

# Clean up columns for display
display_df = df[['domain', 'icp_score', 'reasoning', 'email_hook', 'input_tokens', 'output_tokens']].copy()
display_df.columns = ['Domain', 'ICP Score', 'AI Reasoning', 'Suggested Email Hook', 'In Tokens', 'Out Tokens']

st.dataframe(
    display_df.sort_values(by='ICP Score', ascending=False),
    use_container_width=True,
    height=400
)

# ─── Footer ────────────────────────────────────────────────────
st.caption(f"Dashboard last updated: {df['enriched_at'].iloc[0]} | Powered by Gemini 2.5 Flash & Streamlit")
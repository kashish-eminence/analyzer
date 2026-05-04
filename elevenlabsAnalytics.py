import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="ElevenLabs Call Analytics", 
    page_icon="", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ─── Custom CSS for Professional Look ────────────────────────────
st.markdown("""
    <style>
    /* Dark professional theme overrides */
    .stApp {
        background-color: #0f172a;
    }
    h1, h2, h3, h4, p {
        color: #f8fafc;
    }
    .st-emotion-cache-1wivap2 { 
        color: #f8fafc; /* Adjust top header bar */
    }
    .metric-card {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    hr {
        border-color: #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────
st.title("ElevenLabs Call Analytics")
st.markdown("Detailed breakdown of AI Agent call volumes, status distribution, and LLM costs.")
st.markdown("---")

# ─── Data Loading ────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("elevenlabs_calls_april_2026.csv")
    df["llm_cost"] = pd.to_numeric(df["llm_cost"], errors="coerce").fillna(0)
    df["call_duration"] = pd.to_numeric(df["call_duration"], errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    
    agent_mapping = {
        "agent_9401k3fs5t8pfzqvbsjkcs6xwnze": "AutoSpark Assistant Inbound",
        "agent_01k0s4qchvea89jm5thv1t9mc6": "Aspire_Production_Inbound",
        "agent_4201kgj8xt8yeq4bkvah6ye6e52d": "Aspire Queensland Outbound",
        "agent_8001k9p40bp8fgda2475r0gwhfwp": "Aspire_outbound_WA",
        "agent_9001kgp5q4dyetxvh6aadtjryme8": "Bridgestone Inbound",
        "agent_9101ke69d2nsehxvves0kdpd98pb": "Danjoo_AI_Bot",
        "agent_7901kn7585h5f6xbs427arqqsg7x": "Centre Care"
    }
    df["agent_id"] = df["agent_id"].map(agent_mapping).fillna(df["agent_id"])
    
    return df

try:
    with st.spinner("Loading agent data..."):
        df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ─── Key Metrics Summary ─────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df):,}</div><div class="metric-label">Total AI Calls</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value">${df["llm_cost"].sum():.2f}</div><div class="metric-label">Total LLM Cost (USD)</div></div>', unsafe_allow_html=True)
with col3:
    avg_duration = df["call_duration"].mean()
    st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_duration:.0f}s</div><div class="metric-label">Avg. Call Duration</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ─── Row 1: Pie and Bar Charts (Side by Side) ────────────────────
colA, colB = st.columns([1, 1.2])

with colA:
    st.subheader("Agent Call Status")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    
    fig1 = px.pie(
        status_counts, 
        values="Count", 
        names="Status", 
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig1.update_traces(
        textposition='inside', 
        textinfo='percent+label', 
        marker=dict(line=dict(color='#0f172a', width=2)),
        hovertemplate="<b>%{label}</b><br>Calls: %{value}<br>Percentage: %{percent}<extra></extra>"
    )
    fig1.update_layout(
        template="plotly_dark", 
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig1, use_container_width=True)

with colB:
    st.subheader("Most Active Agents (Call Volume)")
    agent_counts = df["agent_id"].value_counts().head(10).reset_index()
    agent_counts.columns = ["Agent ID", "Count"]
    agent_counts = agent_counts.iloc[::-1]  # Reverse for proper horizontal display
    
    fig3 = px.bar(
        agent_counts, 
        x="Count", 
        y="Agent ID", 
        orientation='h',
        color="Count",
        color_continuous_scale="Viridis",
        text="Count"
    )
    fig3.update_traces(
        textposition='outside', 
        textfont=dict(color="white"),
        hovertemplate="<b>Agent ID:</b> %{y}<br><b>Total Calls:</b> %{x}<extra></extra>"
    )
    fig3.update_layout(
        template="plotly_dark", 
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20),
        coloraxis_showscale=False,
        yaxis_title=None,
        xaxis_title="Number of Calls"
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Row 2: Line Chart (Full Width) ──────────────────────────────
st.subheader("Daily LLM Cost by Top Agents (USD)")

top_cost_series = df.groupby("agent_id")["llm_cost"].sum().nlargest(5)
top_cost_agents = top_cost_series.index
daily_cost_pivot = df.pivot_table(index="date", columns="agent_id", values="llm_cost", aggfunc="sum", fill_value=0).reset_index()

fig2 = go.Figure()
colors = px.colors.qualitative.Vivid

for i, agent in enumerate(top_cost_agents):
    if agent in daily_cost_pivot.columns:
        fig2.add_trace(
            go.Scatter(
                x=daily_cost_pivot["date"], 
                y=daily_cost_pivot[agent], 
                mode="lines+markers",
                name=f"{agent} (Total: ${top_cost_series[agent]:.2f})",
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8, line=dict(width=1, color='white')),
                hovertemplate="<b>%{data.name}</b><br>Date: %{x}<br>Cost: $%{y:.2f}<extra></extra>"
            )
        )

fig2.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)", 
    paper_bgcolor="rgba(0,0,0,0)",
    height=550,
    hovermode="x unified",
    legend=dict(
        orientation="h", 
        yanchor="bottom", 
        y=1.05, 
        xanchor="center", 
        x=0.5,
        font=dict(size=13)
    ),
    margin=dict(l=20, r=20, t=60, b=20)
)
fig2.update_xaxes(title_text="Date", showgrid=True, gridcolor="rgba(255,255,255,0.05)")
fig2.update_yaxes(title_text="Cost (USD)", showgrid=True, gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig2, use_container_width=True)

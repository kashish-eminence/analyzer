import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="Call Data Analysis", 
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
st.title("Twilio Call Data Analysis")
st.markdown("Detailed breakdown of call volumes, status distribution, and associated costs over the last 30 days.")
st.markdown("---")

# ─── Data Loading ────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("twilio_last_month_5-1-2026_6-1-2026.csv")
    df["Price"] = df["Price"].astype(str).str.replace('"', '').astype(float).abs()
    # Convert USD to AUD (Exchange rate: 1 USD = 1.3912 AUD as of June 2026)
    df["Price"] = df["Price"] * 1.3912
    df["Date"] = pd.to_datetime(df["Date Created"], utc=True).dt.date
    df["From"] = df["From"].astype(str).str.replace('"', '').str.strip()
    return df

try:
    with st.spinner("Loading call data..."):
        df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ─── Key Metrics Summary ─────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df):,}</div><div class="metric-label">Total Calls</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value">A${df["Price"].sum():.2f}</div><div class="metric-label">Total Cost (AUD)</div></div>', unsafe_allow_html=True)
with col3:
    completed_pct = (df["Status"] == "Completed").mean() * 100
    st.markdown(f'<div class="metric-card"><div class="metric-value">{completed_pct:.1f}%</div><div class="metric-label">Completion Rate</div></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ─── Row 1: Pie and Bar Charts (Side by Side) ────────────────────
colA, colB = st.columns([1, 1.2])

with colA:
    st.subheader("Call Status Distribution")
    status_counts = df["Status"].value_counts().reset_index()
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
    st.subheader("Top 10 'From' Phone Numbers")
    from_counts = df["From"].value_counts().head(10).reset_index()
    from_counts.columns = ["From", "Count"]
    from_counts = from_counts.iloc[::-1]  # Reverse for proper horizontal display
    
    fig3 = px.bar(
        from_counts, 
        x="Count", 
        y="From", 
        orientation='h',
        color="Count",
        color_continuous_scale="Viridis",
        text="Count"
    )
    fig3.update_traces(
        textposition='outside', 
        textfont=dict(color="white"),
        hovertemplate="<b>Phone Number:</b> %{y}<br><b>Total Calls:</b> %{x}<extra></extra>"
    )
    fig3.update_layout(
        template="plotly_dark", 
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(l=20, r=20, t=30, b=20),
        coloraxis_showscale=False,
        yaxis_title=None,
        xaxis_title="Number of calls (+61876660527, +61879478573) used for Internal Testing"
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─── Row 2: Line Chart (Full Width) ──────────────────────────────
st.subheader("Daily Cost by Top Phone Numbers (AUD)")

top_cost_series = df.groupby("From")["Price"].sum().nlargest(5)
top_cost_numbers = top_cost_series.index
daily_cost_pivot = df.pivot_table(index="Date", columns="From", values="Price", aggfunc="sum", fill_value=0).reset_index()

fig2 = go.Figure()
colors = px.colors.qualitative.Vivid

for i, num in enumerate(top_cost_numbers):
    if num in daily_cost_pivot.columns:
        fig2.add_trace(
            go.Scatter(
                x=daily_cost_pivot["Date"], 
                y=daily_cost_pivot[num], 
                mode="lines+markers",
                name=f"{num} (Total: A${top_cost_series[num]:.2f})",
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8, line=dict(width=1, color='white')),
                hovertemplate="<b>%{data.name}</b><br>Date: %{x}<br>Cost: A$%{y:.2f}<extra></extra>"
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
fig2.update_yaxes(title_text="Cost (AUD)", showgrid=True, gridcolor="rgba(255,255,255,0.05)")

st.plotly_chart(fig2, use_container_width=True)

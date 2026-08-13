import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")

def calculate_drt(t, R, C):
    """Calculate DRT contribution for a single RC element"""
    tau = R * C
    sigma = 0.1  # Controls peak width
    return R * np.exp(-(np.log(t/tau))**2 / (2 * sigma**2))

def calculate_impedance(f, R, C):
    """Calculate complex impedance for a single RC element"""
    w = 2 * np.pi * f
    Z = R / (1 + 1j * w * R * C)
    return Z

# App title
st.title("Impedance & DRT Explorer")

# Create columns for parameter controls
col1, col2, col3 = st.columns(3)

# Parameter inputs - three RC elements standing in for three timescales
with col1:
    st.subheader("High-frequency (charge transfer)")
    R1 = st.slider("R₁ (Ω)", 10, 1000, 50, key="R1")
    C1 = st.slider("C₁ (F)", 1e-7, 1e-5, 1e-6,
                   format="%.1e", key="C1")

with col2:
    st.subheader("Mid-frequency (bulk transport)")
    R2 = st.slider("R₂ (Ω)", 100, 2000, 1000, key="R2")
    C2 = st.slider("C₂ (F)", 1e-6, 1e-4, 1e-4,
                   format="%.1e", key="C2")

with col3:
    st.subheader("Low-frequency (interface / diffusion)")
    R3 = st.slider("R₃ (Ω)", 50, 1000, 100, key="R3")
    C3 = st.slider("C₃ (F)", 1e-5, 1e-3, 1e-5,
                   format="%.1e", key="C3")

# Time and frequency arrays
tau = np.logspace(-6, 2, 1000)
freq = np.logspace(-2, 6, 1000)

# Calculate DRT contributions
gamma1 = calculate_drt(tau, R1, C1)
gamma2 = calculate_drt(tau, R2, C2)
gamma3 = calculate_drt(tau, R3, C3)
gamma_total = gamma1 + gamma2 + gamma3

# Calculate impedance
Z1 = calculate_impedance(freq, R1, C1)
Z2 = calculate_impedance(freq, R2, C2)
Z3 = calculate_impedance(freq, R3, C3)
Z_total = Z1 + Z2 + Z3

# Create subplots
fig = make_subplots(rows=2, cols=1,
                    subplot_titles=("Distribution of Relaxation Times (DRT)",
                                  "Nyquist Plot"),
                    vertical_spacing=0.2)

# DRT Plot
fig.add_trace(
    go.Scatter(x=tau, y=gamma1, name="High-frequency (charge transfer)",
               line=dict(color='#8884d8')), row=1, col=1)
fig.add_trace(
    go.Scatter(x=tau, y=gamma2, name="Mid-frequency (bulk transport)",
               line=dict(color='#82ca9d')), row=1, col=1)
fig.add_trace(
    go.Scatter(x=tau, y=gamma3, name="Low-frequency (interface / diffusion)",
               line=dict(color='#ffc658')), row=1, col=1)
fig.add_trace(
    go.Scatter(x=tau, y=gamma_total, name="Total",
               line=dict(color='#ff7300')), row=1, col=1)

# Nyquist Plot
fig.add_trace(
    go.Scatter(x=Z_total.real, y=-Z_total.imag,
               name="Impedance", line=dict(color='black')), row=2, col=1)

# Update layout
fig.update_xaxes(type="log", title="τ (seconds)", row=1, col=1)
fig.update_xaxes(title="Z' (Ω)", row=2, col=1)
fig.update_yaxes(title="γ(τ) (Ω/ln(s))", row=1, col=1)
fig.update_yaxes(title="-Z'' (Ω)", row=2, col=1)

fig.update_layout(
    height=800,
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Display the figure
st.plotly_chart(fig, use_container_width=True)

# Add frequency toggle for DRT
show_freq = st.checkbox("Show frequency instead of τ")
if show_freq:
    # Recalculate x-axis as frequency
    freq_x = 1/(2*np.pi*tau)

    fig_freq = make_subplots(rows=2, cols=1,
                            subplot_titles=("Distribution of Relaxation Times (DRT)",
                                          "Nyquist Plot"),
                            vertical_spacing=0.2)

    # DRT Plot with frequency
    fig_freq.add_trace(
        go.Scatter(x=freq_x, y=gamma1, name="High-frequency (charge transfer)",
                   line=dict(color='#8884d8')), row=1, col=1)
    fig_freq.add_trace(
        go.Scatter(x=freq_x, y=gamma2, name="Mid-frequency (bulk transport)",
                   line=dict(color='#82ca9d')), row=1, col=1)
    fig_freq.add_trace(
        go.Scatter(x=freq_x, y=gamma3, name="Low-frequency (interface / diffusion)",
                   line=dict(color='#ffc658')), row=1, col=1)
    fig_freq.add_trace(
        go.Scatter(x=freq_x, y=gamma_total, name="Total",
                   line=dict(color='#ff7300')), row=1, col=1)

    # Nyquist Plot remains the same
    fig_freq.add_trace(
        go.Scatter(x=Z_total.real, y=-Z_total.imag,
                   name="Impedance", line=dict(color='black')), row=2, col=1)

    # Update layout
    fig_freq.update_xaxes(type="log", title="Frequency (Hz)", row=1, col=1)
    fig_freq.update_xaxes(title="Z' (Ω)", row=2, col=1)
    fig_freq.update_yaxes(title="γ(τ) (Ω/ln(s))", row=1, col=1)
    fig_freq.update_yaxes(title="-Z'' (Ω)", row=2, col=1)

    fig_freq.update_layout(
        height=800,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_freq, use_container_width=True)

# Add some explanatory text
st.markdown("""
### About this dashboard
This interactive dashboard shows how a generic three-timescale electrochemical
cell responds to an impedance sweep. Three RC elements stand in for three
processes at different characteristic frequencies:

1. **High-frequency process**: fast charge transfer at an interface
2. **Mid-frequency process**: ionic / bulk transport through the material
3. **Low-frequency process**: a slow interfacial step (charge transfer or diffusion)

The DRT plot shows how each process contributes to the total impedance along the
relaxation-time axis, while the Nyquist plot shows the combined response you would
measure in an EIS experiment.
""")

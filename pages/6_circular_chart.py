import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Circos Sandbox", layout="wide")

st.title("Data Visualization: Circos Zodiac")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Testing environment for circular planetary mapping.</div>", unsafe_allow_html=True)
st.divider()

# --- ASTRONOMICAL DATA SETS ---
# 12 Rasis (30 degrees each)
RASIS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
RASIS_TA = ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"]

# 27 Nakshatras (13.333 degrees each)
NAKSHATRAS_EN = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

with st.sidebar:
    st.markdown("### Chart Controls")
    lang = st.radio("Language", ["English", "Tamil"])
    theme = st.radio("Color Theme", ["Executive Minimal", "Elemental Context"])

# Select language arrays
rasi_labels = RASIS_EN if lang == "English" else RASIS_TA
nak_labels = NAKSHATRAS_EN

# We use 360 degrees total. 
# 12 Rasis = 30 deg each. 27 Nakshatras = 13.33 deg each.
rasi_values = [30] * 12
nak_values = [13.333333] * 27

# --- COLOR PALETTES ---
if theme == "Executive Minimal":
    # Muted, highly professional greys and soft tones
    rasi_colors = ['#f8f9fa', '#f1f3f5'] * 6
    nak_colors = ['#e9ecef', '#dee2e6', '#ced4da'] * 9
    line_color = '#adb5bd'
else:
    # Colors based on Elements: Fire (Red), Earth (Green), Air (Blue), Water (Purple)
    rasi_colors = ['#FDEDEC', '#E8F5E9', '#EBF5FB', '#F5EEF8'] * 3 
    nak_colors = ['#FADBD8', '#C8E6C9', '#D6EAF8'] * 9
    line_color = '#ffffff'

# --- BUILD THE PLOTLY FIGURE ---
fig = go.Figure()

# 1. INNER RING: THE 12 RASIS
fig.add_trace(go.Pie(
    labels=rasi_labels,
    values=rasi_values,
    hole=0.45, # Creates the donut hole in the center
    direction='clockwise',
    sort=False, # Crucial: prevents Plotly from rearranging by size
    rotation=90, # Starts Aries at the absolute top center (or use 180 for Left/East)
    textinfo='label',
    textposition='inside',
    insidetextorientation='radial',
    domain={'x': [0.15, 0.85], 'y': [0.15, 0.85]}, # Defines ring thickness
    marker=dict(colors=rasi_colors, line=dict(color=line_color, width=1.5)),
    hoverinfo="label+percent",
    name="Rasi"
))

# 2. OUTER RING: THE 27 NAKSHATRAS
fig.add_trace(go.Pie(
    labels=nak_labels,
    values=nak_values,
    hole=0.75, # Larger hole to sit outside the Rasi ring
    direction='clockwise',
    sort=False,
    rotation=90,
    textinfo='label',
    textposition='inside',
    insidetextorientation='radial',
    domain={'x': [0, 1], 'y': [0, 1]}, # Takes up full width outside
    marker=dict(colors=nak_colors, line=dict(color=line_color, width=1)),
    hoverinfo="label",
    name="Nakshatra"
))

# 3. CENTER ICON & STYLING
fig.update_layout(
    margin=dict(t=20, b=20, l=20, r=20),
    showlegend=False,
    height=750,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    # Adding the minimalist icon/text in the absolute center
    annotations=[
        dict(
            text="✨", # You can replace this with an SVG path or image later
            x=0.5, y=0.53,
            font_size=40,
            showarrow=False
        ),
        dict(
            text="ZODIAC ENGINE",
            x=0.5, y=0.47,
            font_size=12,
            font_color="#888",
            font_family="Helvetica Neue",
            showarrow=False
        )
    ]
)

# --- RENDER IN STREAMLIT ---
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
### Next Steps for Circos Architecture:
1. **Planet Plotting:** We can pass longitude data into this chart to plot planets as "dots" sitting exactly on the specific degree of the specific Nakshatra.
2. **Aspect Ribbons:** Using Plotly's `go.Scatter` with spline lines, we can draw bezier curves across the empty center to show planets "aspecting" (looking at) each other.
3. **Interactivity:** Because this is Plotly, hovering over a Nakshatra can pop up a tooltip with its ruling planet, symbol, and current transits.
""")

import streamlit as st
import plotly.graph_objects as go
import math
import swisseph as swe
from datetime import datetime, time
from supabase import create_client

from astro_engine import get_location_coordinates, get_utc_offset

st.set_page_config(page_title="Circos Sandbox", layout="wide")

# --- SUPABASE PROFILE LOADING ---
@st.cache_resource
def init_connection():
    try: return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except: return None

supabase = init_connection()

def load_profiles_from_db():
    profiles = {}
    if supabase:
        try:
            response = supabase.table("profiles").select("*").execute()
            for row in response.data:
                try:
                    name, dob_str, tob_str, city = row["name"], row["dob"], row["tob"], row["city"]
                    parsed_dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                    try: parsed_tob = datetime.strptime(tob_str, "%H:%M:%S").time()
                    except ValueError: parsed_tob = datetime.strptime(tob_str, "%H:%M").time()
                    profiles[name] = {"dob": parsed_dob, "tob": parsed_tob, "city": city}
                except: pass
        except: pass
    return profiles

st.title("Data Visualization: Circos Zodiac")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Live mathematical plotting with dynamic Lagna 12 o'clock alignment.</div>", unsafe_allow_html=True)
st.divider()

# --- ASTRONOMICAL DATA SETS ---
RASIS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
RASIS_TA = ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"]

NAKSHATRAS_EN = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
NAKSHATRAS_TA = ["அஸ்வினி", "பரணி", "கிருத்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை", "புனர்பூசம்", "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "அஸ்தம்", "சித்திரை", "சுவாதி", "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்", "உத்திராடம்", "திருவோணம்", "அவிட்டம்", "சதயம்", "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"]

with st.sidebar:
    st.markdown("### Chart Controls")
    
    saved_profiles = load_profiles_from_db()
    profile_options = ["(Current Transit)"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Coordinates", profile_options)
    
    st.divider()
    lang = st.radio("Language", ["English", "Tamil"])
    theme = st.radio("Background Theme", ["Executive Minimal", "Elemental Context"])

# --- 1. CALCULATE LIVE PLANETARY LONGITUDES ---
swe.set_sid_mode(swe.SIDM_LAHIRI)
if selected_profile != "(Current Transit)":
    dt_obj = datetime.combine(saved_profiles[selected_profile]["dob"], saved_profiles[selected_profile]["tob"])
    city = saved_profiles[selected_profile]["city"]
else:
    dt_obj = datetime.now()
    city = "Chennai"

try: lat_val, lon_val, tz_val = get_location_coordinates(city)
except: lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata"

offset = get_utc_offset(tz_val, dt_obj)
jd_ut = swe.julday(dt_obj.year, dt_obj.month, dt_obj.day, (dt_obj.hour + (dt_obj.minute/60.0)) - offset)

# Core calculations
moon_lon = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
lagna_lon = swe.houses_ex(jd_ut, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1][0]

moon_rasi_idx = int(moon_lon / 30)
moon_nak_idx = int(moon_lon / (360/27))
lagna_rasi_idx = int(lagna_lon / 30)

# Other Planets
planet_ids = {"Sun": swe.SUN, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
planet_icons = {"Sun":"☀️", "Moon":"🌙", "Mars":"🔴", "Mercury":"🟢", "Jupiter":"🟡", "Venus":"💎", "Saturn":"⚫", "Rahu":"🐉", "Ketu":"🐍", "Asc":"🎯"}

positions = [{"name": "Moon", "lon": moon_lon, "icon": planet_icons["Moon"]}, {"name": "Asc", "lon": lagna_lon, "icon": planet_icons["Asc"]}]
for p_name, p_id in planet_ids.items():
    positions.append({"name": p_name, "lon": swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0], "icon": planet_icons[p_name]})

rahu_lon = next(p['lon'] for p in positions if p['name'] == 'Rahu')
positions.append({"name": "Ketu", "lon": (rahu_lon + 180) % 360, "icon": planet_icons["Ketu"]})

# --- 2. DYNAMIC CHART ROTATION (LOCK LAGNA TO 12 O'CLOCK) ---
# To make the Lagna start exactly at 12 o'clock, we calculate the required counter-clockwise offset.
pie_rotation = (360 - (lagna_rasi_idx * 30)) % 360

# --- 3. DYNAMIC HOUSE LABELS & HIGHLIGHTING ---
base_rasi_labels = RASIS_EN if lang == "English" else RASIS_TA
nak_labels = NAKSHATRAS_EN if lang == "English" else NAKSHATRAS_TA

custom_rasi_labels = []
for i in range(12):
    # Calculate House number (H1, H2...) relative to the Lagna
    house_num = (i - lagna_rasi_idx + 12) % 12 + 1
    custom_rasi_labels.append(f"<b>H{house_num}</b><br>{base_rasi_labels[i]}")

rasi_values = [30] * 12
nak_values = [360/27] * 27

if theme == "Executive Minimal":
    rasi_colors = ['#f8f9fa', '#f1f3f5'] * 6
    nak_colors = ['#e9ecef', '#dee2e6', '#ced4da'] * 9
    line_color = '#adb5bd'
else:
    rasi_colors = ['#FDEDEC', '#E8F5E9', '#EBF5FB', '#F5EEF8'] * 3 
    nak_colors = ['#FADBD8', '#C8E6C9', '#D6EAF8'] * 9
    line_color = '#ffffff'

COLOR_LAGNA = "#27ae60" # Green
COLOR_MOON = "#2980b9"  # Blue
COLOR_STAR = "#85c1e9"  # Light Blue

rasi_colors[lagna_rasi_idx] = COLOR_LAGNA
rasi_colors[moon_rasi_idx] = COLOR_MOON
if lagna_rasi_idx == moon_rasi_idx:
    rasi_colors[lagna_rasi_idx] = "#8e44ad"
nak_colors[moon_nak_idx] = COLOR_STAR

# --- 4. BUILD THE STATIC RINGS ---
fig = go.Figure()

# Inner Ring: Rasis (Dynamic Rotation Applied)
fig.add_trace(go.Pie(
    labels=custom_rasi_labels, values=rasi_values, hole=0.55, direction='clockwise',
    sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
    domain={'x': [0.15, 0.85], 'y': [0.15, 0.85]}, 
    marker=dict(colors=rasi_colors, line=dict(color=line_color, width=1.5)), hoverinfo="none", name="Rasi"
))

# Outer Ring: Nakshatras (Matches Rasi Rotation)
fig.add_trace(go.Pie(
    labels=nak_labels, values=nak_values, hole=0.82, direction='clockwise',
    sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
    domain={'x': [0, 1], 'y': [0, 1]}, 
    marker=dict(colors=nak_colors, line=dict(color=line_color, width=1)), hoverinfo="label", name="Nakshatra"
))

# --- 5. TRIGONOMETRY MAPPING FOR PLANETS ---
annotations = []
center_x, center_y, radius = 0.5, 0.5, 0.22 

for p in positions:
    # Math: We subtract the pie_rotation and the planet's longitude from 90° (12 o'clock Cartesian)
    # This guarantees the planets perfectly follow the rotated visual slices!
    theta_deg = 90 - pie_rotation - p['lon'] 
    theta_rad = math.radians(theta_deg)
    pos_x = center_x + radius * math.cos(theta_rad)
    pos_y = center_y + radius * math.sin(theta_rad)
    
    annotations.append(dict(
        x=pos_x, y=pos_y, text=p['icon'], font_size=24, showarrow=False,
        xanchor='center', yanchor='middle', # pixel-perfect centering
        hovertext=f"{p['name']}: {p['lon']:.1f}°", hoverlabel=dict(bgcolor="white")
    ))

# Central Profile Text
annotations.append(dict(
    text=f"<b>{selected_profile}</b><br><span style='font-size:12px;color:#888;'>Zodiac Engine</span>",
    x=0.5, y=0.5, font_size=16, font_family="Helvetica Neue", showarrow=False
))

fig.update_layout(
    margin=dict(t=20, b=20, l=20, r=20), showlegend=False,
    width=800, height=800, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    annotations=annotations
)

# --- 6. RENDER UI ---
col_chart, col_legend = st.columns([2.5, 1])

with col_chart:
    st.plotly_chart(fig, use_container_width=True)

with col_legend:
    lbl_lagna = "Ascendant (H1) 🎯" if lang == "English" else "லக்னம் (H1) 🎯"
    lbl_moon = "Moon Sign (Rasi) 🌙" if lang == "English" else "ராசி (Moon Sign) 🌙"
    lbl_star = "Moon Star (Nakshatra) ✨" if lang == "English" else "நட்சத்திரம் (Star) ✨"
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("### Highlight Legend")
    st.markdown(f"""
    <div style="background:#fff; border:1px solid #eee; padding:15px; border-radius:6px; margin-bottom:10px;">
        <div style="font-size:11px; color:#888; text-transform:uppercase; font-weight:bold; letter-spacing:1px; margin-bottom:5px;">{lbl_lagna}</div>
        <div style="display:flex; align-items:center;">
            <div style="width:14px; height:14px; background:{COLOR_LAGNA}; border-radius:3px; margin-right:8px;"></div>
            <div style="font-size:16px; font-weight:500; color:#2c3e50;">{base_rasi_labels[lagna_rasi_idx]}</div>
        </div>
        <div style="font-size:12px; color:#666; margin-top:4px;">Locks to the 12 o'clock position (House 1). Dictates the physical self.</div>
    </div>
    
    <div style="background:#fff; border:1px solid #eee; padding:15px; border-radius:6px; margin-bottom:10px;">
        <div style="font-size:11px; color:#888; text-transform:uppercase; font-weight:bold; letter-spacing:1px; margin-bottom:5px;">{lbl_moon}</div>
        <div style="display:flex; align-items:center;">
            <div style="width:14px; height:14px; background:{COLOR_MOON}; border-radius:3px; margin-right:8px;"></div>
            <div style="font-size:16px; font-weight:500; color:#2c3e50;">{base_rasi_labels[moon_rasi_idx]}</div>
        </div>
        <div style="font-size:12px; color:#666; margin-top:4px;">Dictates the psychological operating system and emotional baseline.</div>
    </div>
    
    <div style="background:#fff; border:1px solid #eee; padding:15px; border-radius:6px; margin-bottom:10px;">
        <div style="font-size:11px; color:#888; text-transform:uppercase; font-weight:bold; letter-spacing:1px; margin-bottom:5px;">{lbl_star}</div>
        <div style="display:flex; align-items:center;">
            <div style="width:14px; height:14px; background:{COLOR_STAR}; border-radius:3px; margin-right:8px;"></div>
            <div style="font-size:16px; font-weight:500; color:#2c3e50;">{nak_labels[moon_nak_idx]}</div>
        </div>
        <div style="font-size:12px; color:#666; margin-top:4px;">The 13.33° micro-constellation governing mental processing and Dasha timelines.</div>
    </div>
    """, unsafe_allow_html=True)
    
    if lagna_rasi_idx == moon_rasi_idx:
        st.markdown(f"<div style='background:#fcf3ff; border:1px solid #e8daef; padding:10px; border-radius:6px; font-size:12px; color:#8e44ad; font-weight:500;'>🪐 <b>Alignment Detected:</b> Lagna and Moon occupy the same Rasi, highlighted in deep purple on the chart.</div>", unsafe_allow_html=True)

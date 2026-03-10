import streamlit as st
import plotly.graph_objects as go
import math
import swisseph as swe
from datetime import datetime, time
from supabase import create_client

from astro_engine import get_location_coordinates, get_utc_offset

st.set_page_config(page_title="Dynamic Aspect Engine", layout="wide")

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

# --- DYNAMIC EXECUTIVE INSIGHT GENERATOR ---
def get_aspect_insight(p1, p2, aspect_type):
    pair = {p1, p2}
    
    if "7th" in aspect_type:
        dyn, action, act_class = "Direct Confrontation / Reflection", "MITIGATE RISK", "tag-mitigate"
    elif "5th" in aspect_type:
        dyn, action, act_class = "Frictionless Synergy / Dharma", "HARNESS STRENGTH", "tag-harness"
    else:
        dyn, action, act_class = "Structural Tension / Karma", "MITIGATE RISK", "tag-mitigate"
        
    if {"Sun", "Moon"} == pair:
        desc = "The core identity (Sun) and emotional operating system (Moon) are directly interacting."
        rem = "Balance executive logic with intuition. Do not let ego override team morale."
    elif {"Mars", "Venus"} == pair:
        desc = "High-octane creative and aggressive energy. Passion meets execution."
        rem = "Channel this intense energy into product development. Avoid impulsive financial decisions."
    elif {"Jupiter", "Rahu"} == pair or {"Jupiter", "Ketu"} == pair:
        desc = "Unconventional expansion (Guru-Chandal energy). Rapid scaling but with hidden risks."
        rem = "Ensure legal and ethical compliance during aggressive business scaling."
    elif {"Saturn", "Mars"} == pair:
        desc = "The ultimate friction: Unstoppable force meets immovable object."
        rem = "Extreme patience required. Delays will happen; force will break the system. Methodical execution wins."
    elif {"Mercury", "Jupiter"} == pair:
        desc = "High-level strategic thinking. Data (Mercury) aligns with wisdom (Jupiter)."
        rem = "Perfect window for negotiations, contract drafting, and long-term planning."
    elif "Asc" in pair:
        planet = list(pair - {"Asc"})[0]
        desc = f"The physical brand/self (Lagna) is heavily influenced by the energy of {planet}."
        rem = f"Project this {planet} energy explicitly in your personal branding and leadership style."
    else:
        desc = f"Complex energy exchange between {p1}'s agenda and {p2}'s agenda."
        rem = f"Acknowledge both forces. Use the {dyn} to find a middle ground in operations."

    return dyn, action, act_class, desc, rem

# --- UI HEADER & TOP CONTROLS ---
st.title("Data Visualization: Circos Zodiac")
st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Multi-chord planetary trigonometry with 108 Nakshatra Padas.</div>", unsafe_allow_html=True)

# TOP FILTER: The Aspect Control
st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Active Planetary Aspects</div>", unsafe_allow_html=True)
view_filter = st.radio("Aspect Filter", ["Oppositions (7th House)", "Trines (5th / 9th House)", "Squares (4th / 10th House)", "Conjunctions (Same House)"], horizontal=True, label_visibility="collapsed")
st.divider()

# --- ASTRONOMICAL DATA SETS ---
RASIS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
RASIS_TA = ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"]
NAKSHATRAS_EN = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
NAKSHATRAS_TA = ["அஸ்வினி", "பரணி", "கிருத்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை", "புனர்பூசம்", "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "அஸ்தம்", "சித்திரை", "சுவாதி", "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்", "உத்திராடம்", "திருவோணம்", "அவிட்டம்", "சதயம்", "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"]

# 108 Padas (1, 2, 3, 4 repeating)
PADAS = ["1", "2", "3", "4"] * 27

with st.sidebar:
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>Profile Coordinates</div>", unsafe_allow_html=True)
    saved_profiles = load_profiles_from_db()
    profile_options = ["(Current Transit)"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Coordinates", profile_options, label_visibility="collapsed")
    
    st.divider()
    lang = st.radio("Language", ["English", "Tamil"])
    theme = st.radio("Background Theme", ["Executive Minimal", "Elemental Context"])

# --- CALCULATE LIVE PLANETARY LONGITUDES ---
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

lagna_lon = swe.houses_ex(jd_ut, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1][0]
lagna_rasi_idx = int(lagna_lon / 30)

planet_ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
planet_icons = {"Sun":"☀️", "Moon":"🌙", "Mars":"🔴", "Mercury":"🟢", "Jupiter":"🟡", "Venus":"💎", "Saturn":"⚫", "Rahu":"🐉", "Ketu":"🐍", "Asc":"🎯"}

positions = [{"name": "Asc", "lon": lagna_lon, "icon": planet_icons["Asc"], "rasi": lagna_rasi_idx}]
for p_name, p_id in planet_ids.items():
    lon = swe.calc_ut(jd_ut, p_id, swe.FLG_SIDEREAL)[0][0]
    positions.append({"name": p_name, "lon": lon, "icon": planet_icons[p_name], "rasi": int(lon / 30)})

rahu_lon = next(p['lon'] for p in positions if p['name'] == 'Rahu')
positions.append({"name": "Ketu", "lon": (rahu_lon + 180) % 360, "icon": planet_icons["Ketu"], "rasi": int(((rahu_lon + 180) % 360) / 30)})

# --- DYNAMIC CHART ROTATION ---
pie_rotation = (360 - (lagna_rasi_idx * 30)) % 360

# --- 3-TIER STATIC RINGS SETUP ---
base_rasi_labels = RASIS_EN if lang == "English" else RASIS_TA
nak_labels = NAKSHATRAS_EN if lang == "English" else NAKSHATRAS_TA
custom_rasi_labels = [f"<b>H{(i - lagna_rasi_idx + 12) % 12 + 1}</b><br>{base_rasi_labels[i]}" for i in range(12)]

if theme == "Executive Minimal":
    rasi_colors = ['#f8f9fa', '#f1f3f5'] * 6
    nak_colors = ['#e9ecef', '#dee2e6', '#ced4da'] * 9
    pada_colors = ['#fdfdfe', '#f8f9fa'] * 54
    line_color = '#adb5bd'
else:
    rasi_colors = ['#FDEDEC', '#E8F5E9', '#EBF5FB', '#F5EEF8'] * 3 
    nak_colors = ['#FADBD8', '#C8E6C9', '#D6EAF8'] * 9
    pada_colors = ['#ffffff', '#fcfcfc'] * 54
    line_color = '#ffffff'

# --- BUILD THE PLOTLY FIGURE ---
fig = go.Figure()

# Tier 1: Inner Ring (Rasis)
fig.add_trace(go.Pie(
    labels=custom_rasi_labels, values=[30]*12, hole=0.55, direction='clockwise',
    sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
    domain={'x': [0.22, 0.78], 'y': [0.22, 0.78]}, 
    marker=dict(colors=rasi_colors, line=dict(color=line_color, width=1.5)), hoverinfo="none", name="Rasi"
))

# Tier 2: Middle Ring (Nakshatras)
fig.add_trace(go.Pie(
    labels=nak_labels, values=[360/27]*27, hole=0.82, direction='clockwise',
    sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
    domain={'x': [0.08, 0.92], 'y': [0.08, 0.92]}, 
    marker=dict(colors=nak_colors, line=dict(color=line_color, width=1)), hoverinfo="label", name="Nakshatra"
))

# Tier 3: Outer Ring (108 Padas)
fig.add_trace(go.Pie(
    labels=PADAS, values=[360/108]*108, hole=0.93, direction='clockwise',
    sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
    textfont=dict(size=9, color="#666"),
    domain={'x': [0, 1], 'y': [0, 1]}, 
    marker=dict(colors=pada_colors, line=dict(color='#eaeaea', width=0.5)), hoverinfo="label", name="Pada"
))

# --- TRIGONOMETRY FOR ICONS AND RIBBONS ---
annotations = []
center_x, center_y, radius = 0.5, 0.5, 0.20 

# Planet Coordinates
for p in positions:
    theta_deg = 90 - pie_rotation - p['lon'] 
    theta_rad = math.radians(theta_deg)
    p['x'] = center_x + radius * math.cos(theta_rad)
    p['y'] = center_y + radius * math.sin(theta_rad)
    
    annotations.append(dict(
        x=p['x'], y=p['y'], text=p['icon'], font_size=22, showarrow=False,
        xanchor='center', yanchor='middle',
        hovertext=f"{p['name']}: {p['lon']:.1f}°", hoverlabel=dict(bgcolor="white")
    ))

# --- DYNAMIC CHORD / ASPECT RIBBONS ---
aspect_pairs = []
drawn_pairs = set()

target_distances = []
ribbon_color = "rgba(189, 195, 199, 0.5)" 
if "7th" in view_filter:
    target_distances = [6]
    ribbon_color = "rgba(192, 57, 43, 0.6)" # Deep Red
elif "5th" in view_filter:
    target_distances = [4, 8]
    ribbon_color = "rgba(39, 174, 96, 0.6)" # Green
elif "4th" in view_filter:
    target_distances = [3, 9]
    ribbon_color = "rgba(41, 128, 185, 0.6)" # Blue
elif "Conjunction" in view_filter:
    target_distances = [0]
    ribbon_color = "rgba(142, 68, 173, 0.6)" # Purple

for p1 in positions:
    for p2 in positions:
        if p1['name'] == p2['name']: continue
        
        pair_key = tuple(sorted([p1['name'], p2['name']]))
        if pair_key in drawn_pairs: continue

        dist = (p2['rasi'] - p1['rasi'] + 12) % 12
        
        if dist in target_distances:
            drawn_pairs.add(pair_key)
            aspect_pairs.append((p1['name'], p2['name']))
            
            if dist == 0:
                # Conjunction: Short curved line outside the center
                fig.add_trace(go.Scatter(
                    x=[p1['x'], center_x + (p1['x']-center_x)*0.5, p2['x']], 
                    y=[p1['y'], center_y + (p1['y']-center_y)*0.5, p2['y']],
                    mode='lines', line=dict(color=ribbon_color, width=3, shape='spline'),
                    hoverinfo='text', text=f"{p1['name']} + {p2['name']} (Conjunction)", showlegend=False
                ))
            else:
                # Aspect: Draw a smooth curved chord through the center
                fig.add_trace(go.Scatter(
                    x=[p1['x'], center_x, p2['x']], y=[p1['y'], center_y, p2['y']],
                    mode='lines', line=dict(color=ribbon_color, width=2.5, shape='spline'),
                    hoverinfo='text', text=f"{p1['name']} ↔ {p2['name']} ({view_filter})", showlegend=False
                ))

# Central Profile Text
annotations.append(dict(
    text=f"<b>{selected_profile}</b><br><span style='font-size:11px;color:#888;'>Dynamic Aspect Engine</span>",
    x=0.5, y=0.5, font_size=16, font_family="Helvetica Neue", showarrow=False
))

fig.update_layout(
    margin=dict(t=0, b=0, l=0, r=0), showlegend=False,
    width=750, height=750, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    annotations=annotations
)

# --- RENDER CHART (CENTERED) ---
col_space1, col_center, col_space2 = st.columns([1, 2.5, 1])
with col_center:
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- RENDER DYNAMIC INSIGHT CARDS (EXECUTIVE UI) BELOW ---
st.markdown(f"<h3 style='margin-bottom:20px; color:#2c3e50;'>{view_filter.split(' ')[0]} Forecasts</h3>", unsafe_allow_html=True)

if not aspect_pairs:
    st.info(f"No exact {view_filter} alignments detected in this specific chart configuration.")
else:
    css_block = """<style>
    .bp-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .bp-card { background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }
    .bp-head { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }
    .bp-title { font-size: 18px; font-weight: 500; color: #2c3e50; margin-bottom: 6px; }
    .bp-desc { font-size: 13.5px; color: #444; line-height: 1.5; font-weight: 300; margin-bottom:12px; }
    .tag-harness { display:inline-block; font-size: 10.5px; color: #2E7D32; background: #E8F5E9; border: 1px solid #C8E6C9; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
    .tag-mitigate { display:inline-block; font-size: 10.5px; color: #C0392B; background: #FDEDEC; border: 1px solid #FADBD8; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
    .insight-text { font-size: 13.5px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f5f5f5; }
    </style>"""
    st.markdown(css_block, unsafe_allow_html=True)

    grid_html = """<div class="bp-grid">"""
    card_border = "#e74c3c" if "7th" in view_filter else "#27ae60" if "5th" in view_filter else "#2980b9" if "4th" in view_filter else "#8e44ad"
    
    for p1, p2 in aspect_pairs:
        dyn, action, act_class, desc, rem = get_aspect_insight(p1, p2, view_filter)
        
        grid_html += f"""
        <div class="bp-card" style="border-top: 3px solid {card_border};">
            <div class="bp-head"><span>Planetary Connection</span> <span style="color:{card_border}; font-weight:bold;">{dyn}</span></div>
            <div class="bp-title">{planet_icons.get(p1, '')} {p1} &nbsp;↔&nbsp; {planet_icons.get(p2, '')} {p2}</div>
            <div class="bp-desc">{desc}</div>
            <div style="margin-top:auto; padding-top:12px; border-top: 1px dashed #eee;">
                <div class="{act_class}">{action}</div>
                <div class="insight-text">{rem}</div>
            </div>
        </div>"""
        
    grid_html += "</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

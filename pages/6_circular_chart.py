import streamlit as st
import plotly.graph_objects as go
import math
import swisseph as swe
from datetime import datetime, time
from supabase import create_client

from astro_engine import get_location_coordinates, get_utc_offset

st.set_page_config(page_title="Dynamic Aspect Engine", layout="wide")

# --- SECURITY GATEKEEPER ---
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Please log in to access the Zodiac Flow Engine.")
    st.stop()

user_id = st.session_state.user.id

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
            # ONLY fetch profiles belonging to this user
            response = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
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
    elif "4th" in aspect_type:
        dyn, action, act_class = "Structural Tension / Karma", "MITIGATE RISK", "tag-mitigate"
    else:
        dyn, action, act_class = "Amplification / Fusion", "HARNESS STRENGTH", "tag-harness"
        
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

# --- ASTRONOMICAL DATA SETS ---
RASIS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
RASIS_TA = ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"]
NAKSHATRAS_EN = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
NAKSHATRAS_TA = ["அஸ்வினி", "பரணி", "கிருத்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை", "புனர்பூசம்", "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "அஸ்தம்", "சித்திரை", "சுவாதி", "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்", "உத்திராடம்", "திருவோணம்", "அவிட்டம்", "சதயம்", "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"]
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

pie_rotation = (90 + (lagna_rasi_idx * 30)) % 360

# --- MASTER LAYOUT SPLIT (60% CHART / 40% INSIGHTS) ---
col_viz, col_data = st.columns([1.5, 1], gap="large")

with col_viz:
    st.title("Zodiac Flow Engine")
    st.markdown("<div style='color:#7f8c8d; margin-top:-15px; margin-bottom: 20px;'>Multi-chord planetary trigonometry representing real-time astrological energy flow.</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='font-size: 11px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Active Energy Flow (Aspects)</div>", unsafe_allow_html=True)
    view_filter = st.radio("Aspect Filter", ["Oppositions (7th House)", "Trines (5th / 9th House)", "Squares (4th / 10th House)", "Conjunctions (Same House)"], horizontal=True, label_visibility="collapsed")
    st.write("") # spacing

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

    fig = go.Figure()

    # Tier 3: Outer Ring (108 Padas)
    fig.add_trace(go.Pie(
        labels=PADAS, values=[360/108]*108, hole=0.94, direction='clockwise',
        sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
        textfont=dict(size=8, color="#666"), domain={'x': [0, 1], 'y': [0, 1]}, 
        marker=dict(colors=pada_colors, line=dict(color='#eaeaea', width=0.5)), hoverinfo="none", name="Pada"
    ))

    # Tier 2: Middle Ring (Nakshatras)
    fig.add_trace(go.Pie(
        labels=nak_labels, values=[360/27]*27, hole=0.851, direction='clockwise',
        sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
        domain={'x': [0.03, 0.97], 'y': [0.03, 0.97]}, textfont=dict(size=10),
        marker=dict(colors=nak_colors, line=dict(color=line_color, width=1)), hoverinfo="label", name="Nakshatra"
    ))

    # Tier 1: Inner Ring (Rasis)
    fig.add_trace(go.Pie(
        labels=custom_rasi_labels, values=[30]*12, hole=0.6875, direction='clockwise',
        sort=False, rotation=pie_rotation, textinfo='label', textposition='inside', insidetextorientation='radial',
        domain={'x': [0.10, 0.90], 'y': [0.10, 0.90]}, textfont=dict(size=12),
        marker=dict(colors=rasi_colors, line=dict(color=line_color, width=1.5)), hoverinfo="none", name="Rasi"
    ))

    # --- TRIGONOMETRY FOR ICONS AND TRUE CHORD RIBBONS ---
    annotations = []
    planet_r = 0.46 
    chord_r = 0.41 

    for p in positions:
        theta_deg = 90 - pie_rotation - p['lon'] 
        theta_rad = math.radians(theta_deg)
        p['theta_rad'] = theta_rad
        p['x'] = planet_r * math.cos(theta_rad)
        p['y'] = planet_r * math.sin(theta_rad)
        
        annotations.append(dict(
            x=p['x'], y=p['y'], text=p['icon'], font_size=22, showarrow=False,
            xref='x', yref='y', xanchor='center', yanchor='middle',
            hovertext=f"{p['name']}: {p['lon']:.1f}°", hoverlabel=dict(bgcolor="white")
        ))

    aspect_pairs = []
    drawn_pairs = set()
    shapes = []

    if "7th" in view_filter: target_dist, chord_color = [6], "rgba(192, 57, 43, 0.4)" 
    elif "5th" in view_filter: target_dist, chord_color = [4, 8], "rgba(39, 174, 96, 0.4)" 
    elif "4th" in view_filter: target_dist, chord_color = [3, 9], "rgba(41, 128, 185, 0.4)" 
    elif "Conjunction" in view_filter: target_dist, chord_color = [0], "rgba(142, 68, 173, 0.4)" 

    for p1 in positions:
        for p2 in positions:
            if p1['name'] == p2['name']: continue
            pair_key = tuple(sorted([p1['name'], p2['name']]))
            if pair_key in drawn_pairs: continue

            dist = (p2['rasi'] - p1['rasi'] + 12) % 12
            if dist in target_dist:
                drawn_pairs.add(pair_key)
                aspect_pairs.append((p1['name'], p2['name']))
                
                t1, t2 = p1['theta_rad'], p2['theta_rad']
                delta = 0.06 
                
                x1a, y1a = chord_r * math.cos(t1 - delta), chord_r * math.sin(t1 - delta)
                x1b, y1b = chord_r * math.cos(t1 + delta), chord_r * math.sin(t1 + delta)
                x2a, y2a = chord_r * math.cos(t2 + delta), chord_r * math.sin(t2 + delta)
                x2b, y2b = chord_r * math.cos(t2 - delta), chord_r * math.sin(t2 - delta)
                
                if dist == 0:
                    ctrl_r = 0.15
                    cx, cy = ctrl_r * math.cos(t1), ctrl_r * math.sin(t1)
                else:
                    cx, cy = 0, 0 
                    
                path_str = f"M {x1a},{y1a} Q {cx},{cy} {x2b},{y2b} L {x2a},{y2a} Q {cx},{cy} {x1b},{y1b} Z"
                
                shapes.append(dict(
                    type="path", path=path_str, fillcolor=chord_color, 
                    line=dict(color=chord_color, width=0.5), layer="below",
                    xref='x', yref='y'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[p1['x'], 0, p2['x']], y=[p1['y'], 0, p2['y']],
                    mode='lines', line=dict(color='rgba(0,0,0,0)', width=15),
                    hoverinfo='text', text=f"Flow: {p1['name']} ↔ {p2['name']}", showlegend=False
                ))

    annotations.append(dict(
        text=f"<b>{selected_profile}</b><br><span style='font-size:12px;color:#888;'>Astrological Core</span>",
        x=0.5, y=0.5, xref='paper', yref='paper',
        font_size=18, font_family="Helvetica Neue", showarrow=False, xanchor='center', yanchor='middle'
    ))

    fig.update_layout(
        xaxis=dict(visible=False, range=[-1, 1], fixedrange=True),
        yaxis=dict(visible=False, range=[-1, 1], fixedrange=True, scaleanchor="x", scaleratio=1),
        margin=dict(t=20, b=20, l=20, r=20), showlegend=False,
        height=900, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        annotations=annotations, shapes=shapes
    )

    st.plotly_chart(fig, use_container_width=True)

# --- RIGHT PANEL (THE INTERPRETATION ENGINE) ---
with col_data:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Architecture Guide")
    
    st.markdown("""
    <style>
    .guide-box { background:#fbfcfc; border:1px solid #eee; padding:15px; border-radius:6px; margin-bottom:12px; }
    .guide-title { font-size:11px; color:#888; text-transform:uppercase; font-weight:bold; letter-spacing:1px; margin-bottom:5px; }
    .guide-text { font-size:13.5px; color:#444; line-height:1.5; font-weight:300; }
    </style>
    
    <div class="guide-box">
        <div class="guide-title">Tier 1: The Macro (Inner Ring)</div>
        <div class="guide-text">The 12 <b>Rasis (Zodiac Signs)</b> spanning 30° each. The chart mathematically rotates to ensure House 1 (Your Ascendant/Lagna) always locks exactly to the 12 o'clock position.</div>
    </div>
    
    <div class="guide-box">
        <div class="guide-title">Tier 2: The Constellations (Middle Ring)</div>
        <div class="guide-text">The 27 <b>Nakshatras (Lunar Mansions)</b> spanning 13°20' each. These represent the deep psychological wiring dictating planetary behavior.</div>
    </div>
    
    <div class="guide-box">
        <div class="guide-title">Tier 3: The Micro (Outer Ring)</div>
        <div class="guide-text">The 108 <b>Padas (Quarters)</b>. Each Nakshatra is divided into 4 segments of 3°20', allowing for razor-sharp predictive accuracy in the D9 chart.</div>
    </div>
    
    <div class="guide-box" style="border-left: 3px solid #8e44ad;">
        <div class="guide-title">The Energy Ribbons (Chords)</div>
        <div class="guide-text">The colored Bezier curves simulate the transfer of energy (Aspects) between planetary nodes. Use the toggle above to isolate different types of tension or synergy.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown(f"<h3 style='margin-bottom:15px; color:#2c3e50;'>{view_filter.split(' ')[0]} Forecasts</h3>", unsafe_allow_html=True)

    if not aspect_pairs:
        st.info(f"No {view_filter} alignments detected in this specific layout.")
    else:
        css_block = """<style>
        .bp-grid-col { display: grid; grid-template-columns: 1fr; gap: 16px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
        .bp-card { background: #ffffff; border: 1px solid #eaeaea; border-radius: 4px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.01); }
        .bp-head { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #888; font-weight: 500; margin-bottom: 12px; border-bottom: 1px solid #f9f9f9; padding-bottom: 6px; display: flex; justify-content: space-between; }
        .bp-title { font-size: 17px; font-weight: 500; color: #2c3e50; margin-bottom: 6px; }
        .bp-desc { font-size: 13.5px; color: #444; line-height: 1.5; font-weight: 300; margin-bottom:12px; }
        .tag-harness { display:inline-block; font-size: 10.5px; color: #2E7D32; background: #E8F5E9; border: 1px solid #C8E6C9; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
        .tag-mitigate { display:inline-block; font-size: 10.5px; color: #C0392B; background: #FDEDEC; border: 1px solid #FADBD8; padding: 2px 6px; border-radius: 3px; font-weight: 600; margin-bottom: 6px; letter-spacing: 0.5px;}
        .insight-text { font-size: 13px; color: #222; font-style: italic; background: #fafafa; padding: 10px; border-radius: 4px; border: 1px solid #f5f5f5; }
        </style>"""
        st.markdown(css_block, unsafe_allow_html=True)

        grid_html = """<div class="bp-grid-col">"""
        card_border = "#e74c3c" if "7th" in view_filter else "#27ae60" if "5th" in view_filter else "#2980b9" if "4th" in view_filter else "#8e44ad"
        
        for p1, p2 in aspect_pairs:
            dyn, action, act_class, desc, rem = get_aspect_insight(p1, p2, view_filter)
            
            grid_html += f"""
            <div class="bp-card" style="border-top: 3px solid {card_border};">
                <div class="bp-head"><span>Connection Detected</span> <span style="color:{card_border}; font-weight:bold;">{dyn}</span></div>
                <div class="bp-title">{planet_icons.get(p1, '')} {p1} &nbsp;↔&nbsp; {planet_icons.get(p2, '')} {p2}</div>
                <div class="bp-desc">{desc}</div>
                <div style="margin-top:auto; padding-top:10px; border-top: 1px dashed #eee;">
                    <div class="{act_class}">{action}</div>
                    <div class="insight-text">{rem}</div>
                </div>
            </div>"""
            
        grid_html += "</div>"
        st.markdown(grid_html, unsafe_allow_html=True)

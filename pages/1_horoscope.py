import streamlit as st
import swisseph as swe
from datetime import datetime, time
import google.generativeai as genai
from supabase import create_client
import plotly.graph_objects as go

# --- IMPORTS FROM RESTORED ENGINE ---
from astro_engine import (
    get_location_coordinates, get_utc_offset, get_bhava_chalit, get_navamsa_chart, get_dasamsa_chart,
    determine_house, get_dignity, calculate_sav_score, get_nakshatra_details, scan_yogas,
    analyze_career_professional, analyze_education, analyze_health, analyze_love_marriage,
    generate_annual_forecast, get_transit_data_advanced, analyze_karmic_axis, get_house_strength_analysis,
    generate_mahadasha_table, generate_current_next_bhukti, 
    t_p, t_p_eng, ZODIAC_TA, ZODIAC
)
from report_generator import get_south_indian_chart_html
from database import TAMIL_NAMES, identity_db, RASI_RULERS
from tamil_lang import TAMIL_IDENTITY_DB

# SECURE API SETUP
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if not API_KEY:
    try:
        from api_config import GEMINI_API_KEY
        API_KEY = GEMINI_API_KEY
    except: pass

st.set_page_config(page_title="Vedic Astro AI Engine", layout="wide")

if 'report_generated' not in st.session_state: st.session_state.report_generated = False
if 'messages' not in st.session_state: st.session_state.messages = []

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

st.title(":material/account_circle: Deep Horoscope Engine")
st.markdown("Generate a complete, personalized Vedic astrological profile.")
st.divider()

with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    LANG = st.radio("Language / மொழி", ["English", "Tamil"], horizontal=True)
    st.divider()
    
    st.markdown("### 👤 Birth Details")
    saved_profiles = load_profiles_from_db()
    profile_options = ["✨ Select Profile...", "✏️ Enter Manually"] + list(saved_profiles.keys())
    selected_profile = st.selectbox("Load Saved Profile", profile_options)
    
    if selected_profile in ["✨ Select Profile...", "✏️ Enter Manually"]:
        def_n, def_dob, def_tob, def_loc = "", datetime(2000, 1, 1).date(), time(12, 0), ""
    else:
        def_n = selected_profile
        def_dob = saved_profiles[selected_profile]["dob"]
        def_tob = saved_profiles[selected_profile]["tob"]
        def_loc = saved_profiles[selected_profile]["city"]

    k = selected_profile.replace(" ", "_")
    name_in = st.text_input("Name", value=def_n, key=f"h_name_{k}")
    dob_in = st.date_input("Date of Birth", value=def_dob, min_value=datetime(1950, 1, 1).date(), key=f"h_dob_{k}")
    tob_in = st.time_input("Time of Birth", value=def_tob, step=60, key=f"h_tob_{k}")
    city = st.text_input("City", value=def_loc, key=f"h_loc_{k}")
    f_year = st.number_input("Forecast Year", min_value=datetime.now().year, max_value=2050, value=2026)
    
    lat_val, lon_val, tz_val = 13.0827, 80.2707, "Asia/Kolkata" 
    if city:
        lat_val, lon_val, tz_val = get_location_coordinates(city)
        st.markdown(f"<span style='font-size:12px; color:gray;'>Resolved: {lat_val:.2f}, {lon_val:.2f} ({tz_val})</span>", unsafe_allow_html=True)
    
    calc_btn = st.button("Generate Report", type="primary", use_container_width=True)
    if calc_btn:
        if not name_in or not city: st.error("Please enter a Name and City!")
        else: st.session_state.report_generated = True

# --- EXECUTION ---
if st.session_state.report_generated:
    with st.spinner("Calculating exact astronomical data..." if LANG=="English" else "ஜாதகம் கணிக்கப்படுகிறது..."):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        birth_dt = datetime.combine(dob_in, tob_in)
        offset = get_utc_offset(tz_val, birth_dt)
        ut_hour = (tob_in.hour + (tob_in.minute/60.0)) - offset
        jd_ut = swe.julday(dob_in.year, dob_in.month, dob_in.day, ut_hour)
        
        bhava_cusps = get_bhava_chalit(jd_ut, lat_val, lon_val)
        ascmc = swe.houses_ex(jd_ut, lat_val, lon_val, b'P', swe.FLG_SIDEREAL)[1]
        lagna_rasi = int(ascmc[0]/30)+1
        d9_lagna = get_navamsa_chart(ascmc[0])
        d10_lagna = get_dasamsa_chart(ascmc[0])
        
        moon_res = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0]
        moon_rasi = int(moon_res[0]/30)+1
        current_age = datetime.now().year - dob_in.year

        planets = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
        p_pos, p_d9, p_d10, p_lon_absolute, bhava_placements = {}, {}, {}, {}, {}
        master_table = []
        
        for p, pid in planets.items():
            res = swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL)[0]
            p_lon_absolute[p] = res[0]
            r1 = int(res[0]/30)+1
            p_pos[p] = r1
            p_d9[p] = get_navamsa_chart(res[0])
            p_d10[p] = get_dasamsa_chart(res[0])
            bhava_h = determine_house(res[0], bhava_cusps)
            bhava_placements[p] = bhava_h 
            h = (r1 - lagna_rasi + 1) if (r1 - lagna_rasi + 1) > 0 else (r1 - lagna_rasi + 1) + 12
            dig = get_dignity(p, r1)
            status = "VARGOTTAMA" if r1 == p_d9[p] else "ROYAL" if dig == "Exalted" else "WEAK" if dig == "Neecha" else "Avg"
            
            # Use strict t_p_eng for English, t_p for Tamil
            p_name = t_p.get(p, p) if LANG == "Tamil" else t_p_eng.get(p, p)
            master_table.append({"Planet": p_name, "Rasi": ZODIAC_TA.get(r1, "") if LANG=="Tamil" else ZODIAC[r1], "House": h, "Bhava": bhava_h, "Dignity": dig, "Status": status})

        # KETU INTEGRATION
        ketu_lon = (p_lon_absolute["Rahu"] + 180) % 360
        p_lon_absolute["Ketu"] = ketu_lon
        p_pos["Ketu"] = int(ketu_lon/30) + 1
        p_d9["Ketu"] = get_navamsa_chart(ketu_lon)
        bhava_placements["Ketu"] = determine_house(ketu_lon, bhava_cusps)
        k_h = (p_pos["Ketu"] - lagna_rasi + 1) if (p_pos["Ketu"] - lagna_rasi + 1) > 0 else (p_pos["Ketu"] - lagna_rasi + 1) + 12
        k_dig = get_dignity("Ketu", p_pos["Ketu"])
        k_status = "VARGOTTAMA" if p_pos["Ketu"] == p_d9["Ketu"] else "ROYAL" if k_dig == "Exalted" else "WEAK" if k_dig == "Neecha" else "Avg"
        master_table.append({"Planet": "கேது" if LANG=="Tamil" else "Ketu", "Rasi": ZODIAC_TA.get(p_pos["Ketu"], "") if LANG=="Tamil" else ZODIAC[p_pos["Ketu"]], "House": k_h, "Bhava": bhava_placements["Ketu"], "Dignity": k_dig, "Status": k_status})

        p_pos["Lagna"] = lagna_rasi
        p_d9["Lagna"] = d9_lagna
        sav_scores = calculate_sav_score(p_pos, lagna_rasi)
        nak, lord = get_nakshatra_details(moon_res[0])
        
        karmic_txt = analyze_karmic_axis(p_pos, lagna_rasi, lang=LANG)
        yogas = scan_yogas(p_pos, lagna_rasi, lang=LANG)
        career_txt = analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang=LANG)
        edu_txt = analyze_education(p_pos, lagna_rasi, lang=LANG)
        health_txt = analyze_health(p_pos, lagna_rasi, lang=LANG)
        love_txt = analyze_love_marriage(lagna_rasi, d9_lagna, p_d9, p_pos, lang=LANG)
        fc = generate_annual_forecast(moon_rasi, sav_scores, f_year, current_age, lang=LANG)
        t_data = get_transit_data_advanced(f_year)
        
        db_id = TAMIL_IDENTITY_DB if LANG == "Tamil" else identity_db
        report_id_data = db_id.get(ZODIAC[lagna_rasi], list(db_id.values())[0])

        c_left, c_right = st.columns([3, 1])
        with c_left:
            st.subheader(f"Analysis for {name_in}" if LANG=="English" else f"ஜோதிட அறிக்கை: {name_in}")
            l_name = ZODIAC_TA.get(lagna_rasi, "") if LANG == "Tamil" else ZODIAC[lagna_rasi]
            m_name = ZODIAC_TA.get(moon_rasi, "") if LANG == "Tamil" else ZODIAC[moon_rasi]
            st.markdown(f"> **{'லக்னம்' if LANG=='Tamil' else 'Lagna'}:** {l_name} | **{'ராசி' if LANG=='Tamil' else 'Moon'}:** {m_name} | **{'நட்சத்திரம்' if LANG=='Tamil' else 'Star'}:** {nak}")
        
        tb_lbls = ["Profile", "Scorecard", "Work & Intellect", "Love & Health", "Yogas", "Forecast", "Roadmap", "💬 Oracle"] if LANG == "English" else ["சுயவிவரம்", "அஷ்டகவர்க்கம்", "தொழில்", "திருமணம் & ஆரோக்கியம்", "யோகங்கள்", "ஆண்டு பலன்கள்", "தசா புக்தி", "💬 ஜோதிடர்"]
        t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs(tb_lbls)

        with t1:
            st.subheader("Identity" if LANG == "English" else "சுயவிவரம்")
            st.markdown(f"**{'நோக்கம்' if LANG=='Tamil' else 'Purpose'}:** {report_id_data.get('Purpose', '')}")
            st.markdown(f"**{'குணம்' if LANG=='Tamil' else 'Personality'}:** {report_id_data.get('Personality', '')}")
            st.divider()

            st.markdown(f"<h3 style='text-align: center; margin-top:20px;'>{'ராசி சக்கரம்' if LANG=='Tamil' else 'Birth Chart (Rasi)'}</h3>", unsafe_allow_html=True)
            st.markdown(get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if LANG=="Tamil" else "Rasi Chart", LANG), unsafe_allow_html=True)
            
            headers = ["கிரகம்", "ராசி", "பாவம்", "பலம்", "நிலை"] if LANG == "Tamil" else ["Planet", "Rasi", "House", "Dignity", "Status"]
            table_md = f"<table style='width: 80%; margin: 30px auto; border-collapse: collapse; font-family: sans-serif; font-size: 15px; text-align: center;'><tr style='background-color: #f8f9fa; border-bottom: 2px solid #ccc;'><th style='padding: 12px 8px;'>{headers[0]}</th><th style='padding: 12px 8px;'>{headers[1]}</th><th style='padding: 12px 8px;'>{headers[2]}</th><th style='padding: 12px 8px;'>{headers[3]}</th><th style='padding: 12px 8px;'>{headers[4]}</th></tr>"
            for row in master_table:
                table_md += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 12px 8px;'><b>{row['Planet']}</b></td><td style='padding: 12px 8px;'>{row['Rasi']}</td><td style='padding: 12px 8px;'>{row['House']}</td><td style='padding: 12px 8px;'>{row['Dignity']}</td><td style='padding: 12px 8px;'>{row['Status']}</td></tr>"
            table_md += "</table>"
            st.markdown(table_md, unsafe_allow_html=True)

        with t2:
            st.subheader("Destiny Radar (Ashtakavarga)" if LANG == "English" else "அஷ்டகவர்க்கம் (Destiny Radar)")
            p_lbl = "பாவம்" if LANG == "Tamil" else "H"
            cats_labels = [f"{p_lbl} {i+1}" for i in range(12)]
            vals = [sav_scores[(lagna_rasi-1+i)%12] for i in range(12)]
            text_colors = ['#27ae60' if v >= 30 else '#e74c3c' if v < 25 else '#333333' for v in vals]
            fig_bar = go.Figure(data=[go.Bar(x=vals, y=cats_labels, orientation='h', marker_color='#bdc3c7', text=[f"<b>{v}</b>" for v in vals], textposition='outside', textfont=dict(color=text_colors, size=14))])
            fig_bar.add_vline(x=28, line_width=2, line_dash="dash", line_color="#7f8c8d", annotation_text="Average (28)" if LANG=="English" else "சராசரி (28)", annotation_position="top right")
            fig_bar.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=40, b=20), height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            st.divider()
            c1, c2 = st.columns(2)
            sorted_houses = sorted([(sav_scores[(lagna_rasi-1+i)%12], i+1) for i in range(12)], key=lambda x: x[0], reverse=True)
            with c1:
                st.markdown(f"<h4 style='color: #27ae60; margin-bottom: 10px;'>{'அதிக பலம் பெற்ற பாவங்கள்' if LANG=='Tamil' else 'Top Power Zones'}</h4>", unsafe_allow_html=True)
                for s, h in sorted_houses[:3]:
                    st.markdown(get_house_strength_analysis(h, s, LANG))
            with c2:
                st.markdown(f"<h4 style='color: #e74c3c; margin-bottom: 10px;'>{'கவனம் தேவைப்படும் பாவங்கள்' if LANG=='Tamil' else 'Top Challenge Zones'}</h4>", unsafe_allow_html=True)
                for s, h in sorted_houses[-3:]:
                    st.markdown(get_house_strength_analysis(h, s, LANG))

        with t3:
            st.subheader("Education & Intellect" if LANG == "English" else "கல்வி மற்றும் அறிவு")
            for line in edu_txt: st.markdown(line)
            st.divider()
            st.subheader("Career Strategy & True Authority" if LANG == "English" else "தொழில் மற்றும் அதிகாரம்")
            for line in career_txt: st.markdown(line)
            st.divider()
            for line in karmic_txt: st.markdown(line)

        with t4:
            st.markdown(f"<h3 style='text-align: center; margin-top:20px;'>{'நவாம்ச சக்கரம் (Navamsa)' if LANG=='Tamil' else 'Destiny Chart (Navamsa)'}</h3>", unsafe_allow_html=True)
            st.markdown(get_south_indian_chart_html(p_d9, d9_lagna, "நவாம்சம்" if LANG=="Tamil" else "Navamsa", LANG), unsafe_allow_html=True)
            st.divider()
            st.subheader("Love & Marriage" if LANG == "English" else "காதல் மற்றும் திருமணம்")
            for line in love_txt: st.markdown(line)
            st.divider()
            st.subheader("Health & Vitality" if LANG == "English" else "ஆரோக்கியம்")
            for line in health_txt: st.markdown(line)

        with t5:
            st.subheader("Wealth & Power Combinations" if LANG == "English" else "முக்கிய யோகங்கள்")
            for y in yogas:
                st.markdown(f"#### {y['Name']}")
                st.markdown(f"> **{'Focus' if LANG=='English' else 'பலன்'}:** {y['Type']}")
                st.markdown(y['Description'])

        with t6:
            st.subheader(f"Annual Forecast {f_year}" if LANG == "English" else f"{f_year} ஆண்டு பலன்கள்")
            for cat, data in fc.items():
                st.markdown(f"#### {cat}")
                st.markdown(data[0])
                st.markdown(f"> **{'Remedy' if LANG=='English' else 'பரிகாரம்'}:** {data[1]}")
            
            st.divider()
            st.subheader("Planetary Transit Dates" if LANG == "English" else "முக்கிய கிரகப் பெயர்ச்சிகள்")
            for p_name, trans_data in t_data.items():
                trans_name = t_p.get(p_name, p_name) if LANG == "Tamil" else t_p_eng.get(p_name, p_name)
                r_from = ZODIAC_TA.get(trans_data['Rasi'], "") if LANG == "Tamil" else ZODIAC[trans_data['Rasi']]
                r_to = ZODIAC_TA.get(trans_data['NextSignIdx'], "") if LANG == "Tamil" else ZODIAC[trans_data['NextSignIdx']]
                st.markdown(f"**{trans_name}:** {r_from} ➔ {r_to} ({trans_data['NextDate']})")

        with t7:
            st.subheader("Life Chapters (Timeline)" if LANG == "English" else "மகா தசை விவரங்கள் (காலக்கோடு)")
            
            mahadasha_data = generate_mahadasha_table(moon_res[0], datetime.combine(dob_in, tob_in), lang=LANG)
            phases, pd_info = generate_current_next_bhukti(moon_res[0], datetime.combine(dob_in, tob_in), bhava_placements, lang=LANG)
            
            if pd_info:
                st.markdown(f"#### {'IMMEDIATE FOCUS' if LANG=='English' else 'நடப்பு தசா புக்தி'}")
                st.markdown(f"**{pd_info['Start']} to {pd_info['End']}**: {pd_info['PD']} ({pd_info['MD']} / {pd_info['AD']})")
                st.divider()
            for p in phases:
                st.markdown(f"**{p['Type']}: {p['Phase']}**\n> {p['Dates']}\n\n{p['Text']}")
                st.divider()

            # TIMELINE ALIGNMENT FIX & RESTORED COLORS
            planet_colors = {"Suriyan": "#d35400", "Chandran": "#95a5a6", "Sevvai": "#c0392b", "Budhan": "#27ae60", "Guru": "#f39c12", "Sukran": "#8e44ad", "Sani": "#2c3e50", "Rahu": "#34495e", "Ketu": "#7f8c8d", "சூரியன்": "#d35400", "சந்திரன்": "#95a5a6", "செவ்வாய்": "#c0392b", "புதன்": "#27ae60", "குரு": "#f39c12", "சுக்கிரன்": "#8e44ad", "சனி": "#2c3e50", "ராகு": "#34495e", "கேது": "#7f8c8d"}
            
            dasha_names, start_years, durations = [], [], []
            for row in mahadasha_data:
                dasha_names.append(row['Mahadasha'])
                s_year, e_year = map(int, row['Years'].split(' - '))
                start_years.append(s_year)
                durations.append(e_year - s_year)
                
            fig_timeline = go.Figure()
            fig_timeline.add_trace(go.Bar(
                y=['Life Path']*len(dasha_names), x=durations, base=start_years, name="Mahadashas", orientation='h',
                text=dasha_names, textposition='inside', textangle=0, insidetextfont=dict(color='white', size=14),
                marker=dict(color=[planet_colors.get(d, '#333') for d in dasha_names]) # COLORS RESTORED
            ))
            # Forces Timeline to anchor exactly on the Birth Year on the left
            fig_timeline.update_layout(
                barmode='stack', height=150, margin=dict(l=0, r=0, t=10, b=20), 
                xaxis=dict(range=[start_years[0], start_years[0]+120], tickformat="d"), 
                yaxis=dict(showticklabels=False), showlegend=False
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # RESTORED RICH HTML TABLE
            h_age = "வயது" if LANG == "Tamil" else "Age"
            h_yrs = "ஆண்டுகள்" if LANG == "Tamil" else "Years"
            h_md = "மகா தசை" if LANG == "Tamil" else "Mahadasha"
            h_pred = "கணிப்பு" if LANG == "Tamil" else "Context & Prediction"

            md_table_html = f"<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; margin-top: 20px;'><tr style='border-bottom: 2px solid #ddd; background-color: #fdfdfd;'><th style='padding: 10px 8px; text-align: left; width: 10%;'>{h_age}</th><th style='padding: 10px 8px; text-align: left; width: 10%;'>{h_yrs}</th><th style='padding: 10px 8px; text-align: left; width: 15%;'>{h_md}</th><th style='padding: 10px 8px; text-align: left; width: 65%;'>{h_pred}</th></tr>"
            for row in mahadasha_data:
                s_year, e_year = row['Years'].split(' - ')
                md_table_html += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 10px 8px; vertical-align: top;'>{row['Age (From-To)']}</td><td style='padding: 10px 8px; vertical-align: top;'>{s_year}<br>{e_year}</td><td style='padding: 10px 8px; vertical-align: top; color: {planet_colors.get(row['Mahadasha'], '#333')};'><b>{row['Mahadasha']}</b></td><td style='padding: 10px 8px; vertical-align: top;'>{row['Prediction']}</td></tr>"
            md_table_html += "</table>"
            st.markdown(md_table_html, unsafe_allow_html=True)

        with t8:
            st.subheader("💬 Ask the AI Astrologer" if LANG == "English" else "💬 AI ஜோதிடரிடம் கேளுங்கள்")
            st.info("I am an AI trained on your exact astrological coordinates." if LANG == "English" else "உங்கள் பிறந்த ஜாதகத்தை நான் படித்துவிட்டேன். கேள்விகளைக் கேட்கலாம்.")
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]): st.markdown(msg["content"])

            if prompt_input := st.chat_input("Ask a question..."):
                if not API_KEY: st.error("API Key missing! Please add your Gemini key.")
                else:
                    st.session_state.messages.append({"role": "user", "content": prompt_input})
                    with chat_container:
                        with st.chat_message("user"): st.markdown(prompt_input)
                        with st.chat_message("assistant"):
                            with st.spinner("Consulting the Oracle..." if LANG=="English" else "கணிக்கப்படுகிறது..."):
                                try:
                                    genai.configure(api_key=API_KEY)
                                    chart_context = f"Ascendant {ZODIAC[lagna_rasi]}, Moon {ZODIAC[moon_rasi]}. Planets: {p_pos}."
                                    
                                    # BULLETPROOF AI FIX
                                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                                    target_model = available_models[0] if available_models else 'gemini-1.5-flash'
                                    for m in available_models:
                                        if 'gemini-1.5-flash' in m: target_model = m; break
                                        elif '1.5-pro' in m or '1.0-pro' in m: target_model = m
                                    
                                    model = genai.GenerativeModel(target_model)
                                    response = model.generate_content(f"You are a Vedic Astrologer. Data: {chart_context}. User says: {prompt_input}")
                                    st.markdown(response.text)
                                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                                except Exception as e: st.error(f"AI Generation Failed: {e}")
                    st.rerun()

        if st.session_state.messages:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                st.rerun()

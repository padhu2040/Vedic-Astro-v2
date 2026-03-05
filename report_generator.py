import re
from weasyprint import HTML
from database import ZODIAC
from astro_engine import ZODIAC_TA, t_p_eng

def get_south_indian_chart_html(p_pos, lagna_rasi, title, lang="English"):
    g = {i: [] for i in range(1, 13)}
    
    g[lagna_rasi].append("<span style='color:#e74c3c; font-size:12px; display:block; margin-bottom:2px; font-weight:bold;'>Asc (Lagna)</span>")
    
    for p, r in p_pos.items():
        if p == "Lagna": continue
        name = t_p_eng.get(p, p[:2]) if lang == "English" else p[:2]
        g[r].append(f"<span style='font-size:12px; font-weight:bold; color:#2c3e50; display:block;'>{name}</span>")
    
    for i in g: g[i] = "".join(g[i])
    z = ZODIAC_TA if lang == "Tamil" else ZODIAC
    def get_z(idx): return z.get(idx, "") if isinstance(z, dict) else (z[idx] if idx < len(z) else "")
        
    def cell(idx):
        is_lagna = (idx == lagna_rasi)
        lagna_gradient = "background: linear-gradient(135deg, transparent 49%, rgba(231,76,60,0.3) 49.5%, rgba(231,76,60,0.3) 50.5%, transparent 51%), #fdfdfa;"
        standard_bg = "background-color: #fafafa;"
        style = f"border: 1px solid #bdc3c7; width: 25%; height: 110px; vertical-align: top; padding: 6px; box-sizing: border-box; "
        style += lagna_gradient if is_lagna else standard_bg
        return f"<td style='{style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(idx)} ({idx})</div>{g[idx]}</td>"

    return f"""
    <div style='page-break-inside: avoid; text-align: center; margin: 15px 0;'>
        <table style='width: 450px; margin: 0 auto; table-layout: fixed; border-collapse: collapse; text-align: center; font-size: 14px; background-color: #ffffff; border: 2px solid #333;'>
            <tr>{cell(12)}{cell(1)}{cell(2)}{cell(3)}</tr>
            <tr>{cell(11)}<td colspan='2' rowspan='2' style='border: none; vertical-align: middle; font-weight: bold; font-size: 16px; color:#2c3e50; background-color: #ffffff;'>{title}</td>{cell(4)}</tr>
            <tr>{cell(10)}{cell(5)}</tr>
            <tr>{cell(9)}{cell(8)}{cell(7)}{cell(6)}</tr>
        </table>
    </div>
    """

def get_local_house_analysis_pdf(house, score):
    domains = {
        1: "Self, physical vitality, and personal brand",
        2: "Accumulated wealth, speech, and family assets",
        3: "Courage, short-term efforts, and networking",
        4: "Inner peace, real estate, and foundational security",
        5: "Creative intellect, speculation, and advisory roles",
        6: "Daily routines, overcoming competitors, and debt management",
        7: "Strategic partnerships, marriage, and public relations",
        8: "Crisis management, hidden resources, and transformation",
        9: "Long-term vision, higher learning, and natural luck",
        10: "Career execution, public authority, and industry reputation",
        11: "Massive scaling, professional networks, and major gains",
        12: "Deep rest, foreign investments, and letting go of control"
    }
    power_advice = {
        1: "Lean heavily into your personal charisma. You are the brand.",
        2: "Capitalize on your communication skills and aggressively scale your assets.",
        3: "Take calculated risks and expand your immediate network. Boldness wins here.",
        4: "Invest in real estate or foundational infrastructure. Your inner security is your fortress.",
        5: "Trust your creative instincts and intellectual models. Lead through guidance.",
        6: "Tackle operational bottlenecks head-on. You will easily outlast competitors.",
        7: "Form strategic alliances. Joint ventures will yield massive returns.",
        8: "Do not fear sudden market shifts. You have a unique talent for profiting during crises.",
        9: "Trust your intuition and long-term philosophy. The universe actively supports your vision.",
        10: "Assume absolute leadership. You are built to direct and execute at the highest level.",
        11: "Focus on scaling. Tap into large professional networks to multiply your influence.",
        12: "Use isolation and backend strategy as a weapon. Some of your best work happens off-stage."
    }
    challenge_advice = {
        1: "Guard against burnout. Do not let your ego tie your self-worth solely to your output.",
        2: "Enforce strict financial discipline. Avoid impulsive speech that damages key alliances.",
        3: "Do not waste energy on petty conflicts. Focus your drive on structured goals.",
        4: "Actively protect your private time. Do not let professional stress infect your home.",
        5: "Avoid over-analyzing. Delegate tasks instead of trying to control all creative output.",
        6: "Build strict boundaries to avoid absorbing workplace toxicity. Prioritize health routines.",
        7: "Do not compromise your core vision just to avoid conflict in partnerships.",
        8: "Avoid resisting necessary structural changes. Clinging to the past will stall your growth.",
        9: "Stay flexible. Rigid dogmatism or overly optimistic leaps of faith will backfire.",
        10: "Practice extreme patience. True authority here requires enduring delayed gratification.",
        11: "Audit your network. Cut out professional connections that drain energy without ROI.",
        12: "Prioritize sleep and mental health. Do not ignore your need to disconnect and recharge."
    }
    
    domain = domains.get(house, "")
    if score >= 30:
        advice = power_advice.get(house, "Maximize this energy.")
        return f"<div style='margin-bottom:10px;'><b>Power zone: The {house}th house ({domain}) is exceptionally strong.</b><br><span style='color:#555;'><i>Harnessing guide:</i> {advice}</span></div>"
    else:
        advice = challenge_advice.get(house, "Requires strict discipline.")
        return f"<div style='margin-bottom:10px;'><b>Challenge zone: The {house}th house ({domain}) requires conscious effort.</b><br><span style='color:#555;'><i>Mitigation guide:</i> {advice}</span></div>"

def draw_mbti_bar_html_pdf(title, energy_txt, left_lbl, right_lbl, pct_left):
    pct_right = 100 - pct_left
    active_left = "#2c3e50" if pct_left >= 50 else "#dcdcdc"
    active_right = "#2c3e50" if pct_right > 50 else "#dcdcdc"
    return f"""
    <div style="margin-bottom: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; page-break-inside: avoid;">
        <div style="text-align: center; margin-bottom: 5px;">
            <div style="font-size: 14px; font-weight: bold; color: #111;">{title}</div>
            <div style="font-size: 11px; color: #555; font-style: italic;">{energy_txt}</div>
        </div>
        <table style="width: 100%; font-size: 10px; font-weight: bold; margin-bottom: 4px; border: none;">
            <tr>
                <td style="color: {active_left}; text-align: left; padding: 0; border: none;">{pct_left}% {left_lbl}</td>
                <td style="color: {active_right}; text-align: right; padding: 0; border: none;">{right_lbl} {pct_right}%</td>
            </tr>
        </table>
        <div style="width: 100%; height: 10px; overflow: hidden; font-size: 0;">
            <div style="float: left; width: {pct_left}%; background-color: {active_left}; height: 10px;"></div>
            <div style="float: left; width: {pct_right}%; background-color: {active_right}; height: 10px;"></div>
        </div>
    </div>
    """

def generate_pdf_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, karmic_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, master_table, phases, pd_info, guide, transit_texts, mbti_data, ennea_data, coaching_rules, rahu_h, ketu_h, lang="English"):
    
    def md_to_html(text):
        text = text.replace('\n', '<br>')
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) 
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)     
        return text

    def format_section(text_list):
        out = ""
        for line in text_list:
            line = line.strip()
            if not line: continue
            if line.startswith("#### "): 
                out += f"<h4>{md_to_html(line.replace('#### ', ''))}</h4>"
            elif line.startswith("### "): 
                out += f"<h4>{md_to_html(line.replace('### ', ''))}</h4>"
            elif line.startswith("## "): 
                out += f"<h3>{md_to_html(line.replace('## ', ''))}</h3>"
            elif line.startswith("> "): 
                parsed_quote = md_to_html(line.replace('> ', ''))
                out += f"<blockquote>{parsed_quote}</blockquote>"
            else: 
                out += f"<p>{md_to_html(line)}</p>"
        return out

    h_title = f"Vedic Astrology Premium Report: {name_in}"
    chart1 = get_south_indian_chart_html(p_pos, lagna_rasi, "Rasi Chart", lang)
    d9_lagna_idx = p_d9.get("Lagna", 1)
    chart2 = get_south_indian_chart_html(p_d9, d9_lagna_idx, "Navamsa", lang)

    t_headers = ["Planet", "Rasi", "House", "Dignity", "Status"]
    master_table_html = f"<div style='page-break-inside: avoid;'><table style='width: 100%; margin: 15px 0; border-collapse: collapse; font-size: 12px; text-align: center;'><tr style='background-color: #f0f3f4; border-bottom: 2px solid #ccc;'><th style='padding: 6px;'>{t_headers[0]}</th><th style='padding: 6px;'>{t_headers[1]}</th><th style='padding: 6px;'>{t_headers[2]}</th><th style='padding: 6px;'>{t_headers[3]}</th><th style='padding: 6px;'>{t_headers[4]}</th></tr>"
    for row in master_table:
        master_table_html += f"<tr style='border-bottom: 1px solid #eee;'><td style='padding: 6px;'><b>{row['Planet']}</b></td><td style='padding: 6px;'>{row['Rasi']}</td><td style='padding: 6px;'>{row['House']}</td><td style='padding: 6px;'>{row['Dignity']}</td><td style='padding: 6px;'>{row['Status']}</td></tr>"
    master_table_html += "</table></div>"

    score_html = "<div style='page-break-inside: avoid;'><table class='bar-chart'>"
    for i in range(12):
        score = sav_scores[(lagna_rasi - 1 + i) % 12]
        color = "#27ae60" if score >= 30 else "#e74c3c" if score < 25 else "#95a5a6"
        bar_w = int((score / 45) * 100)
        score_html += f"<tr><td style='width: 15%;'><b>H {i+1}</b></td><td style='width: 75%;'><div class='bar' style='background-color: {color}; width: {bar_w}%;'></div></td><td style='width: 10%; text-align: right;'><b>{score}</b></td></tr>"
    score_html += "</table>"
    
    sorted_houses = sorted([(sav_scores[(lagna_rasi-1+i)%12], i+1) for i in range(12)], key=lambda x: x[0], reverse=True)
    zones_html = "<table style='width:100%; margin-top:15px; border-collapse: collapse; border: none;'><tr><td style='width:50%; vertical-align:top; padding-right:10px; border: none;'>"
    zones_html += f"<h4 style='color: #27ae60; margin-top:0;'>Top Power Zones</h4>"
    for s, h in sorted_houses[:3]: zones_html += f"<div style='font-size:12px;'>{get_local_house_analysis_pdf(h, s)}</div>"
    zones_html += "</td><td style='width:50%; vertical-align:top; padding-left:10px; border: none; border-left: 1px solid #eee;'>"
    zones_html += f"<h4 style='color: #e74c3c; margin-top:0;'>Top Challenge Zones</h4>"
    for s, h in sorted_houses[-3:]: zones_html += f"<div style='font-size:12px;'>{get_local_house_analysis_pdf(h, s)}</div>"
    zones_html += "</td></tr></table></div>"

    en_planet_colors = {
        "Sun": "#d35400", "Moon": "#95a5a6", "Mars": "#c0392b", 
        "Mercury": "#27ae60", "Jupiter": "#f39c12", "Venus": "#8e44ad", 
        "Saturn": "#2c3e50", "Rahu": "#34495e", "Ketu": "#7f8c8d"
    }
    core_color = en_planet_colors.get(ennea_data['ak_eng'], "#2c3e50")
    wing_color = en_planet_colors.get(ennea_data['amk_eng'], "#3498db")

    house_domains = {
        1: "personal identity, physical vitality, and self-projection",
        2: "financial accumulation, verbal communication, and family assets",
        3: "self-directed effort, networking, and calculated risk-taking",
        4: "emotional security, domestic life, and foundational assets",
        5: "creative intelligence, speculative ventures, and guiding subordinates",
        6: "overcoming competition, operational routines, and problem-solving",
        7: "strategic partnerships, negotiations, and public relations",
        8: "managing crises, other people's resources, and deep research",
        9: "high-level philosophy, long-term vision, and global expansion",
        10: "absolute authority, career execution, and public reputation",
        11: "massive scaling, professional networks, and achieving major milestones",
        12: "deep rest, foreign environments, and behind-the-scenes strategy"
    }
    rahu_domain = house_domains.get(rahu_h, "this specific area of life")
    ketu_domain = house_domains.get(ketu_h, "this specific area of life")

    e_txt = "You draw energy from the external environment and social interaction." if mbti_data['extro_pct'] >= 50 else "You draw energy from your inner world of ideas and quiet reflection."
    s_txt = "You process information through tangible facts, details, and present reality." if (100 - mbti_data['int_pct']) > 50 else "You process information through patterns, future possibilities, and abstract concepts."
    t_txt = "You make decisions based on objective logic, structure, and impersonal analysis." if mbti_data['think_pct'] >= 50 else "You make decisions based on personal values, empathy, and social harmony."
    j_txt = "You approach life with structure, planning, and a desire for closure." if mbti_data['judging_pct'] >= 50 else "You approach life with flexibility, adaptability, and keeping your options open."

    html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><title>{h_title}</title>
    <style>
        @page {{ size: A4; margin: 20mm; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.5; font-size: 13px; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; font-size: 22px; margin-bottom: 5px; }}
        .subtitle {{ text-align: center; font-size: 13px; color: #7f8c8d; margin-bottom: 20px; }}
        h2 {{ color: #2980b9; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 18px; page-break-after: avoid; }}
        h3 {{ color: #2c3e50; margin-top: 20px; margin-bottom: 5px; font-size: 15px; page-break-after: avoid; }}
        h4 {{ color: #2c3e50; margin-top: 15px; margin-bottom: 4px; font-size: 14px; page-break-after: avoid; }}
        p {{ margin-top: 5px; margin-bottom: 8px; text-align: justify; color: #444; line-height: 1.6; }}
        .bar-chart {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }}
        .bar-chart td {{ padding: 6px 0; border-bottom: 1px dashed #eee; vertical-align: middle; border-top: none; border-left: none; border-right: none; }}
        .bar {{ height: 16px; border-radius: 3px; }}
        .page-break {{ page-break-before: always; }}
        table.timeline {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
        table.timeline th, table.timeline td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; vertical-align: top; line-height: 1.5; border-top: none; border-left: none; border-right: none; }}
        table.timeline tr {{ page-break-inside: avoid; }}
        table.timeline th {{ background-color: #f0f3f4; color: #2c3e50; font-weight: bold; }}
        blockquote {{ background: #fdfae6; border-left: 4px solid #f1c40f; padding: 10px 15px; margin: 10px 0; font-size: 12.5px; page-break-inside: avoid; }}
        .footer {{ text-align: center; font-size: 11px; color: #95a5a6; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; page-break-inside: avoid; }}
    </style></head><body>
        <h1>{h_title}</h1>
        <div class="subtitle"><b>Lagna:</b> {lagna_str} | <b>Moon:</b> {moon_str} | <b>Star:</b> {star_str}</div>
        
        <h2>1. Profile & placements</h2>
        <p>This section maps the exact astronomical coordinates of the planets at your moment of birth. In Vedic Astrology, your Ascendant (Lagna) forms your physical self and operating framework, while your Moon Sign (Rasi) dictates your internal emotional processor.</p>
        {chart1}
        <h3 style="margin-top: 25px;">Core planetary alignments</h3>
        <p style="font-size: 12px; color: gray;">This table displays the exact dignity and status of your planetary placements. 'Exalted' planets act as your superpowers, while 'Neecha' (debilitated) planets show areas requiring conscious development.</p>
        {master_table_html}
        
        <h2>2. Destiny Radar (Ashtakavarga)</h2>
        {score_html}
        {zones_html}
        
        <div class="page-break"></div>
        
        <h2>3. Executive Playbook</h2>
        
        <h3>Phase 1: The core drive</h3>
        <table style="width: 100%; border-collapse: separate; border-spacing: 10px 10px; border: none; margin-bottom: 15px;">
            <tr>
                <td style="width: 50%; background: #fff; border: 1px solid #eaeaea; border-top: 4px solid {core_color}; padding: 15px; border-radius: 8px; vertical-align: top;">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Atmakaraka:</b> Core Driver</div>
                    <div style="font-size: 16px; font-weight: bold; color: {core_color}; margin-bottom: 10px;">{ennea_data['ak_planet']} ({ennea_data['ak_type']})</div>
                    <div style="font-size: 13px; color: #444; line-height: 1.5;">{ennea_data['ak_coaching']}</div>
                </td>
                <td style="width: 50%; background: #fff; border: 1px solid #eaeaea; border-top: 4px solid {wing_color}; padding: 15px; border-radius: 8px; vertical-align: top;">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Amatyakaraka:</b> Execution Wing</div>
                    <div style="font-size: 16px; font-weight: bold; color: {wing_color}; margin-bottom: 10px;">{ennea_data['amk_planet']}</div>
                    <div style="font-size: 13px; color: #444; line-height: 1.5;">{ennea_data['amk_coaching']}</div>
                </td>
            </tr>
            <tr>
                <td style="background: #f9fbf9; border: 1px solid #eaeaea; border-left: 4px solid #27ae60; padding: 15px; border-radius: 8px; vertical-align: top;">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Ucha:</b> Growth Path</div>
                    <div style="font-size: 15px; font-weight: bold; color: #27ae60; margin-bottom: 8px;">{ennea_data['growth_planet']}</div>
                    <div style="font-size: 13px; color: #444; line-height: 1.5;">{ennea_data['growth_coaching']}</div>
                </td>
                <td style="background: #fdfaf9; border: 1px solid #eaeaea; border-left: 4px solid #e74c3c; padding: 15px; border-radius: 8px; vertical-align: top;">
                    <div style="font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;"><b>Neecha:</b> Stress Path</div>
                    <div style="font-size: 15px; font-weight: bold; color: #c0392b; margin-bottom: 8px;">{ennea_data['stress_planet']}</div>
                    <div style="font-size: 13px; color: #444; line-height: 1.5;">{ennea_data['stress_coaching']}</div>
                </td>
            </tr>
        </table>
        
        <h3>Phase 2: The zone of genius</h3>
        <div style="font-size: 13px;">
            {format_section(edu_txt)}
            {format_section(career_txt)}
        </div>
        
        <div class="page-break"></div>

        <h3>Phase 3: The karmic directive</h3>
        <table style="width: 100%; border-collapse: separate; border-spacing: 15px 0; border: none; margin-bottom: 15px;">
            <tr>
                <td style="width: 50%; background-color: #fafafa; border: 1px solid #eee; padding: 15px; border-radius: 6px; vertical-align: top;">
                    <h4 style="color: #34495e; margin-top: 0; margin-bottom: 8px; font-size: 14px;">Zone of Ambition (Rahu in H{rahu_h})</h4>
                    <p style="font-size: 13px; color: #444; margin: 0; line-height: 1.5;">This is where you must actively disrupt your comfort zone. Specifically, this points to <b>{rahu_domain}</b>. Growth here feels unnatural but yields massive executive returns. Lean heavily into this sector to scale your success.</p>
                </td>
                <td style="width: 50%; background-color: #fafafa; border: 1px solid #eee; padding: 15px; border-radius: 6px; vertical-align: top;">
                    <h4 style="color: #7f8c8d; margin-top: 0; margin-bottom: 8px; font-size: 14px;">Zone of Detachment (Ketu in H{ketu_h})</h4>
                    <p style="font-size: 13px; color: #444; margin: 0; line-height: 1.5;">This is your area of innate mastery. Specifically, this points to <b>{ketu_domain}</b>. You are already naturally gifted here, but obsessing over it will stall your career. Delegate these tasks and use them only as a foundational strength.</p>
                </td>
            </tr>
        </table>

        <h3>Phase 4: The 3 rules for success</h3>
        <div style="background-color: #e8f6f3; border: 1px solid #d1f2eb; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <ol style="margin: 0; padding-left: 20px; font-size: 13px; color: #111; line-height: 1.6;">
                <li style="margin-bottom: 8px;"><b>Protect Your Energy:</b> {coaching_rules[0]}</li>
                <li style="margin-bottom: 8px;"><b>Current Focus:</b> {coaching_rules[1]}</li>
                <li><b>The Ultimate Metric:</b> {coaching_rules[2]}</li>
            </ol>
        </div>

        <h3>Phase 5: The cognitive mechanics</h3>
        <p style="font-size: 13px; color: #666; margin-bottom: 15px;">While your Core Drive (Phase 1) explains <i>why</i> you act, your Cognitive mechanics (<b>{mbti_data['code']}</b>) explains <i>how</i> your brain naturally processes data to get there.</p>
        <div style="max-width: 500px;">
            {draw_mbti_bar_html_pdf("Energy Orientation", e_txt, "EXTRAVERTED", "INTROVERTED", mbti_data['extro_pct'])}
            {draw_mbti_bar_html_pdf("Information Processing", s_txt, "SENSING", "INTUITIVE", 100 - mbti_data['int_pct'])}
            {draw_mbti_bar_html_pdf("Decision Making", t_txt, "THINKING", "FEELING", mbti_data['think_pct'])}
            {draw_mbti_bar_html_pdf("World Structure", j_txt, "JUDGING", "PERCEIVING", mbti_data['judging_pct'])}
        </div>
        
        <div class="page-break"></div>

        <h2>4. Love & Health (Navamsa)</h2>
        <p>This chart represents your deep subconscious, the second half of your life, and the fundamental energetic dynamics of your long-term partnerships.</p>
        {chart2}
        {format_section(love_txt)}
        <hr style="border: 0; border-top: 1px dashed #ccc; margin: 15px 0;">
        {format_section(health_txt)}
        
        <h2>5. Yogas & Forecast</h2>
    """
    
    for y in yogas: 
        html += f"<div style='page-break-inside: avoid;'><h4>{y['Name']} ({y['Type']})</h4><p>{md_to_html(y['Description'])}</p></div>"

    html += f"<h3>Annual Forecast</h3>"
    for cat, data in fc.items():
        parsed_desc = md_to_html(data[0])
        html += f"<div style='page-break-inside: avoid;'><h4>{cat}</h4><p>{parsed_desc}</p><blockquote><b>Remedy:</b> {data[1]}</blockquote></div>"

    html += f"<div style='page-break-inside: avoid;'><h3>Planetary Transits</h3>"
    for txt in transit_texts: 
        html += f"<p>{md_to_html(txt)}</p>"
    html += "</div>"
    
    html += f"""
        <div class="page-break"></div>
        <h2>6. Strategic timeline & mahadashas</h2>
        <table class="timeline">
            <tr><th width="12%">Age</th><th width="14%">Years</th><th width="16%">Dasha</th><th width="58%">Context & Prediction</th></tr>
    """
    dasha_expanded_context = {
        "Suriyan": "This is a phase of intense visibility and authority. Build your personal brand and take decisive actions. Actively manage your ego.",
        "Chandran": "A deeply emotional and intuitive phase. Focus shifts to internal security, home life, and emotional well-being. Adaptability is your greatest asset.",
        "Sevvai": "A high-octane period of aggressive execution and rapid scaling. Tackle massive obstacles and outmaneuver competitors. Channel aggressive energy into structured projects.",
        "Rahu": "A karmic phase characterized by unconventional ambition and breaking boundaries. Expand your footprint, but beware of illusions and stay grounded.",
        "Guru": "A golden era of expansion, wisdom, and ethical growth. Scale your vision, act as a strategic counselor, and accumulate assets.",
        "Sani": "The ultimate phase of structural discipline and delayed gratification. Build unshakeable infrastructure and master your craft through sheer endurance.",
        "Budhan": "A highly stimulating period focused on intellect, communication, and commercial trade. Ideal time for strategic planning and data-driven decision-making.",
        "Ketu": "A profound period of spiritual detachment and highly specialized mastery. Deep, isolated research, backend development, and letting go of things that no longer serve you.",
        "Sukran": "A vibrant phase of aesthetic refinement, diplomacy, and material comfort. Build elite alliances and cultivate harmonious environments."
    }
    for row in mahadasha_data:
        years_one_line = row['Years'].replace(' - ', ' &ndash; ')
        rich_context = dasha_expanded_context.get(row['Mahadasha'], row['Prediction'])
        html += f"<tr><td>{row['Age (From-To)']}</td><td>{years_one_line}</td><td><b>{row['Mahadasha']}</b></td><td>{rich_context}</td></tr>"
    html += "</table>"

    html += f"<div class='footer'>Generated by Vedic Astro AI Engine</div></body></html>"
    
    try:
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes, None 
    except Exception as e:
        return None, str(e)

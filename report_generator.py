from database import ZODIAC, TAMIL_NAMES
from astro_engine import ZODIAC_TA

def get_south_indian_chart_html(p_pos, lagna_rasi, title, lang="English"):
    g = {i: [] for i in range(1, 13)}
    g[lagna_rasi].append("<span style='color:#e74c3c; font-size:12px;'><b>Asc</b></span>")
    for p, r in p_pos.items():
        name = TAMIL_NAMES.get(p, p[:2]) if lang == "Tamil" else p[:2]
        g[r].append(f"<span style='font-size:12px; font-weight:bold; color:#2c3e50;'>{name}</span>")
    for i in g: g[i] = "<br>".join(g[i])
    z = ZODIAC_TA if lang == "Tamil" else ZODIAC
    def get_z(idx): return z.get(idx, "") if isinstance(z, dict) else (z[idx] if idx < len(z) else "")
        
    return f"<div style='max-width: 450px; margin: auto; font-family: sans-serif;'><table style='width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; background-color: #ffffff; border: 2px solid #333;'><tr><td style='border: 1px solid #333; width: 25%; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(12)} (12)</div>{g[12]}</td><td style='border: 1px solid #333; width: 25%; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(1)} (1)</div>{g[1]}</td><td style='border: 1px solid #333; width: 25%; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(2)} (2)</div>{g[2]}</td><td style='border: 1px solid #333; width: 25%; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(3)} (3)</div>{g[3]}</td></tr><tr><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(11)} (11)</div>{g[11]}</td><td colspan='2' rowspan='2' style='border: none; vertical-align: middle; font-weight: bold; font-size: 16px; color:#2c3e50; background-color: #ffffff;'>{title}</td><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(4)} (4)</div>{g[4]}</td></tr><tr><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(10)} (10)</div>{g[10]}</td><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(5)} (5)</div>{g[5]}</td></tr><tr><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(9)} (9)</div>{g[9]}</td><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(8)} (8)</div>{g[8]}</td><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(7)} (7)</div>{g[7]}</td><td style='border: 1px solid #333; height: 95px; vertical-align: top; padding: 5px; background-color:#fafafa;'><div style='font-size:11px; color:#7f8c8d; text-align:left;'>{get_z(6)} (6)</div>{g[6]}</td></tr></table></div>"

def generate_html_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, phases, pd_info, guide, transit_texts, lang="English"):
    
    def format_section(text_list):
        out = ""
        for line in text_list:
            if line.startswith("#### "): out += f"<h4>{line.replace('#### ', '')}</h4>"
            else: out += f"<p>{line}</p>"
        return out

    h_title = f"ஜோதிட அறிக்கை: {name_in}" if lang == "Tamil" else f"Vedic Astrology Premium Report: {name_in}"
    l_lbl = "லக்னம்" if lang == "Tamil" else "Lagna"
    m_lbl = "ராசி" if lang == "Tamil" else "Moon"
    s_lbl = "நட்சத்திரம்" if lang == "Tamil" else "Star"

    chart1 = get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if lang == "Tamil" else "Rasi Chart", lang)
    d9_lagna_idx = p_d9.get("Lagna", 1) 
    chart2 = get_south_indian_chart_html(p_d9, d9_lagna_idx, "நவாம்சம்" if lang == "Tamil" else "Navamsa", lang)

    score_html = "<table class='bar-chart'>"
    for i in range(12):
        house_num = i + 1
        score = sav_scores[(lagna_rasi - 1 + i) % 12]
        bar_w = int((score / 45) * 100)
        color_class = "high" if score >= 30 else "low" if score < 25 else ""
        lbl = "பாவம்" if lang == "Tamil" else "H"
        score_html += f"<tr><td width='15%'><b>{lbl} {house_num}</b></td><td width='75%'><div class='bar {color_class}' style='width: {bar_w}%;'></div></td><td width='10%'><b>{score}</b></td></tr>"
    score_html += "</table>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{h_title}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; padding: 40px; max-width: 900px; margin: auto; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; font-size: 28px; }}
        h2 {{ color: #2980b9; margin-top: 40px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 22px; page-break-after: avoid; }}
        h4 {{ color: #2c3e50; margin-bottom: 5px; font-size: 16px; margin-top: 20px; }}
        p {{ margin-top: 5px; text-align: justify; font-size: 15px; color: #444; }}
        .subtitle {{ text-align: center; font-style: italic; color: #7f8c8d; margin-bottom: 40px; font-size: 16px; }}
        .bar-chart {{ width: 100%; border-collapse: collapse; margin-top: 20px; page-break-inside: avoid; font-size: 15px; }}
        .bar-chart td {{ padding: 8px 0; vertical-align: middle; border-bottom: 1px dashed #eee; }}
        .bar {{ background-color: #95a5a6; height: 22px; border-radius: 4px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.1); }}
        .bar.high {{ background-color: #27ae60; }}
        .bar.low {{ background-color: #e74c3c; }}
        .page-break {{ page-break-before: always; margin-top: 40px; }}
        .footer {{ text-align: center; font-size: 13px; color: #95a5a6; margin-top: 60px; border-top: 1px solid #eee; padding-top: 20px; }}
    </style>
    </head>
    <body>
        <h1>{h_title}</h1>
        <div class="subtitle"><b>{l_lbl}:</b> {lagna_str} &nbsp;|&nbsp; <b>{m_lbl}:</b> {moon_str} &nbsp;|&nbsp; <b>{s_lbl}:</b> {star_str}</div>

        <h2>{"1. சுயவிவரம் (Identity)" if lang == "Tamil" else "1. Identity & Personality"}</h2>
        <p><b>{"நோக்கம்" if lang=="Tamil" else "Purpose"}:</b> {id_data.get('Purpose', '')}</p>
        <p><b>{"குணம்" if lang=="Tamil" else "Personality"}:</b> {id_data.get('Personality', '')}</p>

        <h2>{"2. ராசி சக்கரம் (Rasi Chakra)" if lang == "Tamil" else "2. Birth Chart (Rasi Chakra)"}</h2>
        {chart1}

        <h2>{"3. அஷ்டகவர்க்கம் (Destiny Radar)" if lang == "Tamil" else "3. Destiny Radar (Scorecard)"}</h2>
        {score_html}
        <div class="page-break"></div>
    """
    html += f"<div class='footer'>{'வேத ஜோதிட என்ஜின் மூலம் உருவாக்கப்பட்டது' if lang == 'Tamil' else 'Generated by Astrological Engine'}</div></body></html>"
    return html.encode('utf-8')

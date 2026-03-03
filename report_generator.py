import re
from weasyprint import HTML
from database import ZODIAC
from astro_engine import ZODIAC_TA, t_p_eng

def get_south_indian_chart_html(p_pos, lagna_rasi, title, lang="English"):
    g = {i: [] for i in range(1, 13)}
    
    # Lagna Text
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
        lagna_gradient = "background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 49.2%, rgba(231,76,60,0.3) 49.5%, rgba(231,76,60,0.3) 50.5%, rgba(255,255,255,0) 50.8%, rgba(255,255,255,0) 100%), #fdfdfa;"
        standard_bg = "background-color: #fafafa;"
        style = f"border: 1px solid #bdc3c7; width: 25%; height: 115px; min-height: 115px; max-height: 115px; vertical-align: top; padding: 6px; overflow: hidden; box-sizing: border-box; "
        style += lagna_gradient if is_lagna else standard_bg
        
        return f"<td style='{style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(idx)} ({idx})</div>{g[idx]}</td>"

    return f"""
    <div style='max-width: 450px; margin: auto; font-family: sans-serif;'>
        <table style='width: 100%; table-layout: fixed; border-collapse: collapse; text-align: center; font-size: 14px; background-color: #ffffff; border: 2px solid #333; box-shadow: 0 4px 8px rgba(0,0,0,0.05);'>
            <tr>{cell(12)}{cell(1)}{cell(2)}{cell(3)}</tr>
            <tr>{cell(11)}<td colspan='2' rowspan='2' style='border: none; vertical-align: middle; font-weight: bold; font-size: 16px; color:#2c3e50; background-color: #ffffff;'>{title}</td>{cell(4)}</tr>
            <tr>{cell(10)}{cell(5)}</tr>
            <tr>{cell(9)}{cell(8)}{cell(7)}{cell(6)}</tr>
        </table>
    </div>
    """

def generate_pdf_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, karmic_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, phases, pd_info, guide, transit_texts, lang="English"):
    
    def format_section(text_list):
        out = ""
        for line in text_list:
            if line.startswith("#### "): 
                out += f"<h4>{line.replace('#### ', '')}</h4>"
            elif line.startswith("> "): 
                parsed_quote = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line.replace('> ', ''))
                parsed_quote = re.sub(r'\*(.*?)\*', r'<i>\1</i>', parsed_quote)
                out += f"<blockquote style='background:#fdfae6; border-left:4px solid #f1c40f; padding:10px; margin:10px 0; font-size:13px;'>{parsed_quote}</blockquote>"
            else: 
                html_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                html_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html_line)
                out += f"<p>{html_line}</p>"
        return out

    h_title = f"ஜோதிட அறிக்கை: {name_in}" if lang == "Tamil" else f"Vedic Astrology Premium Report: {name_in}"
    chart1 = get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if lang == "Tamil" else "Rasi Chart", lang)
    d9_lagna_idx = p_d9.get("Lagna", 1)
    chart2 = get_south_indian_chart_html(p_d9, d9_lagna_idx, "நவாம்சம்" if lang == "Tamil" else "Navamsa", lang)

    score_html = "<table class='bar-chart'>"
    for i in range(12):
        score = sav_scores[(lagna_rasi - 1 + i) % 12]
        color_class = "high" if score >= 30 else "low" if score < 25 else ""
        score_html += f"<tr><td width='15%'><b>H {i+1}</b></td><td width='75%'><div class='bar {color_class}' style='width: {int((score/45)*100)}%;'></div></td><td width='10%'><b>{score}</b></td></tr>"
    score_html += "</table>"

    html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><title>{h_title}</title>
    <style>
        @page {{ size: A4; margin: 15mm; }}
        body {{ font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.5; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; font-size: 24px; }}
        h2 {{ color: #2980b9; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 18px; page-break-after: avoid; }}
        h4 {{ color: #2c3e50; margin-top: 15px; margin-bottom: 5px; font-size: 14px; }}
        p {{ margin-top: 5px; font-size: 13px; text-align: justify; color: #444; }}
        .bar-chart {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
        .bar-chart td {{ padding: 6px 0; border-bottom: 1px dashed #eee; vertical-align: middle; }}
        .bar {{ background-color: #95a5a6; height: 16px; border-radius: 3px; }}
        .bar.high {{ background-color: #27ae60; }}
        .bar.low {{ background-color: #e74c3c; }}
        .page-break {{ page-break-before: always; }}
        table.timeline {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; page-break-inside: auto; }}
        table.timeline th, table.timeline td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; vertical-align: top; }}
        table.timeline th {{ background-color: #f0f3f4; color: #2c3e50; font-weight: bold; }}
        .footer {{ text-align: center; font-size: 11px; color: #95a5a6; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; }}
    </style></head><body>
        <h1>{h_title}</h1>
        <p style="text-align:center; font-size:14px;"><b>Lagna:</b> {lagna_str} | <b>Moon:</b> {moon_str} | <b>Star:</b> {star_str}</p>
        
        <h2>{"1. சுயவிவரம் (Identity)" if lang == "Tamil" else "1. Identity"}</h2>
        <p><b>Purpose:</b> {id_data.get('Purpose', '')}</p>
        
        <h2>{"2. ராசி சக்கரம் (Rasi Chart)" if lang == "Tamil" else "2. Rasi Chart"}</h2>{chart1}
        
        <h2>{"3. அஷ்டகவர்க்கம் (Destiny Radar)" if lang == "Tamil" else "3. Destiny Radar"}</h2>{score_html}
        
        <div class="page-break"></div>
        
        <h2>{"4. கல்வி, தொழில் மற்றும் கர்மம் (Work & Karma)" if lang == "Tamil" else "4. Work, Intellect & Karma"}</h2>
        {format_section(edu_txt)}
        <hr style="border: 0; border-top: 1px dashed #ccc; margin: 15px 0;">
        {format_section(career_txt)}
        <hr style="border: 0; border-top: 1px dashed #ccc; margin: 15px 0;">
        {format_section(karmic_txt)}
        
        <h2>{"5. நவாம்சம் மற்றும் திருமணம் (Marriage)" if lang == "Tamil" else "5. Navamsa & Marriage"}</h2>
        <div style="margin-bottom: 15px;">{chart2}</div>
        {format_section(love_txt)}
        
        <h2>{"6. ஆரோக்கியம் (Health & Vitality)" if lang == "Tamil" else "6. Health & Vitality"}</h2>
        {format_section(health_txt)}
        
        <div class="page-break"></div>
        
        <h2>{"7. யோகங்கள் (Wealth Combinations)" if lang == "Tamil" else "7. Wealth & Power Yogas"}</h2>
    """
    
    # Add Yogas
    for y in yogas: 
        html += f"<h4>{y['Name']} ({y['Type']})</h4><p>{re.sub(r'\\*\\*(.*?)\\*\\*', r'<b>\1</b>', y['Description'])}</p>"

    # Add Forecast
    html += f"<h2>{'8. வருடாந்திர கணிப்பு (Annual Forecast)' if lang == 'Tamil' else '8. Annual Forecast'}</h2>"
    for cat, data in fc.items():
        parsed_desc = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', data[0])
        rem_lbl = "பரிகாரம்" if lang == "Tamil" else "Remedy"
        html += f"<h4>{cat}</h4><p>{parsed_desc}</p><blockquote style='background:#fdfae6; border-left:4px solid #f1c40f; padding:8px 12px; margin:5px 0; font-size:13px;'><b>{rem_lbl}:</b> {data[1]}</blockquote>"

    # Add Transits
    html += f"<h2>{'9. முக்கிய கிரகப் பெயர்ச்சிகள் (Transits)' if lang == 'Tamil' else '9. Planetary Transits'}</h2>"
    for txt in transit_texts: 
        html += f"<p>{re.sub(r'\\*\\*(.*?)\\*\\*', r'<b>\1</b>', txt)}</p>"

    # Add Roadmap Table
    age_lbl = "வயது" if lang == "Tamil" else "Age"
    yr_lbl = "ஆண்டுகள்" if lang == "Tamil" else "Years"
    md_lbl = "மகா தசை" if lang == "Tamil" else "Mahadasha"
    pred_lbl = "கணிப்பு" if lang == "Tamil" else "Context & Prediction"
    
    html += f"""
        <div class="page-break"></div>
        <h2>{"10. தசா புக்தி (Strategic Roadmap)" if lang == "Tamil" else "10. Strategic Roadmap"}</h2>
        <table class="timeline">
            <tr><th width="12%">{age_lbl}</th><th width="13%">{yr_lbl}</th><th width="15%">{md_lbl}</th><th width="60%">{pred_lbl}</th></tr>
    """
    for row in mahadasha_data:
        html += f"<tr><td>{row['Age (From-To)']}</td><td>{row['Years']}</td><td><b>{row['Mahadasha']}</b></td><td>{row['Prediction']}</td></tr>"
    html += "</table>"

    html += f"<div class='footer'>{'வேத ஜோதிட என்ஜின் மூலம் உருவாக்கப்பட்டது' if lang == 'Tamil' else 'Generated by Vedic Astro AI Engine'}</div></body></html>"
    
    # Generate the PDF with WeasyPrint
    try:
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes
    except Exception as e:
        return f"PDF Error: {e}. Check WeasyPrint dependencies.".encode('utf-8')

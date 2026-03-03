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
        # Cleaner, safer gradient rendering for WeasyPrint
        lagna_gradient = "background: linear-gradient(135deg, transparent 49%, rgba(231,76,60,0.3) 49.5%, rgba(231,76,60,0.3) 50.5%, transparent 51%), #fdfdfa;"
        standard_bg = "background-color: #fafafa;"
        style = f"border: 1px solid #bdc3c7; width: 25%; height: 110px; vertical-align: top; padding: 6px; box-sizing: border-box; "
        style += lagna_gradient if is_lagna else standard_bg
        return f"<td style='{style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(idx)} ({idx})</div>{g[idx]}</td>"

    # We wrap the chart in 'page-break-inside: avoid;' so it never tears across pages
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

def generate_pdf_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, karmic_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, phases, pd_info, guide, transit_texts, lang="English"):
    
    def md_to_html(text):
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) 
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)     
        return text

    def format_section(text_list):
        out = ""
        for line in text_list:
            line = line.strip()
            if not line: continue
            if line.startswith("#### "): 
                out += f"<h4>{line.replace('#### ', '')}</h4>"
            elif line.startswith("> "): 
                parsed_quote = md_to_html(line.replace('> ', ''))
                out += f"<blockquote>{parsed_quote}</blockquote>"
            else: 
                out += f"<p>{md_to_html(line)}</p>"
        return out

    h_title = f"ஜோதிட அறிக்கை: {name_in}" if lang == "Tamil" else f"Vedic Astrology Premium Report: {name_in}"
    chart1 = get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if lang == "Tamil" else "Rasi Chart", lang)
    d9_lagna_idx = p_d9.get("Lagna", 1)
    chart2 = get_south_indian_chart_html(p_d9, d9_lagna_idx, "நவாம்சம்" if lang == "Tamil" else "Navamsa", lang)

    # Added page-break protections to the Bar Chart
    score_html = "<div style='page-break-inside: avoid;'><table class='bar-chart'>"
    for i in range(12):
        score = sav_scores[(lagna_rasi - 1 + i) % 12]
        color = "#27ae60" if score >= 30 else "#e74c3c" if score < 25 else "#95a5a6"
        bar_w = int((score / 45) * 100)
        score_html += f"<tr><td style='width: 15%;'><b>H {i+1}</b></td><td style='width: 75%;'><div class='bar' style='background-color: {color}; width: {bar_w}%;'></div></td><td style='width: 10%; text-align: right;'><b>{score}</b></td></tr>"
    score_html += "</table></div>"

    html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><title>{h_title}</title>
    <style>
        @page {{ size: A4; margin: 20mm; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.5; font-size: 13px; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; font-size: 22px; margin-bottom: 5px; }}
        .subtitle {{ text-align: center; font-size: 13px; color: #7f8c8d; margin-bottom: 20px; }}
        h2 {{ color: #2980b9; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 16px; page-break-after: avoid; }}
        h4 {{ color: #2c3e50; margin-top: 15px; margin-bottom: 4px; font-size: 14px; page-break-after: avoid; }}
        p {{ margin-top: 5px; margin-bottom: 8px; text-align: justify; color: #444; }}
        .bar-chart {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }}
        .bar-chart td {{ padding: 6px 0; border-bottom: 1px dashed #eee; vertical-align: middle; }}
        .bar {{ height: 16px; border-radius: 3px; }}
        .page-break {{ page-break-before: always; }}
        table.timeline {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }}
        table.timeline th, table.timeline td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; vertical-align: top; }}
        table.timeline tr {{ page-break-inside: avoid; }}
        table.timeline th {{ background-color: #f0f3f4; color: #2c3e50; font-weight: bold; }}
        blockquote {{ background: #fdfae6; border-left: 4px solid #f1c40f; padding: 10px 15px; margin: 10px 0; font-size: 12.5px; page-break-inside: avoid; }}
        .footer {{ text-align: center; font-size: 11px; color: #95a5a6; margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; page-break-inside: avoid; }}
    </style></head><body>
        <h1>{h_title}</h1>
        <div class="subtitle"><b>Lagna:</b> {lagna_str} | <b>Moon:</b> {moon_str} | <b>Star:</b> {star_str}</div>
        
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
        {chart2}
        {format_section(love_txt)}
        
        <h2>{"6. ஆரோக்கியம் (Health & Vitality)" if lang == "Tamil" else "6. Health & Vitality"}</h2>
        {format_section(health_txt)}
        
        <div class="page-break"></div>
        
        <h2>{"7. யோகங்கள் (Wealth Combinations)" if lang == "Tamil" else "7. Wealth & Power Yogas"}</h2>
    """
    
    # Wrap each Yoga in a block so the title and description don't split across pages
    for y in yogas: 
        html += f"<div style='page-break-inside: avoid;'><h4>{y['Name']} ({y['Type']})</h4><p>{md_to_html(y['Description'])}</p></div>"

    html += f"<h2>{'8. வருடாந்திர கணிப்பு (Annual Forecast)' if lang == 'Tamil' else '8. Annual Forecast'}</h2>"
    for cat, data in fc.items():
        parsed_desc = md_to_html(data[0])
        rem_lbl = "பரிகாரம்" if lang == "Tamil" else "Remedy"
        html += f"<div style='page-break-inside: avoid;'><h4>{cat}</h4><p>{parsed_desc}</p><blockquote><b>{rem_lbl}:</b> {data[1]}</blockquote></div>"

    html += f"<div style='page-break-inside: avoid;'><h2>{'9. முக்கிய கிரகப் பெயர்ச்சிகள் (Transits)' if lang == 'Tamil' else '9. Planetary Transits'}</h2>"
    for txt in transit_texts: 
        html += f"<p>{md_to_html(txt)}</p>"
    html += "</div>"

    age_lbl = "வயது" if lang == "Tamil" else "Age"
    yr_lbl = "ஆண்டுகள்" if lang == "Tamil" else "Years"
    md_lbl = "மகா தசை" if lang == "Tamil" else "Mahadasha"
    pred_lbl = "கணிப்பு" if lang == "Tamil" else "Context & Prediction"
    
    html += f"""
        <div class="page-break"></div>
        <h2>{"10. தசா புக்தி (Strategic Roadmap)" if lang == "Tamil" else "10. Strategic Roadmap"}</h2>
        <table class="timeline">
            <tr><th width="12%">{age_lbl}</th><th width="14%">{yr_lbl}</th><th width="16%">{md_lbl}</th><th width="58%">{pred_lbl}</th></tr>
    """
    for row in mahadasha_data:
        html += f"<tr><td>{row['Age (From-To)']}</td><td>{row['Years'].replace(' - ', '<br>')}</td><td><b>{row['Mahadasha']}</b></td><td>{row['Prediction']}</td></tr>"
    html += "</table>"

    html += f"<div class='footer'>{'வேத ஜோதிட என்ஜின் மூலம் உருவாக்கப்பட்டது' if lang == 'Tamil' else 'Generated by Vedic Astro AI Engine'}</div></body></html>"
    
    try:
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes, None 
    except Exception as e:
        return None, str(e)

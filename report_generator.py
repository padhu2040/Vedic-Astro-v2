import re
import io
from xhtml2pdf import pisa
from database import ZODIAC
from astro_engine import ZODIAC_TA, t_p_eng

def get_south_indian_chart_html(p_pos, lagna_rasi, title, lang="English"):
    g = {i: [] for i in range(1, 13)}
    
    g[lagna_rasi].append("<font color='#e74c3c'><b>Asc (Lagna)</b></font><br/>")
    
    for p, r in p_pos.items():
        if p == "Lagna": continue
        name = t_p_eng.get(p, p[:2]) if lang == "English" else p[:2]
        g[r].append(f"<font color='#2c3e50'><b>{name}</b></font><br/>")
    
    for i in g: g[i] = "".join(g[i])
    
    z = ZODIAC_TA if lang == "Tamil" else ZODIAC
    def get_z(idx): return z.get(idx, "") if isinstance(z, dict) else (z[idx] if idx < len(z) else "")
        
    def cell(idx):
        is_lagna = (idx == lagna_rasi)
        bg_color = "#fef0f0" if is_lagna else "#ffffff"
        return f"<td width='25%' valign='top' style='border: 1px solid #333; padding: 5px; background-color: {bg_color}; height: 90px;'><div style='font-size:10px; color:#7f8c8d; margin-bottom: 4px;'>{get_z(idx)} ({idx})</div><div style='text-align:center; font-size:12px; line-height: 1.2;'>{g[idx]}</div></td>"

    return f"""
    <table cellpadding='0' cellspacing='0' style='width: 100%; border-collapse: collapse; border: 2px solid #333;'>
        <tr>{cell(12)}{cell(1)}{cell(2)}{cell(3)}</tr>
        <tr>
            {cell(11)}
            <td colspan='2' rowspan='2' align='center' valign='middle' style='border: none; font-weight: bold; font-size: 16px; color:#2c3e50; background-color: #ffffff;'>{title}</td>
            {cell(4)}
        </tr>
        <tr>{cell(10)}{cell(5)}</tr>
        <tr>{cell(9)}{cell(8)}{cell(7)}{cell(6)}</tr>
    </table>
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
                clean_quote = md_to_html(line.replace('> ', ''))
                out += f"<div style='background-color:#fdfae6; border-left:4px solid #f1c40f; padding:8px; margin:8px 0; font-size:12px;'>{clean_quote}</div>"
            else: 
                out += f"<p>{md_to_html(line)}</p>"
        return out

    h_title = f"ஜோதிட அறிக்கை: {name_in}" if lang == "Tamil" else f"Vedic Astrology Premium Report: {name_in}"
    chart1 = get_south_indian_chart_html(p_pos, lagna_rasi, "ராசி சக்கரம்" if lang == "Tamil" else "Rasi Chart", lang)
    d9_lagna_idx = p_d9.get("Lagna", 1)
    chart2 = get_south_indian_chart_html(p_d9, d9_lagna_idx, "நவாம்சம்" if lang == "Tamil" else "Navamsa", lang)

    score_html = "<table style='width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px;'>"
    for i in range(12):
        score = sav_scores[(lagna_rasi - 1 + i) % 12]
        color = "#27ae60" if score >= 30 else "#e74c3c" if score < 25 else "#95a5a6"
        bar_w = int((score / 45) * 100)
        score_html += f"<tr><td style='width: 15%; padding: 4px 0; border-bottom: 1px solid #eee;'><b>H {i+1}</b></td><td style='width: 75%; border-bottom: 1px solid #eee;'><div style='background-color: {color}; width: {bar_w}%; height: 12px;'></div></td><td style='width: 10%; text-align: right; border-bottom: 1px solid #eee;'><b>{score}</b></td></tr>"
    score_html += "</table>"

    html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8"><title>{h_title}</title>
    <style>
        @page {{ size: A4; margin: 1.5cm; }}
        body {{ font-family: Helvetica, Arial, sans-serif; color: #333; line-height: 1.4; font-size: 12px; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 5px; font-size: 20px; }}
        h2 {{ color: #2980b9; margin-top: 15px; border-bottom: 1px solid #eee; padding-bottom: 3px; font-size: 16px; }}
        h4 {{ color: #2c3e50; margin-top: 10px; margin-bottom: 2px; font-size: 13px; }}
        p {{ margin-top: 3px; text-align: justify; color: #444; }}
        .footer {{ text-align: center; font-size: 10px; color: #95a5a6; margin-top: 20px; border-top: 1px solid #eee; padding-top: 5px; }}
    </style></head><body>
        <h1>{h_title}</h1>
        <p style="text-align:center; font-size:13px;"><b>Lagna:</b> {lagna_str} | <b>Moon:</b> {moon_str} | <b>Star:</b> {star_str}</p>
        
        <h2>{"1. சுயவிவரம் (Identity)" if lang == "Tamil" else "1. Identity"}</h2>
        <p><b>Purpose:</b> {id_data.get('Purpose', '')}</p>
        
        <h2>{"2. ராசி சக்கரம் (Rasi Chart)" if lang == "Tamil" else "2. Rasi Chart"}</h2><br/>{chart1}
        
        <h2>{"3. அஷ்டகவர்க்கம் (Destiny Radar)" if lang == "Tamil" else "3. Destiny Radar"}</h2>{score_html}
        
        <pdf:nextpage />
        
        <h2>{"4. கல்வி, தொழில் மற்றும் கர்மம் (Work & Karma)" if lang == "Tamil" else "4. Work, Intellect & Karma"}</h2>
        {format_section(edu_txt)}
        {format_section(career_txt)}
        {format_section(karmic_txt)}
        
        <h2>{"5. நவாம்சம் மற்றும் திருமணம் (Marriage)" if lang == "Tamil" else "5. Navamsa & Marriage"}</h2>
        <br/>{chart2}<br/>
        {format_section(love_txt)}
        
        <h2>{"6. ஆரோக்கியம் (Health & Vitality)" if lang == "Tamil" else "6. Health & Vitality"}</h2>
        {format_section(health_txt)}
        
        <pdf:nextpage />
        
        <h2>{"7. யோகங்கள் (Wealth Combinations)" if lang == "Tamil" else "7. Wealth & Power Yogas"}</h2>
    """
    
    for y in yogas: 
        html += f"<h4>{y['Name']} ({y['Type']})</h4><p>{md_to_html(y['Description'])}</p>"

    html += f"<h2>{'8. வருடாந்திர கணிப்பு (Annual Forecast)' if lang == 'Tamil' else '8. Annual Forecast'}</h2>"
    for cat, data in fc.items():
        parsed_desc = md_to_html(data[0])
        rem_lbl = "பரிகாரம்" if lang == "Tamil" else "Remedy"
        html += f"<h4>{cat}</h4><p>{parsed_desc}</p><div style='background-color:#fdfae6; border-left:4px solid #f1c40f; padding:6px; margin:3px 0;'><b>{rem_lbl}:</b> {data[1]}</div>"

    html += f"<h2>{'9. முக்கிய கிரகப் பெயர்ச்சிகள் (Transits)' if lang == 'Tamil' else '9. Planetary Transits'}</h2>"
    for txt in transit_texts: 
        html += f"<p>{md_to_html(txt)}</p>"

    age_lbl = "வயது" if lang == "Tamil" else "Age"
    yr_lbl = "ஆண்டுகள்" if lang == "Tamil" else "Years"
    md_lbl = "மகா தசை" if lang == "Tamil" else "Mahadasha"
    pred_lbl = "கணிப்பு" if lang == "Tamil" else "Context & Prediction"
    
    html += f"""
        <pdf:nextpage />
        <h2>{"10. தசா புக்தி (Strategic Roadmap)" if lang == "Tamil" else "10. Strategic Roadmap"}</h2>
        <table cellpadding="4" style="width: 100%; border-collapse: collapse; font-size: 11px;">
            <tr style="background-color: #f0f3f4;">
                <th style="border-bottom: 1px solid #333; text-align:left; width: 12%;">{age_lbl}</th>
                <th style="border-bottom: 1px solid #333; text-align:left; width: 15%;">{yr_lbl}</th>
                <th style="border-bottom: 1px solid #333; text-align:left; width: 15%;">{md_lbl}</th>
                <th style="border-bottom: 1px solid #333; text-align:left; width: 58%;">{pred_lbl}</th>
            </tr>
    """
    for row in mahadasha_data:
        html += f"<tr><td style='border-bottom: 1px solid #eee;' valign='top'>{row['Age (From-To)']}</td><td style='border-bottom: 1px solid #eee;' valign='top'>{row['Years'].replace(' - ', '<br/>')}</td><td style='border-bottom: 1px solid #eee;' valign='top'><b>{row['Mahadasha']}</b></td><td style='border-bottom: 1px solid #eee;' valign='top'>{row['Prediction']}</td></tr>"
    html += "</table>"

    html += f"<div class='footer'>{'வேத ஜோதிட என்ஜின் மூலம் உருவாக்கப்பட்டது' if lang == 'Tamil' else 'Generated by Vedic Astro AI Engine'}</div></body></html>"
    
    result = io.BytesIO()
    try:
        pisa_status = pisa.CreatePDF(io.StringIO(html), dest=result)
        if pisa_status.err:
            return None, "XHTML2PDF Engine encountered an error parsing the HTML."
        return result.getvalue(), None
    except Exception as e:
        return None, str(e)

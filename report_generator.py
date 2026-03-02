import re
import pdfkit
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
        # BEAUTIFUL LAGNA DIAGONAL LINE
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

def generate_pdf_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, phases, pd_info, guide, transit_texts, lang="English"):
    def format_section(text_list):
        out = ""
        for line in text_list:
            if line.startswith("#### "): out += f"<h4>{line.replace('#### ', '')}</h4>"
            else: 
                html_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
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
        body {{ font-family: Helvetica, sans-serif; color: #333; line-height: 1.6; padding: 20px; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        h4 {{ color: #2c3e50; margin-top: 15px; margin-bottom: 5px; }}
        p {{ margin-top: 5px; font-size: 14px; text-align: justify; }}
        .bar-chart {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
        .bar-chart td {{ padding: 6px 0; border-bottom: 1px dashed #eee; }}
        .bar {{ background-color: #95a5a6; height: 18px; border-radius: 4px; }}
        .bar.high {{ background-color: #27ae60; }}
        .bar.low {{ background-color: #e74c3c; }}
        .page-break {{ page-break-before: always; }}
    </style></head><body>
        <h1>{h_title}</h1>
        <p style="text-align:center;"><b>Lagna:</b> {lagna_str} | <b>Moon:</b> {moon_str} | <b>Star:</b> {star_str}</p>
        <h2>Identity</h2><p><b>Purpose:</b> {id_data.get('Purpose', '')}</p>
        <h2>Rasi Chart</h2>{chart1}
        <h2>Destiny Radar</h2>{score_html}
        <div class="page-break"></div>
        <h2>Work & Intellect</h2>{format_section(edu_txt)}{format_section(career_txt)}
        <h2>Navamsa & Marriage</h2>{chart2}{format_section(love_txt)}
        <h2>Health & Vitality</h2>{format_section(health_txt)}
    </body></html>
    """
    
    options = {'page-size': 'A4', 'encoding': "UTF-8", 'enable-local-file-access': None, 'quiet': ''}
    try: return pdfkit.from_string(html, False, options=options)
    except Exception as e: return f"PDF Error: {e}. Add wkhtmltopdf to packages.txt".encode('utf-8')

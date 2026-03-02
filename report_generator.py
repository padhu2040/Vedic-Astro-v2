import pdfkit

def generate_pdf_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, phases, pd_info, guide, transit_texts, lang="English"):
    
    def format_section(text_list):
        out = ""
        for line in text_list:
            if line.startswith("#### "): out += f"<h4>{line.replace('#### ', '')}</h4>"
            else: out += f"<p>{line.replace('**', '<b>').replace('**', '</b>')}</p>"
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
        lbl = "பாவம்" if lang == "Tamil" else "House"
        score_html += f"<tr><td width='15%'><b>{lbl} {house_num}</b></td><td width='75%'><div class='bar {color_class}' style='width: {bar_w}%;'></div></td><td width='10%'><b>{score}</b></td></tr>"
    score_html += "</table>"

    # BUILD THE HTML STRING
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>{h_title}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.6; padding: 20px; }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; font-size: 26px; }}
        h2 {{ color: #2980b9; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 20px; page-break-after: avoid; }}
        h4 {{ color: #2c3e50; margin-bottom: 5px; font-size: 16px; margin-top: 15px; }}
        p {{ margin-top: 5px; text-align: justify; font-size: 14px; color: #444; }}
        .subtitle {{ text-align: center; font-style: italic; color: #7f8c8d; margin-bottom: 30px; font-size: 15px; }}
        
        .bar-chart {{ width: 100%; border-collapse: collapse; margin-top: 15px; page-break-inside: avoid; font-size: 14px; }}
        .bar-chart td {{ padding: 6px 0; vertical-align: middle; border-bottom: 1px dashed #eee; }}
        .bar {{ background-color: #95a5a6; height: 18px; border-radius: 4px; }}
        .bar.high {{ background-color: #27ae60; }}
        .bar.low {{ background-color: #e74c3c; }}
        
        .page-break {{ page-break-before: always; }}
        .footer {{ text-align: center; font-size: 12px; color: #95a5a6; margin-top: 40px; border-top: 1px solid #eee; padding-top: 10px; }}
        
        table.timeline {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; page-break-inside: auto; }}
        table.timeline th, table.timeline td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; vertical-align: top; }}
        table.timeline tr:nth-child(even) {{ background-color: #fcfcfc; }}
        table.timeline th {{ background-color: #f0f3f4; font-weight: bold; color: #2c3e50; }}
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

        <h2>{"4. கல்வி மற்றும் தொழில் (Work & Intellect)" if lang == "Tamil" else "4. Work & Intellect"}</h2>
        {format_section(edu_txt)}
        <hr style="border: 0; border-top: 1px dashed #ccc; margin: 15px 0;">
        {format_section(career_txt)}

        <h2>{"5. திருமணம் (Love & Marriage)" if lang == "Tamil" else "5. Love & Marriage"}</h2>
        <div style="margin-bottom: 15px;">{chart2}</div>
        {format_section(love_txt)}

        <h2>{"6. ஆரோக்கியம் (Health & Vitality)" if lang == "Tamil" else "6. Health & Vitality"}</h2>
        {format_section(health_txt)}

        <div class="page-break"></div>

        <h2>{"7. யோகங்கள் (Wealth & Power Combinations)" if lang == "Tamil" else "7. Wealth & Power Yogas"}</h2>
    """
    
    for y in yogas: html += f"<h4>{y['Name']} ({y['Type']})</h4><p>{y['Description']}</p>"

    html += f"<h2>{'8. வருடாந்திர கணிப்பு (Annual Forecast)' if lang == 'Tamil' else '8. Annual Forecast'}</h2>"
    pred_lbl = "கணிப்பு" if lang == "Tamil" else "Prediction"
    rem_lbl = "பரிகாரம்" if lang == "Tamil" else "Remedy"
    for cat, data in fc.items(): html += f"<h4>{cat}</h4><p><b>{pred_lbl}:</b> {data[0]}<br><span style='color:#e67e22;'><b>{rem_lbl}:</b> {data[1]}</span></p>"

    age_lbl = "வயது" if lang == "Tamil" else "Age"
    yr_lbl = "ஆண்டுகள்" if lang == "Tamil" else "Years"
    md_lbl = "மகா தசை" if lang == "Tamil" else "Mahadasha"
    
    html += f"""
        <div class="page-break"></div>
        <h2>{"9. தசா புக்தி (Strategic Roadmap)" if lang == "Tamil" else "9. Strategic Roadmap"}</h2>
        <table class="timeline">
            <tr><th width="15%">{age_lbl}</th><th width="15%">{yr_lbl}</th><th width="15%">{md_lbl}</th><th width="55%">{pred_lbl}</th></tr>
    """
    for row in mahadasha_data:
        html += f"<tr><td>{row['Age (From-To)']}</td><td>{row['Years']}</td><td><b>{row['Mahadasha']}</b></td><td>{row['Prediction']}</td></tr>"
    html += "</table>"

    html += f"<div class='footer'>{'வேத ஜோதிட என்ஜின் மூலம் உருவாக்கப்பட்டது' if lang == 'Tamil' else 'Generated by Vedic Astro AI Engine'}</div>"
    html += "</body></html>"
    
    # -----------------------------------------
    # PDF GENERATION MAGIC
    # -----------------------------------------
    options = {
        'page-size': 'A4',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'encoding': "UTF-8",
        'enable-local-file-access': None,
        'quiet': ''
    }
    
    try:
        # Convert HTML to PDF bytes
        pdf_bytes = pdfkit.from_string(html, False, options=options)
        return pdf_bytes
    except Exception as e:
        # Fallback error message if wkhtmltopdf isn't installed properly
        return f"PDF Engine Error: {e}. Ensure packages.txt contains wkhtmltopdf.".encode('utf-8')

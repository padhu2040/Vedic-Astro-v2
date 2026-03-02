from database import ZODIAC, TAMIL_NAMES
from astro_engine import ZODIAC_TA

def get_south_indian_chart_html(p_pos, lagna_rasi, title, lang="English"):
    g = {i: [] for i in range(1, 13)}
    g[lagna_rasi].append("<span style='color:#e74c3c; font-size:12px; display:block; margin-bottom:2px;'><b>Asc</b></span>")
    for p, r in p_pos.items():
        name = TAMIL_NAMES.get(p, p[:2]) if lang == "Tamil" else p[:2]
        g[r].append(f"<span style='font-size:12px; font-weight:bold; color:#2c3e50; display:block;'>{name}</span>")
    for i in g: g[i] = "".join(g[i])
    z = ZODIAC_TA if lang == "Tamil" else ZODIAC
    def get_z(idx): return z.get(idx, "") if isinstance(z, dict) else (z[idx] if idx < len(z) else "")
        
    # STRICT CSS: This forces the boxes to be perfectly square and identical in size
    td_style = "border: 1px solid #bdc3c7; width: 25%; height: 110px; min-height: 110px; max-height: 110px; vertical-align: top; padding: 4px; background-color:#fafafa; overflow: hidden; box-sizing: border-box;"
        
    return f"""
    <div style='max-width: 450px; margin: auto; font-family: sans-serif;'>
        <table style='width: 100%; table-layout: fixed; border-collapse: collapse; text-align: center; font-size: 14px; background-color: #ffffff; border: 2px solid #333;'>
            <tr>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(12)} (12)</div>{g[12]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(1)} (1)</div>{g[1]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(2)} (2)</div>{g[2]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(3)} (3)</div>{g[3]}</td>
            </tr>
            <tr>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(11)} (11)</div>{g[11]}</td>
                <td colspan='2' rowspan='2' style='border: none; vertical-align: middle; font-weight: bold; font-size: 16px; color:#2c3e50; background-color: #ffffff;'>{title}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(4)} (4)</div>{g[4]}</td>
            </tr>
            <tr>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(10)} (10)</div>{g[10]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(5)} (5)</div>{g[5]}</td>
            </tr>
            <tr>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(9)} (9)</div>{g[9]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(8)} (8)</div>{g[8]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(7)} (7)</div>{g[7]}</td>
                <td style='{td_style}'><div style='font-size:11px; color:#7f8c8d; text-align:left; margin-bottom:4px;'>{get_z(6)} (6)</div>{g[6]}</td>
            </tr>
        </table>
    </div>
    """

def generate_html_report(name_in, p_pos, p_d9, lagna_rasi, sav_scores, career_txt, edu_txt, health_txt, love_txt, id_data, lagna_str, moon_str, star_str, yogas, fc, micro_transits, mahadasha_data, phases, pd_info, guide, transit_texts, lang="English"):
    # (Placeholder for the Deep Horoscope PDF Exporter to use later)
    return b"<html><body><h1>Report Download Feature Active</h1></body></html>"

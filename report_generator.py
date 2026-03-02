from database import ZODIAC
from astro_engine import ZODIAC_TA, t_p_eng

def get_south_indian_chart_html(p_pos, lagna_rasi, title, lang="English"):
    g = {i: [] for i in range(1, 13)}
    
    # Add Lagna Text
    g[lagna_rasi].append("<span style='color:#e74c3c; font-size:12px; display:block; margin-bottom:2px; font-weight:bold;'>Asc (Lagna)</span>")
    
    for p, r in p_pos.items():
        if p == "Lagna": continue
        # Use Tamil-English names (Suriyan, etc.) if lang is English, else full Tamil script
        name = t_p_eng.get(p, p[:2]) if lang == "English" else p[:2] # Fallback handled in UI
        g[r].append(f"<span style='font-size:12px; font-weight:bold; color:#2c3e50; display:block;'>{name}</span>")
    
    for i in g: g[i] = "".join(g[i])
    
    z = ZODIAC_TA if lang == "Tamil" else ZODIAC
    def get_z(idx): return z.get(idx, "") if isinstance(z, dict) else (z[idx] if idx < len(z) else "")
        
    def cell(idx):
        is_lagna = (idx == lagna_rasi)
        # THE LAGNA DIAGONAL LINE FIX
        lagna_gradient = "background: linear-gradient(135deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0) 49.2%, rgba(231,76,60,0.3) 49.5%, rgba(231,76,60,0.3) 50.5%, rgba(255,255,255,0) 50.8%, rgba(255,255,255,0) 100%), #fdfdfa;"
        standard_bg = "background-color: #fafafa;"
        
        style = f"border: 1px solid #bdc3c7; width: 25%; height: 110px; min-height: 110px; max-height: 110px; vertical-align: top; padding: 6px; overflow: hidden; box-sizing: border-box; "
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

def generate_html_report(*args, **kwargs):
    return b"<html><body><h1>Report Download Placeholder</h1></body></html>"

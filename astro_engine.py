import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from database import DASHA_YEARS, DASHA_ORDER, RASI_RULERS, BINDU_RULES
from tamil_lang import TAMIL_LIFESTYLE

# TRANSLATION DICTIONARIES
t_p = {"Sun": "சூரியன்", "Moon": "சந்திரன்", "Mars": "செவ்வாய்", "Mercury": "புதன்", "Jupiter": "குரு", "Venus": "சுக்கிரன்", "Saturn": "சனி", "Rahu": "ராகு", "Ketu": "கேது", "Lagna": "லக்னம்"}
t_p_eng = {"Sun": "Suriyan", "Moon": "Chandran", "Mars": "Sevvai", "Mercury": "Budhan", "Jupiter": "Guru", "Venus": "Sukran", "Saturn": "Sani", "Rahu": "Rahu", "Ketu": "Ketu", "Lagna": "Lagna"}

ZODIAC_TA = {1: "மேஷம்", 2: "ரிஷபம்", 3: "மிதுனம்", 4: "கடகம்", 5: "சிம்மம்", 6: "கன்னி", 7: "துலாம்", 8: "விருச்சிகம்", 9: "தனுசு", 10: "மகரம்", 11: "கும்பம்", 12: "மீனம்"}
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

# --- TIME & LOCATION ---
def get_location_coordinates(query):
    try:
        if query.strip().isdigit() and len(query.strip()) == 6: query = f"{query}, India"
        location = Nominatim(user_agent="vedic_astro_ai").geocode(query)
        if location: return location.latitude, location.longitude, TimezoneFinder().timezone_at(lng=location.longitude, lat=location.latitude)
    except: pass
    return 13.0827, 80.2707, "Asia/Kolkata"

def get_utc_offset(tz_str, date_obj):
    try:
        tz = pytz.timezone(tz_str)
        if not isinstance(date_obj, datetime): date_obj = datetime.combine(date_obj, datetime(2000, 1, 1, 12, 0).time())
        return tz.localize(date_obj).utcoffset().total_seconds() / 3600
    except: return 5.5 

# --- MATH ---
def get_nakshatra_details(lon):
    nak_names = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    lords = ["Ketu", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Venus"]
    return nak_names[int(lon / 13.333333333)], lords[int(lon / 13.333333333) % 9]

def get_navamsa_chart(lon):
    rasi_num, pada = int(lon / 30) + 1, int((lon % 30) / 3.333333333) + 1
    start = 1 if rasi_num in [1,5,9] else 10 if rasi_num in [2,6,10] else 7 if rasi_num in [3,7,11] else 4
    return (start + pada - 2) % 12 + 1

def get_dasamsa_chart(lon):
    rasi_num, part = int(lon / 30) + 1, int((lon % 30) / 3.0) + 1
    start = rasi_num if rasi_num % 2 != 0 else (rasi_num + 8) % 12 or 12
    return (start + part - 2) % 12 + 1

def get_dignity(p, r):
    own = {"Sun": [5], "Moon": [4], "Mars": [1,8], "Mercury": [3,6], "Jupiter": [9,12], "Venus": [2,7], "Saturn": [10,11]}
    exalted = {"Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 2, "Ketu": 8}
    neecha = {"Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12, "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 8, "Ketu": 2}
    if r in own.get(p, []): return "Own"
    if exalted.get(p) == r: return "Exalted"
    if neecha.get(p) == r: return "Neecha"
    return "Neutral"

def calculate_sav_score(p_pos, lagna):
    scores = [0] * 12
    curr = p_pos.copy(); curr['Lagna'] = lagna
    for p, rules in BINDU_RULES.items():
        if p not in curr: continue
        for ref, offsets in rules.items():
            if ref not in curr: continue
            for off in offsets: scores[(curr[ref] - 1 + off - 1) % 12] += 1
    return scores

def get_bhava_chalit(jd, lat, lon): return swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)[0]

def determine_house(planet_lon, cusps):
    p_lon = planet_lon % 360
    for i in range(12):
        lower, upper = cusps[i], cusps[(i+1)%12]
        if lower < upper:
            if lower <= p_lon < upper: return i + 1
        else:
            if p_lon >= lower or p_lon < upper: return i + 1
    return 1

# --- DEEP TEXT ENGINES ---
def get_house_strength_analysis(house_num, score, lang="English"):
    topics = {
        1: "Self, Vitality & Direction", 2: "Wealth, Family & Speech", 3: "Courage & Self-Effort", 
        4: "Home, Mother & Inner Peace", 5: "Intellect, Creativity & Risk", 6: "Health, Debt & Overcoming Rivals",
        7: "Marriage & Partnerships", 8: "Transformation & Hidden Wealth", 9: "Luck, Wisdom & Fortune", 
        10: "Career & Authority", 11: "Major Gains & Networks", 12: "Spiritual Retreats & Expenditures"
    }
    t_topics = {
        1: "சுய அடையாளம், உடல் ஆரோக்கியம்", 2: "செல்வம், குடும்பம்", 3: "தைரியம், சுயமாக முன்னேறுதல்", 
        4: "வீடு, தாயார், மன அமைதி", 5: "புத்திசாலித்தனம், குழந்தைகள்", 6: "கடன் தீர்வு, எதிரிகளை வெல்லுதல்",
        7: "திருமணம், கூட்டாண்மை", 8: "ரகசியங்கள், எதிர்பாராத மாற்றங்கள்", 9: "பாக்கியம், உயர்கல்வி", 
        10: "தொழில் வெற்றி, அந்தஸ்து", 11: "லாபம், நெட்வொர்க்", 12: "பயணங்கள், முதலீடுகள்"
    }
    
    if score >= 30:
        if lang == "Tamil": return f"**மிகவும் வலிமையான பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) இயற்கையாகவே அதிக சக்தி பெற்றுள்ளது.\n> **பரிகாரம்/வழிகாட்டுதல்:** இந்தத் துறையில் நீங்கள் தைரியமாக புதிய முயற்சிகளை எடுக்கலாம். இது உங்கள் வெற்றிக்கு இயற்கையாகவே உதவும் பிரம்மாஸ்திரம்."
        return f"**Power Zone:** The {house_num}th House ({topics[house_num]}) is exceptionally strong. Energy flows effortlessly here.\n> **Harnessing Guide:** Double down your efforts here. Take calculated risks and assume leadership in this specific area of your life. The universe will support you seamlessly."
    elif score < 25:
        if lang == "Tamil": return f"**கவனம் தேவைப்படும் பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) சற்று பலவீனமாக உள்ளது.\n> **பரிகாரம்/வழிகாட்டுதல்:** இந்தத் துறையில் அவசர முடிவுகளைத் தவிர்க்கவும். அனுபவம் வாய்ந்தவர்களின் ஆலோசனையைப் பெறுவது தடைகளைத் தகர்க்க உதவும்."
        return f"**Challenge Zone:** The {house_num}th House ({topics[house_num]}) requires highly conscious, strategic effort.\n> **Mitigation Guide:** Do not rely on 'luck' here. Apply intense structure, seek external mentorship, and avoid impulsive decisions regarding this house's matters."
    else:
        if lang == "Tamil": return f"**சமநிலையான பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) சீராக உள்ளது. உழைப்பிற்கு ஏற்ற நியாயமான பலன்கள் கிடைக்கும்."
        return f"**Balanced Zone:** The {house_num}th House ({topics[house_num]}) is stable. It operates strictly on the rule of cause and effect. Your direct input equals your direct output."

def analyze_karmic_axis(p_pos, lagna_rasi, lang="English"):
    rahu_h = (p_pos["Rahu"] - lagna_rasi + 1) if (p_pos["Rahu"] - lagna_rasi + 1) > 0 else (p_pos["Rahu"] - lagna_rasi + 1) + 12
    ketu_h = (p_pos.get("Ketu", (p_pos["Rahu"]+6)%12 or 12) - lagna_rasi + 1) if (p_pos.get("Ketu", (p_pos["Rahu"]+6)%12 or 12) - lagna_rasi + 1) > 0 else (p_pos.get("Ketu", (p_pos["Rahu"]+6)%12 or 12) - lagna_rasi + 1) + 12
    res = []
    if lang == "Tamil":
        res.append("#### கர்ம வினை அச்சு (ராகு / கேது தாக்கம்)")
        res.append(f"உங்கள் ஜாதகத்தில் ராகு {rahu_h}-ஆம் வீட்டிலும், கேது {ketu_h}-ஆம் வீட்டிலும் அமர்ந்துள்ளனர். இது உங்களின் ஆன்மீக நோக்கத்தைக் குறிக்கிறது.")
        res.append(f"**ராகுவின் ஆசை ({rahu_h}-ஆம் பாவம்):** இந்தத் துறையில் நீங்கள் மிகப்பெரிய உச்சத்தை தொட வேண்டும் என்ற அளவற்ற ஆசை உங்களுக்குள் இருக்கும். இது இப்பிறவியின் மிகப்பெரிய சவாலாகும்.")
        res.append(f"**கேதுவின் ஞானம் ({ketu_h}-ஆம் பாவம்):** முற்பிறவியிலேயே இந்தத் துறையில் நீங்கள் முழு நிபுணத்துவம் பெற்றுவிட்டீர்கள். எனவே, உங்களுக்கு இயல்பான அறிவும், அதே சமயம் ஒருவித பற்றின்மையும் (Detachment) இருக்கும்.")
    else:
        res.append("#### The Karmic Axis (Rahu & Ketu Impact)")
        res.append(f"Rahu and Ketu operate exactly 180 degrees apart in your {rahu_h}th and {ketu_h}th houses. This axis pulls you between deep past-life comfort and uncharted ambition.")
        res.append(f"**Rahu's Obsession ({rahu_h}th House):** Rahu creates a relentless, almost obsessive hunger for growth in this house. You are meant to take massive, unconventional leaps here to evolve your soul.")
        res.append(f"**Ketu's Mastery & Detachment ({ketu_h}th House):** Ketu signifies deep past-life mastery. You possess effortless, intuitive genius in this area, but you simultaneously feel a profound sense of 'been there, done that' detachment. Use Ketu's deep analytical skills to support Rahu's ambitions.")
    return res

def scan_yogas(p_pos, lagna_rasi, lang="English"):
    yogas = []
    p_houses = {p: ((r - lagna_rasi + 1) if (r - lagna_rasi + 1) > 0 else (r - lagna_rasi + 1) + 12) for p, r in p_pos.items() if p != "Lagna"}
    
    if p_pos.get("Sun") == p_pos.get("Mercury"):
        if lang == "Tamil": yogas.append({"Name": "புதாதித்ய யோகம் (Budhaditya)", "Type": "அறிவு மற்றும் வணிகம்", "Description": f"சூரியனும் புதனும் உங்கள் {p_houses.get('Sun')}-ஆம் வீட்டில் இணைந்து இந்த யோகத்தை உருவாக்குகின்றன. இது மிகச்சிறந்த பகுப்பாய்வு திறனையும், கூர்மையான வணிக அறிவையும் தருகிறது. தசா/புக்தி காலங்களில் இது உங்களுக்கு சிறந்த பெயரையும் பணத்தையும் பெற்றுத் தரும்."})
        else: yogas.append({"Name": "Budhaditya Yoga", "Type": "Intellect & Commerce", "Description": f"Suriyan and Budhan are conjunct in your {p_houses.get('Sun')}th House, forming a highly analytical business mind. **Impact:** It enhances executive communication and creates heavy wealth potential through advisory or trade. You likely noticed this mental edge emerging early in your childhood education."})
    
    if "Jupiter" in p_pos and "Moon" in p_pos:
        jup_from_moon = (p_pos["Jupiter"] - p_pos["Moon"] + 1) if (p_pos["Jupiter"] - p_pos["Moon"] + 1) > 0 else (p_pos["Jupiter"] - p_pos["Moon"] + 1) + 12
        if jup_from_moon in [1, 4, 7, 10]:
            if lang == "Tamil": yogas.append({"Name": "கஜகேசரி யோகம் (Gajakesari)", "Type": "புகழ் மற்றும் தெய்வீக பாதுகாப்பு", "Description": "குரு உங்கள் சந்திரனுக்கு கேந்திரத்தில் இருப்பதால் இந்த மாபெரும் யோகம் உருவாகிறது. இது சமுதாயத்தில் பெரும் மதிப்பையும், எதிரிகளை வெல்லும் சாதுரியத்தையும் தரும். எக்காலத்திலும் உங்களை காக்கும் அரணாக செயல்படும்."})
            else: yogas.append({"Name": "Gajakesari Yoga", "Type": "Fame & Institutional Protection", "Description": "Guru is placed in a foundational angle from your Natal Moon. **Impact:** It grants a noble reputation and strong divine protection against crises. This yoga acts as a lifetime safety net, often resolving major life or financial issues at the 11th hour."})
    
    if not yogas:
        if lang == "Tamil": yogas.append({"Name": "சுயமுயற்சி யோகம்", "Type": "சுயம்புவான வெற்றி", "Description": "உங்கள் ஜாதகம் எந்த ஒரு பாரம்பரிய யோகத்தையும் சார்ந்து இல்லை. உங்கள் வெற்றி முற்றிலும் உங்கள் சுயமுயற்சியாலும், விடாமுயற்சியாலும் மட்டுமே அமையும்."})
        else: yogas.append({"Name": "Independent Karma Yoga", "Type": "Self-Made Destiny", "Description": "Your chart relies purely on active free-will rather than passive, inherited yogas. **Impact:** Every single victory in your life is 100% self-earned. You possess incredible grit, as nothing has been handed to you easily."})
    return yogas

def analyze_education(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(lagna_rasi + 4) % 12 or 12]
    mercury_dig = get_dignity("Mercury", p_pos["Mercury"])
    if lang == "Tamil":
        analysis.append("#### கல்வி மற்றும் அறிவுசார் திறன்")
        analysis.append(f"உங்கள் கல்வி மற்றும் அறிவாற்றலை 5-ஆம் அதிபதியான **{t_p[lord_5]}** தீர்மானிக்கிறார். நீங்கள் எதையும் மேலோட்டமாக படிக்காமல், தர்க்கரீதியாக ஆராய்ந்து ஆழமாகப் புரிந்து கொள்ளும் குணம் கொண்டவர்.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append("புதன் மிகவும் வலுவாக இருப்பதால், சிக்கலான தரவுகளைப் பகுப்பாய்வு செய்யும் அபார திறன் உங்களுக்கு உண்டு. கணக்கீடு, தொழில்நுட்பம் மற்றும் நிதி துறைகளில் உங்களால் மற்றவர்களை எளிதாக முந்த முடியும்.")
        elif mercury_dig == "Neecha": analysis.append("புதன் பலவீனமாக இருப்பதால், வெறும் மனப்பாடம் செய்வதை விட, அனுபவபூர்வமான மற்றும் கற்பனைத்திறன் சார்ந்த கல்வியே உங்களுக்கு உகந்தது.")
        else: analysis.append("உங்களின் தர்க்க அறிவும், கற்கும் திறனும் சீராக உள்ளது. கவனச்சிதறல்களைத் தவிர்த்து ஒருமுகப்படுத்தப்பட்ட பயிற்சியின் மூலம் நீங்கள் எந்தத் துறையிலும் வல்லவராகலாம்.")
    else:
        analysis.append("#### Academic Profile & Strategic Intellect")
        analysis.append(f"Your primary intellect and cognitive processing are governed by the 5th House lord, **{t_p_eng[lord_5]}**. This dictates your unique learning style: you do not just memorize facts; the subject matter must deeply resonate with the core energy of {t_p_eng[lord_5]} for you to master it.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append("Because Budhan (the planet of logic) is highly dignified, your capacity to process, structure, and deploy complex information is elite. You have a distinct, highly analytical advantage in technical, financial, or heavily communicative environments.")
        elif mercury_dig == "Neecha": analysis.append("Your Budhan is mathematically debilitated. This does not imply low intelligence; rather, it indicates you possess highly intuitive, abstract, or creative intelligence. Traditional rote-memorization may frustrate you, but your ability to see the 'big picture' is unparalleled.")
        else: analysis.append("Your logical processing is balanced and adaptable. You are capable of mastering a wide variety of subjects, provided you enforce strict academic discipline and actively guard against daily distractions.")
    return analysis

def analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang="English"):
    analysis = []
    sun_rasi_h = (p_pos['Sun'] - lagna_rasi + 1) if (p_pos['Sun'] - lagna_rasi + 1) > 0 else (p_pos['Sun'] - lagna_rasi + 1) + 12
    sun_bhava_h = bhava_placements['Sun'] 
    d10_lord = RASI_RULERS[(d10_lagna + 9) % 12 or 12]
    
    if lang == "Tamil":
        analysis.append("#### தொழில் மற்றும் செயல் வியூகம்")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"**முக்கிய மாற்றம்:** உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியில் இருந்தாலும், அது {sun_bhava_h}-ஆம் பாவத்திலேயே முழுமையாகச் செயல்படுகிறது. உங்களின் உண்மையான அங்கீகாரம் இந்த பாவத்தின் வழியாகவே கிடைக்கும்.")
        else: analysis.append(f"**நேரடி பலன்:** உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியிலும் பாவத்திலும் சரியாகப் பொருந்தி செயல்படுகிறார். இது உங்கள் சிந்தனைக்கும் செயலுக்கும் இடையே நேரடி ஒத்திசைவை உருவாக்குகிறது.")
        analysis.append("#### தசாம்ச (D10) தலைமைத்துவ ரகசியம்")
        analysis.append(f"உங்கள் தொழில் வெற்றியை நிர்ணயிக்கும் தசாம்ச அதிபதி **{t_p[d10_lord]}**. கார்ப்பரேட் அல்லது வணிகச் சூழலில், நீங்கள் இந்த கிரகத்தின் குணாதிசயங்களை முதன்மையாக பயன்படுத்த வேண்டும். இதுவே உங்களின் மிகப்பெரிய பிரம்மாஸ்திரம்.")
    else:
        analysis.append("#### Career Strategy & True Authority")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"**Crucial Alignment Shift:** Your Suriyan is psychologically seated in the {sun_rasi_h}th Sign, but functionally produces actual worldly results in the {sun_bhava_h}th House. This means you must pivot your career focus to deliver value specifically in {sun_bhava_h}th House matters to gain true recognition.")
        else: analysis.append(f"**Direct Alignment:** Your Suriyan perfectly aligns in both Sign and House ({sun_rasi_h}th). Your internal psychological drive perfectly matches the external leadership the world expects of you.")
        analysis.append("#### The CEO Engine (Dasamsa D10)")
        analysis.append(f"Your deepest professional capability is revealed in the D10 chart. Your Dasamsa Career Lord is **{t_p_eng[d10_lord]}**. In high-pressure environments, meetings, or executive decisions, you must completely lean into the core traits of {t_p_eng[d10_lord]}. Do not try to copy others' management styles; your unique competitive advantage lies strictly in operating through {t_p_eng[d10_lord]}'s specific energy.")
    return analysis

def analyze_love_marriage(d1_lagna, d9_lagna, p_d9, p_d1, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(d1_lagna + 4) % 12 or 12]
    d9_7th_lord = RASI_RULERS[(d9_lagna + 6) % 12 or 12]
    
    traits = {
        "Sun": "absolute loyalty, dignified leadership, and taking immense mutual pride in each other's public status",
        "Moon": "deep emotional empathy, nurturing domestic care, and highly intuitive understanding without words",
        "Mars": "protective action, setting clear boundaries, and guarding the relationship fiercely against outsiders",
        "Mercury": "crystal-clear communication, intellectual banter, and treating each other fundamentally as best friends",
        "Jupiter": "moral grounding, shared philosophical or religious growth, and mature wisdom",
        "Venus": "unconditional romantic devotion, aesthetic harmony in the home, and actively prioritizing peace",
        "Saturn": "unshakeable duty, absolute loyalty through financial hardships, and extreme, enduring patience"
    }
    t_traits = {
        "Sun": "நேர்மை, கௌரவம் மற்றும் பரஸ்பர மரியாதை",
        "Moon": "ஆழமான பாசம், அக்கறை மற்றும் வார்த்தைகள் இல்லாத உணர்வுபூர்வமான புரிதல்",
        "Mars": "உறவை பாதுகாக்கும் குணம், தைரியம் மற்றும் தெளிவான முடிவுகள்",
        "Mercury": "சிறந்த தகவல் தொடர்பு, நகைச்சுவை உணர்வு மற்றும் மிகச்சிறந்த நட்பு",
        "Jupiter": "தெய்வீக பக்தி, முதிர்ச்சியான ஞானம் மற்றும் பரஸ்பர வழிகாட்டுதல்",
        "Venus": "அளவற்ற அன்பு, அழகுணர்ச்சி மற்றும் சமரச மனப்பான்மை",
        "Saturn": "கடமையுணர்வு, கடினமான நேரங்களில் கைவிடாத விசுவாசம் மற்றும் அதீத பொறுமை"
    }
    
    if lang == "Tamil":
        analysis.append("#### காதல் மற்றும் திருமண வாழ்க்கை (D9 நவாம்சம்)")
        analysis.append(f"உங்கள் ஆரம்பகால காதல் உணர்வுகள் 5-ஆம் அதிபதியான **{t_p[lord_5]}** ஆல் ஆளப்படுகிறது. எனவே தொடக்கத்தில் உற்சாகமான உறவுகளை நாடுவீர்கள்.")
        analysis.append(f"ஆனால், உங்கள் உண்மையான, நிரந்தர திருமண வாழ்க்கை நவாம்சத்தின் 7-ஆம் அதிபதியான **{t_p[d9_7th_lord]}** இன் குணங்களைச் சார்ந்திருக்கும். உங்கள் துணை '{t_traits[d9_7th_lord]}' ஆகிய முதிர்ச்சியான குணங்களைக் கொண்டிருக்க வேண்டும். அப்போதுதான் உங்கள் திருமண வாழ்க்கை ஒரு உடையாத கோட்டையாக மாறும்.")
    else:
        analysis.append("#### The Dating Phase vs. The Lifelong Marriage Phase")
        analysis.append(f"Your approach to early romance (5th House) is governed by **{t_p_eng[lord_5]}**. This implies you initially seek partners who are exciting, dynamic, and align with {t_p_eng[lord_5]}'s immediate energy. However, what you *want* in dating is entirely different from what you fundamentally *need* to sustain a lifelong marriage.")
        analysis.append(f"The 7th House of your Navamsa (D9) reveals your ultimate spousal archetype. It is ruled by **{t_p_eng[d9_7th_lord]}**. To achieve a permanently successful marriage, your partner must fundamentally embody {t_p_eng[d9_7th_lord]}'s mature traits. Specifically, your union must be actively built upon **{traits[d9_7th_lord]}**.")
    return analysis

def analyze_health(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lagna_lord = RASI_RULERS[lagna_rasi]
    ll_dig = get_dignity(lagna_lord, p_pos[lagna_lord])
    lord_6 = RASI_RULERS[(lagna_rasi + 5) % 12 or 12]
    
    remedies = {
        "Sun": "Worship Lord Shiva daily. Offer water to the rising sun to strengthen cardiovascular health.",
        "Moon": "Practice deep meditation. Keep your mind calm to avoid psychosomatic chest or lung issues.",
        "Mars": "Practice grounding physical exercises. Worship Lord Murugan to cool internal inflammation and prevent accidents.",
        "Mercury": "Unplug from screens to rest your nervous system. Chant Vishnu Sahasranamam for mental clarity.",
        "Jupiter": "Avoid over-indulgence in rich foods. Offer yellow sweets and respect your spiritual teachers.",
        "Venus": "Maintain strict dietary cleanliness to avoid sugar/hormonal imbalances. Keep your surroundings aesthetic and pure.",
        "Saturn": "Perform regular stretching/yoga for bone and joint health. Light a sesame oil lamp on Saturdays to ease chronic pain."
    }
    t_remedies = {
        "Sun": "தினமும் சிவ வழிபாடு செய்யவும். காலையில் சூரிய நமஸ்காரம் செய்வது இதய ஆரோக்கியத்தை மேம்படுத்தும்.",
        "Moon": "மன அமைதியே சிறந்த மருந்து. தியானம் செய்யவும், திங்கட்கிழமைகளில் அம்பாளை வழிபடவும்.",
        "Mars": "உடல் உஷ்ணத்தை சீராக வைத்திருக்கவும். விபத்துகளைத் தவிர்க்க செவ்வாய்க்கிழமைகளில் முருகனை வழிபடவும்.",
        "Mercury": "நரம்பு தளர்ச்சியைத் தவிர்க்க முறையான ஓய்வு தேவை. விஷ்ணு சகஸ்ரநாமம் கேட்பது மன அமைதி தரும்.",
        "Jupiter": "உடல் பருமன் மற்றும் கொலஸ்ட்ராலைக் கட்டுப்படுத்தவும். வியாழக்கிழமைகளில் குரு தட்சிணாமூர்த்தியை வழிபடவும்.",
        "Venus": "சர்க்கரை அளவை கவனமாகக் கண்காணிக்கவும். மகாலட்சுமி வழிபாடு மற்றும் முறையான உணவுப் பழக்கம் அவசியம்.",
        "Saturn": "எலும்பு மற்றும் மூட்டு வலிகளைத் தவிர்க்க தினமும் யோகா அல்லது நடைப்பயிற்சி அவசியம். சனிக்கிழமைகளில் நல்லெண்ணெய் தீபம் ஏற்றவும்."
    }

    if lang == "Tamil":
        analysis.append("#### உடல் வலிமை மற்றும் நோய் எதிர்ப்பு சக்தி")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) மிகவும் வலுவாக உள்ளார். இது உங்களுக்கு இரும்பு போன்ற உடல் வலிமையையும், வியக்கத்தக்க நோய் எதிர்ப்பு சக்தியையும் அளிக்கிறது.")
        elif ll_dig == "Neecha": analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) பலவீனமாக உள்ளார். உங்கள் உடல் சக்தியை நீங்கள் மிகவும் கவனமாக கையாள வேண்டும். முறையான தூக்கமே சிறந்த மருந்து.")
        else: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) சமநிலையில் உள்ளார். உங்களின் தினசரி வாழ்க்கை முறை மற்றும் பழக்கவழக்கங்களே உங்கள் ஆரோக்கியத்தை நேரடியாக தீர்மானிக்கும்.")
        analysis.append(f"**கவனம் தேவை:** ஆரோக்கியத்தை குறிக்கும் 6-ஆம் அதிபதி **{t_p[lord_6]}** ஆவார். இதற்கான ஆன்மீக மற்றும் நடைமுறை பரிகாரம்: *{t_remedies[lord_6]}*")
    else:
        analysis.append("#### Core Physical Resilience & Preventative Care")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"Your Ascendant Lord ({t_p_eng[lagna_lord]}) is exceptionally strong. This grants you a highly robust physical constitution and excellent natural immunity.")
        elif ll_dig == "Neecha": analysis.append(f"Your Ascendant Lord ({t_p_eng[lagna_lord]}) is weak by sign placement. Your physical energy is finite and must be carefully budgeted. Strict sleep and dietary discipline are mandatory.")
        else: analysis.append(f"Your Ascendant Lord ({t_p_eng[lagna_lord]}) is in a neutral state. Your physical resilience is perfectly average and will act as a direct mirror to your lifestyle choices.")
        analysis.append(f"**Vulnerabilities & Remedy:** The 6th House of acute health is ruled by **{t_p_eng[lord_6]}**. You must proactively monitor the physiological systems associated with this planet. \n> **Remedy:** {remedies[lord_6]}")
    return analysis

def generate_annual_forecast(moon_rasi, sav_scores, f_year, age, lang="English"):
    jd = swe.julday(f_year, 1, 1, 12.0)
    sat_tr = int(swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0] / 30) + 1
    jup_tr = int(swe.calc_ut(jd, swe.JUPITER, swe.FLG_SIDEREAL)[0][0] / 30) + 1
    rahu_tr = int(swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] / 30) + 1
    sat_dist = (sat_tr - moon_rasi + 1) if (sat_tr - moon_rasi + 1) > 0 else (sat_tr - moon_rasi + 1) + 12
    jup_dist = (jup_tr - moon_rasi + 1) if (jup_tr - moon_rasi + 1) > 0 else (jup_tr - moon_rasi + 1) + 12
    rahu_dist = (rahu_tr - moon_rasi + 1) if (rahu_tr - moon_rasi + 1) > 0 else (rahu_tr - moon_rasi + 1) + 12
    fc = {}
    
    if lang == "Tamil":
        if sat_dist in [3, 6, 11]: fc['தொழில் மற்றும் சவால்கள் (Sani Transit)'] = ("மிகப்பெரிய வளர்ச்சி நிலை. உங்களின் கடந்த கால கடின உழைப்பிற்கு மிகப்பெரிய அங்கீகாரம், பதவி உயர்வு மற்றும் எதிரிகளை வீழ்த்தும் வெற்றி இந்த ஆண்டு கிடைக்கும்.", "சனிக்கிழமைகளில் ஏழைகளுக்கு உணவு அளித்து நல்லெண்ணெய் தீபம் ஏற்றவும்.")
        elif sat_dist in [1, 2, 12]: fc['தொழில் மற்றும் சவால்கள் (Sani Transit)'] = ("ஏழரைச் சனி காலம். பொறுமை மிக மிக அவசியம். தொழில் மற்றும் குடும்பத்தில் உங்கள் பொறுப்புகள் பலமடங்கு கூடும். அவசர முடிவுகளைத் தவிர்க்கவும்.", "தினமும் ஹனுமான் சாலிசா படிக்கவும், கடின உழைப்பை மட்டும் நம்பவும்.")
        else: fc['தொழில் மற்றும் சவால்கள் (Sani Transit)'] = ("சீரான நிலை. இது அடித்தளத்தை வலுப்படுத்தும் ஆண்டு. எந்த குறுக்கு வழியையும் நாடாமல், உங்கள் திறமைகளை வளர்த்துக் கொள்வதில் கவனம் செலுத்துங்கள்.", "பணியிடத்தை எப்போதும் சுத்தமாக வைத்திருக்கவும், நேர்மையைக் கடைப்பிடிக்கவும்.")

        if jup_dist in [2, 5, 7, 9, 11]: fc['பொருளாதாரம் மற்றும் அதிர்ஷ்டம் (Guru Transit)'] = ("பிரமாண்டமான பணவரவு மற்றும் அதிர்ஷ்டம். திருமணம், குழந்தை பாக்கியம் மற்றும் சொத்து சேர்க்கை போன்ற சுப காரியங்கள் தடையின்றி நடைபெறும்.", "வியாழக்கிழமைகளில் மஞ்சள் நிற உணவுகளை தானம் செய்யவும்.")
        else: fc['பொருளாதாரம் மற்றும் அதிர்ஷ்டம் (Guru Transit)'] = ("நிலையான வருமானம். அதிக ரிஸ்க் உள்ள முதலீடுகளைத் தவிர்க்கவும். செலவுகள் வருமானத்தை மீறாமல் பார்த்துக்கொள்ள சேமிப்பில் அதிக கவனம் செலுத்தவும்.", "பணப்பையில் ஒரு சிறிய விரலி மஞ்சள் துண்டை வைத்திருக்கவும்.")
        
        if rahu_dist in [3, 6, 10, 11]: fc['கர்ம வினை மற்றும் தைரியம் (Rahu/Ketu)'] = ("ராகு உங்களுக்கு அளப்பரிய தைரியத்தையும், வெளிநாட்டு தொடர்புகளால் மாபெரும் லாபத்தையும் தருவார். தடைகளைத் தகர்த்து வெற்றி பெறுவீர்கள்.", "துர்க்கை அம்மனை செவ்வாய்க்கிழமைகளில் வழிபடவும்.")
        else: fc['கர்ம வினை மற்றும் தைரியம் (Rahu/Ketu)'] = ("தேவையற்ற மனக்குழப்பங்கள் மற்றும் மாயைகளைத் தவிர்க்க வேண்டும். பேராசையைக் குறைத்து யதார்த்தமாக சிந்திப்பது அவசியம்.", "தினமும் தியானம் செய்யவும், அமைதியைத் தேடவும்.")
    else:
        if sat_dist in [3, 6, 11]: fc['Career & Ambition (Sani Transit)'] = ("**EXCELLENT GROWTH PHASE.** Sani is transiting a highly favorable growth house. Expect a major, structural promotion, deep recognition for past hard work, and a breakthrough victory over professional obstacles.", "Feed the needy on Saturdays and light a sesame oil lamp.")
        elif sat_dist in [1, 2, 12]: fc['Career & Ambition (Sani Transit)'] = ("**SADE SATI PHASE.** You are under immense cosmic pressure to mature. You may feel professionally undervalued or heavily burdened. This is a time for extreme patience and strictly avoiding ego clashes.", "Chant Hanuman Chalisa daily. Rely entirely on extreme hard work, not luck.")
        else: fc['Career & Ambition (Sani Transit)'] = ("**STEADY PROGRESS.** There are no extreme highs or lows indicated by Sani. This is a highly productive, 'heads-down' year. Use it to clear pending projects and build quiet momentum.", "Keep your workspace completely decluttered and maintain strict professional integrity.")

        if jup_dist in [2, 5, 7, 9, 11]: fc['Wealth & Expansion (Guru Transit)'] = ("**HIGH LUCK & INFLOW.** Guru actively blesses your chart this year. This is a phenomenal window for financial investments, purchasing property, or experiencing joyous family expansions (marriage/births).", "Donate yellow food (bananas/dal) on Thursdays.")
        else: fc['Wealth & Expansion (Guru Transit)'] = ("**STABLE CONSOLIDATION.** Guru’s placement advises extreme financial caution. Strictly avoid high-risk speculation or gambling this year. Focus purely on savings and protecting your current assets.", "Keep a small turmeric stick in your wallet for sustained financial protection.")
        
        if rahu_dist in [3, 6, 10, 11]: fc['Karmic Push & Courage (Rahu/Ketu)'] = ("**AGGRESSIVE VICTORIES.** Rahu grants you immense courage and out-of-the-box thinking. You will aggressively conquer obstacles. Excellent time for tech, foreign dealings, or massive leaps of faith.", "Worship Goddess Durga on Tuesdays.")
        else: fc['Karmic Push & Courage (Rahu/Ketu)'] = ("**KARMIC CLOUDS.** Rahu may create illusions, anxiety, or unrealistic desires. Do not make massive life changes based purely on sudden impulses. Ground yourself in reality.", "Practice deep meditation daily. Unplug from social media regularly.")
    return fc

def get_transit_data_advanced(f_year):
    jd = swe.julday(f_year, 1, 1, 12.0)
    current_date = datetime(f_year, 1, 1)
    data = {}
    for p_name, p_id in [("Saturn", swe.SATURN), ("Jupiter", swe.JUPITER), ("Rahu", swe.MEAN_NODE)]:
        curr_rasi = int(swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)[0][0] / 30) + 1
        search_date = current_date
        next_date, next_sign_idx = "Long Term", curr_rasi
        for _ in range(1200):
            search_date += timedelta(days=2)
            jd_s = swe.julday(search_date.year, search_date.month, search_date.day, 12.0)
            n_r = int(swe.calc_ut(jd_s, p_id, swe.FLG_SIDEREAL)[0][0] / 30) + 1
            if n_r != curr_rasi:
                next_date, next_sign_idx = search_date.strftime("%d %b %Y"), n_r
                break
        data[p_name] = {"Rasi": curr_rasi, "NextDate": next_date, "NextSignIdx": next_sign_idx}
    return data

def generate_mahadasha_table(moon_lon, birth_date, lang="English"):
    nak_idx = int(moon_lon / 13.333333333)
    bal = 1 - ((moon_lon % 13.333333333) / 13.333333333)
    curr_date = birth_date
    first_lord = DASHA_ORDER[nak_idx % 9]
    first_end = curr_date + timedelta(days=DASHA_YEARS[first_lord] * bal * 365.25)
    
    if lang == "Tamil":
        preds = {
            "Ketu": "பற்றுதலின்மை, சுயபரிசோதனை மற்றும் ஆன்மீக வளர்ச்சியின் காலம். மேலோட்டமான ஆசைகளில் இருந்து விலகி இருப்பீர்கள். உங்களை சரியான பாதையில் திருப்புவதற்காக சில திடீர் மாற்றங்கள் நிகழலாம்.",
            "Venus": "பொருளாதார வசதிகள், ஆடம்பரம் மற்றும் உறவுகளில் அதிக கவனம் செலுத்தும் காலம். கலை, வாகனங்கள் மற்றும் சொத்துகள் வாங்கும் யோகம் உண்டு. திருமண வாழ்க்கை சிறப்பாக இருக்கும்.",
            "Sun": "ஆளுமைத் திறன் மற்றும் அதிகார உச்சத்தின் காலம். சமுதாயத்தில் மிகப்பெரிய மதிப்பும், தலைமைப் பொறுப்பும் தேடி வரும். உங்களின் சுயமரியாதை ஓங்கி நிற்கும்.",
            "Moon": "உணர்ச்சிப்பூர்வமான பயணங்கள் மற்றும் மக்கள் தொடர்புகள் அதிகரிக்கும் காலம். குடும்பம் மற்றும் தாயார் மீது அதீத பாசம் ஏற்படும். நீர் சார்ந்த தொழில்கள் கை கொடுக்கும்.",
            "Mars": "கட்டுக்கடங்காத ஆற்றலும், துணிச்சலும் நிறைந்த காலம். எதிரிகளை வீழ்த்துவீர்கள். நிலம் வாங்குவதற்கும், தொழில்நுட்பத் துறையில் சாதிப்பதற்கும் மிகவும் உகந்த நேரம்.",
            "Rahu": "எப்படியாவது வெற்றி பெற வேண்டும் என்ற தீராத லட்சியம் தோன்றும் காலம். எதிர்பாராத திடீர் உயர்வுகள் ஏற்படும். வெளிநாட்டு பயணங்கள் மற்றும் தொடர்புகளால் பெரும் லாபம் உண்டு.",
            "Jupiter": "ஆழ்ந்த ஞானம், தெய்வீக அருள் மற்றும் பொருளாதார வளர்ச்சியின் காலம். சமூகத்தில் நல்ல மதிப்பும் மரியாதையும் கூடும். குடும்பம் செழிக்கும், செல்வம் பெருகும்.",
            "Saturn": "கடும் உழைப்பு, யதார்த்தமான சிந்தனை மற்றும் ஆழமான பாடங்களைக் கற்கும் காலம். மெதுவாக இருந்தாலும் உங்கள் வளர்ச்சி மிகவும் உறுதியானதாக இருக்கும்.",
            "Mercury": "கூர்மையான புத்திசாலித்தனம், வணிகம் மற்றும் வேகமான தகவல் தொடர்பின் காலம். வியாபாரம் தழைக்கும். புதிய விஷயங்களை மிக விரைவாகக் கற்றுக்கொண்டு சாதிப்பீர்கள்."
        }
        name_t = t_p.get(first_lord, first_lord)
    else:
        preds = {
            "Ketu": "A period of detachment, introspection, and spiritual growth. Sudden breaks in career or relationships are highly possible, engineered specifically to redirect you towards your true path.",
            "Venus": "A period of material comfort, luxury, and heavy relationship focus. Significant career growth comes through networking, arts, or female figures.",
            "Sun": "A period of absolute authority, power, and identity formation. You actively seek recognition and leadership roles.",
            "Moon": "A period of emotional fluctuation, geographical travel, and deep public interaction. Your internal focus shifts to the home and mother figures.",
            "Mars": "A period of high energy, directed aggression, and technical achievement. This is an excellent period for engineering, sports, or acquiring real estate.",
            "Rahu": "A period of intense obsession, high ambition, and breaking traditional norms. You crave success at any absolute cost. Foreign travel is highly favorable.",
            "Jupiter": "A period of deep wisdom, structural expansion, and divine grace. You gain immense respect through knowledge, teaching, or consulting.",
            "Saturn": "A period of iron discipline, hard work, and profound reality checks. Growth is mathematically steady but slow. You will face heavy responsibilities.",
            "Mercury": "A period of sharp intellect, commerce, and rapid communication. You learn new technical skills rapidly. Business and trade flourish."
        }
        name_t = t_p_eng.get(first_lord, first_lord)
    
    timeline = [{"Age (From-To)": f"0 - {int((first_end - birth_date).days/365.25)}", "Years": f"{curr_date.year} - {first_end.year}", "Mahadasha": name_t, "Prediction": preds.get(first_lord, "")}]
    curr_date = first_end
    for i in range(1, 9):
        lord = DASHA_ORDER[(nak_idx + i) % 9]
        end_date = curr_date + timedelta(days=DASHA_YEARS[lord] * 365.25)
        n_t = t_p.get(lord, lord) if lang=="Tamil" else t_p_eng.get(lord, lord)
        timeline.append({"Age (From-To)": f"{int((curr_date - birth_date).days/365.25)} - {int((end_date - birth_date).days/365.25)}", "Years": f"{curr_date.year} - {end_date.year}", "Mahadasha": n_t, "Prediction": preds.get(lord, "")})
        curr_date = end_date
    return timeline

def get_detailed_bhukti_analysis(md, ad, planet_bhava_map, lang="English"):
    md_house = planet_bhava_map.get(md, 1)
    ad_house = planet_bhava_map.get(ad, 1)
    
    if lang == "Tamil":
        t_topics = {1: "சுய அடையாளம், உடல் ஆரோக்கியம்", 2: "செல்வம், குடும்பம்", 3: "தைரியம், குறுகிய பயணங்கள்", 4: "வீடு, வாகனம், தாயார்", 5: "குழந்தைகள், கலை, புத்திசாலித்தனம்", 6: "ஆரோக்கியம், எதிரிகளை வெல்லுதல்", 7: "திருமணம், கூட்டாண்மை", 8: "திடீர் மாற்றங்கள், ரகசியங்கள்", 9: "பாக்கியம், தந்தை, உயர் கல்வி", 10: "தொழில் வெற்றி, பதவி உயர்வு", 11: "லாபம், நெட்வொர்க்", 12: "பயணங்கள், முதலீடுகள்"}
        t_md, t_ad = t_p.get(md, md), t_p.get(ad, ad)
        base = f"இந்த காலகட்டம் {t_md} தசையின் ஒட்டுமொத்த நோக்கங்களை, {t_ad} புக்தியின் மூலமாக நிஜ வாழ்க்கையில் பிரதிபலிக்கும்.\n\n"
        if md == ad: base += f"உங்கள் ஜாதகத்தில் {t_md} {md_house}-ஆம் வீட்டில் அமர்ந்துள்ளதால், இந்த காலகட்டம் முற்றிலும் '{t_topics[md_house]}' என்பதை சுற்றியே அமையும்.\n\n"
        else: base += f"நீண்டகால இலக்குகள் {md_house}-ஆம் வீட்டைச் சார்ந்திருந்தாலும், தற்போது {t_ad} புக்தி நடப்பதால் உங்கள் அன்றாட நிகழ்வுகள் '{t_topics[ad_house]}' வழியே நடைபெறும்.\n\n"
    else:
        topics = {1: "personal identity, physical vitality", 2: "wealth accumulation, family dynamics", 3: "courage, short travels", 4: "domestic peace, real estate", 5: "creativity, intellect", 6: "health routines, overcoming competitors", 7: "marriage, business partnerships", 8: "deep transformation, hidden knowledge", 9: "luck, higher learning", 10: "career advancement, public status", 11: "network expansion, large gains", 12: "spiritual retreats, high expenditures"}
        t_md, t_ad = t_p_eng.get(md, md), t_p_eng.get(ad, ad)
        base = f"This phase brings the overarching agenda of {t_md} (Strategy) into physical reality through the specific execution of {t_ad} (Tactics).\n\n"
        if md == ad: base += f"Because {t_md} is placed in your {md_house}th House, this period is intensely focused on {topics[md_house]}.\n\n"
        else: base += f"Your long-term focus centers on the {md_house}th House. However, {t_ad} is currently activating your {ad_house}th House, meaning immediate events manifest specifically through {topics[ad_house]}.\n\n"
    return base

def generate_current_next_bhukti(moon_lon, birth_date, planet_bhava_map, lang="English"):
    current_date = datetime.now()
    nak_idx = int(moon_lon / 13.333333333)
    bal = 1 - ((moon_lon % 13.333333333) / 13.333333333)
    curr_md_start = birth_date
    md_idx = nak_idx % 9
    
    for _ in range(20):
        md_lord = DASHA_ORDER[md_idx % 9]
        md_dur = DASHA_YEARS[md_lord] * bal if curr_md_start == birth_date else DASHA_YEARS[md_lord]
        md_end = curr_md_start + timedelta(days=md_dur * 365.25)
        
        if curr_md_start <= current_date <= md_end:
            ad_start = curr_md_start
            ad_idx = DASHA_ORDER.index(md_lord)
            for i in range(9):
                ad_lord = DASHA_ORDER[(ad_idx + i) % 9]
                ad_dur = (DASHA_YEARS[md_lord] * DASHA_YEARS[ad_lord]) / 120
                ad_end = ad_start + timedelta(days=ad_dur * 365.25)
                
                if ad_start <= current_date <= ad_end:
                    pd_start = ad_start
                    pd_idx = DASHA_ORDER.index(ad_lord)
                    for j in range(9):
                        pd_lord = DASHA_ORDER[(pd_idx + j) % 9]
                        pd_dur = (ad_dur * DASHA_YEARS[pd_lord]) / 120
                        pd_end = pd_start + timedelta(days=pd_dur * 365.25)
                        if pd_start <= current_date <= pd_end:
                            t_md, t_ad, t_pd = (t_p.get(md_lord, md_lord), t_p.get(ad_lord, ad_lord), t_p.get(pd_lord, pd_lord)) if lang=="Tamil" else (t_p_eng.get(md_lord, md_lord), t_p_eng.get(ad_lord, ad_lord), t_p_eng.get(pd_lord, pd_lord))
                            active_pd = {"MD": t_md, "AD": t_ad, "PD": t_pd, "Start": pd_start.strftime('%d %b %Y'), "End": pd_end.strftime('%d %b %Y')}
                            lbl_curr = "நடப்பு புக்தி" if lang == "Tamil" else "CURRENT PHASE"
                            lbl_next = "அடுத்த புக்தி" if lang == "Tamil" else "NEXT PHASE"
                            p1 = {"Type": lbl_curr, "Phase": f"{t_md} - {t_ad}", "Dates": f"{ad_start.strftime('%b %Y')} to {ad_end.strftime('%b %Y')}", "Text": get_detailed_bhukti_analysis(md_lord, ad_lord, planet_bhava_map, lang)}
                            
                            next_ad = DASHA_ORDER[(ad_idx + i + 1) % 9]
                            t_next_ad = t_p.get(next_ad, next_ad) if lang=="Tamil" else t_p_eng.get(next_ad, next_ad)
                            p2 = {"Type": lbl_next, "Phase": f"{t_md} - {t_next_ad}", "Dates": "விரைவில்..." if lang=="Tamil" else "Upcoming", "Text": get_detailed_bhukti_analysis(md_lord, next_ad, planet_bhava_map, lang)}
                            return [p1, p2], active_pd
                        pd_start = pd_end
                ad_start = ad_end
        curr_md_start = md_end
        md_idx += 1
        bal = 1

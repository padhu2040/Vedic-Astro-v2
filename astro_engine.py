import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

from database import DASHA_YEARS, DASHA_ORDER, RASI_RULERS, BINDU_RULES
from tamil_lang import TAMIL_LIFESTYLE

# --- TRANSLATION DICTIONARIES ---
t_p = {"Sun": "சூரியன்", "Moon": "சந்திரன்", "Mars": "செவ்வாய்", "Mercury": "புதன்", "Jupiter": "குரு", "Venus": "சுக்கிரன்", "Saturn": "சனி", "Rahu": "ராகு", "Ketu": "கேது", "Lagna": "லக்னம்"}
t_p_eng = {"Sun": "Suriyan", "Moon": "Chandran", "Mars": "Sevvai", "Mercury": "Budhan", "Jupiter": "Guru", "Venus": "Sukran", "Saturn": "Sani", "Rahu": "Rahu", "Ketu": "Ketu", "Lagna": "Lagna"}

ZODIAC_TA = {1: "மேஷம்", 2: "ரிஷபம்", 3: "மிதுனம்", 4: "கடகம்", 5: "சிம்மம்", 6: "கன்னி", 7: "துலாம்", 8: "விருச்சிகம்", 9: "தனுசு", 10: "மகரம்", 11: "கும்பம்", 12: "மீனம்"}
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

# --- TIME & LOCATION MATH ---
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

# --- ASTRONOMY MATH ---
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

# --- DEEP TEXT ANALYSIS ENGINES ---
def get_house_strength_analysis(house_num, score, lang="English"):
    topics = {1: "Self & Vitality", 2: "Wealth & Speech", 3: "Courage & Self-Effort", 4: "Home & Inner Peace", 5: "Intellect & Speculation", 6: "Health & Overcoming Rivals", 7: "Marriage & Partnerships", 8: "Transformation & Hidden Wealth", 9: "Luck & Wisdom", 10: "Career & Authority", 11: "Major Gains", 12: "Spiritual Retreats"}
    t_topics = {1: "சுய அடையாளம், ஆரோக்கியம்", 2: "செல்வம், குடும்பம்", 3: "தைரியம், வெற்றி", 4: "வீடு, மன அமைதி", 5: "புத்திசாலித்தனம்", 6: "கடன் தீர்வு, எதிரிகள்", 7: "திருமணம், கூட்டாண்மை", 8: "ரகசியங்கள், மாற்றங்கள்", 9: "பாக்கியம், உயர்கல்வி", 10: "தொழில் வெற்றி, அந்தஸ்து", 11: "லாபம், நெட்வொர்க்", 12: "பயணங்கள், முதலீடுகள்"}
    
    if score >= 30:
        if lang == "Tamil": return f"**மிகவும் வலிமையான பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) இயற்கையாகவே அதிக சக்தி பெற்றுள்ளது.\n> **பரிகாரம்/வழிகாட்டுதல்:** இந்தத் துறையில் நீங்கள் தைரியமாக புதிய முயற்சிகளை எடுக்கலாம். இது உங்கள் வெற்றிக்கு இயற்கையாகவே உதவும் பிரம்மாஸ்திரம்."
        return f"**Power Zone:** The {house_num}th House ({topics[house_num]}) is exceptionally strong.\n> **Harnessing Guide:** Double down your efforts here. Take calculated risks and assume leadership in this area. The universe supports you."
    elif score < 25:
        if lang == "Tamil": return f"**கவனம் தேவைப்படும் பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) சற்று பலவீனமாக உள்ளது.\n> **பரிகாரம்/வழிகாட்டுதல்:** இந்தத் துறையில் அவசர முடிவுகளைத் தவிர்க்கவும். அனுபவம் வாய்ந்தவர்களின் ஆலோசனையைப் பெறுவது தடைகளைத் தகர்க்க உதவும்."
        return f"**Challenge Zone:** The {house_num}th House ({topics[house_num]}) requires highly conscious effort.\n> **Mitigation Guide:** Do not rely on 'luck' here. Apply intense structure, seek mentorship, and avoid impulsive decisions."
    else:
        if lang == "Tamil": return f"**சமநிலையான பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) சீராக உள்ளது. உழைப்பிற்கு ஏற்ற நியாயமான பலன்கள் கிடைக்கும்."
        return f"**Balanced Zone:** The {house_num}th House ({topics[house_num]}) is stable. Your direct input strictly equals your direct output."

def analyze_karmic_axis(p_pos, lagna_rasi, lang="English"):
    rahu_h = (p_pos["Rahu"] - lagna_rasi + 1) if (p_pos["Rahu"] - lagna_rasi + 1) > 0 else (p_pos["Rahu"] - lagna_rasi + 1) + 12
    ketu_h = (p_pos.get("Ketu", (p_pos["Rahu"]+6)%12 or 12) - lagna_rasi + 1) if (p_pos.get("Ketu", (p_pos["Rahu"]+6)%12 or 12) - lagna_rasi + 1) > 0 else (p_pos.get("Ketu", (p_pos["Rahu"]+6)%12 or 12) - lagna_rasi + 1) + 12
    res = []
    if lang == "Tamil":
        res.append("#### கர்ம வினை அச்சு (ராகு / கேது தாக்கம்)")
        res.append(f"உங்கள் ஜாதகத்தில் ராகு {rahu_h}-ஆம் வீட்டிலும், கேது {ketu_h}-ஆம் வீட்டிலும் அமர்ந்துள்ளனர்.")
        res.append(f"**ராகுவின் ஆசை ({rahu_h}-ஆம் பாவம்):** இந்தத் துறையில் நீங்கள் மிகப்பெரிய உச்சத்தை தொட வேண்டும் என்ற அளவற்ற ஆசை உங்களுக்குள் இருக்கும். இது இப்பிறவியின் மிகப்பெரிய சவாலாகும்.")
        res.append(f"**கேதுவின் ஞானம் ({ketu_h}-ஆம் பாவம்):** முற்பிறவியிலேயே இந்தத் துறையில் நீங்கள் முழு நிபுணத்துவம் பெற்றுவிட்டீர்கள். எனவே, உங்களுக்கு இயல்பான அறிவும், அதே சமயம் ஒருவித பற்றின்மையும் (Detachment) இருக்கும்.")
    else:
        res.append("#### The Karmic Axis (Rahu & Ketu Impact)")
        res.append(f"Rahu and Ketu operate exactly 180 degrees apart in your {rahu_h}th and {ketu_h}th houses. This axis pulls you between deep past-life comfort and uncharted ambition.")
        res.append(f"**Rahu's Obsession ({rahu_h}th House):** Rahu creates a relentless, almost obsessive hunger for growth in this house. You are meant to take massive, unconventional leaps here to evolve your soul.")
        res.append(f"**Ketu's Mastery & Detachment ({ketu_h}th House):** Ketu signifies deep past-life mastery. You possess effortless, intuitive genius in this area, but you simultaneously feel a profound sense of 'been there, done that' detachment.")
    return res

def scan_yogas(p_pos, lagna_rasi, lang="English"):
    yogas = []
    p_houses = {p: ((r - lagna_rasi + 1) if (r - lagna_rasi + 1) > 0 else (r - lagna_rasi + 1) + 12) for p, r in p_pos.items() if p != "Lagna"}
    
    if p_pos.get("Sun") == p_pos.get("Mercury"):
        if lang == "Tamil": yogas.append({"Name": "புதாதித்ய யோகம் (Budhaditya)", "Type": "அறிவு மற்றும் வணிகம்", "Description": f"சூரியனும் புதனும் உங்கள் {p_houses.get('Sun')}-ஆம் வீட்டில் இணைந்து இந்த யோகத்தை உருவாக்குகின்றன. இது மிகச்சிறந்த பகுப்பாய்வு திறனையும், கூர்மையான வணிக அறிவையும் தருகிறது. தசா/புக்தி காலங்களில் இது சிறந்த பெயரையும் பணத்தையும் பெற்றுத் தரும்."})
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
        if mercury_dig in ["Exalted", "Own"]: analysis.append("புதன் மிகவும் வலுவாக இருப்பதால், சிக்கலான தரவுகளைப் பகுப்பாய்வு செய்யும் அபார திறன் உங்களுக்கு உண்டு. கணக்கீடு மற்றும் நிதி துறைகளில் உங்களால் மற்றவர்களை எளிதாக முந்த முடியும்.")
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
        "Sun": "absolute loyalty, dignified leadership, and mutual pride",
        "Moon": "deep emotional empathy, nurturing domestic care, and intuitive understanding",
        "Mars": "protective action, clear boundaries, and guarding the relationship fiercely",
        "Mercury": "crystal-clear communication, intellectual banter, and treating each other as best friends",
        "Jupiter": "moral grounding, shared philosophical growth, and mature wisdom",
        "Venus": "unconditional romantic devotion, aesthetic harmony, and prioritizing peace",
        "Saturn": "unshakeable duty, absolute loyalty through hardships, and extreme patience"
    }
    t_traits = {"Sun": "நேர்மை, கௌரவம் மற்றும் பரஸ்பர மரியாதை", "Moon": "ஆழமான பாசம், அக்கறை மற்றும் உணர்வுபூர்வமான புரிதல்", "Mars": "உறவை பாதுகாக்கும் குணம், தைரியம் மற்றும் தெளிவான முடிவுகள்", "Mercury": "சிறந்த தகவல் தொடர்பு, நகைச்சுவை உணர்வு மற்றும் சிறந்த நட்பு", "Jupiter": "தெய்வீக பக்தி, முதிர்ச்சியான ஞானம் மற்றும் பரஸ்பர வழிகாட்டுதல்", "Venus": "அளவற்ற அன்பு, அழகுணர்ச்சி மற்றும் சமரச மனப்பான்மை", "Saturn": "கடமையுணர்வு, கடினமான நேரங்களில் விசுவாசம் மற்றும் பொறுமை"}
    
    if lang == "Tamil":
        analysis.append("#### காதல் மற்றும் திருமண வாழ்க்கை (D9 நவாம்சம்)")
        analysis.append(f"உங்கள் ஆரம்பகால காதல் உணர்வுகள் 5-ஆம் அதிபதியான **{t_p[lord_5]}** ஆல் ஆளப்படுகிறது. எனவே தொடக்கத்தில் உற்சாகமான உறவுகளை நாடுவீர்கள்.")
        analysis.append(f"ஆனால், உங்கள் உண்மையான, நிரந்தர திருமண வாழ்க்கை நவாம்சத்தின் 7-ஆம் அதிபதியான **{t_p[d9_7th_lord]}** இன் குணங்களைச் சார்ந்திருக்கும். உங்கள் துணை '{t_traits[d9_7th_lord]}' ஆகிய முதிர்ச்சியான குணங்களைக் கொண்டிருக்க வேண்டும். அப்போதுதான் உங்கள் திருமணம் ஒரு உடையாத கோட்டையாக மாறும்.")
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
        "Mars": "Practice grounding physical exercises. Worship Lord Murugan to cool internal inflammation.",
        "Mercury": "Unplug from screens to rest your nervous system. Chant Vishnu Sahasranamam for clarity.",
        "Jupiter": "Avoid over-indulgence in rich foods. Offer yellow sweets and respect your spiritual teachers.",
        "Venus": "Maintain strict dietary cleanliness to avoid sugar/hormonal imbalances. Keep surroundings pure.",
        "Saturn": "Perform regular stretching/yoga for bone and joint health. Light a sesame oil lamp on Saturdays."
    }
    t_remedies = {"Sun": "தினமும் சிவ வழிபாடு செய்யவும். காலையில் சூரிய நமஸ்காரம் செய்வது இதய ஆரோக்கியத்தை மேம்படுத்தும்.", "Moon": "மன அமைதியே சிறந்த மருந்து. தியானம் செய்யவும், திங்கட்கிழமைகளில் அம்பாளை வழிபடவும்.", "Mars": "உடல் உஷ்ணத்தை சீராக வைத்திருக்கவும். விபத்துகளைத் தவிர்க்க செவ்வாய்க்கிழமைகளில் முருகனை வழிபடவும்.", "Mercury": "நரம்பு தளர்ச்சியைத் தவிர்க்க முறையான ஓய்வு தேவை. விஷ்ணு சகஸ்ரநாமம் கேட்பது மன அமைதி தரும்.", "Jupiter": "உடல் பருமன் மற்றும் கொலஸ்ட்ராலைக் கட்டுப்படுத்தவும். வியாழக்கிழமைகளில் குரு தட்சிணாமூர்த்தியை வழிபடவும்.", "Venus": "சர்க்கரை அளவை கவனமாகக் கண்காணிக்கவும். மகாலட்சுமி வழிபாடு மற்றும் முறையான உணவுப் பழக்கம் அவசியம்.", "Saturn": "எலும்பு மற்றும் மூட்டு வலிகளைத் தவிர்க்க தினமும் யோகா அவசியம். சனிக்கிழமைகளில் நல்லெண்ணெய் தீபம் ஏற்றவும்."}

    if lang == "Tamil":
        analysis.append("#### உடல் வலிமை மற்றும் நோய் எதிர்ப்பு சக்தி")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) மிகவும் வலுவாக உள்ளார். இது உங்களுக்கு இரும்பு போன்ற உடல் வலிமையையும், வியக்கத்தக்க நோய் எதிர்ப்பு சக்தியையும் அளிக்கிறது.")
        elif ll_dig == "Neecha": analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) பலவீனமாக உள்ளார். உங்கள் உடல் சக்தியை நீங்கள் மிகவும் கவனமாக கையாள வேண்டும். முறையான தூக்கமே சிறந்த மருந்து.")
        else: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) சமநிலையில் உள்ளார். உங்களின் தினசரி வாழ்க்கை முறை மற்றும் பழக்கவழக்கங்களே உங்கள் ஆரோக்கியத்தை நேரடியாக தீர்மானிக்கும்.")
        analysis.append(f"**கவனம் தேவை:** ஆரோக்கியத்தை குறிக்கும் 6-ஆம் அதிபதி **{t_p[lord_6]}** ஆவார். இதற்கான ஆன்மீக மற்றும் நடைமுறை பரிகாரம்: \n> *{t_remedies[lord_6]}*")
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

def get_micro_transits(f_year, p_lon_absolute, lang="English"):
    jd_start = swe.julday(f_year, 1, 1, 12.0)
    events = []
    tr_planets = {"Saturn": swe.SATURN, "Jupiter": swe.JUPITER, "Rahu": swe.MEAN_NODE}
    nat_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna", "Ketu"]
    active_conjunctions = {}

    for step in range(0, 365, 5): 
        jd = jd_start + step
        dt = swe.revjul(jd, swe.GREG_CAL)
        current_date = datetime(dt[0], dt[1], dt[2])
        for trp, tid in tr_planets.items():
            tr_lon = swe.calc_ut(jd, tid, swe.FLG_SIDEREAL)[0][0]
            for np in nat_planets:
                n_lon = p_lon_absolute.get(np, 0)
                if n_lon == 0 and np != "Lagna": continue
                diff = abs(tr_lon - n_lon)
                if diff > 180: diff = 360 - diff
                if diff <= 2.5: 
                    key = (trp, np)
                    if key not in active_conjunctions: active_conjunctions[key] = []
                    active_conjunctions[key].append(current_date)

    for (trp, np), dates in active_conjunctions.items():
        if not dates: continue
        start_d = min(dates).strftime("%d %b")
        end_d = max(dates).strftime("%d %b")
        date_txt = f"{start_d} to {end_d}" if start_d != end_d else f"Around {start_d}"
        meaning = ""
        if lang == "Tamil":
            trigger_txt = f"கோச்சார {t_p.get(trp, trp)}, ஜனன {t_p.get(np, np)} மீது இணைகிறது"
            if trp == "Saturn": meaning = "கர்ம வினைகளின் அழுத்தம் கூடும். தியானம் மற்றும் பொறுமை அவசியம்."
            elif trp == "Jupiter": meaning = "தெய்வீக அருள் உங்களை பாதுகாக்கும். சுபகாரியங்கள் நடைபெறும்."
            elif trp == "Rahu": meaning = "மாயைகள் மற்றும் பேராசைகள் தோன்றும். நிதானமாகச் செயல்படவும்."
        else:
            trigger_txt = f"Transiting {t_p_eng.get(trp, trp)} crosses Natal {t_p_eng.get(np, np)}"
            if trp == "Saturn": meaning = "Intense karmic pressure. Past actions catch up. Stay highly disciplined."
            elif trp == "Jupiter": meaning = "Physical and spiritual protection. A highly optimistic period where your personal aura shines."
            elif trp == "Rahu": meaning = "Karmic acceleration. Breaking old rules. Beware of impulsive life changes."
        if meaning: events.append({"Trigger": trigger_txt, "Dates": date_txt, "Impact": meaning})
    return events

def generate_mahadasha_table(moon_lon, birth_date, lang="English"):
    nak_idx = int(moon_lon / 13.333333333)
    bal = 1 - ((moon_lon % 13.333333333) / 13.333333333)
    curr_date = birth_date
    first_lord = DASHA_ORDER[nak_idx % 9]
    first_end = curr_date + timedelta(days=DASHA_YEARS[first_lord] * bal * 365.25)
    
    if lang == "Tamil":
        preds = {
            "Ketu": "பற்றுதலின்மை மற்றும் ஆன்மீக வளர்ச்சியின் காலம். தேவையற்ற உறவுகள் தானாகவே விலகும்.",
            "Venus": "பொருளாதார வசதிகள் மற்றும் ஆடம்பரத்தின் காலம். கலை மற்றும் சொத்துகள் வாங்கும் யோகம் உண்டு.",
            "Sun": "அதிகார உச்சத்தின் காலம். சமுதாயத்தில் மிகப்பெரிய மதிப்பும், தலைமைப் பொறுப்பும் தேடி வரும்.",
            "Moon": "உணர்ச்சிப்பூர்வமான பயணங்கள் அதிகரிக்கும் காலம். குடும்பம் மற்றும் தாயார் மீது அதீத பாசம் ஏற்படும்.",
            "Mars": "துணிச்சலும் ஆற்றலும் நிறைந்த காலம். நிலம் வாங்குவதற்கும், எதிரிகளை வெல்வதற்கும் உகந்த நேரம்.",
            "Rahu": "எப்படியாவது வெற்றி பெற வேண்டும் என்ற லட்சியம் தோன்றும் காலம். எதிர்பாராத திடீர் உயர்வுகள் ஏற்படும்.",
            "Jupiter": "ஆழ்ந்த ஞானம் மற்றும் தெய்வீக அருளின் காலம். குடும்பம் செழிக்கும், செல்வம் பெருகும்.",
            "Saturn": "கடும் உழைப்பு மற்றும் யதார்த்தமான சிந்தனையின் காலம். வளர்ச்சி மெதுவாக இருந்தாலும் உறுதியாக இருக்கும்.",
            "Mercury": "கூர்மையான புத்திசாலித்தனம் மற்றும் வணிகத்தின் காலம். புதிய விஷயங்களை மிக விரைவாகக் கற்று சாதிப்பீர்கள்."
        }
        name_t = t_p.get(first_lord, first_lord)
    else:
        preds = {
            "Ketu": "A period of detachment and spiritual growth. Sudden breaks in relationships are possible to redirect your path.",
            "Venus": "A period of material comfort and luxury. Career growth comes through networking and arts.",
            "Sun": "A period of absolute authority. You actively seek recognition and leadership roles.",
            "Moon": "A period of emotional fluctuation and travel. Your internal focus shifts to the home and mother.",
            "Mars": "A period of high energy and directed aggression. Excellent for engineering, sports, or real estate.",
            "Rahu": "A period of intense obsession. You crave success at any cost. Foreign travel is highly favorable.",
            "Jupiter": "A period of deep wisdom and divine grace. You gain immense respect and wealth accumulates steadily.",
            "Saturn": "A period of iron discipline. Growth is mathematically steady but slow. You learn deep patience.",
            "Mercury": "A period of sharp intellect and commerce. You learn new skills rapidly and trade flourishes."
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
                            
                            p1 = {"Type": lbl_curr, "Phase": f"{t_md} - {t_ad}", "Dates": f"{ad_start.strftime('%b %Y')} to {ad_end.strftime('%b %Y')}", "Text": f"Currently executing the karmic script of {t_ad}."}
                            next_ad = DASHA_ORDER[(ad_idx + i + 1) % 9]
                            t_next_ad = t_p.get(next_ad, next_ad) if lang=="Tamil" else t_p_eng.get(next_ad, next_ad)
                            p2 = {"Type": lbl_next, "Phase": f"{t_md} - {t_next_ad}", "Dates": "விரைவில்..." if lang=="Tamil" else "Upcoming", "Text": f"Preparing to shift into the energy of {t_next_ad}."}
                            return [p1, p2], active_pd
                        pd_start = pd_end
                ad_start = ad_end
        curr_md_start = md_end
        md_idx += 1
        bal = 1
    return [], {}

def calculate_10_porutham(b_nak, g_nak, b_rasi, g_rasi, b_name, g_name):
    score = 0
    results = {}
    dist = (b_nak - g_nak) if (b_nak >= g_nak) else (b_nak + 27 - g_nak)
    dist += 1 
    
    GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
    RAJJU = ["Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai", "Paadam", "Thodai", "Udaram", "Kantham", "Sirasu", "Sirasu", "Kantham", "Udaram", "Thodai"]
    VEDHA_PAIRS = {0: 17, 17: 0, 1: 16, 16: 1, 2: 15, 15: 2, 3: 14, 14: 3, 4: 13, 13: 4, 5: 21, 21: 5, 6: 20, 20: 6, 7: 19, 19: 7, 8: 18, 18: 8, 9: 11, 11: 9, 10: 12, 12: 10, 22: 26, 26: 22, 23: 25, 25: 23}

    dina_match = (dist % 9) in [2, 4, 6, 8, 0]
    results["Dina (Daily Harmony)"] = {"match": dina_match, "desc": "Excellent day-to-day emotional flow." if dina_match else "Potential for minor daily frictions. Patience required."}
    if dina_match: score += 1
        
    b_gana, g_gana = GANA[b_nak], GANA[g_nak]
    gana_match = (b_gana == g_gana) or (g_gana == "Deva" and b_gana == "Manushya") or (g_gana == "Manushya" and b_gana == "Deva")
    results["Gana (Temperament)"] = {"match": gana_match, "desc": f"Highly compatible inherent natures." if gana_match else f"Core natures may clash. One partner is naturally more aggressive."}
    if gana_match: score += 1

    mahendra_match = dist in [4, 7, 10, 13, 16, 19, 22, 25]
    results["Mahendra (Wealth & Progeny)"] = {"match": mahendra_match, "desc": "Strong indication for family growth and asset building." if mahendra_match else "Average wealth expansion metrics."}
    if mahendra_match: score += 1
        
    stree_match = dist >= 13
    results["Stree Deergha (Prosperity)"] = {"match": stree_match, "desc": f"The stars are distanced perfectly to ensure mutual support." if stree_match else f"Stars are too close; shared prosperity requires effort."}
    if stree_match: score += 1
        
    b_rajju, g_rajju = RAJJU[b_nak], RAJJU[g_nak]
    rajju_match = b_rajju != g_rajju
    results["Rajju (Longevity - CRITICAL)"] = {"match": rajju_match, "desc": "Different Rajjus (Safe). Excellent longevity for the bond." if rajju_match else f"Both share {b_rajju} Rajju. Traditionally a severe mismatch."}
    if rajju_match: score += 1
        
    vedha_match = VEDHA_PAIRS.get(b_nak) != g_nak
    results["Vedha (Mutual Affliction)"] = {"match": vedha_match, "desc": "No mutual affliction." if vedha_match else "Stars directly afflict each other (Vedha)."}
    if vedha_match: score += 1
        
    rasi_dist = (b_rasi - g_rasi) if (b_rasi >= g_rasi) else (b_rasi + 12 - g_rasi)
    rasi_dist += 1
    rasi_match = rasi_dist > 6 or b_rasi == g_rasi
    results["Rasi (Lineage Harmony)"] = {"match": rasi_match, "desc": "Favorable moon sign placements." if rasi_match else "Moon signs are placed in challenging angles."}
    if rasi_match: score += 1
        
    results["Yoni (Physical Chemistry)"] = {"match": True, "desc": "Generally harmonious physical connection."}
    results["Rasyadhipati (Lord Friendship)"] = {"match": True, "desc": "Lords of the Moon signs are neutral/friendly."}
    results["Vasya (Attraction)"] = {"match": True, "desc": "Standard magnetic attraction."}
    score += 3
    return score, results

def generate_360_persona(lagna_rasi, moon_rasi, sav_scores, p_pos, bhava_placements, lang="English"):
    persona = {}
    
    # 1. CORE ARCHETYPE TITLES (Simha Lagna + Dhanu Moon example = "The Visionary Commander")
    # This is a sample matrix. You can expand these titles in the future.
    archetypes = {
        (5, 9): "The Visionary Commander (Strategic, Inspiring, Uncompromising)",
        (12, 7): "The Diplomatic Mystic (Empathetic, Imaginative, Harmonious)"
    }
    # Fallback if specific combo isn't defined yet
    default_title = "The Strategic Architect (Analytical, Driven, Independent)"
    persona['Archetype'] = archetypes.get((lagna_rasi, moon_rasi), default_title)

    # 2. CALCULATE CAREER PATH (Corporate vs Business)
    h6_score = sav_scores[(lagna_rasi - 1 + 5) % 12] # Corporate/Service
    h7_score = sav_scores[(lagna_rasi - 1 + 6) % 12] # Business/Partners
    h10_score = sav_scores[(lagna_rasi - 1 + 9) % 12] # Leadership
    
    career_profile = ""
    if h10_score >= 30:
        career_profile += "**The Executive Setup:** You are wired for the top of the pyramid. You operate best when given total autonomy and a team to direct. "
    if h6_score > h7_score:
        career_profile += "**Corporate Path:** You have a massive competitive advantage in structured corporate environments. You easily out-work rivals and thrive in complex hierarchies."
    else:
        career_profile += "**Business Path:** You possess an entrepreneurial spirit. You are built for equity, independent ventures, and leveraging strategic partnerships over standard employment."
    persona['Professional'] = career_profile

    # 3. CALCULATE INTELLECT & STUDIES
    h5_score = sav_scores[(lagna_rasi - 1 + 4) % 12]
    if h5_score >= 28:
        persona['Studies'] = "You possess a highly absorbent intellect. You learn exceptionally fast and do well in structured academic environments or complex technical certifications."
    else:
        persona['Studies'] = "You are an experiential learner. Traditional classroom memorization may bore you. You master subjects by doing, building, and applying concepts in the real world."

    # 4. CALCULATE RELATIONSHIPS & FAMILY
    h4_score = sav_scores[(lagna_rasi - 1 + 3) % 12]
    if h4_score >= 28:
        persona['Relationships'] = "You draw immense power from a stable home life. Your private domestic space is your fortress, and you invest heavily in maintaining family harmony."
    else:
        persona['Relationships'] = "You are fiercely independent. Your sense of 'home' is tied to your ambitions rather than a physical place. In relationships, you require a partner who respects your need for space and continuous growth."

    # 5. SUPERPOWERS & SHADOW (Based on top and bottom SAV scores)
    sorted_houses = sorted([(sav_scores[(lagna_rasi-1+i)%12], i+1) for i in range(12)], key=lambda x: x[0], reverse=True)
    top_house = sorted_houses[0][1]
    bottom_house = sorted_houses[-1][1]
    
    superpower_map = {
        1: "Magnetic presence and physical vitality.", 2: "Financial compounding and persuasive speech.", 
        3: "Fearless execution and risk-taking.", 4: "Emotional intelligence and asset building.",
        5: "Creative genius and rapid problem solving.", 6: "Crushing obstacles and outlasting competition.",
        7: "Mastery of negotiation and human psychology.", 8: "Crisis management and uncovering hidden truths.",
        9: "High-level strategic wisdom and natural luck.", 10: "Commanding authority and industry leadership.",
        11: "Building massive networks and scaling profits.", 12: "Global vision and deep spiritual intuition."
    }
    
    shadow_map = {
        1: "Can struggle with self-doubt or burnout.", 2: "Prone to fluctuating finances if undisciplined.", 
        3: "May hesitate to take necessary leaps of faith.", 4: "Can experience inner restlessness or domestic friction.",
        5: "Over-analyzes decisions; struggles to delegate.", 6: "Avoids direct confrontation; easily stressed by rivals.",
        7: "Attracts imbalanced partnerships or codependency.", 8: "Fears sudden changes; resists necessary transformations.",
        9: "Can become dogmatic or rigid in personal beliefs.", 10: "Struggles to find consistent career recognition.",
        11: "Networks may drain energy rather than provide ROI.", 12: "Prone to burnout from poor boundary setting."
    }
    
    persona['Strengths'] = superpower_map.get(top_house, "Adaptable and resilient.")
    persona['Shadow'] = shadow_map.get(bottom_house, "Requires conscious self-reflection.")

    return persona

# --- DAILY EXECUTIVE WEATHER ENGINE ---
def get_daily_executive_weather(current_jd_ut, natal_moon_rasi, natal_lagna_rasi, lang="English"):
    """
    Calculates exact daily transits and provides actionable tactical remedies.
    """
    import swisseph as swe
    from datetime import datetime

    t_moon_res = swe.calc_ut(current_jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    t_sun_res = swe.calc_ut(current_jd_ut, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    t_merc_res = swe.calc_ut(current_jd_ut, swe.MERCURY, swe.FLG_SIDEREAL)[0][0]
    
    t_moon_rasi = int(t_moon_res / 30) + 1
    t_sun_rasi = int(t_sun_res / 30) + 1
    t_merc_rasi = int(t_merc_res / 30) + 1
    
    moon_from_moon = (t_moon_rasi - natal_moon_rasi) % 12 + 1
    moon_from_lagna = (t_moon_rasi - natal_lagna_rasi) % 12 + 1
    merc_from_lagna = (t_merc_rasi - natal_lagna_rasi) % 12 + 1
    sun_from_lagna = (t_sun_rasi - natal_lagna_rasi) % 12 + 1

    # 1. STRATEGIC FOCUS (Moon)
    focus_color = "#3498db" 
    if moon_from_moon == 8:
        focus_title = "High Alert: Tactical Retreat (Chandrashtama)"
        focus_desc = "The Moon is transiting a highly volatile sector relative to your natal mind. Emotional static is high. Do not sign major contracts, launch products, or engage in aggressive negotiations today."
        focus_remedy = "💡 Tactical Action: Postpone high-stakes meetings. Limit caffeine, practice breathwork before stressful conversations, and focus strictly on low-risk administrative tasks."
        focus_color = "#e74c3c"
    elif moon_from_lagna == 10:
        focus_title = "Maximum Visibility: Execute"
        focus_desc = "The current cosmic weather is lighting up your sector of absolute authority. You are highly visible today. This is the perfect 24-hour window to step confidently into a leadership role."
        focus_remedy = "💡 Tactical Action: Send the pitch deck. Ask for the promotion or close the deal. Visibility is your highest leverage asset today—do not hide in the background."
        focus_color = "#27ae60" 
    elif moon_from_lagna == 12:
        focus_title = "Deep Backend & Strategy"
        focus_desc = "Your energy is naturally withdrawing. Do not force external networking today. This is a highly productive day for deep, isolated research and behind-the-scenes development."
        focus_remedy = "💡 Tactical Action: Turn off notifications. Block out 2-3 hours of uninterrupted time for deep strategic planning. Protect your mental bandwidth."
        focus_color = "#9b59b6" 
    elif moon_from_lagna in [1, 5, 9]:
        focus_title = "Visionary & Creative Flow"
        focus_desc = "Your intuition and creative problem-solving are operating at peak efficiency. Trust your gut instincts today. Excellent for looking at the big picture."
        focus_remedy = "💡 Tactical Action: Host a brainstorming session. Your ability to connect abstract ideas is peaking. Write down sudden insights immediately."
        focus_color = "#f39c12" 
    elif moon_from_lagna in [2, 6, 10]:
        focus_title = "Operational & Financial Focus"
        focus_desc = "Your mind is naturally attuned to practical, material realities today. Excellent weather for auditing finances, restructuring workflows, and tackling operational bottlenecks."
        focus_remedy = "💡 Tactical Action: Review budgets, optimize team workflows, and clear your inbox. Be relentlessly practical and detail-oriented today."
        focus_color = "#2980b9" 
    else:
        focus_title = "Steady Execution"
        focus_desc = "The daily environment is neutral and stable. Maintain your current operational momentum. Focus on clearing your backlog and ensuring foundational systems run smoothly."
        focus_remedy = "💡 Tactical Action: Stick strictly to your established routines. This is a day for steady, predictable output rather than massive pivots."

    # 2. COMMUNICATION WEATHER (Mercury)
    if merc_from_lagna in [3, 11]:
        comm_title = "High-Velocity Networking"
        comm_desc = "Data processing and communication are highly favored. Send the difficult emails, host the all-hands meeting, and leverage your professional network."
        comm_remedy = "💡 Tactical Action: Over-communicate your vision today. Reach out to mentors or clients you've been putting off; your words will carry high impact."
    elif merc_from_lagna in [6, 8, 12]:
        comm_title = "Data Friction & Misalignment"
        comm_desc = "There is friction in the communication channels. Double-check all data, assume emails might be misread, and over-communicate clarity to avoid drama."
        comm_remedy = "💡 Tactical Action: Get all verbal agreements in writing today. Delay sending emotionally charged emails by 24 hours. Verify all metrics twice."
    else:
        comm_title = "Clear & Direct Logic"
        comm_desc = "Standard communication flows smoothly. Trust your data analysis and present your logic directly. No hidden agendas in the operational weather today."
        comm_remedy = "💡 Tactical Action: Trust your baseline data. Present arguments using cold, hard facts rather than emotional appeals."

    # 3. VITALITY & AUTHORITY (Sun)
    if sun_from_lagna in [1, 10, 11]:
        energy_title = "Commanding Presence"
        energy_desc = "You possess a massive reserve of executive vitality right now. You naturally command respect in rooms. Use this window to lead with absolute authority."
        energy_remedy = "💡 Tactical Action: Lead the room. Do not shy away from taking ultimate responsibility for team outcomes right now. Step up."
    elif sun_from_lagna in [6, 8, 12]:
        energy_title = "Energy Conservation"
        energy_desc = "Your core vitality is being tested by external friction. Do not burn out trying to micromanage everything. Conserve your energy."
        energy_remedy = "💡 Tactical Action: Guard your immune system and physical health. Delegate heavy lifting to your team and prioritize getting enough sleep."
    else:
        energy_title = "Sustained Baseline"
        energy_desc = "Your executive energy levels are balanced. You have enough vitality to lead effectively without burning out, provided you maintain basic discipline."
        energy_remedy = "💡 Tactical Action: Maintain steady leadership. Avoid creating unnecessary conflicts just to prove a point; conserve energy for real battles."

    return {
        "focus": {"title": focus_title, "desc": focus_desc, "color": focus_color, "remedy": focus_remedy},
        "communication": {"title": comm_title, "desc": comm_desc, "remedy": comm_remedy},
        "energy": {"title": energy_title, "desc": energy_desc, "remedy": energy_remedy},
        "positions": {
            "Moon": ZODIAC[t_moon_rasi],
            "Sun": ZODIAC[t_sun_rasi],
            "Mercury": ZODIAC[t_merc_rasi]
        }
    }

# --- DAILY PANCHANGAM & EXACT TIMELINE ENGINE ---
def get_daily_panchangam_metrics(target_date, lat_val, lon_val, tz_name="Asia/Kolkata", lang="English", user_lagna=None, user_moon=None, natal_moon_lon=None):
    import swisseph as swe
    from datetime import datetime, timedelta, time, timezone
    import pytz

    local_tz = pytz.timezone(tz_name)
    now_dt = datetime.now(local_tz)
    
    is_today = target_date == now_dt.date()
    if is_today:
        dt_obj = now_dt
    else:
        dt_obj = local_tz.localize(datetime.combine(target_date, time(12, 0)))
    
    # 1. Sunrise & Sunset
    midnight_local = local_tz.localize(datetime(dt_obj.year, dt_obj.month, dt_obj.day, 0, 0, 0))
    midnight_utc = midnight_local.astimezone(pytz.utc)
    jd_midnight = swe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day, midnight_utc.hour + midnight_utc.minute/60.0)
    
    geopos = (float(lon_val), float(lat_val), 0.0)
    try:
        res_rise = swe.rise_trans(jd_midnight, swe.SUN, b"", swe.FLG_SWIEPH, swe.CALC_RISE, geopos, 0.0, 0.0)
        sunrise_jd = res_rise[1][0] if isinstance(res_rise, tuple) and isinstance(res_rise[1], tuple) else (res_rise[0] if isinstance(res_rise, tuple) else res_rise)
        res_set = swe.rise_trans(sunrise_jd + 0.1, swe.SUN, b"", swe.FLG_SWIEPH, swe.CALC_SET, geopos, 0.0, 0.0)
        sunset_jd = res_set[1][0] if isinstance(res_set, tuple) and isinstance(res_set[1], tuple) else (res_set[0] if isinstance(res_set, tuple) else res_set)
    except:
        sunrise_jd = jd_midnight + (6.0 / 24.0)
        sunset_jd = jd_midnight + (18.0 / 24.0)

    def jd_to_local_dt(jd):
        y, m, d, h = swe.revjul(jd)
        hr = int(h)
        min_val = int((h - hr) * 60)
        sec = int((((h - hr) * 60) - min_val) * 60)
        utc_dt = datetime(y, m, d, hr, min_val, sec, tzinfo=timezone.utc)
        return utc_dt.astimezone(local_tz)

    def format_end_time(jd):
        edt = jd_to_local_dt(jd)
        t_str = edt.strftime('%I:%M %p').lstrip('0')
        if edt.date() != target_date:
            return f"{t_str} ({edt.strftime('%b %d')})"
        return t_str

    sunrise_dt = jd_to_local_dt(sunrise_jd)
    sunset_dt = jd_to_local_dt(sunset_jd)
    horai_len_hrs = ((sunset_jd - sunrise_jd) * 24) / 12

    current_utc = dt_obj.astimezone(pytz.utc)
    current_jd_ut = swe.julday(current_utc.year, current_utc.month, current_utc.day, current_utc.hour + (current_utc.minute/60.0))

    def get_sun_lon(jd): return swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    
    # 2. True Sankramana (Exact Tamil Day Calculation)
    curr_lon = get_sun_lon(current_jd_ut)
    sun_rasi_idx = int(curr_lon / 30) + 1
    jd_sank = current_jd_ut
    
    while int(get_sun_lon(jd_sank) / 30) == (sun_rasi_idx - 1): jd_sank -= 1.0
    while int(get_sun_lon(jd_sank) / 30) != (sun_rasi_idx - 1): jd_sank += 0.01
    jd_sank -= 0.01
    while int(get_sun_lon(jd_sank) / 30) != (sun_rasi_idx - 1): jd_sank += 0.001
        
    sank_dt = jd_to_local_dt(jd_sank)
    day_1_date = sank_dt.date() + timedelta(days=1) if sank_dt.hour >= 18 else sank_dt.date()
    tamil_day = (target_date - day_1_date).days + 1

    # 3. 60-Year Tamil Cycle & Months
    tamil_years_en = ["Prabhava", "Vibhava", "Sukla", "Pramodoota", "Prachorpaththi", "Aangirasa", "Srimuga", "Bhava", "Yuva", "Dhaadhu", "Eesvara", "Vehudhanya", "Pramathi", "Vikrama", "Vishu", "Chitrabhanu", "Subhanu", "Tharana", "Parthiba", "Viya", "Sarvajith", "Sarvadhari", "Virodhi", "Vikruthi", "Kara", "Nandhana", "Vijaya", "Jaya", "Manmatha", "Dhurmuki", "Hevilambi", "Vilambi", "Vikari", "Sarvari", "Plava", "Shubakruth", "Sobakruth", "Krodhi", "Viswavasu", "Parabhava", "Plavanga", "Keelaka", "Saumya", "Sadharana", "Virodhikruth", "Paridhaabi", "Pramaadhisa", "Aanandha", "Rakshasa", "Nala", "Pingala", "Kalayukthi", "Siddharthi", "Raudhri", "Dunmathi", "Dhundhubhi", "Rudhrodhgaari", "Raktakshi", "Krodhana", "Akshaya"]
    tamil_years_ta = ["பிரபவ", "விபவ", "சுக்ல", "பிரமோதூத", "பிரஜோத்பத்தி", "ஆங்கீரச", "ஸ்ரீமுக", "பவ", "யுவ", "தாது", "ஈஸ்வர", "வெகுதான்ய", "பிரமாதி", "விக்ரம", "விஷு", "சித்ரபானு", "சுபானு", "தாரண", "பார்த்திப", "விய", "சர்வஜித்", "சர்வதாரி", "விரோதி", "விக்ருதி", "கர", "நந்தன", "விஜய", "ஜய", "மன்மத", "துன்முகி", "ஹேவிளம்பி", "விளம்பி", "விகாரி", "சார்வரி", "பிலவ", "சுபகிருது", "சோபகிருது", "க்ரோதி", "விஸ்வாவசு", "பராபவ", "பிலவங்க", "கீலக", "சௌம்ய", "சாதாரண", "விரோதிகிருது", "பரிதாபி", "பிரமாதீச", "ஆனந்த", "ராக்ஷச", "நள", "பிங்கள", "காளயுக்தி", "சித்தார்த்தி", "ரௌத்ரி", "துன்மதி", "துந்துபி", "ருத்ரோத்காரி", "ரக்தாக்ஷி", "க்ரோதன", "அக்ஷய"]
    
    s_year = dt_obj.year
    if dt_obj.month <= 4 and sun_rasi_idx >= 10: s_year -= 1
    ty_idx = (s_year - 1987) % 60
    t_year = tamil_years_en[ty_idx] if lang == "English" else tamil_years_ta[ty_idx]

    tamil_months_en = {1:"Chithirai", 2:"Vaikasi", 3:"Aani", 4:"Aadi", 5:"Avani", 6:"Purattasi", 7:"Aippasi", 8:"Karthigai", 9:"Margazhi", 10:"Thai", 11:"Masi", 12:"Panguni"}
    tamil_months_ta = {1:"சித்திரை", 2:"வைகாசி", 3:"ஆனி", 4:"ஆடி", 5:"ஆவணி", 6:"புரட்டாசி", 7:"ஐப்பசி", 8:"கார்த்திகை", 9:"மார்கழி", 10:"தை", 11:"மாசி", 12:"பங்குனி"}
    t_month = tamil_months_en[sun_rasi_idx] if lang == "English" else tamil_months_ta[sun_rasi_idx]
    
    tamil_days_dict = {0:"திங்கள்", 1:"செவ்வாய்", 2:"புதன்", 3:"வியாழன்", 4:"வெள்ளி", 5:"சனி", 6:"ஞாயிறு"}
    day_ta = tamil_days_dict[dt_obj.weekday()]

    # 4. Iterative End-Time Calculators
    def get_tithi(jd): return int(((((swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]) - (swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0])) % 360) / 12) + 1)
    def get_nak(jd): return int((swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360) / (360/27))
    def get_rasi(jd): return int(swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0] / 30) + 1
    def get_yoga(jd): return int((((swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]) + (swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0])) % 360) / (360/27))

    def find_end_time(start_jd, func, max_hours):
        start_val = func(start_jd)
        jd = start_jd
        for _ in range(max_hours * 2):
            jd += 0.5
            if func(jd) != start_val: break
        jd -= 0.5
        for _ in range(720):
            jd += (1/1440)
            if func(jd) != start_val: return jd, func(jd)
        return jd, func(jd)

    jd_tithi_end, next_t_idx = find_end_time(current_jd_ut, get_tithi, 30)
    jd_nak_end, next_n_idx = find_end_time(current_jd_ut, get_nak, 30)
    jd_rasi_end, next_r_idx = find_end_time(current_jd_ut, get_rasi, 72)
    jd_yoga_end, next_y_idx = find_end_time(current_jd_ut, get_yoga, 30)

    # Dictionaries
    tithi_names_en = {1:"Prathamai", 2:"Dwitiyai", 3:"Tritiyai", 4:"Chaturthi", 5:"Panchami", 6:"Shashti", 7:"Saptami", 8:"Ashtami", 9:"Navami", 10:"Dasami", 11:"Ekadasi", 12:"Dwadasi", 13:"Thirayodasi", 14:"Chaturdasi"}
    tithi_names_ta = {1:"பிரதமை", 2:"துவிதியை", 3:"திருதியை", 4:"சதுர்த்தி", 5:"பஞ்சமி", 6:"சஷ்டி", 7:"சப்தமி", 8:"அஷ்டமி", 9:"நவமி", 10:"தசமி", 11:"ஏகாதசி", 12:"துவாதசி", 13:"திரயோதசி", 14:"சதுர்த்தசி"}
    
    def format_tithi(idx):
        if idx == 30: return "Amavasai" if lang=="English" else "அமாவாசை"
        if idx == 15: return "Pournami" if lang=="English" else "பௌர்ணமி"
        return tithi_names_en.get(idx if idx<=15 else idx-15, "") if lang=="English" else tithi_names_ta.get(idx if idx<=15 else idx-15, "")

    tithi_idx = get_tithi(current_jd_ut)
    t_name, next_t_name = format_tithi(tithi_idx), format_tithi(next_t_idx)

    is_waxing = tithi_idx <= 15
    paksha = "Valarpirai (Shukla Paksham)" if is_waxing else "Theipirai (Krishna Paksham)"
    if lang == "Tamil": paksha = "வளர்பிறை (சுக்கில பட்சம்)" if is_waxing else "தேய்பிறை (கிருஷ்ண பட்சம்)"
    
    days_to_target = 15 - tithi_idx if is_waxing else 30 - tithi_idx
    target_dt = dt_obj + timedelta(days=days_to_target)
    target_name = "Pournami" if is_waxing else "Amavasai"
    if lang == "Tamil": target_name = "பௌர்ணமி" if is_waxing else "அமாவாசை"
    countdown_str = f"{days_to_target}d to {target_name} ({target_dt.strftime('%b %d')})" if lang=="English" else f"{target_name}க்கு {days_to_target} நாள் ({target_dt.strftime('%d %b')})"

    yogas_en = ["Vishkumbham", "Priti", "Ayushman", "Saubhagyam", "Shobhanam", "Atigandam", "Sukarmam", "Dhriti", "Shulam", "Gandam", "Vriddhi", "Dhruvam", "Vyaghatam", "Harshanam", "Vajram", "Siddhi", "Vyatipatam", "Variyan", "Parigham", "Shivam", "Siddham", "Sadhyam", "Shubham", "Shuklam", "Brahmam", "Indram", "Vaidhriti"]
    yogas_ta = ["விஷ்கம்பம்", "பிரீதி", "ஆயுஷ்மான்", "சௌபாக்கியம்", "சோபனம்", "அதிகண்டம்", "சுகர்மம்", "திருதி", "சூலம்", "கண்டம்", "விருத்தி", "துருவம்", "வியாகாதம்", "ஹர்ஷணம்", "வஜ்ரம்", "சித்தி", "வியதிபாதம்", "வரியான்", "பரிகம்", "சிவம்", "சித்தம்", "சாத்தியம்", "சுபம்", "சுக்கிலம்", "பிரம்மா", "இந்திரம்", "வைதிருதி"]
    daily_yoga = yogas_en[get_yoga(current_jd_ut)] if lang=="English" else yogas_ta[get_yoga(current_jd_ut)]
    next_yoga_name = yogas_en[next_y_idx] if lang=="English" else yogas_ta[next_y_idx]

    zodiac_en = ["Mesham", "Rishabam", "Mithunam", "Kadagam", "Simmam", "Kanni", "Thulam", "Viruchigam", "Dhanusu", "Magaram", "Kumbam", "Meenam"]
    zodiac_ta = ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"]
    daily_rasi_name = zodiac_en[get_rasi(current_jd_ut)-1] if lang=="English" else zodiac_ta[get_rasi(current_jd_ut)-1]
    next_rasi_name = zodiac_en[next_r_idx-1] if lang=="English" else zodiac_ta[next_r_idx-1]

    nak_en = ["Ashwini", "Bharani", "Karthigai", "Rohini", "Mirugasiridam", "Thiruvathirai", "Punarpoosam", "Poosam", "Ayilyam", "Magam", "Pooram", "Uthiram", "Hastham", "Chithirai", "Swathi", "Visakam", "Anusham", "Kettai", "Moolam", "Pooradam", "Uthiradam", "Thiruvonam", "Avittam", "Sathayam", "Poorattathi", "Uthirattathi", "Revathi"]
    nak_ta = ["அஸ்வினி", "பரணி", "கிருத்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை", "புனர்பூசம்", "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "அஸ்தம்", "சித்திரை", "சுவாதி", "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்", "உத்திராடம்", "திருவோணம்", "அவிட்டம்", "சதயம்", "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"]
    nak_name = nak_en[get_nak(current_jd_ut)] if lang=="English" else nak_ta[get_nak(current_jd_ut)]
    next_nak_name = nak_en[next_n_idx] if lang=="English" else nak_ta[next_n_idx]

    ch_rasi_idx = (get_rasi(current_jd_ut) - 8) % 12 + 1
    rasi_to_nak_en = {1: "Ashwini, Bharani, Karthigai", 2: "Karthigai, Rohini, Mirugasiridam", 3: "Mirugasiridam, Thiruvathirai, Punarpoosam", 4: "Punarpoosam, Poosam, Ayilyam", 5: "Magam, Pooram, Uthiram", 6: "Uthiram, Hastham, Chithirai", 7: "Chithirai, Swathi, Visakam", 8: "Visakam, Anusham, Kettai", 9: "Moolam, Pooradam, Uthiradam", 10: "Uthiradam, Thiruvonam, Avittam", 11: "Avittam, Sathayam, Poorattathi", 12: "Poorattathi, Uthirattathi, Revathi"}
    rasi_to_nak_ta = {1: "அஸ்வினி, பரணி, கிருத்திகை", 2: "கிருத்திகை, ரோகிணி, மிருகசீரிடம்", 3: "மிருகசீரிடம், திருவாதிரை, புனர்பூசம்", 4: "புனர்பூசம், பூசம், ஆயில்யம்", 5: "மகம், பூரம், உத்திரம்", 6: "உத்திரம், அஸ்தம், சித்திரை", 7: "சித்திரை, சுவாதி, விசாகம்", 8: "விசாகம், அனுஷம், கேட்டை", 9: "மூலம், பூராடம், உத்திராடம்", 10: "உத்திராடம், திருவோணம், அவிட்டம்", 11: "அவிட்டம், சதயம், பூரட்டாதி", 12: "பூரட்டாதி, உத்திரட்டாதி, ரேவதி"}
    ch_naks = rasi_to_nak_en[ch_rasi_idx] if lang=="English" else rasi_to_nak_ta[ch_rasi_idx]

    tara_name, tara_color = "-", "#95a5a6"
    if natal_moon_lon is not None:
        natal_nak_idx = int((natal_moon_lon % 360) / (360/27))
        tara_calc = ((get_nak(current_jd_ut) - natal_nak_idx) % 9) + 1
        tara_meanings_en = {1: "Janma (Average)", 2: "Sampat (Excellent)", 3: "Vipat (Caution)", 4: "Kshema (Good)", 5: "Pratyak (Obstacles)", 6: "Sadhana (Success)", 7: "Naidhana (Severe)", 8: "Mitra (Favorable)", 9: "Parama Mitra (Excellent)"}
        tara_meanings_ta = {1: "ஜென்ம (சராசரி)", 2: "சம்பத் (சிறப்பு)", 3: "விபத்து (கவனம்)", 4: "க்ஷேம (நன்று)", 5: "பிரத்யக் (தடைகள்)", 6: "சாதனா (வெற்றி)", 7: "நைதன (கடுமை)", 8: "மித்ர (சாதகம்)", 9: "பரம மித்ர (மிகச் சிறப்பு)"}
        tara_name = (tara_meanings_en if lang == "English" else tara_meanings_ta)[tara_calc]
        tara_color = "#27ae60" if tara_calc in [2,4,6,8,9] else "#e74c3c" if tara_calc in [3,5,7] else "#f39c12"

    wd_idx = (dt_obj.weekday() + 1) % 7 
    rk_start_hrs = {0: 10.5, 1: 1.5, 2: 9.0, 3: 6.0, 4: 7.5, 5: 4.5, 6: 3.0}
    yg_start_hrs = {0: 6.0, 1: 4.5, 2: 3.0, 3: 1.5, 4: 0.0, 5: 9.0, 6: 7.5}
    nn_starts = {0: [1.5, 9.5], 1: [0.0, 10.5], 2: [1.5, 10.5], 3: [3.0, 10.5], 4: [4.5, 10.5], 5: [3.5, 10.5], 6: [1.5, 10.5]}
    gnn_starts = {0: [1.5, 4.5], 1: [3.0, 7.5], 2: [4.5, 10.5], 3: [6.0, 1.5], 4: [7.5, 4.5], 5: [6.5, 12.5], 6: [0.0, 3.0]}

    def get_time_str(start_offset, duration=1.5):
        s = sunrise_dt + timedelta(hours=start_offset)
        e = s + timedelta(hours=duration)
        return f"{s.strftime('%I:%M %p').lstrip('0')} - {e.strftime('%I:%M %p').lstrip('0')}"

    nn_str = "<br>".join([get_time_str(sh, 1.0) for sh in nn_starts[wd_idx]])
    gnn_str = "<br>".join([get_time_str(sh, 1.0) for sh in gnn_starts[wd_idx]])

    power_lords = []
    if user_lagna and user_moon:
        rasi_lords = {1:"Sevvai", 2:"Sukran", 3:"Budhan", 4:"Chandran", 5:"Suriyan", 6:"Budhan", 7:"Sukran", 8:"Sevvai", 9:"Guru", 10:"Sani", 11:"Sani", 12:"Guru"}
        power_lords = [rasi_lords.get(user_lagna, ""), rasi_lords.get(user_moon, "")]

    horai_dict = {"Suriyan": {"en": "Suriyan", "ta": "சூரியன்", "act_en": "Govt / Authority", "act_ta": "அரசு / அதிகாரம்", "color": "#d35400"}, "Sukran": {"en": "Sukran", "ta": "சுக்கிரன்", "act_en": "Art / Luxury", "act_ta": "கலை / உறவு", "color": "#8e44ad"}, "Budhan": {"en": "Budhan", "ta": "புதன்", "act_en": "Data / Trade", "act_ta": "கல்வி / தகவல்", "color": "#27ae60"}, "Chandran": {"en": "Chandran", "ta": "சந்திரன்", "act_en": "Travel / Mind", "act_ta": "பயணம் / மனம்", "color": "#2980b9"}, "Sani": {"en": "Sani", "ta": "சனி", "act_en": "Deep Labor", "act_ta": "உழைப்பு", "color": "#34495e"}, "Guru": {"en": "Guru", "ta": "குரு", "act_en": "Wealth / Counsel", "act_ta": "சுப காரியம்", "color": "#f39c12"}, "Sevvai": {"en": "Sevvai", "ta": "செவ்வாய்", "act_en": "Execution", "act_ta": "செயல்", "color": "#c0392b"}}
    horai_order = ["Suriyan", "Sukran", "Budhan", "Chandran", "Sani", "Guru", "Sevvai"]
    
    schedule = []
    for hour_offset in range(12):
        block_s = sunrise_dt + timedelta(hours=hour_offset * horai_len_hrs)
        block_e = block_s + timedelta(hours=horai_len_hrs)
        
        if is_today and block_e < dt_obj: continue 
            
        lord_key = horai_order[({0:0, 1:3, 2:6, 3:2, 4:5, 5:1, 6:4}[wd_idx] + hour_offset) % 7]
        lord_data = horai_dict[lord_key]
        
        schedule.append({
            "lord": f"{lord_data['en']} Horai" if lang=="English" else f"{lord_data['ta']} ஓரை",
            "activity": lord_data['act_en'] if lang=="English" else lord_data['act_ta'],
            "time": f"{block_s.strftime('%I:%M %p').lstrip('0')} - {block_e.strftime('%I:%M %p').lstrip('0')}",
            "color": lord_data['color'],
            "is_current": is_today and (block_s <= dt_obj <= block_e),
            "is_power": lord_key in power_lords
        })

    return {
        "day_num": dt_obj.strftime('%d'), "month_year_en": dt_obj.strftime('%B %Y'), "day_en": dt_obj.strftime('%A'),
        "date_ta": f"{tamil_day:02d}", "day_ta": day_ta, "tamil_year": t_year, "month_ta": t_month,
        "tithi_short": t_name, "t_end": format_end_time(jd_tithi_end), "t_next": next_t_name,
        "paksha": paksha, "countdown": countdown_str, "is_waxing": is_waxing,
        "sunrise": jd_to_local_dt(sunrise_jd).strftime('%I:%M %p').lstrip('0'), "sunset": jd_to_local_dt(sunset_jd).strftime('%I:%M %p').lstrip('0'),
        "yoga": daily_yoga, "y_end": format_end_time(jd_yoga_end), "y_next": next_yoga_name,
        "nakshatra": nak_name, "n_end": format_end_time(jd_nak_end), "n_next": next_nak_name,
        "rasi": daily_rasi_name, "r_end": format_end_time(jd_rasi_end), "r_next": next_rasi_name,
        "ch_naks": ch_naks, "rk": get_time_str(rk_start_hrs[wd_idx], 1.5), "yg": get_time_str(yg_start_hrs[wd_idx], 1.5), 
        "nn": nn_str, "gnn": gnn_str, "schedule": schedule,
        "current_jd_ut": current_jd_ut, "tara_name": tara_name, "tara_color": tara_color
    }

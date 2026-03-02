import swisseph as swe
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# Fallback translation dicts to prevent missing database keys
t_p = {"Sun": "சூரியன்", "Moon": "சந்திரன்", "Mars": "செவ்வாய்", "Mercury": "புதன்", "Jupiter": "குரு", "Venus": "சுக்கிரன்", "Saturn": "சனி", "Rahu": "ராகு", "Ketu": "கேது", "Lagna": "லக்னம்"}
ZODIAC_TA = {1: "மேஷம்", 2: "ரிஷபம்", 3: "மிதுனம்", 4: "கடகம்", 5: "சிம்மம்", 6: "கன்னி", 7: "துலாம்", 8: "விருச்சிகம்", 9: "தனுசு", 10: "மகரம்", 11: "கும்பம்", 12: "மீனம்"}
ZODIAC = ["", "Mesha", "Rishabha", "Mithuna", "Kataka", "Simha", "Kanya", "Thula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
RASI_RULERS = {1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"}

# --- TIME & LOCATION ---
def get_location_coordinates(query):
    try:
        if query.strip().isdigit() and len(query.strip()) == 6: query = f"{query}, India"
        location = Nominatim(user_agent="vedic_astro_ai").geocode(query)
        if location:
            tz_str = TimezoneFinder().timezone_at(lng=location.longitude, lat=location.latitude)
            return location.latitude, location.longitude, tz_str
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
    nak_idx = int(lon / 13.333333333)
    return nak_names[nak_idx], lords[nak_idx % 9]

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
    BINDU_RULES = {
        "Sun": {"Sun":[1,2,4,7,8,9,10,11], "Moon":[3,6,10,11], "Mars":[1,2,4,7,8,9,10,11], "Mercury":[3,5,6,9,10,11,12], "Jupiter":[5,6,9,11], "Venus":[6,7,12], "Saturn":[1,2,4,7,8,9,10,11], "Lagna":[3,4,6,10,11,12]},
        "Moon": {"Sun":[3,6,7,8,10,11], "Moon":[1,3,6,7,10,11], "Mars":[2,3,5,6,9,10,11], "Mercury":[1,3,4,5,7,8,10,11], "Jupiter":[1,4,7,8,10,11,12], "Venus":[3,4,5,7,9,10,11], "Saturn":[3,5,6,11], "Lagna":[3,6,10,11]},
        "Mars": {"Sun":[3,5,6,10,11], "Moon":[3,6,11], "Mars":[1,2,4,7,8,10,11], "Mercury":[3,5,6,11], "Jupiter":[6,10,11,12], "Venus":[6,8,11,12], "Saturn":[1,4,7,8,9,10,11], "Lagna":[1,3,6,10,11]},
        "Mercury": {"Sun":[5,6,9,11,12], "Moon":[2,4,6,8,10,11], "Mars":[1,2,4,7,8,9,10,11], "Mercury":[1,3,5,6,9,10,11,12], "Jupiter":[6,8,11,12], "Venus":[1,2,3,4,5,8,9,11], "Saturn":[1,2,4,7,8,9,10,11], "Lagna":[1,2,4,6,8,10,11]},
        "Jupiter": {"Sun":[1,2,3,4,7,8,9,10,11], "Moon":[2,5,7,9,11], "Mars":[1,2,4,7,8,10,11], "Mercury":[1,2,4,5,6,9,10,11], "Jupiter":[1,2,3,4,7,8,10,11], "Venus":[2,5,6,9,10,11], "Saturn":[3,5,6,12], "Lagna":[1,2,4,5,6,9,10,11]},
        "Venus": {"Sun":[8,11,12], "Moon":[1,2,3,4,5,8,9,11,12], "Mars":[3,5,6,9,11,12], "Mercury":[3,5,6,9,11], "Jupiter":[5,8,9,10,11], "Venus":[1,2,3,4,5,8,9,10,11], "Saturn":[3,4,5,8,9,10,11], "Lagna":[1,2,3,4,5,8,9,11]},
        "Saturn": {"Sun":[1,2,4,7,8,10,11], "Moon":[3,6,11], "Mars":[3,5,6,10,11], "Mercury":[6,8,9,10,11,12], "Jupiter":[5,6,11,12], "Venus":[6,11,12], "Saturn":[3,5,6,11], "Lagna":[1,3,4,6,10,11]}
    }
    scores = [0] * 12
    curr = p_pos.copy(); curr['Lagna'] = lagna
    for p, rules in BINDU_RULES.items():
        if p not in curr: continue
        for ref, offsets in rules.items():
            if ref not in curr: continue
            for off in offsets: scores[(curr[ref] - 1 + off - 1) % 12] += 1
    return scores

def get_bhava_chalit(jd, lat, lon):
    return swe.houses_ex(jd, lat, lon, b'P', swe.FLG_SIDEREAL)[0]

def determine_house(planet_lon, cusps):
    p_lon = planet_lon % 360
    for i in range(12):
        lower, upper = cusps[i], cusps[(i+1)%12]
        if lower < upper:
            if lower <= p_lon < upper: return i + 1
        else:
            if p_lon >= lower or p_lon < upper: return i + 1
    return 1

# --- SCORECARD TEXT GENERATOR ---
def get_house_strength_analysis(house_num, score, lang="English"):
    topics = {
        1: "Self, Physical Body, General Vitality", 2: "Wealth, Family Assets, Speech", 3: "Courage, Short Trips, Self-Effort", 
        4: "Home, Mother, Deep Inner Peace", 5: "Intellect, Creativity, Speculation", 6: "Health Routines, Debt, Overcoming Rivals",
        7: "Marriage, Business Partnerships, Public Image", 8: "Transformation, Sudden Events, Hidden Wealth", 
        9: "Luck, Higher Wisdom, Mentors, Fortune", 10: "Career, Executive Authority, Reputation", 
        11: "Major Gains, Professional Networks", 12: "Foreign Travel, Spiritual Retreats, Expenditures"
    }
    t_topics = {
        1: "சுய அடையாளம், உடல் ஆரோக்கியம்", 2: "செல்வம், குடும்பம்", 3: "தைரியம், சுயமாக முன்னேறுதல்", 
        4: "வீடு, தாயார், மன அமைதி", 5: "புத்திசாலித்தனம், குழந்தைகள், கலை", 6: "ஆரோக்கியம், கடன் தீர்வு, எதிரிகளை வெல்லுதல்",
        7: "திருமணம், கூட்டாண்மை", 8: "ரகசியங்கள், எதிர்பாராத மாற்றங்கள்", 9: "பாக்கியம், உயர்கல்வி, தந்தை", 
        10: "தொழில் வெற்றி, சமூக அந்தஸ்து", 11: "லாபம், நெட்வொர்க்", 12: "பயணங்கள், முதலீடுகள், ஆன்மீகம்"
    }
    
    if score >= 30:
        if lang == "Tamil": return f"**மிகவும் வலிமையான பாவம்:** இந்த {house_num}-ஆம் பாவம் ({t_topics[house_num]}) உங்கள் ஜாதகத்தில் இயற்கையாகவே அதிக சக்தி பெற்றுள்ளது. இந்தத் துறையில் நீங்கள் எடுக்கும் சிறிய முயற்சிகள் கூட மாபெரும் வெற்றியைத் தரும். இது உங்களின் மிகப்பெரிய பலம்."
        return f"**Power Zone:** The {house_num}th House ({topics[house_num]}) is exceptionally strong. Energy flows effortlessly here. You possess a natural, built-in advantage in this area of life. Leverage this to build your empire."
    elif score < 25:
        if lang == "Tamil": return f"**கவனம் தேவைப்படும் பாவம்:** இந்த {house_num}-ஆம் பாவம் ({t_topics[house_num]}) சற்று பலவீனமாக உள்ளது. இந்தத் துறையில் வெற்றி பெற நீங்கள் மற்றவர்களை விட அதிக கவனமும், கடின உழைப்பும், திட்டமிடலும் செலுத்த வேண்டும்."
        return f"**Challenge Zone:** The {house_num}th House ({topics[house_num]}) requires highly conscious, strategic effort. This area does not yield easy luck; you must actively manage it and avoid careless risks."
    else:
        if lang == "Tamil": return f"**சமநிலையான பாவம்:** {house_num}-ஆம் பாவம் ({t_topics[house_num]}) சீராக உள்ளது. உங்கள் உழைப்பிற்கு ஏற்ற நியாயமான பலன்கள் கிடைக்கும்."
        return f"**Balanced Zone:** The {house_num}th House ({topics[house_num]}) is stable. It operates strictly on the rule of cause and effect. Your direct input will equal your direct output."

# --- DEEP TEXT ANALYSIS ENGINES ---
def analyze_karmic_axis(p_pos, lagna_rasi, lang="English"):
    rahu_h = (p_pos["Rahu"] - lagna_rasi + 1) if (p_pos["Rahu"] - lagna_rasi + 1) > 0 else (p_pos["Rahu"] - lagna_rasi + 1) + 12
    ketu_h = (p_pos["Ketu"] - lagna_rasi + 1) if (p_pos["Ketu"] - lagna_rasi + 1) > 0 else (p_pos["Ketu"] - lagna_rasi + 1) + 12
    res = []
    
    if lang == "Tamil":
        res.append("#### கர்ம வினை மற்றும் ஆன்மீக அச்சு (ராகு/கேது)")
        res.append(f"உங்கள் ஜாதகத்தில் ராகு {rahu_h}-ஆம் வீட்டிலும், கேது {ketu_h}-ஆம் வீட்டிலும் அமர்ந்துள்ளனர். இது உங்களின் முற்பிறவி மற்றும் இப்பிறவியின் நோக்கத்தைக் குறிக்கிறது.")
        res.append(f"**ராகுவின் தாக்கம் ({rahu_h}-ஆம் பாவம்):** இந்தத் துறையில் நீங்கள் மிகப்பெரிய உச்சத்தை தொட வேண்டும் என்ற அளவற்ற ஆசை இருக்கும். இது இப்பிறவியின் மிகப்பெரிய சவாலாகும்.")
        res.append(f"**கேதுவின் தாக்கம் ({ketu_h}-ஆம் பாவம்):** முற்பிறவியிலேயே இந்தத் துறையில் நீங்கள் முழு நிபுணத்துவம் பெற்றுவிட்டீர்கள். எனவே, இந்த விஷயங்களில் உங்களுக்கு இயல்பான அறிவும், அதே சமயம் ஒருவித பற்றின்மையும் (Detachment) இருக்கும்.")
    else:
        res.append("#### The Karmic Axis (Rahu & Ketu)")
        res.append(f"Rahu and Ketu operate exactly 180 degrees apart in your {rahu_h}th and {ketu_h}th houses. This axis describes your soul's deepest evolutionary journey.")
        res.append(f"**Rahu's Ambition ({rahu_h}th House):** Rahu creates a relentless, almost obsessive hunger for growth in this house. This is uncharted territory for your soul. You are meant to take massive, unconventional leaps here.")
        res.append(f"**Ketu's Mastery & Detachment ({ketu_h}th House):** Ketu is placed here, signifying deep past-life mastery. You possess effortless, intuitive genius in this area, but you may simultaneously feel a profound sense of 'been there, done that' detachment. Use Ketu's research skills without completely abandoning the house's duties.")
    return res

def scan_yogas(p_pos, lagna_rasi, lang="English"):
    yogas = []
    p_houses = {p: ((r - lagna_rasi + 1) if (r - lagna_rasi + 1) > 0 else (r - lagna_rasi + 1) + 12) for p, r in p_pos.items() if p != "Lagna"}
    
    if p_pos.get("Sun") == p_pos.get("Mercury"):
        if lang == "Tamil": yogas.append({"Name": "புதாதித்ய யோகம் (Budhaditya)", "Type": "அறிவு மற்றும் வணிகம்", "Description": f"சூரியனும் புதனும் உங்கள் {p_houses.get('Sun')}-ஆம் வீட்டில் இணைந்து இந்த யோகத்தை உருவாக்குகின்றன. இது மிகச்சிறந்த பகுப்பாய்வு திறனையும், கூர்மையான வணிக அறிவையும் தருகிறது. தசா/புக்தி காலங்களில் இது உங்களுக்கு சிறந்த பெயரையும் பணத்தையும் பெற்றுத் தரும்."})
        else: yogas.append({"Name": "Budhaditya Yoga", "Type": "Intellect & Commerce", "Description": f"The Sun and Mercury are structurally conjunct in your {p_houses.get('Sun')}th House. This forms a highly analytical and brilliant business mind. **Impact:** It enhances executive communication and creates wealth potential through advisory or trade. You likely noticed this mental edge emerging during your formal education."})
    
    if "Jupiter" in p_pos and "Moon" in p_pos:
        jup_from_moon = (p_pos["Jupiter"] - p_pos["Moon"] + 1) if (p_pos["Jupiter"] - p_pos["Moon"] + 1) > 0 else (p_pos["Jupiter"] - p_pos["Moon"] + 1) + 12
        if jup_from_moon in [1, 4, 7, 10]:
            if lang == "Tamil": yogas.append({"Name": "கஜகேசரி யோகம் (Gajakesari)", "Type": "புகழ் மற்றும் தெய்வீக பாதுகாப்பு", "Description": "குரு உங்கள் சந்திரனுக்கு கேந்திரத்தில் இருப்பதால் இந்த மாபெரும் யோகம் உருவாகிறது. இது சமுதாயத்தில் பெரும் மதிப்பையும், எதிரிகளை வெல்லும் சாதுரியத்தையும் தரும். எக்காலத்திலும் உங்களை காக்கும் அரணாக செயல்படும்."})
            else: yogas.append({"Name": "Gajakesari Yoga", "Type": "Fame & Institutional Protection", "Description": "Jupiter is placed in a foundational angle from your Natal Moon. This is an elite combination for widespread respect. **Impact:** It grants a noble reputation and divine protection against crises. This yoga acts as a lifetime safety net, resolving major issues at the 11th hour."})
    
    pm_planets = {"Mars": "Ruchaka", "Mercury": "Bhadra", "Jupiter": "Hamsa", "Venus": "Malavya", "Saturn": "Sasa"}
    for p, y_name in pm_planets.items():
        if p in p_houses and p_houses[p] in [1, 4, 7, 10] and get_dignity(p, p_pos[p]) in ["Own", "Exalted"]:
            if lang == "Tamil": yogas.append({"Name": f"{y_name} மகாபுருஷ யோகம்", "Type": "தனித்துவமான ஆளுமை", "Description": f"{t_p[p]} உங்கள் {p_houses[p]}-ஆம் வீட்டில் மிகவும் வலுவாக அமைந்திருப்பதால் இந்த யோகம் அமைகிறது. இது உங்களை ஒரு மாபெரும் தலைவராகவும் உங்கள் துறையில் அசைக்க முடியாத சக்தியாகவும் உயர்த்தும்."})
            else: yogas.append({"Name": f"{y_name} Mahapurusha Yoga", "Type": "Exceptional Domain Authority", "Description": f"{p} is exceptionally strong in a foundational angle ({p_houses[p]}th House). **Impact:** You are mathematically destined to be a recognized authority in the domain ruled by {p}. This grants immense psychological resilience."})
    
    lord_9 = RASI_RULERS[(lagna_rasi + 8) % 12 or 12]
    lord_10 = RASI_RULERS[(lagna_rasi + 9) % 12 or 12]
    if p_pos.get(lord_9) == p_pos.get(lord_10) and lord_9 != lord_10:
        if lang == "Tamil": yogas.append({"Name": "தர்ம கர்மாதிபதி யோகம்", "Type": "உயர்ந்த தொழில் அந்தஸ்து", "Description": "உங்களின் 9-ஆம் அதிபதியும் 10-ஆம் அதிபதியும் இணைந்திருப்பதால் இந்த யோகம் அமைகிறது. இது தொழில் ரீதியான மிக உயர்ந்த ராஜ யோகமாகும். தொட்டதெல்லாம் துலங்கும்."})
        else: yogas.append({"Name": "Dharma Karmadhipati Yoga", "Type": "Ultimate Career Destiny", "Description": f"The rulers of your 9th House of Luck and 10th House of Career are united. **Impact:** This represents the highest form of professional Raja Yoga. Your internal life purpose and external profession are seamlessly aligned."})
    
    if not yogas:
        if lang == "Tamil": yogas.append({"Name": "சுயமுயற்சி யோகம்", "Type": "சுயம்புவான வெற்றி", "Description": "உங்கள் ஜாதகம் எந்த ஒரு பாரம்பரிய யோகத்தையும் சார்ந்து இல்லை. உங்கள் வெற்றி முற்றிலும் உங்கள் சுயமுயற்சியாலும், விடாமுயற்சியாலும் மட்டுமே அமையும்."})
        else: yogas.append({"Name": "Independent Karma Yoga", "Type": "Self-Made Destiny", "Description": "Your chart relies purely on active free-will rather than passive, inherited yogas. **Impact:** Every victory in your life is 100% self-earned through execution and strategy."})
    
    return yogas

def analyze_education(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(lagna_rasi + 4) % 12 or 12]
    mercury_dig = get_dignity("Mercury", p_pos["Mercury"])
    if lang == "Tamil":
        analysis.append("#### கல்வி மற்றும் அறிவுசார் திறன்")
        analysis.append(f"உங்கள் கல்வி மற்றும் அறிவாற்றலை 5-ஆம் அதிபதியான {t_p[lord_5]} தீர்மானிக்கிறார். நீங்கள் எதையும் மேலோட்டமாக படிக்காமல், தர்க்கரீதியாக ஆராய்ந்து ஆழமாகப் புரிந்து கொள்ளும் குணம் கொண்டவர்.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append("புதன் மிகவும் வலுவாக இருப்பதால், சிக்கலான தரவுகளைப் பகுப்பாய்வு செய்யும் அபார திறன் உங்களுக்கு உண்டு. தொழில்நுட்பம் மற்றும் நிதி துறைகளில் உங்களால் மற்றவர்களை எளிதாக முந்த முடியும்.")
        elif mercury_dig == "Neecha": analysis.append("புதன் பலவீனமாக இருப்பதால், வெறும் மனப்பாடம் செய்வதை விட, அனுபவபூர்வமான கல்வியே உங்களுக்கு உகந்தது. மிகச்சிறந்த கற்பனைத்திறன் உங்களுக்கு உண்டு.")
        else: analysis.append("உங்களின் தர்க்க அறிவும், கற்கும் திறனும் சீராக உள்ளது. கவனச்சிதறல்களைத் தவிர்த்து ஒருமுகப்படுத்தப்பட்ட பயிற்சியின் மூலம் நீங்கள் எந்தத் துறையிலும் வல்லவராகலாம்.")
    else:
        analysis.append("#### Academic Profile & Strategic Intellect")
        analysis.append(f"Your primary intellect and cognitive processing are governed by the 5th House lord, {lord_5}. This dictates your unique learning style: you do not just memorize facts; the subject matter must deeply resonate with the core energy of {lord_5} for you to master it.")
        if mercury_dig in ["Exalted", "Own"]: analysis.append("Because Mercury (the planet of logic and data) is highly dignified, your capacity to process, structure, and deploy complex information is elite. You have a distinct, highly analytical advantage in technical, financial, or heavily communicative environments.")
        elif mercury_dig == "Neecha": analysis.append("Your Mercury is mathematically debilitated. This does not imply low intelligence; rather, it indicates you possess highly intuitive, abstract, or creative intelligence. Traditional rote-memorization may frustrate you, but your ability to see the 'big picture' is unparalleled.")
        else: analysis.append("Your logical processing is balanced and adaptable. You are capable of mastering a wide variety of subjects, provided you enforce strict academic discipline and actively guard against daily distractions.")
    return analysis

def analyze_career_professional(p_pos, d10_lagna, lagna_rasi, sav_scores, bhava_placements, lang="English"):
    analysis = []
    sun_rasi_h = (p_pos['Sun'] - lagna_rasi + 1) if (p_pos['Sun'] - lagna_rasi + 1) > 0 else (p_pos['Sun'] - lagna_rasi + 1) + 12
    sun_bhava_h = bhava_placements['Sun'] 
    d10_lord = RASI_RULERS[(d10_lagna + 9) % 12 or 12]
    
    if lang == "Tamil":
        analysis.append("#### தொழில் மற்றும் செயல் வியூகம்")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"முக்கிய மாற்றம்: உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியில் இருந்தாலும், அது {sun_bhava_h}-ஆம் பாவத்திலேயே முழுமையாகச் செயல்படுகிறது. உங்களின் உண்மையான அங்கீகாரம் இந்த பாவத்தின் வழியாகவே கிடைக்கும்.")
        else: analysis.append(f"நேரடி பலன்: உங்கள் சூரியன் {sun_rasi_h}-ஆம் ராசியிலும் பாவத்திலும் சரியாகப் பொருந்தி செயல்படுகிறார். இது உங்கள் சிந்தனைக்கும் செயலுக்கும் இடையே நேரடி ஒத்திசைவை உருவாக்குகிறது.")
        
        analysis.append("#### தசாம்ச (D10) தலைமைத்துவ ரகசியம்")
        analysis.append(f"உங்கள் தொழில் வெற்றியை நிர்ணயிக்கும் தசாம்ச அதிபதி {t_p[d10_lord]}. கார்ப்பரேட் அல்லது வணிகச் சூழலில், நீங்கள் இந்த கிரகத்தின் குணாதிசயங்களை (உதாரணமாக: செவ்வாய் என்றால் வேகம், குரு என்றால் வழிகாட்டுதல், சனி என்றால் ஒழுக்கம்) முதன்மையாக பயன்படுத்த வேண்டும். இதுவே உங்களின் மிகப்பெரிய பிரம்மாஸ்திரம்.")
    else:
        analysis.append("#### Career Strategy & True Authority")
        if sun_rasi_h != sun_bhava_h: analysis.append(f"**Crucial Alignment Shift:** Your Sun is psychologically seated in the {sun_rasi_h}th Sign, but functionally produces results in the {sun_bhava_h}th House. This means you must pivot your career focus to deliver value specifically in {sun_bhava_h}th House matters to gain true recognition.")
        else: analysis.append(f"**Direct Alignment:** Your Sun perfectly aligns in both Sign and House ({sun_rasi_h}th). Your internal psychological drive perfectly matches the external results the world expects of you.")
        
        analysis.append("#### The CEO Engine (Dasamsa D10)")
        analysis.append(f"Your deepest professional capability is revealed in the D10 chart. Your Dasamsa Career Lord is **{d10_lord}**. In high-pressure environments, meetings, or executive decisions, you must completely lean into the traits of {d10_lord}. Do not try to copy others' management styles; your unique competitive advantage lies strictly in operating through {d10_lord}'s specific energy.")
    return analysis

def analyze_love_marriage(d1_lagna, d9_lagna, p_d9, p_d1, lang="English"):
    analysis = []
    lord_5 = RASI_RULERS[(d1_lagna + 4) % 12 or 12]
    d9_7th_lord = RASI_RULERS[(d9_lagna + 6) % 12 or 12]
    
    traits = {
        "Sun": "absolute loyalty, dignified leadership, and taking mutual pride in each other's status",
        "Moon": "deep emotional empathy, nurturing domestic care, and intuitive understanding",
        "Mars": "protective action, setting clear boundaries, and guarding the relationship fiercely",
        "Mercury": "crystal-clear communication, intellectual banter, and treating each other as best friends",
        "Jupiter": "moral grounding, shared philosophical growth, and mature wisdom",
        "Venus": "unconditional romantic devotion, aesthetic harmony, and prioritizing peace",
        "Saturn": "unshakeable duty, absolute loyalty through hard times, and extreme maturity"
    }
    t_traits = {
        "Sun": "நேர்மை, கௌரவம் மற்றும் பரஸ்பர மரியாதை",
        "Moon": "ஆழமான பாசம், அக்கறை மற்றும் உணர்வுபூர்வமான புரிதல்",
        "Mars": "உறவை பாதுகாக்கும் குணம், தைரியம் மற்றும் தெளிவான முடிவுகள்",
        "Mercury": "சிறந்த தகவல் தொடர்பு, நகைச்சுவை உணர்வு மற்றும் சிறந்த நட்பு",
        "Jupiter": "தெய்வீக பக்தி, முதிர்ச்சியான ஞானம் மற்றும் பரஸ்பர வழிகாட்டுதல்",
        "Venus": "அளவற்ற அன்பு, அழகுணர்ச்சி மற்றும் சமரச மனப்பான்மை",
        "Saturn": "கடமையுணர்வு, கடினமான நேரங்களில் கைவிடாத விசுவாசம் மற்றும் அதீத பொறுமை"
    }
    
    if lang == "Tamil":
        analysis.append("#### காதல் மற்றும் திருமண வாழ்க்கை (D9 நவாம்சம்)")
        analysis.append(f"உங்கள் ஆரம்பகால காதல் உணர்வுகள் 5-ஆம் அதிபதியான {t_p[lord_5]} ஆல் ஆளப்படுகிறது. எனவே தொடக்கத்தில் உற்சாகமான உறவுகளை நாடுவீர்கள்.")
        analysis.append(f"ஆனால், உங்கள் உண்மையான, நிரந்தர திருமண வாழ்க்கை நவாம்சத்தின் 7-ஆம் அதிபதியான **{t_p[d9_7th_lord]}** இன் குணங்களைச் சார்ந்திருக்கும். உங்கள் துணை '{t_traits[d9_7th_lord]}' ஆகிய முதிர்ச்சியான குணங்களைக் கொண்டிருக்க வேண்டும். அப்போதுதான் உங்கள் திருமண வாழ்க்கை ஒரு உடையாத கோட்டையாக மாறும்.")
    else:
        analysis.append("#### The Dating Phase vs. The Lifelong Marriage Phase")
        analysis.append(f"Your approach to early romance (5th House) is governed by {lord_5}. This implies you initially seek partners who are exciting, dynamic, and align with {lord_5}'s immediate energy. However, what you *want* in dating is entirely different from what you fundamentally *need* to sustain a lifelong marriage.")
        analysis.append(f"The 7th House of your Navamsa (D9) reveals your ultimate spousal archetype. It is ruled by **{d9_7th_lord}**. To achieve a permanently successful marriage, your partner must fundamentally embody {d9_7th_lord}'s mature traits. Specifically, your union must be built upon **{traits[d9_7th_lord]}**.")
    return analysis

def analyze_health(p_pos, lagna_rasi, lang="English"):
    analysis = []
    lagna_lord = RASI_RULERS[lagna_rasi]
    ll_dig = get_dignity(lagna_lord, p_pos[lagna_lord])
    lord_6 = RASI_RULERS[(lagna_rasi + 5) % 12 or 12]
    
    if lang == "Tamil":
        analysis.append("#### உடல் வலிமை மற்றும் நோய் எதிர்ப்பு சக்தி")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) மிகவும் வலுவாக உள்ளார். இது உங்களுக்கு இரும்பு போன்ற உடல் வலிமையையும், வியக்கத்தக்க நோய் எதிர்ப்பு சக்தியையும் அளிக்கிறது.")
        elif ll_dig == "Neecha": analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) பலவீனமாக உள்ளார். உங்கள் உடல் சக்தியை நீங்கள் மிகவும் கவனமாக கையாள வேண்டும். முறையான தூக்கமே சிறந்த மருந்து.")
        else: analysis.append(f"லக்னாதிபதி ({t_p[lagna_lord]}) சமநிலையில் உள்ளார். உங்களின் தினசரி வாழ்க்கை முறை மற்றும் பழக்கவழக்கங்களே உங்கள் ஆரோக்கியத்தை நேரடியாக தீர்மானிக்கும்.")
        analysis.append(f"**கவனம் தேவை:** ஆரோக்கியத்தை குறிக்கும் 6-ஆம் அதிபதி {t_p[lord_6]} ஆவார். இந்த கிரகத்துடன் தொடர்புடைய உடல் பாகங்களில் (உதாரணமாக: புதன் என்றால் நரம்பு, சந்திரன் என்றால் நெஞ்சு) நீங்கள் கூடுதல் தடுப்பு நடவடிக்கைகளை மேற்கொள்ள வேண்டும்.")
    else:
        analysis.append("#### Core Physical Resilience & Preventative Care")
        if ll_dig in ["Exalted", "Own"]: analysis.append(f"Your Ascendant Lord ({lagna_lord}) is exceptionally strong. This grants you a highly robust physical constitution and excellent natural immunity. You naturally recover from physical exhaustion much faster than average.")
        elif ll_dig == "Neecha": analysis.append(f"Your Ascendant Lord ({lagna_lord}) is weak by sign placement. Your physical energy is finite and must be carefully budgeted. You cannot rely on 'natural' vitality; strict sleep and dietary discipline are mandatory to avoid burnout.")
        else: analysis.append(f"Your Ascendant Lord ({lagna_lord}) is in a neutral state. Your physical resilience is perfectly average and will act as a direct mirror to your lifestyle choices. Good routines yield high energy, while poor habits show immediate physical consequences.")
        analysis.append(f"**Vulnerabilities:** The 6th House of acute health is ruled by **{lord_6}**. You must proactively monitor the physiological systems associated with {lord_6} (e.g., Mercury = nervous system/gut, Mars = inflammation/blood) throughout your life to prevent chronic issues.")
    return analysis

def generate_annual_forecast(moon_rasi, sav_scores, f_year, age, lang="English"):
    jd = swe.julday(f_year, 1, 1, 12.0)
    sat_tr = int(swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)[0][0] / 30) + 1
    jup_tr = int(swe.calc_ut(jd, swe.JUPITER, swe.FLG_SIDEREAL)[0][0] / 30) + 1
    sat_dist = (sat_tr - moon_rasi + 1) if (sat_tr - moon_rasi + 1) > 0 else (sat_tr - moon_rasi + 1) + 12
    jup_dist = (jup_tr - moon_rasi + 1) if (jup_tr - moon_rasi + 1) > 0 else (jup_tr - moon_rasi + 1) + 12
    fc = {}
    
    if lang == "Tamil":
        if sat_dist in [3, 6, 11]: fc['தொழில் மற்றும் சவால்கள் (Saturn)'] = ("மிகப்பெரிய வளர்ச்சி நிலை. சனி பகவான் உங்களுக்கு சாதகமான வீட்டில் உள்ளார். உங்களின் கடந்த கால கடின உழைப்பிற்கு மிகப்பெரிய அங்கீகாரம், பதவி உயர்வு மற்றும் எதிரிகளை வீழ்த்தும் வெற்றி இந்த ஆண்டு கிடைக்கும்.", "சனிக்கிழமைகளில் நல்லெண்ணெய் தீபம் ஏற்றவும்.")
        elif sat_dist in [1, 2, 12]: fc['தொழில் மற்றும் சவால்கள் (Saturn)'] = ("ஏழரைச் சனி காலம். பொறுமை மிக மிக அவசியம். தொழில் மற்றும் குடும்பத்தில் உங்கள் பொறுப்புகள் பலமடங்கு கூடும். அவசர முடிவுகள் மற்றும் ஈகோ மோதல்களை முற்றிலும் தவிர்க்க வேண்டும்.", "தினமும் ஹனுமான் சாலிசா படிக்கவும்.")
        else: fc['தொழில் மற்றும் சவால்கள் (Saturn)'] = ("சீரான நிலை. இது அடித்தளத்தை வலுப்படுத்தும் ஆண்டு. எந்த குறுக்கு வழியையும் நாடாமல், உங்கள் திறமைகளை வளர்த்துக் கொள்வதில் கவனம் செலுத்துங்கள்.", "பணியிடத்தை எப்போதும் சுத்தமாக வைத்திருக்கவும்.")

        if jup_dist in [2, 5, 7, 9, 11]: fc['பொருளாதாரம் மற்றும் குடும்பம் (Jupiter)'] = ("பிரமாண்டமான பணவரவு மற்றும் அதிர்ஷ்டம். குரு பகவான் சிறந்த ஸ்தானத்தில் சஞ்சரிக்கிறார். திருமணம், குழந்தை பாக்கியம் மற்றும் சொத்து சேர்க்கை போன்ற சுப காரியங்கள் தடையின்றி நடைபெறும்.", "வியாழக்கிழமைகளில் மஞ்சள் நிற உணவுகளை தானம் செய்யவும்.")
        else: fc['பொருளாதாரம் மற்றும் குடும்பம் (Jupiter)'] = ("நிலையான வருமானம். அதிக ரிஸ்க் உள்ள முதலீடுகளைத் தவிர்க்கவும். செலவுகள் வருமானத்தை மீறாமல் பார்த்துக்கொள்ள சேமிப்பில் அதிக கவனம் செலுத்தவும்.", "பணப்பையில் ஒரு சிறிய விரலி மஞ்சள் துண்டை வைத்திருக்கவும்.")
    else:
        if sat_dist in [3, 6, 11]: fc['Career & Ambition (Saturn)'] = ("**EXCELLENT GROWTH PHASE.** Saturn is transiting a highly favorable growth house. Expect a major, structural promotion, deep recognition for past hard work, and a breakthrough victory over professional obstacles. Push hard this year.", "Light a lamp with sesame oil on Saturdays.")
        elif sat_dist in [1, 2, 12]: fc['Career & Ambition (Saturn)'] = ("**SADE SATI PHASE.** You are under immense cosmic pressure to mature. You may feel professionally undervalued or heavily burdened. This is a time for extreme patience, internal skill-building, and strictly avoiding ego clashes.", "Chant Hanuman Chalisa daily.")
        else: fc['Career & Ambition (Saturn)'] = ("**STEADY PROGRESS.** There are no extreme highs or lows indicated by Saturn. This is a highly productive, 'heads-down' year. Use it to clear pending projects, organize your workflow, and build quiet momentum.", "Keep your workspace completely decluttered.")

        if jup_dist in [2, 5, 7, 9, 11]: fc['Wealth & Family Expansion (Jupiter)'] = ("**HIGH LUCK & INFLOW.** Jupiter actively blesses your chart this year. This is a phenomenal window for financial investments, purchasing property, or experiencing joyous family expansions (marriage/births). The universe is opening doors for you.", "Donate yellow food (bananas/dal) on Thursdays.")
        else: fc['Wealth & Family Expansion (Jupiter)'] = ("**STABLE CONSOLIDATION.** Jupiter’s placement advises extreme financial caution. Strictly avoid high-risk speculation or gambling this year. Focus purely on savings, protecting your current assets, and managing your diet.", "Keep a small turmeric stick in your wallet.")
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

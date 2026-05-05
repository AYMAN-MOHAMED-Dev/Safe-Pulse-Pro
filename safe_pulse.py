import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
import time
import secrets
import random
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import string

def get_ai_response(u_input):
    import random
    import google.generativeai as genai
    keys_pool = st.secrets.get("GEMINI_KEYS", [])
    if not keys_pool: 
        return "❌ خطأ: لم يتم العثور على مفاتيح API."
    
    name = st.session_state.get('current_user', 'مستخدم')
    full_prompt = f"المستخدم اسمه {name}. أجب على هذا السؤال الطبي/الطوارئ: {u_input}"

    for attempt in range(len(keys_pool)):
        current_key = random.choice(keys_pool)
        try:
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(full_prompt)
            return response.text
        except Exception:
            continue 
    return "⚠️ جميع المفاتيح مشغولة حالياً، حاول مرة أخرى."

def get_dynamic_key(base_name):
    """تولد مفتاح فريد لمنع خطأ التكرار في ستريم ليت"""
    random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"{base_name}_{random_id}"

# 1. تهيئة المتغير db كـ None في البداية لتجنب NameError
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# تعريف المتغير بشكل عالمي في بداية الملف
if 'db' not in locals():
    db = None

def init_firebase():
    global db # هام جداً للوصول للمتغير في كل مكان
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                fb_conf = dict(st.secrets["firebase"])
                cred = credentials.Certificate(fb_conf)
                firebase_admin.initialize_app(cred)
            else:
                cred = credentials.Certificate("serviceAccountKey.json")
                firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Firebase Init Error: {e}")
            return None
    
    # التأكد من تعريف db بعد التهيئة
    if db is None:
        db = firestore.client()
    return db

# تشغيل التهيئة فوراً عند فتح التطبيق
db = init_firebase()

# --- 3. جلب المفاتيح العامة (Keys) ---
try:
    if "general" in st.secrets:
        INTERNAL_KEY = st.secrets["general"].get("internal_key")
        GEMINI_KEY = st.secrets["general"].get("GEMINI_API_KEY")
        encryption_key = st.secrets["general"].get("ENCRYPTION_KEY")
    else:
        INTERNAL_KEY = st.secrets.get("internal_key")
        GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
        encryption_key = st.secrets.get("ENCRYPTION_KEY")
except Exception as e:
    st.warning("⚠️ بعض المفاتيح العامة مفقودة في الإعدادات")

# --- 4. إدارة حالة الجلسة ---
if 'check_attempts' not in st.session_state:
    st.session_state.check_attempts = 0
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "HOME"

# --- 4. واجهة CSS والتصميم ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        [data-testid="stSidebar"] { display: none !important; width: 0px !important; }
        [data-testid="stMainView"] { width: 100% !important; margin-left: 0px !important; }
        .stAppDeployButton {display: none !important;}
        header { visibility: hidden; }
        /* كارت رد المسعف الذكي النيوني */
.ai-neon-card {
    background: #0d1117;
    border: 2px solid #00d4ff;
    border-radius: 15px;
    padding: 20px;
    margin-top: 20px;
    box-shadow: 0 0 15px #00d4ff, inset 0 0 10px #00d4ff;
    animation: slide_up 0.5s ease-out;
}

.ai-title {
    color: #00d4ff;
    font-size: 1.2rem;
    font-weight: bold;
    margin-bottom: 15px;
    text-shadow: 0 0 10px #00d4ff;
    display: flex;
    align-items: center;
    gap: 10px;
}

.ai-content {
    color: #ffffff;
    line-height: 1.8;
    font-size: 1rem;
}
    </style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "HOME"

# --- 2. تعريف الدوال الأساسية وإدارة الملفات السحابية ---

SESSION_FILE = "assets/sessions.json"
KEY_FILE = "assets/internal.key"
REGISTRY_FILE = "assets/user_registry.json"

if not os.path.exists("assets"): 
    os.makedirs("assets")

def get_cipher():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f: f.write(key)
    return Fernet(open(KEY_FILE, "rb").read())

cipher = get_cipher()

def get_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f: 
            try: return json.load(f)
            except: return {}
    return {}

def save_to_registry(username, password):
    registry = get_registry()
    # تشفير كلمة المرور باستخدام فرنيت (Fernet) بدلاً من الـ Hash
    encrypted_password = cipher.encrypt(password.encode('utf-8')).decode('utf-8')
    registry[username] = encrypted_password
    with open(REGISTRY_FILE, "w") as f: 
        json.dump(registry, f)

def save_user_data(username, data):
    if db is not None:
        # تشفير البيانات قبل إرسالها للسحابة لضمان الخصوصية
        encrypted_data = cipher.encrypt(json.dumps(data).encode()).decode()
        db.collection("users").document(username).set({"vault": encrypted_data})
    else:
        st.error("قاعدة البيانات غير متصلة. تأكد من إعدادات Firebase.")

def load_user_data(username):
    try:
        doc_ref = db.collection("users").document(username)
        doc = doc_ref.get()
        if doc.exists:
            encrypted_data = doc.to_dict().get("vault")
            user_data = json.loads(cipher.decrypt(encrypted_data.encode()).decode())
            if "ai_chat_history" not in user_data:
                user_data["ai_chat_history"] = []
            if "personal_chat" not in user_data:
                user_data["personal_chat"] = []
            return user_data
    except:
        return None
    return None

def get_64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def get_user_defaults(username):
    return {
        "username": username, "fav_person_1_name": "شخصي المفضل 1", "fav_person_1_phone": "01206141380", 
        "fav_person_2_name": "شخصي المفضل 2", "fav_person_2_phone": "01206141380", "neon": True, "lang": "AR", 
        "blood": "O+", "meds": [], "shake_on": True, "theft_on": True, "has_allergy": "No / لا", 
        "allergy_type": "", "app_lock": False, "med_reminder": False, "med_name": "", "med_time": "08:00",
        "water_reminder": True, "battery_alert": True, "personal_chat": [], "ai_chat_history": []
    }

# --- 3. نظام الجلسات (Token-Based) ---

def get_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_sessions(data):
    with open(SESSION_FILE, "w") as f: json.dump(data, f)

def create_session(username):
    sessions = get_sessions()
    token = secrets.token_urlsafe(32)
    expire_time = (datetime.now() + timedelta(days=30)).isoformat()
    sessions[token] = {"username": username, "expires": expire_time}
    save_sessions(sessions)
    return token

def delete_session(token):
    sessions = get_sessions()
    if token in sessions:
        del sessions[token]
        save_sessions(sessions)

def get_user_from_token(token):
    sessions = get_sessions()
    if not token or token not in sessions: return None
    session = sessions[token]
    if datetime.fromisoformat(session["expires"]) < datetime.now():
        del sessions[token]
        save_sessions(sessions)
        return None
    return session["username"]

# --- 4. إدارة الجلسة المستقرة واستعادة التوكن ---

token_from_browser = streamlit_js_eval(
    js_expressions="localStorage.getItem('sp_token')",
    key="persistent_session_check_v5"
)

if not st.session_state.authenticated:
    if token_from_browser:
        user = get_user_from_token(token_from_browser)
        if user:
            user_data = load_user_data(user)
            if user_data:
                st.session_state.current_user = user
                st.session_state.secure_vault = user_data
                st.session_state.authenticated = True
                st.session_state.page = "HOME"
                st.rerun()
        else:
            st.session_state.check_attempts = 10

    elif st.session_state.check_attempts < 3:
        st.session_state.check_attempts += 1
        st.info("جاري استعادة جلسة العمل... يرجى الانتظار")
        time.sleep(1)
        st.rerun()

vault = st.session_state.get('secure_vault', get_user_defaults("guest"))
if "lang" not in st.session_state:
    st.session_state.lang = vault.get("lang", "AR")

# --- 5. القواميس والترجمة ---
AID_CONTENT = {
    "AR": [
        {"title": "1️⃣ حالات الإغماء", "icon": "fainting.png", "tips": ["ضع الشخص مستلقيًا على ظهره مع رفع القدمين قليلًا.", "تأكد من وعيه وتنفسه.", "افتح النوافذ لتوفير هواء نقي.", "فك أي ملابس ضيقة حول الرقبة والصدر.", "إذا لم يستعد وعيه بعد دقيقة أو ظهرت علامات خطيرة، اتصل بالإسعاف فورًا."]},
        {"title": "2️⃣ الحروق بالنار في المنزل", "icon": "burns.png", "tips": ["أبعد المصاب عن مصدر النار فورًا.", "برد الحرق بماء فاتر وليس مثلج لمدة 10–20 دقيقة.", "لا تفرقع الفقاعات أو تضع دهانات أو معجون أسنان.", "غطِّ الحرق بشاش نظيف ومعقم.", "إذا كان الحرق كبيرًا أو عميقًا، اتصل بالطوارئ فورًا."]},
        {"title": "3️⃣ الأزمات القلبية", "icon": "heart_attack.png", "tips": ["اجعل الشخص مستلقيًا أو نصف جالس حسب راحته.", "اطلب المساعدة الطبية الطارئة فورًا.", "لا تجعله يتحرك أو يبذل مجهودًا.", "إذا كان متوفر، أعطه أسبرين (إذا لا يعاني من تحسس).", "راقب التنفس والنبض وحضر لإجراء الإنعاش إذا لزم الأمر."]},
        {"title": "4️⃣ تسريب الغاز", "icon": "gas.png", "tips": ["افتح كل النوافذ والأبواب لتهوية المكان.", "أطفئ أي مصادر شرارة أو لهب.", "لا تستخدم الأجهزة الكهربائية أو الهواتف داخل المكان.", "أخرج الجميع من المكان فورًا.", "اتصل بالطوارئ أو خدمة الغاز قبل العودة."]},
        {"title": "5️⃣ قفلة الكهرباء", "icon": "electric.png", "tips": ["افصل الكهرباء عن المصبر الرئيسي فورًا.", "لا تحاول لمس أي شخص تعرض لصعقة كهربائية قبل فصل الكهرباء.", "إذا كان هناك حريق صغير، استخدم طفاية مناسبة (مثل ثاني أكسيد الكربون).", "ابتعد عن المياه أثناء التعامل مع الكهرباء.", "اتصل بالفني المتخصص لإعادة التيار بأمان."]},
        {"title": "6️⃣ جروح اليد (بسيطة وعميقة)", "icon": "finger_cut.png", "tips": ["اغسل يديك جيدًا قبل لمس الجرح لتجنب العدوى.", "اشطف الجرح مباشرة بالماء النظيف لإزالة الأوساخ والشوائب.", "إذا كان النزيف شديدًا، اضغط مباشرة على الجرح بشاش نظيف.", "غطِّ الجرح بضمادة معقمة أو شاش نظيف.", "إذا كان الجرح عميقًا، يحتوي على شوائب، أو استمر النزيف، توجه للطبيب فورًا."]},
        {"title": "7️⃣ عدم توازن الضغط", "icon": "blood_pressure.png", "tips": ["اجعل الشخص جالسًا أو مستلقيًا براحة.", "شرب الماء لتجنب الجفاف.", "تجنب الوقوف المفاجئ.", "إذا كان هناك دوار شديد، حاول رفع القدمين قليلًا.", "راقب أي أعراض خطيرة مثل فقدان وعي أو غثيان شديد، واتصل بالطبيب."]},
        {"title": "8️⃣ إغماء مرضي السكري", "icon": "diabetes.png", "tips": ["أعطِ المصاب سكريات سريعة (مثل عصير أو حلوى).", "ضع الشخص مستلقيًا على جانبه إذا كان فاقد الوعي.", "راقب التنفس والنبض باستمرار.", "لا تعطي أدوية عن طريق الفم إذا لم يكن مستيقظًا.", "اتصل بالإسعاف إذا لم يتحسن خلال دقائق."]},
        {"title": "9️⃣ ارتفاع درجة حرارة الأطفال", "icon": "child_fever.png", "tips": ["استخدم كمادات ماء فاتر على الجبين والإبطين.", "أعطِ الطفل سوائل بانتظام لتجنب الجفاف.", "أزل الملابس الزائدة.", "راقب درجة الحرارة باستمرار.", "استشر الطبيب فورًا إذا تجاوزت الحرارة 39 درجة مئوية أو ظهرت أعراض خطيرة."]},
        {"title": "🔟 الانبطاح القوي (السقوط)", "icon": "fall.png", "tips": ["ابق الشخص مستلقيًا ولا تحركه إلا للضرورة.", "تحقق من وعيه وتنفسه ونبضه.", "إذا كان هناك نزيف، اضغط عليه بشاش نظيف.", "اتصل بالإسعاف فورًا إذا ظهرت كدمات كبيرة، تشنجات، فقدان وعي أو صعوبة في التنفس."]}
    ],
    "EN": [
        {"title": "1️⃣ Fainting Cases", "icon": "fainting.png", "tips": ["Lay the person on their back with their legs slightly elevated.", "Check if they are conscious and breathing.", "Open windows to provide fresh air.", "Loosen any tight clothing around the neck and chest.", "Call ambulance if they don't wake up in a minute."]},
        {"title": "2️⃣ Fire Burns", "icon": "burns.png", "tips": ["Move the person away from fire immediately.", "Cool with lukewarm water for 10-20 mins.", "Do not pop blisters or use toothpaste.", "Cover with clean sterile gauze.", "Call emergency for deep or large burns."]},
        {"title": "3️⃣ Heart Attacks", "icon": "heart_attack.png", "tips": ["Keep the person sitting or semi-sitting comfortably.", "Call emergency services immediately.", "No movement or physical effort.", "Give aspirin if available (and no allergy).", "Monitor pulse and prepare for CPR."]},
        {"title": "4️⃣ Gas Leak", "icon": "gas.png", "tips": ["Open all windows and doors for ventilation.", "Extinguish all sparks or flames.", "Do not use electrical devices or phones inside.", "Evacuate everyone immediately.", "Call gas emergency before returning."]},
        {"title": "5️⃣ Electric Shock", "icon": "electric.png", "tips": ["Cut off power from main source immediately.", "Do not touch the victim before power is off.", "Use suitable extinguisher (CO2) for fires.", "Stay away from water.", "Call a professional technician."]},
        {"title": "6️⃣ Hand Wounds", "icon": "finger_cut.png", "tips": ["Wash hands before touching the wound.", "Rinse directly with clean water.", "Apply direct pressure with gauze for bleeding.", "Cover with a sterile bandage.", "Seek doctor for deep or infected wounds."]},
        {"title": "7️⃣ Pressure Imbalance", "icon": "blood_pressure.png", "tips": ["Let the person sit or lie down comfortably.", "Drink water to avoid dehydration.", "Avoid sudden movements.", "Elevate feet slightly if dizzy.", "Monitor for loss of consciousness."]},
        {"title": "8️⃣ Diabetic Coma", "icon": "diabetes.png", "tips": ["Give fast-acting sugar if conscious.", "Lay on their side if unconscious.", "Monitor breathing and pulse.", "No oral medicine if unconscious.", "Call ambulance if no improvement."]},
        {"title": "9️⃣ Child Fever", "icon": "child_fever.png", "tips": ["Use lukewarm compresses (forehead/armpits).", "Give regular fluids.", "Remove extra clothing.", "Monitor temperature constantly.", "Consult doctor if temp exceeds 39°C."]},
        {"title": "🔟 Strong Falls", "icon": "fall.png", "tips": ["Keep lying down; do not move them.", "Check consciousness and pulse.", "Apply pressure to any bleeding.", "Call ambulance for seizures or breathing issues."]}
    ]
}

LEX = {
    "AR": {
        "nav": ["الرئيسية", "الإسعافات", "الذكاء الاصطناعي", "الإعدادات", "عن البرنامج", "🌐 EN"],
        "sos_h": "🚨 نجدة الطوارئ السريعة", "radar_h": "🏥 الرادار الطبي",
        "p": "الشرطة", "a": "الإسعاف", "f": "المطافئ", "g": "الغاز",
        "hosp": "أقرب مستشفى", "pharm": "أقرب صيدلية", "lab": "أقرب معمل", "save_btn": "حفظ الإعدادات",
        "ai_label": "صف حالة الطوارئ للحصول على مساعدة ذكية:",
        "ai_btn": "استشارة المسعف الذكي ⚡", "sub_name": "نبض الأمان",
        "locks_h": "🛡️ أنظمة الحماية الرقمية", "l_theft": "قفل السرقة", "l_app": "قفل التطبيق",
        "neon_label": "تفعيل تأثير النيون ⚡",
        "login_h": "🔐 بوابة الدخول الآمن", "login_pass": "كلمة المرور", "login_user": "اسم المستخدم", "login_btn": "دخول",
        "setup_h": "✨ إنشاء حساب جديد وقفل البيانات", "logout": "تسجيل الخروج",
        "welcome": "مرحباً بك،"
    },
    "EN": {
        "nav": ["Home", "First Aid", "AI Medic", "Settings", "About", "🌐 AR"],
        "sos_h": "🚨 Emergency SOS", "radar_h": "🏥 Medical Radar",
        "p": "Police", "a": "Ambulance", "f": "Fire", "g": "Gas",
        "hosp": "Hospital", "pharm": "Pharmacy", "lab": "Medical Lab", "save_btn": "Save Settings",
        "ai_label": "Describe the emergency for AI help:",
        "ai_btn": "Consult AI Medic ⚡", "sub_name": "Safe Pulse PRO",
        "locks_h": "🛡️ Digital Security Systems", "l_theft": "Theft Lock", "l_app": "App Lock",
        "neon_label": "Enable Neon Mode ⚡",
        "login_h": "🔐 Secure Access Portal", "login_pass": "Password", "login_user": "Username", "login_btn": "Login",
        "setup_h": "✨ Create & Encrypt Account", "logout": "Logout",
        "welcome": "Welcome,"
    }
}

L = LEX[st.session_state.lang]

# --- 6. التصميم و CSS ---
font_base64 = get_64("assets/myfont.ttf")
font_face = f"@font-face {{ font-family: 'CustomFont'; src: url(data:font/ttf;base64,{font_base64}) format('truetype'); }} * {{ font-family: 'CustomFont', sans-serif !important; }}" if font_base64 else "@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap'); * { font-family: 'Cairo', sans-serif !important; }"

BLUE = "#00d4ff"; GREEN_NEON = "#25D366"
GLOW = f"0 0 20px {BLUE}" if vault.get('neon', True) else "none"
GLOW_GREEN = f"0 0 20px {GREEN_NEON}" if vault.get('neon', True) else "none"
DIR = "rtl" if st.session_state.lang == "AR" else "ltr"
background = "#0d1117"

# --- 6. التصميم و CSS المحدث ---
st.markdown(f"""
<style>
    {font_face}
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #010409; color: white; direction: {DIR}; }}
    
    /* تعديل الأزرار لتكون أكبر وتستوعب النص بشكل أفضل */
    .stButton>button {{ 
        background: #0d1117 !important; 
        border: 2px solid {BLUE} !important; 
        color: white !important; 
        border-radius: 12px; 
        
        /* زيادة الارتفاع والمسافات */
        height: 65px !important;  /* تم زيادة الارتفاع من 50 إلى 65 */
        padding: 10px 5px !important; 
        
        box-shadow: {GLOW}; 
        transition: 0.4s; 
        width: 120%; 
        
        /* ضبط الخط ليتناسب مع حجم الزر الجديد */
        font-size: 20px !important; 
        font-weight: bold !important;
        line-height: 1.2 !important; /* لضمان توسط الكلام عمودياً */
        overflow: hidden; /* لمنع خروج النص */
    }}

    .stButton>button:hover {{
        transform: scale(1.02);
        box-shadow: 0 0 30px {BLUE};
    }}

    /* بقية التنسيقات كما هي */
    .neon-card {{ background: #0d1117; border: 2px solid {BLUE}; border-radius: 15px; padding: 20px 10px; margin-bottom: 12px; text-align: center; box-shadow: {GLOW}; line-height: 1.6; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
    .neon-card-green {{ background: #0d1117; border: 2px solid {GREEN_NEON}; border-radius: 15px; padding: 20px 10px; margin-bottom: 12px; text-align: center; box-shadow: {GLOW_GREEN}; line-height: 1.6; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
    header {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# --- 7. واجهة تسجيل الدخول ---

if not st.session_state.authenticated:
    # --- 1. قسم التنسيق (Neon Style) ---
    st.markdown(f"""
    <style>
        div[data-testid="stTextInput"] input {{
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 2px solid #00d4ff !important;
            border-radius: 10px !important;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.3) !important;
        }}
        div.stButton > button {{
            background-color: #000000 !important;
            color: #00d4ff !important;
            border: 2px solid #00d4ff !important;
            border-radius: 20px !important;
            text-shadow: 0 0 5px #00d4ff !important;
            box-shadow: 0 0 10px #00d4ff !important;
            width: 100%;
        }}
        .footer-signature {{
            text-align: center;
            color: #00d4ff;
            font-weight: bold;
            text-shadow: 0 0 5px #00d4ff;
            padding: 20px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # --- 2. اللوجو والترحيب ---
    logo_data = get_64("assets/icons/icon.png")
    st.markdown(f"""
        <div style="text-align:center; padding-top:30px;">
            <img src="data:image/png;base64,{logo_data}" style="width:180px;">
            <h1 style="color:#00d4ff; font-size:2.8rem; text-shadow:0 0 10px #00d4ff;">Safe Pulse PRO</h1>
            <h2 style="color:white; font-size:2.8rem; text-shadow:0 0 6px white;">نبض الآمان</h2>
            <h3 style="color:white; text-shadow: 0 0 10px #00d4ff;">مرحباً بك</h3>
            <p style="color:#e6edf3; opacity:0.9;">أمانك الطبي، حمايتك من السرقة، والاستغاثة.. في مكان واحد</p>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_setup = st.tabs(["🔐 تسجيل الدخول", "✨ إنشاء حساب جديد"])
    
    with tab_login:
        in_user = st.text_input("اسم المستخدم", key="l_user")
        in_pass = st.text_input("كلمة المرور", type="password", key="l_pass")
        
        if st.button("تسجيل الدخول"):
            reg = get_registry()
            if in_user in reg:
                stored_encrypted = reg[in_user].encode('utf-8')
                try:
                    # فك تشفير كلمة المرور بواسطة Fernet
                    decrypted_pass = cipher.decrypt(stored_encrypted).decode('utf-8')
                    if in_pass == decrypted_pass:
                        token = create_session(in_user)
                        st.session_state.current_user = in_user
                        st.session_state.secure_vault = load_user_data(in_user) or get_user_defaults(in_user)
                        st.session_state.authenticated = True
                        st.session_state.page = "HOME"
                        streamlit_js_eval(js_expressions=f"localStorage.setItem('sp_token', '{token}')")
                        st.rerun()
                    else:
                        st.error("❌ كلمة المرور غير صحيحة")
                except Exception as e:
                    st.error("⚠️ خطأ في تشفير الحساب القديم أو فك التشفير. يرجى مسح ملف registry وإنشاء حساب جديد.")
            else:
                st.error("❌ المستخدم غير موجود")

    with tab_setup:
        st.subheader(L["setup_h"])
        new_user = st.text_input(L["login_user"], key="s_user")
        new_pass = st.text_input(L["login_pass"], type="password", key="s_pass")
        confirm_pass = st.text_input("تأكيد كلمة المرور", type="password", key="s_pass_conf")
        
        if st.button("إنشاء الحساب وتشفير المحفظة"):
            if not new_user or not new_pass:
                st.error("يرجى ملء كافة البيانات")
            elif new_pass != confirm_pass:
                st.error("كلمات المرور غير متطابقة")
            elif new_user in get_registry():
                st.error("اسم المستخدم موجود مسبقاً")
            else:
                with st.spinner("جاري إنشاء الحساب وتشفير البيانات..."):
                    # 1. حفظ في الريجستري المحلي (مشفراً)
                    save_to_registry(new_user, new_pass)
                    # 2. إنشاء بيانات افتراضية وحفظها في Firestore
                    default_data = get_user_defaults(new_user)
                    save_user_data(new_user, default_data)
                    st.success("✨ تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")

    st.markdown('<div class="footer-signature">Ayman Dev</div>', unsafe_allow_html=True)
    st.stop()

# --- 8. محتوى البرنامج (بعد الدخول) ---

# --- 1. عرض اللوجو والعناوين (المدمج) ---
logo_data = get_64("assets/icons/icon.png")

# دمج اللوجو مع النص الإنجليزي (أزرق) والنص العربي (أبيض) في بلوك واحد
st.markdown(f"""
    <div style="text-align:center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{logo_data}" style="width:110px; filter:drop-shadow({GLOW});">
        <h2 style="color:{BLUE}; text-shadow:{GLOW}; font-size:2rem; margin-bottom: 0px;">
            Safe Pulse PRO
        </h2>
        <h2 style="color:white; font-size:2.2rem; text-shadow:0 0 6px white; margin-top: -8px;">
            نبض الآمان
        </h2>
    </div>
""", unsafe_allow_html=True)

# --- 2. شريط التنقل (Navigation Bar) ---
nav_keys = ["HOME", "AID", "AI", "SET", "ABOUT", "LANG"]
n_cols = st.columns(len(L["nav"]) + 1)

for idx, label in enumerate(L["nav"]):
    if n_cols[idx].button(label, key=f"nav_{idx}"):
        if nav_keys[idx] == "LANG":
            st.session_state.lang = "EN" if st.session_state.lang == "AR" else "AR"
            vault["lang"] = st.session_state.lang
            save_user_data(st.session_state.current_user, vault)
            st.rerun()
        else:
            st.session_state.page = nav_keys[idx]
            st.rerun()

# زر تسجيل الخروج
if n_cols[-1].button(L["logout"], key="logout_final_btn"):
    st.session_state.authenticated = False
    st.session_state.current_user = ""
    try:
        streamlit_js_eval(js_expressions="localStorage.removeItem('sp_token')")
    except:
        pass
    st.rerun()

st.divider()
page = st.session_state.page

if page == "HOME":
    st.markdown(f"""
        <style>
            @keyframes logo_pulse {{
                0% {{ transform: scale(1); filter: drop-shadow(0 0 10px {BLUE}); }}
                50% {{ transform: scale(1.1); filter: drop-shadow(0 0 30px {BLUE}) brightness(1.2); }}
                100% {{ transform: scale(1); filter: drop-shadow(0 0 10px {BLUE}); }}
            }}
            .main-logo-pulse {{
                animation: logo_pulse 3s infinite ease-in-out;
                display: block;
                margin: auto;
                width: 150px;
                margin-bottom: 30px;
            }}
            @keyframes slide_up {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            div.stButton > button {{
                width: 120% !important;
                height: 60px !important;
                font-size: 25px !important;
                font-weight: bold !important;
                border-radius: 15px !important;
                animation: slide_up 0.6s ease-out forwards;
                transition: 0.3s all ease-in-out !important;
            }}
            .neon-card, .neon-card-green {{
                animation: slide_up 0.6s ease-out forwards;
                padding: 10px !important;
                min-height: 30px !important;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 25px !important;
                text-align: center;
                border-radius: 30px !important;
                transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                cursor: pointer;
                margin-bottom: 15px;
            }}
            .neon-card:hover, .neon-card-green:hover, div.stButton > button:hover {{
                transform: scale(1.05) !important;
                box-shadow: 0 0 40px {BLUE} !important;
                filter: brightness(1.2);
            }}
        </style>
    """, unsafe_allow_html=True)

# عرض اللوجو
    img_logo = get_64("assets/icons/icon.png")
    if img_logo:
        st.markdown(f'<img src="data:image/png;base64,{img_logo}" class="main-logo-pulse">', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center; font-size:50px;" class="main-logo-pulse">🛡️</div>', unsafe_allow_html=True)

    # عرض نص الترحيب مع تلوين اسم المستخدم باللون اللبني (BLUE)
    # ملاحظة: تأكد أن متغير BLUE معرف لديك مسبقاً بقيمة مثل "#00D4FF"
    st.markdown(f"""
        <div class="welcome-text" style="text-align:center;">
            {L["welcome"]} 
            <span class="neon-user" style="color:{BLUE}; font-weight:bold; text-shadow: 0 0 10px {BLUE}44;">
                {st.session_state.current_user}
            </span>
        </div>
    """, unsafe_allow_html=True)
    c_chat, c_neon = st.columns([1, 1])
    with c_chat:
        if st.button("💬 شاتك الشخصي"): 
            st.session_state.page = "CHAT"
            st.rerun()
    with c_neon:
        neon_check = st.toggle(L["neon_label"], value=vault.get("neon", False))
        if neon_check != vault.get("neon"):
            vault["neon"] = neon_check
            save_user_data(st.session_state.current_user, vault)
            st.rerun()
    
    st.subheader(L["locks_h"])
    l1, l2 = st.columns(2)
    with l1: vault["theft_on"] = st.toggle(L["l_theft"], value=vault.get("theft_on", True))
    with l2: vault["app_lock"] = st.toggle(L["l_app"], value=vault.get("app_lock", False))
    
    loc = get_geolocation()
    lat_lon = f"{loc['coords']['latitude']},{loc['coords']['longitude']}" if loc and 'coords' in loc else "0,0"
    loc_link = f"https://www.google.com/maps?q={lat_lon}"
    encoded_msg = f"🚨 SOS! My Location: {loc_link}"
    
    f_col, m_col = st.columns(2)
    with f_col: 
        st.markdown(f'''
            <a href="https://wa.me/{vault.get("fav_person_1_phone")}?text={encoded_msg}" target="_blank" style="text-decoration:none;">
                <div class="neon-card-green" style="border:2px solid #25D366; padding:20px; border-radius:15px; text-align:center; color:#25D366;">
                    <span style="font-size:25px;">🟢</span><br>واتساب {vault.get("fav_person_1_name")}
                </div>
            </a>''', unsafe_allow_html=True)
    with m_col: 
        st.markdown(f'''
            <a href="https://wa.me/{vault.get("fav_person_2_phone")}?text={encoded_msg}" target="_blank" style="text-decoration:none;">
                <div class="neon-card-green" style="border:2px solid #25D366; padding:20px; border-radius:15px; text-align:center; color:#25D366;">
                    <span style="font-size:25px;">🟢</span><br>واتساب {vault.get("fav_person_2_name")}
                </div>
            </a>''', unsafe_allow_html=True)
    
    st.subheader(L["radar_h"])
    r1, r2, r3 = st.columns(3)
    with r1: st.markdown(f'<a href="https://www.google.com/maps/search/hospital" target="_blank" style="text-decoration:none;"><div class="neon-card">🏥<br>{L["hosp"]}</div></a>', unsafe_allow_html=True)
    with r2: st.markdown(f'<a href="https://www.google.com/maps/search/pharmacy" target="_blank" style="text-decoration:none;"><div class="neon-card">💊<br>{L["pharm"]}</div></a>', unsafe_allow_html=True)
    with r3: st.markdown(f'<a href="https://www.google.com/maps/search/medical+lab" target="_blank" style="text-decoration:none;"><div class="neon-card">🔬<br>{L["lab"]}</div></a>', unsafe_allow_html=True)

    st.subheader(L["sos_h"])
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.markdown(f'<a href="tel:122" style="text-decoration:none;"><div class="neon-card">🚓<br>{L["p"]}</div></a>', unsafe_allow_html=True)
    with s2: st.markdown(f'<a href="tel:123" style="text-decoration:none;"><div class="neon-card" style="border-color:#ff4b4b; color:#ff4b4b;">🚑<br>{L["a"]}</div></a>', unsafe_allow_html=True)
    with s3: st.markdown(f'<a href="tel:180" style="text-decoration:none;"><div class="neon-card">🚒<br>{L["f"]}</div></a>', unsafe_allow_html=True)
    with s4: st.markdown(f'<a href="tel:129" style="text-decoration:none;"><div class="neon-card">🔥<br>{L["g"]}</div></a>', unsafe_allow_html=True)

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

if st.session_state.page == "AI":
    st.markdown(f"""
    <style>
        div[data-testid="stTextArea"] textarea {{
            background-color: #1c1f26 !important;
            color: #ffffff !important;
            border: 2px solid #000000 !important;
            border-radius: 15px !important;
            padding: 15px !important;
            box-shadow: 0 0 10px #000000, 0 0 5px #00d4ff !important; 
            transition: 0.4s all ease-in-out;
        }}
        div[data-testid="stTextArea"] textarea:focus {{
            border-color: #00d4ff !important;
            box-shadow: 0 0 20px #00d4ff !important;
            outline: none !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<h1 style="text-align:center; color:#00d4ff; text-shadow:0 0 10px #00d4ff;">الذكاء الاصطناعي 🤖</h1>', unsafe_allow_html=True)
    
    u_input_final = st.text_area(L["ai_label"], height=150, key="fixed_neon_ai_input") 
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button(L["ai_btn"], key="fixed_neon_ai_button"):
            if u_input_final:
                with st.spinner("جاري استشارة المسعف الذكي..."):
                    result = get_ai_response(u_input_final)
                    st.session_state.ai_result = result
            else:
                st.warning("يرجى كتابة سؤالك أولاً.")
    
    with col2:
        if st.button("مسح 🗑️", key="clear_ai_fixed"):
            st.session_state.ai_result = None
            st.rerun()

    if st.session_state.ai_result:
        st.markdown(f"""
        <div class="ai-neon-card">
            <div style="color:#00d4ff; font-weight:bold; margin-bottom:10px;">🤖 المسعف الذكي:</div>
            <div style="color:white; line-height:1.7;">{st.session_state.ai_result}</div>
        </div>
        """, unsafe_allow_html=True)

elif page == "AID":
    lang = st.session_state.lang
    title_text = "🚑 الإسعافات الأولية" if lang == "AR" else "🚑 First Aid Guide"
    st.markdown(f"<h1 style='text-align:center; color:{BLUE}; text-shadow: 0 0 15px {BLUE};'>{title_text}</h1>", unsafe_allow_html=True)
    
    content = AID_CONTENT.get(lang, AID_CONTENT["AR"])

    st.markdown(f"""
        <style>
            .aid-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 25px;
                padding: 20px;
            }}
            .neon-aid-card {{
                background: rgba(13, 17, 23, 0.95);
                border: 2px solid {BLUE};
                border-radius: 20px;
                padding: 20px;
                transition: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                height: 100%;
                box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
                display: flex;
                flex-direction: column;
                align-items: center;
                position: relative;
                overflow: hidden;
            }}
            .neon-aid-card:hover {{
                transform: scale(1.05) translateY(-5px);
                box-shadow: 0 0 35px rgba(0, 212, 255, 0.4);
                background: rgba(0, 212, 255, 0.05);
                border-color: #00f2ff;
            }}
            .aid-img-frame {{
                width: 100%;
                height: 180px;
                background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, rgba(0, 0, 0, 0) 70%);
                border-radius: 15px;
                margin-bottom: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .aid-img-frame img {{
                max-width: 85%;
                max-height: 85%;
                object-fit: contain;
                filter: drop-shadow(0 0 10px {BLUE}) brightness(1.2);
            }}
            .aid-header {{
                color: {BLUE};
                font-size: 1.4rem;
                font-weight: bold;
                margin-bottom: 15px;
                padding-bottom: 12px;
                width: 100%;
                text-align: center;
                border-bottom: 1px solid rgba(0, 212, 255, 0.3);
                text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
            }}
            .tips-container {{
                width: 100%;
                text-align: right;
                direction: {'rtl' if lang == 'AR' else 'ltr'};
            }}
            .tip-item {{
                color: #e6edf3;
                font-size: 1rem;
                margin-bottom: 10px;
                line-height: 1.6;
                padding-right: 15px;
                position: relative;
            }}
            .tip-item::before {{
                content: "•";
                color: {BLUE};
                position: absolute;
                right: 0;
                font-weight: bold;
            }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="aid-grid">', unsafe_allow_html=True)
    
    for item in content:
        icon_file = item.get('icon', 'hospital.png')
        if not icon_file.endswith('.png'):
            icon_file += '.png'
            
        img_path = f"assets/icons/{icon_file}"
        img_64 = get_64(img_path)
        
        tips = item.get('tips', item.get('text', []))
        tips_html = "".join([f'<div class="tip-item">{tip}</div>' for tip in (tips if isinstance(tips, list) else [tips])])
        
        if img_64:
            image_tag = f'<img src="data:image/png;base64,{img_64}">'
        else:
            def_img = get_64("assets/icons/hospital.png")
            image_tag = f'<img src="data:image/png;base64,{def_img}">' if def_img else '<div style="font-size:60px;">🏥</div>'

        st.markdown(f"""
            <div class="neon-aid-card">
                <div class="aid-img-frame">
                    {image_tag}
                </div>
                <div class="aid-header">{item['title']}</div>
                <div class="tips-container">
                    {tips_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "CHAT":
    # ضمان وجود سجل الرسائل في الجلسة
    if "messages" not in st.session_state:
        st.session_state.messages = st.session_state.secure_vault.get("chat_history", [])

    # تحديد اللغة الحالية بناء على إعدادات المستخدم
    current_lang = st.session_state.get("lang", "AR")

    # 1. قاعدة بيانات الاقتباسات الكاملة والمترجمة
    all_quotes = {
        "AR": [
            "فشل علاقة لا يعني فشلك كإنسان، بل يعني أن هذا الفصل من حياتك قد انتهى لتبدأ فصلاً أجمل.",
            "القلب الذي ينكسر، يلتئم ليصبح أقوى في مواجهة الخيبات القادمة.",
            "من لا يعرف قيمتك وأنت معه، سيعرفها جيداً حين يراك تمضي بدونه.",
            "لا تعتذر أبداً عن صدق مشاعرك، العيب فيمن لم يمتلك وعاءً كافياً لاحتوائها.",
            "أحياناً يكسر الله قلبك لينقذ روحك من علاقة كانت ستدمرك تماماً.",
            "الرحيل بكرامة هو انتصار عظيم لن تشعر بلذته إلا بعد حين.",
            "أنت تستحق شخصاً يحارب ليحميك، لا شخصاً تحارب أنت لتبقى في حياته.",
            "الحب لا يعني التضحية بكرامتك، فمن يحبك حقاً سيعزز كرامتك لا يهينها.",
            "لا تجعل خيبة واحدة تحول قلبك إلى حجر، فالعالم لا يزال مليئاً بالأوفياء.",
            "الوحدة أجمل بكثير من رفقة تجعلك تشعر أنك وحيد وأنت معهم.",
            "تعلم فن الاستغناء، فليس كل من دخل حياتك جاء ليبقى.",
            "النهايات هي في الحقيقة بدايات متنكرة، استعد لما هو قادم.",
            "لا تبكِ على من باعك، بل اشكر الله لأنه كشف لك الحقيقة قبل فوات الأوان.",
            "قيمتك لا يحددها رأي شخص فيك، بل يحددها تقديرك أنت لنفسك.",
            "الشفاء من علاقة سامة يبدأ بقرارك أنك لن تعود ضحية مرة أخرى.",
            "أعطِ نفسك وقتاً للحداد على ما مضى، ثم انهض كأنك لم تسقط أبداً.",
            "القلب الذي يمنح الفرص كثيراً، يرحل مرة واحدة دون عودة.",
            "أنت لست خياراً ثانياً لأحد، إما أن تكون الأول أو لا تكون.",
            "الخروج من علاقة مؤذية هو ولادة جديدة لروحك.",
            "لا تندم على معروف قدمته، فالنوايا الطيبة لا تضيع عند الله.",
            "النسيان ليس نسيان الأحداث، بل نسيان الشعور الذي خلفته تلك الأحداث.",
            "أحياناً نحتاج لفقدان أحدهم لكي نجد أنفسنا الضائعة.",
            "الحياة قصيرة جداً لتقضيها في انتظار من لا ينتظرك.",
            "كن كالنور، من أرادك سيسعى إليك، ومن فقدك سيعيش في الظلام.",
            "الحب الحقيقي يبني ولا يهدم، يرمم ولا يكسر.",
            "لا تقارن بدايتك بنهاية غيرك، لكل شخص مسار وقصة مختلفة.",
            "الثقة التي تُكسر لا تُرمم، لكنها تعلمك كيف تختار بعناية في المرة القادمة.",
            "سامح لترتاح أنت، وليس لأنهم يستحقون السماح.",
            "الكرامة هي الخط الأحمر الذي لا يجب أن يتخطاه أي حب في العالم.",
            "لا تستجدي الاهتمام، فالأشياء الجميلة تُمنح ولا تُطلب.",
            "من يحبك سيهتم بكسرك، ومن يهواك سيزيدك انكساراً.",
            "القوة ليست في عدم السقوط، بل في النهوض بعد كل سقطة.",
            "اكتفِ بنفسك، فالاعتماد العاطفي هو سجن لروحك.",
            "الحياة ستستمر بك أو بدونهم، فاختر أن تستمر وأنت شامخ.",
            "كل وجع مررت به هو درس صامت يجعلك أكثر حكمة.",
            "ضعف جسدك اليوم هو نداء لروحك لترتاح، فلا تقسُ على نفسك.",
            "المرض ليس نهاية الطريق، بل هو محطة لتتعلم الامتنان لأبسط النعم.",
            "صحتك هي استثمارك الأغلى، لا بأس أن تتوقف قليلاً لترمم جسدك.",
            "كل ألم تشعر به الآن هو زكاة لجسدك، ورفعة لدرجاتك.",
            "القوة النفسية قادرة على هزيمة أعتى الأمراض الجسدية.",
            "لا تحزن على عجز مؤقت، فالقمر يمر بمراحل المحاق قبل أن يكتمل نوراً.",
            "جسدك يحتاج لصبرك كما يحتاج للدواء، كن رحيماً به.",
            "الإرادة هي نصف العلاج، والتفاؤل هو النصف الآخر.",
            "الصحة تاج لا يراه إلا من مر بلحظات الضعف، حافظ على تاجك.",
            "أنت قوي بما يكفي لتجاوز هذه الوعكة، غداً ستكون ذكرى.",
            "التعافي رحلة وليس سباقاً، خذ وقتك بالكامل.",
            "لا تسمح للمرض أن يسرق بريق عينيك، الأمل دواء لا يُباع في الصيدليات.",
            "حتى في ذروة تعبك، تذكر أن هناك من ينتظر نهوضك بفارغ الصبر.",
            "جسدك هو منزلك الوحيد، اعتنِ به بالحب والهدوء.",
            "المرض يختبر معادن الناس من حولك، ويصقل معدنك أنت.",
            "كل يوم تشرق فيه الشمس هو فرصة جديدة لتعافي أفضل.",
            "لا تقلق، فالذي خلق الداء خلق الدواء، والثقة بالله هي الشفاء.",
            "استمتع بلحظات الهدوء، فالسكينة هي بيئة التعافي المثالية.",
            "أنت لست تشخيصاً طبياً، أنت روح عظيمة تقاوم ببطولة.",
            "الصبر على الألم هو أعلى مراتب الشجاعة.",
            "اعتبر فترة مرضك خلوة مع الله وإعادة ترتيب لأولوياتك.",
            "ابتسامتك في وجه الألم هي نصف الانتصار عليه.",
            "لا تنظر إلى ما فقدت صحياً، انظر إلى القوة التي اكتسبتها داخلياً.",
            "الغد يحمل لك صحة أفضل وصباحاً أجمل، كن مؤمناً بذلك.",
            "حتى الشجر يسقط ورقه ليعود مخضراً من جديد، وكذلك أنت.",
            "الضعف الجسدي ليس عيباً، بل هو طبيعة البشر، القوة هي في روحك.",
            "كل جرعة دواء هي خطوة نحو العافية، وكل دعاء هو تقصير للمسافة.",
            "كن ممتناً لكل خلية في جسدك تعمل الآن لأجلك.",
            "لا تيأس، فالمعجزات تحدث لأولئك الذين لا يتوقفون عن المحاولة.",
            "راحتك النفسية هي المحرك الأول لتعافي جسدك.",
            "اجعل من ألمك وقوداً لإبداعك، فالكثير من العظماء خرجوا من رحم الوجع.",
            "نفسك تستحق منك الدلال والاهتمام، خاصة في أوقات الضعف.",
            "تذكر أن الشدة لا تدوم، والعافية قادمة كفلق الصبح.",
            "أنت محارب، والمحاربون لا يستسلمون من المعركة الأولى.",
            "جسدك سيشكرك يوماً ما لأنك لم تستسلم في هذه اللحظة.",
            "عوض الله لا يأتي عادياً، بل يأتي ليُنسيك مرارة كل ما فقدت.",
            "ما ذهب منك لم يكن لك من البداية، وما هو لك لن يذهب لغيرك.",
            "الفقد موجع، لكنه يفتح في روحك مساحات لن يملأها إلا الله.",
            "عندما يأخذ الله منك شيئاً، فإنه يهيئ يديك لاستقبال شيء أعظم.",
            "الجبر قادم، وبطريقة لم تخطر على بالك أبداً.",
            "لا تبكِ على أطلال الماضي، فالمستقبل يبني لك قصوراً من العوض.",
            "خسارة الأشياء المادية هي أرخص أنواع الخسائر، طالما روحك بخير.",
            "أحياناً يرحل الجميل ليأتي الأجمل، ثق في تدبير الخالق.",
            "كل باب أُغلق في وجهك كان يحميك من شر لا تراه.",
            "الفقد يعلمنا قيمة اللحظة، والتعويض يعلمنا قيمة الصبر.",
            "سيعوضك الله حتى تظن أنك لم تحزن يوماً.",
            "الصبر على الفقد هو عبادة صامتة أجرها بغير حساب.",
            "الغياب ليس دائماً خسارة، أحياناً يكون نجاة.",
            "من فقد غاليًا، سيرزقه الله أنيساً يملأ قلبه طمأنينة.",
            "الحياة دولاب، اليوم فقد وغداً وجد، والرضا هو المكسب الحقيقي.",
            "لا تحزن على ما فات، فلو كان خيراً لبقي.",
            "العوض الحقيقي هو أن يرزقك الله راحة البال بعد شتات الروح.",
            "الفقد يكسرنا، لكن جبر الله يعيد تشكيلنا لنصبح أجمل.",
            "سيمسح الله على قلبك بلطفه حتى تبتسم رغماً عن كل شيء.",
            "كل دمعة سقطت منك في الخفاء، لها عوض كبير في العلن.",
            "استبشر خيراً، فالأقدار تخبئ لك ما يقر عينك.",
            "الفراغ الذي تركه الراحلون، سيملؤه الله بنور السكينة.",
            "لست وحدك، فالله معك في كل لحظة انكسار وفقد.",
            "العوض ليس دائماً شخصاً آخر، قد يكون سلاماً داخلياً لا يُقدّر بثمن.",
            "ما كان لك سيأتيك على ضعفك، وما ليس لك لن تناله بقوتك.",
            "أنت تسير في رعاية الله، فلا تخف من ضياع شيء.",
            "جبر القلوب من شيم العظماء، والله هو أعظم الجابرين.",
            "ابتسم، فعوض الله مدهش لدرجة تفوق الخيال.",
            "نهاية القصة دائماً سعيدة، إذا لم تكن سعيدة فهي ليست النهاية بعد.",
            "Safe Pulse PRO يذكرك دائماً: أنت تستحق الأفضل، والتعافي يبدأ من الداخل."
        ],
        "EN": [
            "A relationship failure does not define you as a human; it simply means this chapter has ended for a better one to begin.",
            "A broken heart heals to become much stronger in the face of all future disappointments.",
            "Those who do not recognize your value while you are present will certainly realize it once they see you moving on.",
            "Never feel the need to apologize for the sincerity of your feelings; the fault lies with those who could not contain them.",
            "Sometimes life breaks your heart just to save your soul from a relationship that would have eventually destroyed you.",
            "Walking away with your dignity intact is a magnificent victory that you will only truly appreciate after some time.",
            "You deserve a partner who fights to protect you, not someone you constantly have to fight for just to remain in their life.",
            "True love never requires you to sacrifice your dignity; those who truly love you will always cherish and uphold it.",
            "Do not allow a single disappointment to turn your heart into stone; the world is still filled with many loyal souls.",
            "Loneliness is far more beautiful than being in the company of people who make you feel completely alone.",
            "Master the art of letting go, because not everyone who enters your life is meant to stay forever.",
            "Endings are actually beautiful beginnings in disguise; keep yourself ready for the wonderful things that are coming.",
            "Do not cry over someone who abandoned you; instead, thank life for revealing the truth before it was too late.",
            "Your worth is never determined by someone else’s opinion of you; it is defined solely by how much you value yourself.",
            "Healing from a toxic relationship truly begins at the moment you decide you will never be a victim again.",
            "Give yourself the necessary time to grieve what has passed, then stand up as if you have never fallen before.",
            "The heart that gives too many chances eventually leaves once and for all without ever looking back.",
            "You are never a second choice for anyone; you should either be the first priority or not exist in their life at all.",
            "Escaping an abusive or harmful relationship is nothing less than a brand new birth for your weary soul.",
            "Never regret any kindness you have shown; good intentions are never lost in the eyes of the universe.",
            "Forgetting is not about erasing events from memory, but rather about losing the painful feeling those events left behind.",
            "Sometimes we honestly need to lose someone else in order to finally find our own lost selves.",
            "Life is far too short to spend it waiting for someone who is not waiting for you in return.",
            "Be like the light; those who want you will find their way to you, and those who lose you will remain in darkness.",
            "Real love is meant to build you up, not tear you down; it is meant to repair you, not break you.",
            "Never compare your beginning to someone else's end; every person has their own unique path and story.",
            "Trust that has been broken can never be fully restored, but it teaches you how to choose much more carefully next time.",
            "Forgive others so that you can find your own peace, not necessarily because they deserve to be forgiven.",
            "Dignity is the ultimate red line that no love in this world should ever be allowed to cross.",
            "Do not beg for someone’s attention; the most beautiful things in life are given freely and never requested.",
            "Someone who truly loves you will care about your pain; someone who only desires you will only add to your brokenness.",
            "Strength is not the absence of falling; it is the ability to rise up again after every single fall.",
            "Be enough for yourself; emotional dependency is nothing more than a prison for your free spirit.",
            "Life will continue with or without them; therefore, choose to move forward with your head held high.",
            "Every single pain you have endured is a silent lesson that makes you much wiser than you were before.",
            "The weakness of your body today is a call for your soul to rest; do not be too hard on yourself.",
            "Illness is not the end of the road; it is a station where you learn to appreciate even the simplest blessings.",
            "Your health is your most precious investment; it is perfectly fine to stop and repair your body for a while.",
            "Every bit of pain you feel right now is a purification for your body and an elevation of your status.",
            "Psychological strength is fully capable of defeating even the most difficult physical illnesses.",
            "Do not be saddened by temporary weakness; the moon goes through phases of darkness before it shines brightly.",
            "Your body needs your patience just as much as it needs medicine; be exceptionally kind and gentle with it.",
            "Willpower is half of the cure, and maintaining a positive outlook is the other half.",
            "Health is a crown that only those who have experienced weakness can see; protect your crown at all costs.",
            "You are strong enough to overcome this temporary setback; tomorrow it will be nothing more than a memory.",
            "Recovery is a long journey and not a quick race; allow yourself to take all the time you need.",
            "Do not allow illness to steal the light from your eyes; hope is a medicine that cannot be bought in any pharmacy.",
            "Even at the peak of your exhaustion, remember there are those waiting for you to rise with great anticipation.",
            "Your body is the only home you truly have; take care of it with absolute love and quiet patience.",
            "Illness tests the metal of the people around you and polishes your own character in the process.",
            "Every day the sun rises is a brand new opportunity for a much better and faster recovery.",
            "Do not worry; the one who created the disease also created the cure, and trust is the ultimate healing.",
            "Enjoy the moments of silence and calm; serenity is the perfect environment for deep recovery.",
            "You are not a medical diagnosis; you are a magnificent soul fighting with great heroism and courage.",
            "Patience in the face of physical pain is one of the highest forms of human bravery.",
            "Consider your period of illness as a private retreat and a chance to reorganize your life’s priorities.",
            "Your smile in the face of pain is already half of the victory over your physical suffering.",
            "Do not look at what you have lost health-wise; instead, look at the internal strength you have gained.",
            "Tomorrow brings with it better health and a more beautiful morning; keep your faith strong in that.",
            "Even trees lose their leaves only to return green and vibrant once again; you will do the same.",
            "Physical weakness is not a flaw; it is the nature of humans. True power resides within your soul.",
            "Every dose of medicine is a step toward wellness, and every prayer shortens the distance to health.",
            "Be truly grateful for every single cell in your body that is working hard for you right now.",
            "Never give up; miracles happen specifically for those who never stop trying and believing.",
            "Your psychological comfort is the primary engine for the physical recovery of your body.",
            "Make your pain the fuel for your creativity; many great people were born from the womb of suffering.",
            "Your self deserves pampering and care from you, especially during times of weakness.",
            "Remember that hardship never lasts forever, and wellness is coming just like the break of dawn.",
            "You are a true warrior, and warriors do not surrender simply because they lost the first battle.",
            "Your body will thank you one day because you did not give up on it during this difficult moment.",
            "God’s compensation never comes in an ordinary way; it comes to make you forget the bitterness of all you lost.",
            "What left you was never yours to begin with; and what is meant for you will never go to anyone else.",
            "Loss is painful, but it opens up spaces in your soul that only peace and faith can eventually fill.",
            "When life takes something from you, it is simply preparing your hands to receive something much greater.",
            "The mending of your heart is coming, and in a way that has never even crossed your mind.",
            "Do not cry over the ruins of the past; the future is building palaces of compensation for you.",
            "Losing material things is the cheapest kind of loss, as long as your spirit remains well and intact.",
            "Sometimes the beautiful leaves so that the most beautiful can arrive; trust in the divine plan.",
            "Every door that was closed in your face was actually protecting you from a harm you could not see.",
            "Loss teaches us the value of the moment, while compensation teaches us the true value of patience.",
            "Life will compensate you so much that you will eventually feel as if you have never been sad a day in your life.",
            "Patience during loss is a silent form of worship whose reward is beyond any human calculation.",
            "Absence is not always a loss; sometimes it is a complete and necessary rescue from harm.",
            "Whoever has lost someone dear will be granted a companion by life who fills their heart with tranquility.",
            "Life is a cycle; today there is loss and tomorrow there is gain; true contentment is the real profit.",
            "Do not be sad about what has passed; for if it had been good for you, it would have stayed.",
            "True compensation is being granted peace of mind after your soul has been through a state of scatteredness.",
            "Loss may break us, but divine mending reshapes us to become more beautiful than ever before.",
            "Kindness will wipe over your heart until you find yourself smiling despite everything that happened.",
            "Every tear that fell from you in secret has a massive compensation waiting for you in the open.",
            "Be optimistic; destiny is hiding for you exactly what will bring joy and comfort to your eyes.",
            "The void left by those who departed will be filled with the brilliant light of inner serenity.",
            "You are never alone; support is with you in every single moment of brokenness and loss.",
            "Compensation is not always another person; it could be an internal peace that is absolutely priceless.",
            "What was meant for you will reach you despite your weakness; and what was not will not be reached by your strength.",
            "You are walking under a great care; therefore, do not fear the loss of anything in this journey.",
            "Mending hearts is the quality of the great, and the ultimate mending comes from the source of life.",
            "Smile, because the coming compensation is so amazing that it will far exceed your imagination.",
            "The end of the story is always happy; if it is not happy yet, then it is simply not the end.",
            "Safe Pulse PRO always reminds you: You deserve the absolute best, and healing truly starts from within."
        ]
    }

    # 2. قاموس ترجمة نصوص الواجهة
    ui_translations = {
        "AR": {
            "title": "✨ مفكرتك الذكية",
            "manage": "### 🛠️ إدارة السجل",
            "show": "إظهار سجل المحادثات",
            "clear": "🗑️ مسح السجل نهائياً",
            "success": "تم الحذف بنجاح!",
            "support": "💖 دعم نفسي",
            "hidden": "سجل المحادثات مخفي الآن.",
            "input": "اكتب فكرة جديدة..."
        },
        "EN": {
            "title": "✨ Smart Diary",
            "manage": "### 🛠️ Manage History",
            "show": "Show Chat History",
            "clear": "🗑️ Clear History Permanently",
            "success": "Deleted successfully!",
            "support": "💖 Psychological Support",
            "hidden": "Chat history is currently hidden.",
            "input": "Write a new idea..."
        }
    }

    # جلب الترجمة المناسبة للغة المختارة
    t = ui_translations[current_lang]
    active_quotes = all_quotes[current_lang]

    # تنسيقات الواجهة (CSS) مع تطهير الرموز
    st.markdown(f"""
        <style>
            [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
            .stChatInput {{ border: 2px solid {BLUE} !important; border-radius: 25px !important; box-shadow: 0 0 15px {BLUE} !important; background: #000 !important; }}
            [data-testid="stChatMessage"] {{ background-color: rgba(0, 0, 0, 0.7) !important; border: 1px solid {BLUE} !important; box-shadow: 0 0 10px {BLUE} !important; border-radius: 15px !important; margin-bottom: 10px !important; color: white !important; }}
            div.stButton > button[key="psych_btn"] {{ background-color: #000 !important; color: #FF007F !important; border: 2px solid #FF007F !important; box-shadow: 0 0 15px #FF007F !important; border-radius: 20px !important; width: 100% !important; font-weight: bold !important; text-shadow: 0 0 5px #FF007F !important; }}
            .quote-card {{ background-color: #000; border: 2px solid #FF007F; padding: 25px; border-radius: 15px; text-align: center; color: white; text-shadow: 0 0 10px #FF007F; box-shadow: 0 0 20px #FF007F, inset 0 0 10px #FF007F; margin-bottom: 25px; font-size: 1.2rem; line-height: 1.6; }}
        </style>
    """, unsafe_allow_html=True)

    # عرض العنوان المترجم
    st.markdown(f'<h1 style="text-align:center; color:{BLUE}; text-shadow:0 0 20px {BLUE};">{t["title"]}</h1>', unsafe_allow_html=True)

    st.markdown(t["manage"])
    
    col_manage1, col_manage2 = st.columns(2)
    with col_manage1:
        show_history = st.toggle(t["show"], value=True, key="toggle_history")

    with col_manage2:
        if st.button(t["clear"], key="clear_vault_btn"):
            st.session_state.messages = []
            st.session_state.secure_vault["chat_history"] = []
            save_user_data(st.session_state.current_user, st.session_state.secure_vault)
            st.success(t["success"])
            st.rerun()

    # زر الدعم النفسي المترجم
    if st.button(t["support"], key="psych_btn"):
        import random
        selected_quote = random.choice(active_quotes)
        st.markdown(f'<div class="quote-card">{selected_quote}</div>', unsafe_allow_html=True)

    # عرض الرسائل المخزنة
    if show_history:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    else:
        st.info(t["hidden"])

    # منطقة إدخال النص المترجمة
    if prompt := st.chat_input(t["input"]):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.secure_vault["chat_history"] = st.session_state.messages
        save_user_data(st.session_state.current_user, st.session_state.secure_vault)
        st.rerun()

elif page == "SET":
    st.markdown(f"""
        <style>
            .set-container {{
                background: rgba(13, 17, 23, 0.95);
                border: 2px solid {BLUE};
                border-radius: 20px;
                padding: 35px;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
                direction: {'rtl' if st.session_state.lang == 'AR' else 'ltr'};
            }}
            .set-header {{
                color: {BLUE};
                font-weight: 800;
                text-shadow: 0 0 15px {BLUE};
                margin-bottom: 30px;
                text-align: center;
                font-size: 2.5rem;
            }}
            .info-card {{
                background: rgba(0, 212, 255, 0.05);
                border-left: 4px solid {BLUE};
                padding: 15px;
                border-radius: 10px;
                margin-top: 10px;
                border: 1px solid rgba(0, 212, 255, 0.2);
                animation: fadeIn 0.5s ease-in-out;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(-10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .stTextInput>div>div>input {{
                background-color: rgba(0, 0, 0, 0.3) !important;
                border: 1px solid {BLUE} !important;
                color: white !important;
            }}
            .stSubheader h3 {{
                color: {BLUE} !important;
                text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
            }}
        </style>
    """, unsafe_allow_html=True)

   # تأكد أن هذا السطر وما يليه يقع تحت تعريف الدالة المناسبة بنفس مستوى الإزاحة
    st.markdown(f'<div class="set-container"><h1 class="set-header">⚙️ {L["nav"][3]}</h1>', unsafe_allow_html=True)

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        st.subheader("👥 " + ("الأشخاص المفضلين" if st.session_state.lang == "AR" else "Emergency Contacts"))
        vault["fav_person_1_name"] = st.text_input("اسم الشخص المفضل (1)", vault.get("fav_person_1_name"))
        vault["fav_person_1_phone"] = st.text_input("رقم هاتف الشخص (1)", vault.get("fav_person_1_phone"))
        vault["fav_person_2_name"] = st.text_input("اسم الشخص المفضل (2)", vault.get("fav_person_2_name"))
        vault["fav_person_2_phone"] = st.text_input("رقم هاتف الشخص (2)", vault.get("fav_person_2_phone"))
        
        vault["blood"] = st.selectbox("فصيلة الدم", ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"])
        
        st.markdown("---")
        st.subheader("🛡️ " + ("أنظمة الاستغاثة الذكية" if st.session_state.lang == "AR" else "Smart Rescue Systems"))
        
        vault["anti_theft"] = st.toggle("🚨 تفعيل استغاثة السرقة", value=vault.get("anti_theft", False))
        if vault["anti_theft"]:
            st.markdown(f"""
                <div class="info-card">
                    <b style="color:{BLUE};">🔍 تعرف ماذا يفعل هذا النظام؟</b><br>
                    عند رصد حركة جري مفاجئة أو سحب الهاتف من اليد بقوة، يقوم النظام فوراً بتشفير كافة بياناتك الحساسة وإرسال إحداثيات موقعك الأخير لجهات الاتصال المفضلة.
                </div>
            """, unsafe_allow_html=True)

        vault["fall_detection"] = st.toggle("🚑 تفعيل استغاثة الاغماء", value=vault.get("fall_detection", False))
        if vault["fall_detection"]:
            st.markdown(f"""
                <div class="info-card">
                    <b style="color:{BLUE};">🔍 تعرف ماذا يفعل هذا النظام؟</b><br>
                    يقوم البرنامج بمراقبة حساسات التسارع؛ وفي حالة سقوط الهاتف بشكل مفاجئ مع انعدام الحركة، يتم إرسال رسالة تحذير فورية.
                </div>
            """, unsafe_allow_html=True)
        
    with col_set2:
        st.subheader("🧬 " + ("الملف الصحي" if st.session_state.lang == "AR" else "Medical Profile"))
        
        # 1. الحساسية
        vault["has_allergy"] = st.radio("هل تعاني من حساسية؟", ["No / لا", "Yes / نعم"], key="radio_allergy")
        if "Yes" in vault["has_allergy"]:
            vault["allergy_type"] = st.text_input("حدد نوع الحساسية (مثلاً: لاكتوز، بنسلين)", vault.get("allergy_type", ""))
            st.info("💡 شفاك الله وعافاك، يرجى الحذر دائماً.")

        # 2. السكر
        vault["has_diabetes"] = st.radio("هل تعاني من السكر؟", ["No / لا", "Yes / نعم"], key="radio_diabetes")
        if "Yes" in vault["has_diabetes"]:
            vault["diabetes_type"] = st.text_input("حدد النوع أو النسبة المعتادة", vault.get("diabetes_type", ""))
            st.success("🤲 أسأل الله العظيم رب العرش العظيم أن يشفيك.")

        # 3. الضغط
        vault["has_pressure"] = st.radio("هل تعاني من ضغط الدم؟", ["No / لا", "Yes / نعم"], key="radio_pressure")
        if "Yes" in vault["has_pressure"]:
            vault["pressure_details"] = st.text_input("وصف الحالة (مثلاً: ضغط مرتفع مزمن)", vault.get("pressure_details", ""))
            st.success("🤲 اللهم رب الناس أذهب البأس، اشفِ أنت الشافي.")

        # 4. القلب
        vault["has_heart"] = st.radio("هل تعاني من أمراض القلب؟", ["No / لا", "Yes / نعم"], key="radio_heart")
        if "Yes" in vault["has_heart"]:
            vault["heart_details"] = st.text_input("حدد نوع الإصابة أو العملية السابقة", vault.get("heart_details", ""))
            st.success("🤲 شفاءً لا يغادر سقماً، طهور إن شاء الله.")
        
        st.markdown("---")
        st.subheader("💧 " + ("نظام ترطيب الجسم" if st.session_state.lang == "AR" else "Hydration System"))
        vault["water_reminder"] = st.toggle("تفعيل تذكير المياه", value=vault.get("water_reminder", True))
        
        if vault.get("water_reminder"):
            water_count = vault.get("water_glasses", 0)
            st.markdown(f"""
                <div style="background:rgba(0,212,255,0.1); padding:15px; border-radius:15px; text-align:center; border:1px solid {BLUE};">
                    <h4 style="color:white; margin:0;">🥤 حصتك اليومية الحالية</h4>
                    <span style="font-size:2rem; color:{BLUE}; font-weight:bold;">{water_count}</span> <small>أكواب</small>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("➕ شربت الآن"):
                vault["water_glasses"] = water_count + 1
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(L["save_btn"], use_container_width=True): 
        save_user_data(st.session_state.current_user, vault)
        st.balloons()
        st.success("✅ تم حفظ إعداداتك بنجاح ")
elif page == "ABOUT":
    ABOUT_DATA = {
        "AR": {
            "legal_title": "⚖️ حقوق الملكية الفكرية",
            "legal_text": "هذا النظام ومكوناته البرمجية وتصميمه البصري محمي دولياً لعام 2026. يمنع منعاً باتاً الهندسة العكسية أو سرقة الأكواد.",
            "copyright": "جميع الحقوق محفوظة © 2026 Ayman Dev",
            "sections": {
                "🛡️ 1. الأمان الشخصي": ["استغاثة السرقة الذكية", "تتبع الموقع عند الجري", "قفل البيانات التلقائي", "تنبيه الأشخاص المفضلين", "رصد السحب العنيف للهاتف"],
                "🏥 2. الأمان الطبي": ["استغاثة حالات الإغماء", "رصد السقوط المفاجئ", "تحليل فوري للأعراض", "تنبيه الطوارئ الطبي", "بروتوكول إنقاذ الحياة"],
                "🔐 3. أمن البيانات": ["تشفير AES-256 عسكري", "تشفير Fernet للمرور", "معمارية المعرفة الصفرية", "حماية الخصوصية المطلقة", "درع منع الاختراق"],
                "🤖 4. الذكاء الاصطناعي": ["مسعف Gemini 2.5 الذكي", "تحليل ذكي للبيانات", "استجابة فورية للأوامر", "دعم فني AI متواصل", "نصائح صحية متطورة"],
                "🚨 5. أنظمة الطوارئ": ["زر SOS فائق السرعة", "تحديد GPS دقيق جداً", "اتصال مباشر بالنجدة", "مشاركة مسار الاستغاثة", "تكامل أنظمة الحماية"],
                "🏥 6. الرادار الطبي": ["ملاح المستشفيات القريب", "رادار الصيدليات اللحظي", "خرائط المختبرات الطبية", "حساب المسافة والوقت", "توجيه ذكي للوجهة"],
                "📊 7. المراقبة الصحية": ["سجل الفصيلة والحساسية", "منبه الأدوية الذكي", "مراقب ترطيب الجسم", "إحصائيات استهلاك المياه", "خزنة التاريخ الطبي"],
                "🎨 8. واجهة UX/UI": ["تصميم نيون ديناميكي", "وضع ليلي مريح جداً", "تجاوب مع كافة الشاشات", "تأثيرات بصرية تفاعلية", "تجربة مستخدم انسيابية"],
                "🌍 9. اللغات والنصائح": ["تبديل فوري (AR/EN)", "نصائح طبية متجددة", "دليل إسعافات متكامل", "دعم الثقافة الصحية", "تخصيص كامل للمحتوى"]
            }
        },
        "EN": {
            "legal_title": "⚖️ Intellectual Property",
            "legal_text": "This system and its code are internationally protected 2026. Reverse engineering is strictly prohibited.",
            "copyright": "All Rights Reserved © 2026 Ayman Dev",
            "sections": {
                "🛡️ 1. Personal Security": ["Smart Anti-Theft Alert", "Motion Tracking Log", "Auto Data Lockdown", "Contacts Notifications", "Sudden Pull Detection"],
                "🏥 2. Medical Safety": ["Fainting Emergency Ops", "Sudden Fall Monitoring", "Instant Symptom Analysis", "Medical Alert System", "Life-Saving Protocols"],
                "🔐 3. Data Security": ["AES-256 Encryption", "Fernet Security", "Zero-Knowledge Link", "Privacy Shield", "Anti-Hacking Guard"],
                "🤖 4. AI Intelligence": ["Gemini 2.5 Smart Medic", "Advanced Data Analysis", "Instant AI Response", "24/7 AI Support", "Smart Health Context"],
                "🚨 5. Emergency Systems": ["High-Speed SOS Button", "Ultra-Precise GPS", "Direct Rescue Links", "Distress Path Sharing", "Integrated Shield"],
                "🏥 6. Medical Radar": ["Hospital Finder GPS", "Real-time Pharmacy Map", "Lab Service Navigator", "Distance Calculation", "Smart Routing"],
                "📊 7. Health Monitoring": ["Blood & Allergy Logs", "Medication Reminder", "Hydration Tracker", "Water Usage Stats", "Medical History Vault"],
                "🎨 8. UX/UI Excellence": ["Dynamic Neon Design", "Eye-Comfort Dark Mode", "Responsive Layout", "Interactive Visuals", "Smooth Flow UX"],
                "🌍 9. Multi-Language": ["Instant (AR/EN) Swap", "Updated Medical Tips", "First Aid Guide", "Health Literacy", "Customized Content"]
            }
        }
    }

    lang = st.session_state.lang
    content = ABOUT_DATA[lang]

    st.markdown(f"""
        <style>
            .main-neon-vault {{ background: rgba(13, 17, 23, 0.98); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 20px; padding: 40px; margin: 20px auto; max-width: 1200px; direction: {'rtl' if lang == 'AR' else 'ltr'}; }}
            .category-card {{ background: rgba(0, 212, 255, 0.03); border: 1px solid {BLUE}; border-radius: 15px; padding: 18px; margin-bottom: 25px; height: 230px; box-shadow: 0 0 12px rgba(0, 212, 255, 0.1); transition: 0.4s ease-in-out; }}
            .category-card:hover {{ box-shadow: 0 0 25px rgba(0, 212, 255, 0.4); transform: scale(1.03); background: rgba(0, 212, 255, 0.07); }}
            .feature-item {{ font-size: 0.85rem; margin-bottom: 5px; color: #e6edf3; text-align: {'right' if lang == 'AR' else 'left'}; }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-neon-vault">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for i, (title, features) in enumerate(content['sections'].items()):
        with cols[i % 3]:
            feat_html = "".join([f'<div class="feature-item">● {f}</div>' for f in features])
            st.markdown(f"""
                <div class="category-card">
                    <div style="color:{BLUE}; font-weight:bold; border-bottom:1px solid rgba(0,212,255,0.3); margin-bottom:12px; text-align:center; padding-bottom:5px; font-size:1.1rem;">{title}</div>
                    {feat_html}
                </div>
            """, unsafe_allow_html=True)
    st.markdown(f'<h1 style="text-align:center; color:{BLUE};"></h1>', unsafe_allow_html=True)
    
    st.write("برنامج Safe Pulse PRO هو رفيقك الذكي للسلامة والإسعافات الأولية.")

    whatsapp_number = "201153897231"
    whatsapp_url = f"https://wa.me/{whatsapp_number}"

    st.markdown(f"""
    <style>
    .whatsapp-btn {{ background-color: #25D366; color: white !important; padding: 15px 25px; text-align: center; text-decoration: none; display: inline-block; font-size: 18px; font-weight: bold; border-radius: 50px; box-shadow: 0 0 15px #25D366; transition: 0.3s; border: none; cursor: pointer; margin: 20px auto; display: block; width: fit-content; }}
    .whatsapp-btn:hover {{ box-shadow: 0 0 30px #25D366; transform: scale(1.05); }}
    </style>
    
    <a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">
        💬 تواصل مع المبرمج عبر واتساب
    </a>
    """, unsafe_allow_html=True)

    st.markdown(f"""
            <div style="margin-top:20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top:25px; text-align:center;">
                <p style="color:#ff4b4b; font-weight:bold;">{content['legal_title']}</p>
                <p style="color:#888; font-size:0.9rem;">{content['legal_text']}</p>
                <p style="color:{BLUE}; font-size:0.8rem; margin-top:10px;">{content['copyright']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"""
    <style>
    .footer-text {{ text-align: center; color: {BLUE}; font-family: 'Arial', sans-serif; font-size: 18px; font-weight: bold; text-shadow: 0 0 10px {BLUE}, 0 0 20px {BLUE}; padding: 20px; letter-spacing: 2px; }}
    </style>
    <div class="footer-text">
         جميع الحقوق محفوظة © 2026 Ayman Dev
    </div>
""", unsafe_allow_html=True)

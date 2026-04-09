import streamlit as st
import google.generativeai as genai
import os
import json
import base64
import time
import random
import string
import secrets
import google.generativeai
import random
import bcrypt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import firebase_admin
from firebase_admin import credentials, firestore
import firebase_admin
import re
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import os
import json
import base64
import time
import random
import string
import secrets
import bcrypt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from streamlit_js_eval import streamlit_js_eval, get_geolocation
import streamlit as st
# ... باقي المكتبات ...

# ضيف الكود هنا
if 'check_attempts' not in st.session_state:
    st.session_state.check_attempts = 0

# بعد كدة كمل باقي الكود بتاعك عادي
# --- 1. الإعدادات الأساسية (يجب أن تكون في البداية تماماً) ---
st.set_page_config(page_title="Safe Pulse Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. دالة تهيئة Firebase الموحدة ---
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

def init_fb():
    # المسار لملف الـ JSON الذي أعدت تسميته
    json_path = "serviceAccountKey.json"
    
    if not firebase_admin._apps:
        if os.path.exists(json_path):
            try:
                cred = credentials.Certificate(json_path)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                st.error(f"حدث خطأ في قراءة ملف المفاتيح: {e}")
                st.stop()
        else:
            st.error("ملف serviceAccountKey.json غير موجود في المجلد!")
            st.stop()

# تشغيل الدالة
init_fb()
db = firestore.client()

# حل مشكلة AttributeError: st.session_state has no attribute "check_attempts"
if "check_attempts" not in st.session_state:
    st.session_state.check_attempts = 0
# --- 3. التحقق من مفتاح التشفير ---
# ملاحظة: تم إزالة استدعاء st.sidebar هنا لأنك قمت بإخفاء السايدبار في CSS لاحقاً
# التأكد من قراءة مفتاح التشفير
if "ENCRYPTION_KEY" in st.secrets:
    encryption_key = st.secrets["ENCRYPTION_KEY"]
else:
    st.warning("مفتاح التشفير ENCRYPTION_KEY غير موجود في Secrets.")

# --- 4. واجهة CSS والتصميم ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        [data-testid="stSidebar"] { display: none !important; width: 0px !important; }
        [data-testid="stMainView"] { width: 100% !important; margin-left: 0px !important; }
        .stAppDeployButton {display: none !important;}
        header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- استكمال بقية الكود الخاص بالجلسات والمنطق البرمجي كما هو ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "HOME"
# ... (بقية كودك من هنا فصاعداً)
# --- 2. تعريف الدوال الأساسية وإدارة الملفات السحابية ---

SESSION_FILE = "assets/sessions.json"
KEY_FILE = "assets/internal.key"
REGISTRY_FILE = "assets/user_registry.json"

if not os.path.exists("assets"): 
    os.makedirs("assets")

def get_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f: 
            try: return json.load(f)
            except: return {}
    return {}

def save_to_registry(username, password):
    registry = get_registry()
    # تشفير كلمة المرور قبل حفظها
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    # نحفظها كنص مشفر
    registry[username] = hashed_password.decode('utf-8')
    with open(REGISTRY_FILE, "w") as f: 
        json.dump(registry, f)

def get_cipher():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f: f.write(key)
    return Fernet(open(KEY_FILE, "rb").read())

cipher = get_cipher()

def save_user_data(username, data):
    # تشفير البيانات قبل إرسالها للسحابة لضمان الخصوصية
    encrypted_data = cipher.encrypt(json.dumps(data).encode()).decode()
    db.collection("users").document(username).set({"vault": encrypted_data})

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

st.markdown(f"""
<style>
    {font_face}
    html, body, [data-testid="stAppViewContainer"] {{ background-color: #010409; color: white; direction: {DIR}; }}
    .stButton>button {{ background: #0d1117 !important; border: 2px solid {BLUE} !important; color: white !important; 
                        border-radius: 12px; height: 50px; box-shadow: {GLOW}; transition: 0.4s; width: 100%; font-size: 18px; }}
    .neon-card {{ background: #0d1117; border: 2px solid {BLUE}; border-radius: 15px; padding: 20px 10px; margin-bottom: 12px; text-align: center; box-shadow: {GLOW}; line-height: 1.6; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
    .neon-card-green {{ background: #0d1117; border: 2px solid {GREEN_NEON}; border-radius: 15px; padding: 20px 10px; margin-bottom: 12px; text-align: center; box-shadow: {GLOW_GREEN}; line-height: 1.6; min-height: 100px; display: flex; flex-direction: column; justify-content: center; align-items: center; }}
    .aid-box {{ background: rgba(0, 212, 255, 0.05); border: 1px solid {BLUE}; padding: 15px; border-radius: 15px; margin-bottom: 20px; box-shadow: {GLOW}; }}
    .aid-img {{ width: 120px; height: 120px; object-fit: contain; border-radius: 15px; filter: drop-shadow({GLOW}); margin-bottom: 10px; }}
    .welcome-text {{ font-size: 1.5rem; color: white; margin-bottom: 10px; text-align: center; }}
    .neon-user {{ color: {BLUE}; text-shadow: {GLOW}; font-weight: bold; }}
    .ai-response-box {{ background: #0d1117; border: 1px solid #00f2fe; padding: 15px; border-radius: 12px; box-shadow: inset 0 0 10px #00f2fe; color: white; margin-top: 10px; line-height: 1.6; }}
    .main-neon-card {{ background: rgba(0, 0, 0, 0.3); border: 2px solid {BLUE}; border-radius: 20px; padding: 20px; box-shadow: {GLOW}; margin-bottom: 20px; }}
    .neon-text-item {{ color: #FFFFFF !important; font-size: 1.1rem; padding: 12px 0; border-bottom: 1px solid rgba(0, 212, 255, 0.1); text-shadow: 0 0 8px {BLUE}; font-weight: 500; }}
    .note-time {{ color: {BLUE}; font-size: 0.8rem; margin-left: 15px; text-shadow: none; }}
    header {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# --- 7. واجهة تسجيل الدخول ---

if not st.session_state.authenticated:
    logo_data = get_64("assets/icons/icon.png")
    st.markdown(f'<div style="text-align:center; padding-top:30px;"><img src="data:image/png;base64,{logo_data}" style="width:180px; filter:drop-shadow({GLOW});"><h1 style="color:{BLUE}; font-size:2.8rem; text-shadow:{GLOW};">Safe Pulse PRO</h1></div>', unsafe_allow_html=True)
    
    # إضافة ميزة الاسترداد الأوفلاين في صفحة الدخول
    with st.sidebar:
        st.header("🔑 استرداد البيانات (Offline)")
        uploaded_backup = st.file_uploader("ارفع ملف الـ .dat الخاص بك للقراءة", type=['dat'], key="login_recovery")
        if uploaded_backup:
            try:
                recovered_data = json.loads(cipher.decrypt(uploaded_backup.read()).decode())
                st.session_state['temp_recovered_data'] = recovered_data
                st.success("تم قراءة الملف بنجاح!")
            except: st.error("فشل قراءة الملف")

    tab_login, tab_setup = st.tabs(["🔐 تسجيل الدخول", "✨ إنشاء حساب جديد"])
    with tab_login:
        in_user = st.text_input(L["login_user"], key="l_user")
        in_pass = st.text_input(L["login_pass"], type="password", key="l_pass")
        if st.button(L["login_btn"]):
            reg = get_registry()
            if in_user in reg:
                # جلب الباسورد المشفر المخزن وتحويله لـ bytes
                stored_hash = reg[in_user].encode('utf-8')
                
                # التحقق باستخدام bcrypt
                if bcrypt.checkpw(in_pass.encode('utf-8'), stored_hash):
                    token = create_session(in_user)
                    st.session_state.current_user = in_user
                    # تحميل البيانات من Firestore
                    st.session_state.secure_vault = load_user_data(in_user) or get_user_defaults(in_user)
                    st.session_state.authenticated = True
                    st.session_state.page = "HOME"
                    
                    # حفظ التوكن في المتصفح لاستعادة الجلسة
                    streamlit_js_eval(
                        js_expressions=f"localStorage.setItem('sp_token', '{token}')",
                        key="set_token_final"
                    )
                    st.success("✅ أهلاً بك مجدداً!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة")
            else:
                st.error("❌ مستخدم غير موجود")
    
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

    # عرض البيانات المستردة في صفحة الدخول إن وجدت
    if 'temp_recovered_data' in st.session_state:
        st.markdown('<div class="main-neon-card">', unsafe_allow_html=True)
        st.subheader("📋 البيانات المستردة:")
        st.write(st.session_state['temp_recovered_data'])
        if st.button("إغلاق"): del st.session_state['temp_recovered_data']; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()

# --- 8. محتوى البرنامج (بعد الدخول) ---

logo_data = get_64("assets/icons/icon.png")
st.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{logo_data}" style="width:110px; filter:drop-shadow({GLOW});"><h2 style="color:{BLUE}; text-shadow:{GLOW}; font-size:2rem;">Safe Pulse PRO</h2></div>', unsafe_allow_html=True)

nav_keys = ["HOME", "AID", "AI", "SET", "ABOUT", "LANG"]
n_cols = st.columns(len(L["nav"]) + 1)
for idx, label in enumerate(L["nav"]):
    if n_cols[idx].button(label, key=f"nav_{idx}"):
        if nav_keys[idx] == "LANG":
            st.session_state.lang = "EN" if st.session_state.lang == "AR" else "AR"
            vault["lang"] = st.session_state.lang
            save_user_data(st.session_state.current_user, vault); st.rerun()
        else: st.session_state.page = nav_keys[idx]; st.rerun()

if n_cols[-1].button(L["logout"]):
    streamlit_js_eval(js_expressions="localStorage.removeItem('sp_token')", key="remove_token_final")
    st.session_state.authenticated = False
    st.session_state.current_user = ""
    st.rerun()

st.divider()
page = st.session_state.page

if page == "HOME":
    # 1. تعريف نظام التحريك الاحترافي (Animations)
    st.markdown(f"""
        <style>
            /* تحريك اللوجو: نبض مع إشعاع نيون */
            @keyframes logo_pulse {{
                0% {{ transform: scale(1); filter: drop-shadow(0 0 10px {BLUE}); }}
                50% {{ transform: scale(1.1); filter: drop-shadow(0 0 30px {BLUE}) brightness(1.2); }}
                100% {{ transform: scale(1); filter: drop-shadow(0 0 10px {BLUE}); }}
            }}
            .main-logo-pulse {{
                animation: logo_pulse 3s infinite ease-in-out;
                display: block;
                margin: auto;
                width: 120px;
                margin-bottom: 20px;
            }}

            /* تحريك العناصر عند دخول الصفحة */
            @keyframes slide_up {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .stButton, .neon-card, .neon-card-green {{
                animation: slide_up 0.6s ease-out forwards;
            }}

            /* تأثير التفاعل عند تمرير الماوس (Hover) */
            .neon-card, .neon-card-green {{
                transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                cursor: pointer;
            }}
            .neon-card:hover, .neon-card-green:hover {{
                transform: scale(1.08) !important;
                box-shadow: 0 0 30px {BLUE} !important;
                filter: brightness(1.2);
            }}
        </style>
    """, unsafe_allow_html=True)

    # 2. عرض اللوجو بتأثير النبض
    img_logo = get_64("assets/icons/icon.png")
    if img_logo:
        st.markdown(f'<img src="data:image/png;base64,{img_logo}" class="main-logo-pulse">', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center; font-size:50px;" class="main-logo-pulse">🛡️</div>', unsafe_allow_html=True)

    # 3. نصوص الترحيب
    st.markdown(f'<div class="welcome-text" style="text-align:center;">{L["welcome"]} <span class="neon-user">{st.session_state.current_user}</span></div>', unsafe_allow_html=True)
    
    # 4. أزرار التحكم العلوية
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
    
    # 5. قسم الأمان (Locks)
    st.subheader(L["locks_h"])
    l1, l2 = st.columns(2)
    with l1: vault["theft_on"] = st.toggle(L["l_theft"], value=vault.get("theft_on", True))
    with l2: vault["app_lock"] = st.toggle(L["l_app"], value=vault.get("app_lock", False))
    
    # 6. إعداد بيانات الموقع والـ SOS
    loc = get_geolocation()
    lat_lon = f"{loc['coords']['latitude']},{loc['coords']['longitude']}" if loc and 'coords' in loc else "0,0"
    loc_link = f"https://www.google.com/maps?q={lat_lon}"
    encoded_msg = f"🚨 SOS! My Location: {loc_link}"
    
    # 7. كروت الواتساب الخضراء
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
    
    # 8. قسم الرادار (Radar)
    st.subheader(L["radar_h"])
    r1, r2, r3 = st.columns(3)
    with r1: st.markdown(f'<a href="https://www.google.com/maps/search/hospital" target="_blank" style="text-decoration:none;"><div class="neon-card">🏥<br>{L["hosp"]}</div></a>', unsafe_allow_html=True)
    with r2: st.markdown(f'<a href="https://www.google.com/maps/search/pharmacy" target="_blank" style="text-decoration:none;"><div class="neon-card">💊<br>{L["pharm"]}</div></a>', unsafe_allow_html=True)
    with r3: st.markdown(f'<a href="https://www.google.com/maps/search/medical+lab" target="_blank" style="text-decoration:none;"><div class="neon-card">🔬<br>{L["lab"]}</div></a>', unsafe_allow_html=True)

    # 9. قسم الطوارئ (Emergency)
    st.subheader(L["sos_h"])
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.markdown(f'<a href="tel:122" style="text-decoration:none;"><div class="neon-card">🚓<br>{L["p"]}</div></a>', unsafe_allow_html=True)
    with s2: st.markdown(f'<a href="tel:123" style="text-decoration:none;"><div class="neon-card" style="border-color:#ff4b4b; color:#ff4b4b;">🚑<br>{L["a"]}</div></a>', unsafe_allow_html=True)
    with s3: st.markdown(f'<a href="tel:180" style="text-decoration:none;"><div class="neon-card">🚒<br>{L["f"]}</div></a>', unsafe_allow_html=True)
    with s4: st.markdown(f'<a href="tel:129" style="text-decoration:none;"><div class="neon-card">🔥<br>{L["g"]}</div></a>', unsafe_allow_html=True)
elif page == "AI":
    st.header("🤖 " + L["nav"][2])
    def get_ai_response(u_input):
        keys_pool = st.secrets.get("GEMINI_KEYS", [])
        if not keys_pool: return "❌ خطأ: لم يتم العثور على قائمة المفاتيح في Secrets."
        
        # إضافة نداء الاسم في التعليمات الخفية للموديل
        name = st.session_state.current_user
        full_prompt = f"المستخدم اسمه {name}. أجب على هذا السؤال الطبي/الطوارئ وقم بمناداته باسمه بطريقة مهذبة في بداية أو نهاية الرد: {u_input}"

        for attempt in range(len(keys_pool)):
            current_key = random.choice(keys_pool)
            try:
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                if "429" in str(e) or "exhausted" in str(e):
                    time.sleep(1)
                    continue 
                return f"❌ خطأ فني: {str(e)}"
        return "⚠️ جميع المفاتيح مشغولة حالياً."

    u_input = st.text_area(L["ai_label"], height=150, key="ai_final_input")
    if st.button(L["ai_btn"], key="ai_final_btn"):
        if u_input:
            with st.spinner("جاري استشارة المسعف الذكي..."):
                result = get_ai_response(u_input)
                st.markdown(f"<div class='ai-response-box'>{result}</div>", unsafe_allow_html=True)
                vault["ai_chat_history"].append({"time": datetime.now().strftime("%H:%M"), "q": u_input, "a": result})
                save_user_data(st.session_state.current_user, vault)


elif page == "AID":
    lang = st.session_state.lang
    title_text = "🚑 الإسعافات الأولية" if lang == "AR" else "🚑 First Aid Guide"
    st.markdown(f"<h1 style='text-align:center; color:{BLUE}; text-shadow: 0 0 15px {BLUE};'>{title_text}</h1>", unsafe_allow_html=True)
    
    content = AID_CONTENT.get(lang, AID_CONTENT["AR"])

    # إعداد CSS الاحترافي مع تأثير النيون المطور للصور
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
        # المسار الصحيح بناءً على صورة المجلد المرفقة assets/icons/
        icon_file = item.get('icon', 'hospital.png')
        if not icon_file.endswith('.png'):
            icon_file += '.png'
            
        img_path = f"assets/icons/{icon_file}"
        img_64 = get_64(img_path)
        
        tips = item.get('tips', item.get('text', []))
        tips_html = "".join([f'<div class="tip-item">{tip}</div>' for tip in (tips if isinstance(tips, list) else [tips])])
        
        # عرض الأيقونة الافتراضية hospital.png في حال لم يجد الصورة المحددة
        if img_64:
            image_tag = f'<img src="data:image/png;base64,{img_64}">'
        else:
            # محاولة جلب hospital.png كخيار افتراضي احترافي
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
    # 1. تصميم نيون مخصص وتحويل السهم إلى زر نصي "تحدث"
    st.markdown(f"""
        <style>
            /* إخفاء أيقونات المستخدم والمساعد */
            [data-testid="stChatMessageAvatarUser"], 
            [data-testid="stChatMessageAvatarAssistant"] {{
                display: none !important;
            }}
            
            [data-testid="stChatMessageContent"] {{
                margin-left: 0px !important;
            }}

            /* خلفية منطقة الشات */
            .stChatFloatingInputContainer {{
                background-color: rgba(0, 0, 0, 0) !important;
            }}
            
            /* تصميم صندوق الإدخال نيون */
            .stChatInput {{
                border: 1px solid {BLUE} !important;
                border-radius: 25px !important;
                box-shadow: 0 0 15px {BLUE} !important;
                background: rgba(10, 10, 10, 0.9) !important;
            }}

            /* تحويل سهم الإرسال إلى زر "تحدث" نيون */
            button[data-testid="stChatInputSubmit"] {{
                background-color: white !important;
                border: 2px solid {BLUE} !important;
                box-shadow: 0 0 10px white, 0 0 20px {BLUE} !important;
                border-radius: 15px !important;
                width: 80px !important; /* عرض أكبر لاستيعاب النص */
                height: 35px !important;
                transition: all 0.3s ease !important;
                position: relative !important;
            }}

            /* إخفاء أيقونة السهم الأصلية */
            button[data-testid="stChatInputSubmit"] svg {{
                display: none !important;
            }}

            /* إضافة كلمة "تحدث" داخل الزر */
            button[data-testid="stChatInputSubmit"]::after {{
                content: "تحدث";
                color: {BLUE};
                font-weight: bold;
                font-size: 14px;
                display: block;
            }}

            button[data-testid="stChatInputSubmit"]:hover {{
                transform: scale(1.05) !important;
                box-shadow: 0 0 15px white, 0 0 30px {BLUE} !important;
                filter: brightness(1.2);
            }}

            /* فقاعات الشات نيون */
            [data-testid="stChatMessage"] {{
                background: rgba(0, 255, 255, 0.03) !important;
                border: 1px solid rgba(0, 255, 255, 0.15) !important;
                border-radius: 20px !important;
                margin-bottom: 12px !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # 2. عنوان الشات
    st.markdown(f'<h2 style="text-align:center; color:{BLUE}; text-shadow: 0 0 20px {BLUE};">✨ مفكرتك الذكية</h2>', unsafe_allow_html=True)
    
    # 3. نظام الشات
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("اكتب فكرة جديدة..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    st.write("---")
    if st.button("⬅️ العودة للرئيسية"):
        st.session_state.page = "HOME"
        st.rerun()
elif page == "SET":
    # 1. إعدادات CSS النيون الشاملة لجميع العناصر
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
            /* كارت الوظيفة الذكي */
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
            /* تحسين شكل الأزرار والحقول لتناسب النيون */
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
        
        # ميزة استغاثة السرقة + كارت الوظيفة
        vault["anti_theft"] = st.toggle("🚨 تفعيل استغاثة السرقة", value=vault.get("anti_theft", False))
        if vault["anti_theft"]:
            st.markdown(f"""
                <div class="info-card">
                    <b style="color:{BLUE};">🔍 تعرف ماذا يفعل هذا النظام؟</b><br>
                    عند رصد حركة جري مفاجئة أو سحب الهاتف من اليد بقوة، يقوم النظام فوراً بتشفير كافة بياناتك الحساسة وإرسال إحداثيات موقعك الأخير لجهات الاتصال المفضلة قبل محاولة إغلاق الهاتف.
                </div>
            """, unsafe_allow_html=True)

        # ميزة استغاثة الإغماء + كارت الوظيفة
        vault["fall_detection"] = st.toggle("🚑 تفعيل استغاثة الاغماء", value=vault.get("fall_detection", False))
        if vault["fall_detection"]:
            st.markdown(f"""
                <div class="info-card">
                    <b style="color:{BLUE};">🔍 تعرف ماذا يفعل هذا النظام؟</b><br>
                    يقوم البرنامج بمراقبة حساسات التسارع والجاذبية (Sensors)؛ وفي حالة سقوط الهاتف بشكل مفاجئ مع انعدام الحركة، يتم إرسال رسالة "تحذير حالة إغماء" فورية مع رابط موقعك الجغرافي للمقربين.
                </div>
            """, unsafe_allow_html=True)
        
    with col_set2:
        st.subheader("🧬 " + ("الحساسية" if st.session_state.lang == "AR" else "Allergies"))
        vault["has_allergy"] = st.radio("هل تعاني من حساسية؟", ["No / لا", "Yes / نعم"])
        if "Yes" in vault["has_allergy"]:
            vault["allergy_type"] = st.text_input("نوع الحساسية", vault.get("allergy_type", ""))
        
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
                st.components.v1.html("""
                    <audio autoplay><source src="https://www.soundjay.com/nature/sounds/water-droplet-1.mp3" type="audio/mpeg"></audio>
                """, height=0)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    # زر الحفظ النيون الكبير
    if st.button(L["save_btn"], use_container_width=True): 
        save_user_data(st.session_state.current_user, vault)
        st.balloons()
        st.success("✅ تم حفظ إعداداتك بنجاح في خزنة Ayman Dev")
    
    st.markdown('</div>', unsafe_allow_html=True)
# قسم التحذيرات وحقوق الملكية
elif page == "ABOUT":
    # 1. قاموس المحتوى المحدث (9 أقسام مركزة)
    ABOUT_DATA = {
        "AR": {
            "legal_title": "⚖️ حقوق الملكية الفكرية",
            "legal_text": "هذا النظام ومكوناته البرمجية وتصميمه البصري محمي دولياً لعام 2026. يمنع منعاً باتاً الهندسة العكسية أو سرقة الأكواد.",
            "copyright": "جميع الحقوق محفوظة © 2026 Ayman Dev",
            "sections": {
                "🛡️ 1. الأمان الشخصي": [
                    "استغاثة السرقة الذكية", "تتبع الموقع عند الجري", "قفل البيانات التلقائي", 
                    "تنبيه الأشخاص المفضلين", "رصد السحب العنيف للهاتف"
                ],
                "🏥 2. الأمان الطبي": [
                    "استغاثة حالات الإغماء", "رصد السقوط المفاجئ", "تحليل فوري للأعراض", 
                    "تنبيه الطوارئ الطبي", "بروتوكول إنقاذ الحياة"
                ],
                "🔐 3. أمن البيانات": [
                    "تشفير AES-256 عسكري", "تشفير Bcrypt للمرور", "معمارية المعرفة الصفرية", 
                    "حماية الخصوصية المطلقة", "درع منع الاختراق"
                ],
                "🤖 4. الذكاء الاصطناعي": [
                    "مسعف Gemini 2.5 الذكي", "تحليل ذكي للبيانات", "استجابة فورية للأوامر", 
                    "دعم فني AI متواصل", "نصائح صحية متطورة"
                ],
                "🚨 5. أنظمة الطوارئ": [
                    "زر SOS فائق السرعة", "تحديد GPS دقيق جداً", "اتصال مباشر بالنجدة", 
                    "مشاركة مسار الاستغاثة", "تكامل أنظمة الحماية"
                ],
                "🏥 6. الرادار الطبي": [
                    "ملاح المستشفيات القريب", "رادار الصيدليات اللحظي", "خرائط المختبرات الطبية", 
                    "حساب المسافة والوقت", "توجيه ذكي للوجهة"
                ],
                "📊 7. المراقبة الصحية": [
                    "سجل الفصيلة والحساسية", "منبه الأدوية الذكي", "مراقب ترطيب الجسم", 
                    "إحصائيات استهلاك المياه", "خزنة التاريخ الطبي"
                ],
                "🎨 8. واجهة UX/UI": [
                    "تصميم نيون ديناميكي", "وضع ليلي مريح جداً", "تجاوب مع كافة الشاشات", 
                    "تأثيرات بصرية تفاعلية", "تجربة مستخدم انسيابية"
                ],
                "🌍 9. اللغات والنصائح": [
                    "تبديل فوري (AR/EN)", "نصائح طبية متجددة", "دليل إسعافات متكامل", 
                    "دعم الثقافة الصحية", "تخصيص كامل للمحتوى"
                ]
            }
        },
        "EN": {
            "legal_title": "⚖️ Intellectual Property",
            "legal_text": "This system and its code are internationally protected 2026. Reverse engineering is strictly prohibited.",
            "copyright": "All Rights Reserved © 2026 Ayman Dev",
            "sections": {
                "🛡️ 1. Personal Security": [
                    "Smart Anti-Theft Alert", "Motion Tracking Log", "Auto Data Lockdown", 
                    "Contacts Notifications", "Sudden Pull Detection"
                ],
                "🏥 2. Medical Safety": [
                    "Fainting Emergency Ops", "Sudden Fall Monitoring", "Instant Symptom Analysis", 
                    "Medical Alert System", "Life-Saving Protocols"
                ],
                "🔐 3. Data Security": [
                    "AES-256 Encryption", "Bcrypt Security", "Zero-Knowledge Link", 
                    "Privacy Shield", "Anti-Hacking Guard"
                ],
                "🤖 4. AI Intelligence": [
                    "Gemini 2.5 Smart Medic", "Advanced Data Analysis", "Instant AI Response", 
                    "24/7 AI Support", "Smart Health Context"
                ],
                "🚨 5. Emergency Systems": [
                    "High-Speed SOS Button", "Ultra-Precise GPS", "Direct Rescue Links", 
                    "Distress Path Sharing", "Integrated Shield"
                ],
                "🏥 6. Medical Radar": [
                    "Hospital Finder GPS", "Real-time Pharmacy Map", "Lab Service Navigator", 
                    "Distance Calculation", "Smart Routing"
                ],
                "📊 7. Health Monitoring": [
                    "Blood & Allergy Logs", "Medication Reminder", "Hydration Tracker", 
                    "Water Usage Stats", "Medical History Vault"
                ],
                "🎨 8. UX/UI Excellence": [
                    "Dynamic Neon Design", "Eye-Comfort Dark Mode", "Responsive Layout", 
                    "Interactive Visuals", "Smooth Flow UX"
                ],
                "🌍 9. Multi-Language": [
                    "Instant (AR/EN) Swap", "Updated Medical Tips", "First Aid Guide", 
                    "Health Literacy", "Customized Content"
                ]
            }
        }
    }

    lang = st.session_state.lang
    content = ABOUT_DATA[lang]

    # 2. إعدادات CSS (النيون المطور للـ 9 كروت)
    st.markdown(f"""
        <style>
            .main-neon-vault {{
                background: rgba(13, 17, 23, 0.98);
                border: 1px solid rgba(0, 212, 255, 0.3);
                border-radius: 20px;
                padding: 40px;
                margin: 20px auto;
                max-width: 1200px;
                direction: {'rtl' if lang == 'AR' else 'ltr'};
            }}
            .category-card {{
                background: rgba(0, 212, 255, 0.03);
                border: 1px solid {BLUE};
                border-radius: 15px;
                padding: 18px;
                margin-bottom: 25px;
                height: 230px;
                box-shadow: 0 0 12px rgba(0, 212, 255, 0.1);
                transition: 0.4s ease-in-out;
            }}
            .category-card:hover {{
                box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
                transform: scale(1.03);
                background: rgba(0, 212, 255, 0.07);
            }}
            .feature-item {{
                font-size: 0.85rem;
                margin-bottom: 5px;
                color: #e6edf3;
                text-align: {'right' if lang == 'AR' else 'left'};
            }}
        </style>
    """, unsafe_allow_html=True)

    # 3. بناء الواجهة
    st.markdown('<div class="main-neon-vault">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    # توزيع الـ 9 كروت على الـ 3 أعمدة
    for i, (title, features) in enumerate(content['sections'].items()):
        with cols[i % 3]:
            feat_html = "".join([f'<div class="feature-item">● {f}</div>' for f in features])
            st.markdown(f"""
                <div class="category-card">
                    <div style="color:{BLUE}; font-weight:bold; border-bottom:1px solid rgba(0,212,255,0.3); margin-bottom:12px; text-align:center; padding-bottom:5px; font-size:1.1rem;">{title}</div>
                    {feat_html}
                </div>
            """, unsafe_allow_html=True)

    # قسم الحقوق
    st.markdown(f"""
            <div style="margin-top:20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top:25px; text-align:center;">
                <p style="color:#ff4b4b; font-weight:bold;">{content['legal_title']}</p>
                <p style="color:#888; font-size:0.9rem;">{content['legal_text']}</p>
                <p style="color:{BLUE}; font-size:0.8rem; margin-top:10px;">{content['copyright']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

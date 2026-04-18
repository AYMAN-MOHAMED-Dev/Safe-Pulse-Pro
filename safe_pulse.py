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
import streamlit as st
from cryptography.fernet import Fernet
import streamlit as st

# التحقق مما إذا كان المستخدم قد سجل دخوله سابقاً من خلال رابط المتصفح
if 'check_attempts' not in st.session_state:
    st.session_state.check_attempts = 0
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "HOME"
SUPPORT_QUOTES = {
	"AR": [
"فشل علاقة لا يعني فشلك كإنسان، بل يعني أن هذا الفصل من حياتك قد انتهى لتبدأ فصلاً أجمل.", "القلب الذي ينكسر، يلتئم ليصبح أقوى في مواجهة الخيبات القادمة.", "من لا يعرف قيمتك وأنت معه، سيعرفها جيداً حين يراك تمضي بدونه.", "لا تعتذر أبداً عن صدق مشاعرك، العيب فيمن لم يمتلك وعاءً كافياً لاحتوائها.", "أحياناً يكسر الله قلبك لينقذ روحك من علاقة كانت ستدمرك تماماً.", "الرحيل بكرامة هو انتصار عظيم لن تشعر بلذته إلا بعد حين.", "أنت تستحق شخصاً يحارب ليحميك، لا شخصاً تحارب أنت لتبقى في حياته.", "الحب لا يعني التضحية بكرامتك، فمن يحبك حقاً سيعزز كرامتك لا يهينها.", "لا تجعل خيبة واحدة تحول قلبك إلى حجر، فالعالم لا يزال مليئاً بالأوفياء.", "الوحدة أجمل بكثير من رفقة تجعلك تشعر أنك وحيد وأنت معهم.", "تعلم فن الاستغناء، فليس كل من دخل حياتك جاء ليبقى.", "النهايات هي في الحقيقة بدايات متنكرة، استعد لما هو قادم.", "لا تبكِ على من باعك، بل اشكر الله لأنه كشف لك الحقيقة قبل فوات الأوان.", "قيمتك لا يحددها رأي شخص فيك، بل يحددها تقديرك أنت لنفسك.", "الشفاء من علاقة سامة يبدأ بقرارك أنك لن تعود ضحية مرة أخرى.", "أعطِ نفسك وقتاً للحداد على ما مضى، ثم انهض كأنك لم تسقط أبداً.", "القلب الذي يمنح الفرص كثيراً، يرحل مرة واحدة دون عودة.", "أنت لست خياراً ثانياً لأحد، إما أن تكون الأول أو لا تكون.", "الخروج من علاقة مؤذية هو ولادة جديدة لروحك.", "لا تندم على معروف قدمته، فالنوايا الطيبة لا تضيع عند الله.", "النسيان ليس نسيان الأحداث، بل نسيان الشعور الذي خلفته تلك الأحداث.", "أحياناً نحتاج لفقدان أحدهم لكي نجد أنفسنا الضائعة.", "الحياة قصيرة جداً لتقضيها في انتظار من لا ينتظرك.", "كن كالنور، من أرادك سيسعى إليك، ومن فقدك سيعيش في الظلام.", "الحب الحقيقي يبني ولا يهدم، يرمم ولا يكسر.", "لا تقارن بدايتك بنهاية غيرك، لكل شخص مسار وقصة مختلفة.", "الثقة التي تُكسر لا تُرمم، لكنها تعلمك كيف تختار بعناية في المرة القادمة.", "سامح لترتاح أنت، وليس لأنهم يستحقون السماح.", "الكرامة هي الخط الأحمر الذي لا يجب أن يتخطاه أي حب في العالم.", "لا تستجدي الاهتمام، فالأشياء الجميلة تُمنح ولا تُطلب.", "من يحبك سيهتم بكسرك، ومن يهواك سيزيدك انكساراً.", "القوة ليست في عدم السقوط، بل في النهوض بعد كل سقطة.", "اكتفِ بنفسك، فالاعتماد العاطفي هو سجن لروحك.", "الحياة ستستمر بك أو بدونهم، فاختر أن تستمر وأنت شامخ.", "كل وجع مررت به هو درس صامت يجعلك أكثر حكمة.", "ضعف جسدك اليوم هو نداء لروحك لترتاح، فلا تقسُ على نفسك.", "المرض ليس نهاية الطريق، بل هو محطة لتتعلم الامتنان لأبسط النعم.", "صحتك هي استثمارك الأغلى، لا بأس أن تتوقف قليلاً لترمم جسدك.", "كل ألم تشعر به الآن هو زكاة لجسدك، ورفعة لدرجاتك.", "القوة النفسية قادرة على هزيمة أعتى الأمراض الجسدية.", "لا تحزن على عجز مؤقت، فالقمر يمر بمراحل المحاق قبل أن يكتمل نوراً.", "جسدك يحتاج لصبرك كما يحتاج للدواء، كن رحيماً به.", "الإرادة هي نصف العلاج، والتفاؤل هو النصف الآخر.", "الصحة تاج لا يراه إلا من مر بلحظات الضعف، حافظ على تاجك.", "أنت قوي بما يكفي لتجاوز هذه الوعكة، غداً ستكون ذكرى.", "التعافي رحلة وليس سباقاً، خذ وقتك بالكامل.", "لا تسمح للمرض أن يسرق بريق عينيك، الأمل دواء لا يُباع في الصيدليات.", "حتى في ذروة تعبك، تذكر أن هناك من ينتظر نهوضك بفارغ الصبر.", "جسدك هو منزلك الوحيد، اعتنِ به بالحب والهدوء.", "المرض يختبر معادن الناس من حولك، ويصقل معدنك أنت.", "كل يوم تشرق فيه الشمس هو فرصة جديدة لتعافي أفضل.", "لا تقلق، فالذي خلق الداء خلق الدواء، والثقة بالله هي الشفاء.", "استمتع بلحظات الهدوء، فالسكينة هي بيئة التعافي المثالية.", "أنت لست تشخيصاً طبياً، أنت روح عظيمة تقاوم ببطولة.", "الصبر على الألم هو أعلى مراتب الشجاعة.", "اعتبر فترة مرضك خلوة مع الله وإعادة ترتيب لأولوياتك.", "ابتسامتك في وجه الألم هي نصف الانتصار عليه.", "لا تنظر إلى ما فقدت صحياً، انظر إلى القوة التي اكتسبتها داخلياً.", "الغد يحمل لك صحة أفضل وصباحاً أجمل، كن مؤمناً بذلك.", "حتى الشجر يسقط ورقه ليعود مخضراً من جديد، وكذلك أنت.", "الضعف الجسدي ليس عيباً، بل هو طبيعة البشر، القوة هي في روحك.", "كل جرعة دواء هي خطوة نحو العافية، وكل دعاء هو تقصير للمسافة.", "كن ممتناً لكل خلية في جسدك تعمل الآن لأجلك.", "لا تيأس، فالمعجزات تحدث لأولئك الذين لا يتوقفون عن المحاولة.", "راحتك النفسية هي المحرك الأول لتعافي جسدك.", "اجعل من ألمك وقوداً لإبداعك، فالكثير من العظماء خرجوا من رحم الوجع.", "نفسك تستحق منك الدلال والاهتمام، خاصة في أوقات الضعف.", "تذكر أن الشدة لا تدوم، والعافية قادمة كفلق الصبح.", "أنت محارب، والمحاربون لا يستسلمون من المعركة الأولى.", "جسدك سيشكرك يوماً ما لأنك لم تستسلم في هذه اللحظة.", "عوض الله لا يأتي عادياً، بل يأتي ليُنسيك مرارة كل ما فقدت.", "ما ذهب منك لم يكن لك من البداية، وما هو لك لن يذهب لغيرك.", "الفقد موجع، لكنه يفتح في روحك مساحات لن يملأها إلا الله.", "عندما يأخذ الله منك شيئاً، فإنه يهيئ يديك لاستقبال شيء أعظم.", "الجبر قادم، وبطريقة لم تخطر على بالك أبداً.", "لا تبكِ على أطلال الماضي، فالمستقبل يبني لك قصوراً من العوض.", "خسارة الأشياء المادية هي أرخص أنواع الخسائر، طالما روحك بخير.", "أحياناً يرحل الجميل ليأتي الأجمل، ثق في تدبير الخالق.", "كل باب أُغلق في وجهك كان يحميك من شر لا تراه.", "الفقد يعلمنا قيمة اللحظة، والتعويض يعلمنا قيمة الصبر.", "سيعوضك الله حتى تظن أنك لم تحزن يوماً.", "الصبر على الفقد هو عبادة صامتة أجرها بغير حساب.", "الغياب ليس دائماً خسارة، أحياناً يكون نجاة.", "من فقد غاليًا، سيرزقه الله أنيساً يملأ قلبه طمأنينة.", "الحياة دولاب، اليوم فقد وغداً وجد، والرضا هو المكسب الحقيقي.", "لا تحزن على ما فات، فلو كان خيراً لبقي.", "العوض الحقيقي هو أن يرزقك الله راحة البال بعد شتات الروح.", "الفقد يكسرنا، لكن جبر الله يعيد تشكيلنا لنصبح أجمل.", "سيمسح الله على قلبك بلطفه حتى تبتسم رغماً عن كل شيء.", "كل دمعة سقطت منك في الخفاء، لها عوض كبير في العلن.", "استبشر خيراً، فالأقدار تخبئ لك ما يقر عينك.", "الفراغ الذي تركه الراحلون، سيملؤه الله بنور السكينة.", "لست وحدك، فالله معك في كل لحظة انكسار وفقد.", "العوض ليس دائماً شخصاً آخر، قد يكون سلاماً داخلياً لا يُقدّر بثمن.", "ما كان لك سيأتيك على ضعفك، وما ليس لك لن تناله بقوتك.", "أنت تسير في رعاية الله، فلا تخف من ضياع شيء.", "جبر القلوب من شيم العظماء، والله هو أعظم الجابرين.", "ابتسم، فعوض الله مدهش لدرجة تفوق الخيال.", "نهاية القصة دائماً سعيدة، إذا لم تكن سعيدة فهي ليست النهاية بعد.", "Safe Pulse PRO يذكرك دائماً: أنت تستحق الأفضل، والتعافي يبدأ من الداخل."
	
	],
	"EN": [
	 "A failed relationship does not mean you failed as a person; it simply means that chapter of your life has ended so a better one can begin.", "A broken heart heals to become stronger against future disappointments.", "Those who don’t know your worth when you’re with them will realize it when you walk away.", "Never apologize for your genuine feelings; the flaw lies in those who couldn’t hold them.", "Sometimes God breaks your heart to save your soul from a relationship that would have destroyed you.", "Leaving with dignity is a great victory you’ll only appreciate later.", "You deserve someone who fights to keep you, not someone you fight to stay with.", "Love doesn’t mean sacrificing your dignity; true love elevates you, not humiliates you.", "Don’t let one disappointment turn your heart to stone; the world still has loyal people.", "Being alone is far better than feeling lonely among others.", "Learn the art of letting go; not everyone who enters your life is meant to stay.", "Endings are often beginnings in disguise—prepare for what’s coming.", "Don’t cry over those who left you; thank God for revealing their truth.", "Your worth is not defined by others, but by how you value yourself.", "Healing from a toxic relationship begins when you decide not to be a victim again.", "Give yourself time to grieve, then rise as if you never fell.", "The heart that gives too many chances leaves once—and never returns.", "You are not a second option; either you are first, or nothing.", "Leaving a toxic relationship is a rebirth of your soul.", "Never regret kindness; sincere intentions are never wasted with God.", "Forgetting isn’t about events, but about letting go of the feelings they left behind.", "Sometimes losing someone helps us find ourselves.", "Life is too short to wait for someone who doesn’t wait for you.", "Be like light—those who want you will find their way to you.", "True love builds, it doesn’t destroy.", "Don’t compare your beginning to someone else’s end.", "Broken trust may not be repaired, but it teaches you to choose wisely.", "Forgive for your peace, not because they deserve it.", "Dignity is a red line no love should cross.", "Don’t beg for attention; beautiful things are given, not requested.", "The one who loves you cares for your brokenness; the one who doesn’t will deepen it.", "Strength is rising after every fall.", "Be enough for yourself; emotional dependence is a prison.", "Life goes on—with or without them.", "Every pain is a silent lesson.", "Your weakness today is your soul asking for rest.", "Illness is a lesson in gratitude.", "Your health is your greatest investment.", "Pain purifies and elevates you.", "Mental strength defeats illness.", "Temporary weakness is not the end.", "Your body needs your kindness.", "Hope and willpower heal.", "Health is a crown seen only by the sick.", "You are strong enough to heal.", "Recovery is a journey, not a race.", "Hope is the best medicine.", "Someone is waiting for your recovery.", "Your body is your home.", "Illness reveals true people.", "Each day is a new chance to heal.", "God created cure with disease.", "Peace is healing.", "You are more than a diagnosis.", "Patience is strength.", "Your struggle is spiritual growth.", "Smile through pain.", "Focus on your inner strength.", "Tomorrow is better.", "You will bloom again.", "Your soul is stronger than your body.", "Every step is healing.", "Be grateful for your body.", "Miracles happen to those who persist.", "Peace drives healing.", "Pain creates greatness.", "You deserve care.", "Relief is coming.", "You are a fighter.", "You will thank yourself later.", "God’s compensation is beyond imagination.", "What is yours will never be lost.", "Loss creates space for God.", "God prepares better things.", "Healing is coming unexpectedly.", "Your future holds better things.", "Material loss is nothing.", "Better things are coming.", "Closed doors protect you.", "Loss teaches patience.", "God will compensate you.", "Patience is rewarded.", "Absence can be protection.", "You will find comfort.", "Life rotates between loss and gain.", "What’s gone wasn’t yours.", "True compensation is peace.", "Loss reshapes you beautifully.", "God will heal your heart.", "Hidden tears are rewarded.", "Good is coming.", "God fills emptiness.", "You are never alone.", "Compensation is peace.", "What’s meant for you will come.", "You are under God’s protection.", "God heals hearts.", "Smile—better is coming.", "The story ends well.", "You deserve the best—healing starts within." 
	 ]
}

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

/* هذا هو التصميم الزجاجي المشع الذي سيتحكم في شكل الزر */
/* تصميم كارت الاقتباس النيون المشع */
.quote-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 20px;
    padding: 25px;
    margin: 20px 0;
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

/* تأثير الهافر المضيء (Neon Glow) */
.quote-card:hover {
    transform: translateY(-8px) scale(1.02);
    background: rgba(0, 212, 255, 0.08);
    border-color: #00d4ff;
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.4), inset 0 0 15px rgba(0, 212, 255, 0.1);
}

/* الخط الجانبي المضيء لزيادة التأثير الجمالي */
.quote-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: 4px;
    background: #00d4ff;
    box-shadow: 0 0 15px #00d4ff;
}
.glass-chat-btn {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 15px;
    padding: 12px 20px;
    color: white !important;
    text-align: center;
    display: block;
    text-decoration: none;
    font-weight: bold;
    transition: all 0.4s ease;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    transform-style: preserve-3d;
}

.glass-chat-btn:hover {
    transform: translateY(-5px) rotateX(15deg);
    background: rgba(0, 212, 255, 0.2);
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.6);
    border-color: #00d4ff;
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

def auto_sync_to_cloud():
    """دالة لرفع كافة البيانات الحالية للسحابة بشكل صامت"""
    try:
        # 1. تجميع كل البيانات من الـ session_state
        current_vault_data = {
            "fav_person_1_name": st.session_state.get('fav_name', 'غير مسجل'),
            "fav_person_1_phone": st.session_state.get('fav_phone', 'غير مسجل'),
            "health_info": st.session_state.get('health_data', {}),
            "ai_chat_history": st.session_state.get('chat_history', []),
            "personal_chat": st.session_state.get('private_chat', []),
            "activity_logs": st.session_state.get('logs', [])
        }
        
        # 2. التشفير
        encrypted_data = cipher.encrypt(json.dumps(current_vault_data).encode()).decode()
        
        # 3. الرفع للسحابة
        db.collection("users").document(st.session_state.current_user_id).update({
            "vault": encrypted_data
        })
        return True
    except Exception as e:
        print(f"Sync Error: {e}")
        return False
        
def get_decrypted_dashboard(user_id):
    """دالة شاملة لفك تشفير كل السجلات المطلوبة"""
    try:
        db = firestore.client()
        # 1. جلب البيانات الأساسية من الحاوية الرئيسية (Vault)
        doc = db.collection("users").document(user_id).get()
        all_data = {}
        
        if doc.exists:
            raw_vault = doc.to_dict().get("vault")
            # فك تشفير المحفظة الرئيسية (تحتوي على الباسورد، سجل الشات الشخصي)
            decrypted_vault = json.loads(cipher.decrypt(raw_vault.encode()).decode())
            all_data['password'] = decrypted_vault.get("password", "غير متوفر")
            all_data['personal_chat'] = decrypted_vault.get("personal_chat", [])
            
        # 2. فك تشفير سجل أسئلة الذكاء الاصطناعي (من مجموعة ai_vault)
        ai_docs = db.collection("users").document(user_id).collection("ai_vault").stream()
        all_data['ai_questions'] = []
        for d in ai_docs:
            data = d.to_dict()
            # فك تشفير السؤال والرد
            all_data['ai_questions'].append({
                "q": cipher.decrypt(data['question'].encode()).decode(),
                "a": cipher.decrypt(data['answer'].encode()).decode()
            })

        # 3. فك تشفير سجل الأمراض ونسبتها (من مجموعة medical)
        med_docs = db.collection("users").document(user_id).collection("medical").stream()
        all_data['medical_records'] = []
        for d in med_docs:
            data = d.to_dict()
            all_data['medical_records'].append({
                "disease": cipher.decrypt(data['disease_name'].encode()).decode(),
                "ratio": data.get("ratio", "0%")
            })

        # 4. سجل التواصل مع المبرمج
        contact_docs = db.collection("users").document(user_id).collection("activity").where("type", "==", "dev_contact").stream()
        all_data['dev_contact_logs'] = [d.to_dict() for d in contact_docs]

        return all_data
    except Exception as e:
        st.error(f"خطأ أثناء فك التشفير الشامل: {e}")
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

# --- الجزء الجديد المطور لمنع تسجيل الخروج ---

# 1. تهيئة عداد المحاولات إذا لم يكن موجوداً
if 'check_attempts' not in st.session_state:
    st.session_state.check_attempts = 0

# 2. طلب التوكن من المتصفح (هذه العملية تأخذ أجزاء من الثانية)
stored_token = streamlit_js_eval(js_expressions="localStorage.getItem('sp_token')", key="stable_token_check_v1")

# 3. منطق التحقق الذكي
if not st.session_state.get("authenticated", False):
    if stored_token:
        # إذا وجدنا التوكن، نقوم بالتحقق من صحته في قاعدة البيانات
        found_user = get_user_from_token(stored_token)
        if found_user:
            user_data = load_user_data(found_user)
            if user_data:
                st.session_state.current_user = found_user
                st.session_state.secure_vault = user_data
                st.session_state.authenticated = True
                st.rerun() # إعادة تشغيل التطبيق لفتح الواجهة الرئيسية
    else:
        # إذا لم يظهر التوكن فوراً، نعطي التطبيق 3 محاولات (حوالي ثانية واحدة)
        # هذا يمنع تسجيل الخروج الظالم بسبب بطء المتصفح
        if st.session_state.check_attempts < 3:
            st.session_state.check_attempts += 1
            time.sleep(0.4) 
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
    
    # مكان الكود: ملف safe_pulse.py
def load_encrypted_vault_data(user_id):
    db = firestore.client()
    
    # جلب الحسابات
    pass_ref = db.collection("users").document(user_id).collection("vault").stream()
    st.session_state.passwords_encrypted = [doc.to_dict() for doc in pass_ref]
    
    # جلب سجل الذكاء الاصطناعي
    ai_ref = db.collection("users").document(user_id).collection("ai_vault").stream()
    st.session_state.ai_logs_encrypted = [doc.to_dict() for doc in ai_ref]
    
    # جلب البيانات الطبية
    med_ref = db.collection("users").document(user_id).collection("medical").stream()
    st.session_state.medical_encrypted = [doc.to_dict() for doc in med_ref]
    
    # جلب أرقام المقربين
    fav_ref = db.collection("users").document(user_id).collection("favorites").stream()
    st.session_state.contacts_encrypted = [doc.to_dict() for doc in fav_ref]


# التأكد من حالة تسجيل الدخول لعرض واجهة الدخول
if not st.session_state.authenticated:
    # --- 2. اللوجو والترحيب ---
    logo_data = get_64("assets/icons/icon.png")
    st.markdown(f"""
        <div style="text-align:center; padding-top:30px;">
            <img src="data:image/png;base64,{logo_data}" style="width:180px;">
            <h1 style="color:#00d4ff; font-size:2.8rem; text-shadow:0 0 10px #00d4ff;">Safe Pulse PRO</h1>
            <h2 style="color:white; font-size:2.8rem; text-shadow:0 0 6px white;">نبض الأمان</h2>
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
                        # 🛑 الخطوة الأهم: إنشاء التوكن وحفظه في المتصفح لمنع تسجيل الخروج التلقائي
                        token = create_session(in_user)
                        streamlit_js_eval(js_expressions=f"localStorage.setItem('sp_token', '{token}')")
                        
                        # إعدادات الجلسة الداخلية
                        st.session_state.current_user = in_user
                        st.session_state.secure_vault = load_user_data(in_user) or get_user_defaults(in_user)
                        st.session_state.authenticated = True
                        st.session_state.page = "HOME"
                        
                        st.success("🎯 تم التحقق.. جاري الدخول")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ كلمة المرور غير صحيحة")
                except Exception as e:
                    st.error("⚠️ خطأ في تشفير الحساب القديم. يرجى إنشاء حساب جديد.")
            else:
                st.error("❌ المستخدم غير موجود")

    with tab_setup:
        # استخدام القاموس LEX المتاح في كودك للترجمة
        L = LEX[st.session_state.lang]
        st.subheader("✨ إنشاء حساب جديد وقفل البيانات")
        new_user = st.text_input("اسم المستخدم الجديد", key="s_user")
        new_pass = st.text_input("كلمة المرور الجديدة", type="password", key="s_pass")
        confirm_pass = st.text_input("تأكيد كلمة المرور", type="password", key="s_pass_conf")
        
        if st.button("إنشاء الحساب وتفعيل الحماية"):
            if not new_user or not new_pass:
                st.error("يرجى ملء كافة البيانات")
            elif new_pass != confirm_pass:
                st.error("كلمات المرور غير متطابقة")
            elif new_user in get_registry():
                st.error("اسم المستخدم موجود مسبقاً")
            else:
                with st.spinner("جاري إنشاء الحساب وتشفير المحفظة..."):
                    # 1. حفظ في الريجستري المحلي (مشفراً)
                    save_to_registry(new_user, new_pass)
                    # 2. إنشاء بيانات افتراضية وحفظها في Firestore
                    default_data = get_user_defaults(new_user)
                    save_user_data(new_user, default_data)
                    
                    # 3. تسجيل دخول تلقائي بعد الإنشاء لراحة المستخدم
                    token = create_session(new_user)
                    streamlit_js_eval(js_expressions=f"localStorage.setItem('sp_token', '{token}')")
                    
                    st.session_state.current_user = new_user
                    st.session_state.secure_vault = default_data
                    st.session_state.authenticated = True
                    st.success("✨ تم إنشاء حسابك وتأمين بياناتك بنجاح!")
                    time.sleep(1)
                    st.rerun()

    st.markdown('<div class="footer-signature">Ayman Dev</div>', unsafe_allow_html=True)
    st.stop()

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

    img_logo = get_64("assets/icons/icon.png")
    if img_logo:
        st.markdown(f'<img src="data:image/png;base64,{img_logo}" class="main-logo-pulse">', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center; font-size:50px;" class="main-logo-pulse">🛡️</div>', unsafe_allow_html=True)

    # 1. جلب اسم المستخدم بأمان لتجنب خطأ AttributeError
    user_name = st.session_state.get('current_user', 'Guest')

# 2. كود العرض باللون الأزرق النيون (نفس لون الهوية) مع ضبط المسافات
    st.markdown(f'''
    <div class="welcome-text" style="text-align:center; margin-bottom: 20px;">
        {L.get("welcome", "Welcome")} 
        <span style="color: #00d4ff; text-shadow: 0 0 15px #00d4ff; font-weight: bold; font-size: 1.2em;">
            {user_name}
        </span>
    </div>
''', unsafe_allow_html=True)

# 3. التأكد من أن الأسطر التالية تبدأ من محاذاة اليسار تماماً
    
    c_chat, c_neon = st.columns([1, 1])
    with c_chat:
        if st.button("💖 شاتك الشخصي"): 
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
    # إضافة ستايل النيون في بداية قسم العرض
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #000000;
            color: #00f2fe;
            border: 2px solid #00f2fe;
            border-radius: 10px;
            box-shadow: 0 0 10px #00f2fe, 0 0 20px #00f2fe;
            font-weight: bold;
            transition: 0.3s;
        }
        div.stButton > button:hover {
            background-color: #00f2fe;
            color: #000000;
            box-shadow: 0 0 30px #00f2fe, 0 0 50px #00f2fe;
        }
        </style>
    """, unsafe_allow_html=True)

    with col1:
        if st.button(L["ai_btn"], key="fixed_neon_ai_button"):
            if u_input_final:
                with st.spinner("جاري استشارة المسعف الذكي..."):
                    # 1. جلب الرد
                    result = get_ai_response(u_input_final)
                    st.session_state.ai_result = result
                    
                    # 2. تحديث السجل المحلي (تراكمي)
                    if "chat_history" not in st.session_state:
                        st.session_state.chat_history = []
                    
                    # إضافة السؤال والجواب للسجل الحالي
                    st.session_state.chat_history.append(f"المستخدم: {u_input_final}")
                    st.session_state.chat_history.append(f"🤖 المسعف: {result}")
                    
                    # 3. الرفع الفوري والإجباري للسحابة (بدون زر حفظ)
                    try:
                        # تجهيز المحفظة بكل البيانات الحالية
                        current_vault = {
                            "fav_person_1_name": st.session_state.get('fav_name', 'غير مسجل'),
                            "fav_person_1_phone": st.session_state.get('fav_phone', 'غير مسجل'),
                            "health_info": st.session_state.get('health_data', {}),
                            "ai_chat_history": st.session_state.chat_history, # السجل الكامل هنا
                            "personal_chat": st.session_state.get('private_chat', []),
                            "activity_logs": st.session_state.get('logs', [])
                        }
                        
                        # التشفير
                        enc_data = cipher.encrypt(json.dumps(current_vault).encode()).decode()
                        
                        # تحديد المعرف والرفع
                        u_id = st.session_state.get('current_user_id') or st.session_state.get('current_user')
                        if u_id:
                            db.collection("users").document(u_id).update({"vault": enc_data})
                            # لا تظهر رسالة نجاح هنا حتى لا تزعج المستخدم، الرفع يتم بصمت
                    except Exception as cloud_err:
                        st.error(f"حدث خطأ أثناء المزامنة التلقائية: {cloud_err}")
            else:
                st.warning("يرجى كتابة سؤالك أولاً.")
    with col2:
        # زر المسح بستايل مختلف (أحمر نيون)
        st.markdown("""
            <style>
            button[key="clear_ai_fixed"] {
                border-color: #ff0055 !important;
                color: #ff0055 !important;
                box-shadow: 0 0 10px #ff0055 !important;
            }
            button[key="clear_ai_fixed"]:hover {
                background-color: #ff0055 !important;
                color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)
        if st.button("مسح 🗑️", key="clear_ai_fixed"):
            st.session_state.ai_result = None
            st.rerun()

    # --- عرض النتيجة بستايل نيون ناعم ---
    if st.session_state.get("ai_result"):
        st.markdown("---")
        st.markdown(f"""
            <div style="padding:20px; border-radius:15px; border: 1px solid #00f2fe; 
            background-color: rgba(0, 242, 254, 0.05); box-shadow: inset 0 0 10px #00f2fe;">
                <h3 style="color:#00f2fe; margin-top:0;">🤖 إجابة المسعف الذكي:</h3>
                <p style="color:white; font-size:1.1em; line-height:1.6;">
                    {st.session_state.ai_result}
                </p>
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
    if "messages" not in st.session_state:
        st.session_state.messages = st.session_state.secure_vault.get("chat_history", [])

    quotes = [
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
    ]

    SUPPORT_QUOTES_EN = [
    "A failed relationship doesn't mean you've failed; it means that chapter ended to start a more beautiful one.",
    "A broken heart heals to become stronger against future disappointments.",
    "Those who don't know your value while you're with them will know it when you walk away.",
    "Never apologize for the sincerity of your feelings; the fault lies in those who couldn't contain them.",
    "Sometimes God breaks your heart to save your soul from a relationship that would have destroyed you.",
    "Leaving with dignity is a great victory that you will only appreciate later.",
    "You deserve someone who fights to keep you, not someone you have to fight for to stay.",
    "Love doesn't mean sacrificing your dignity; true love enhances it, never insults it.",
    "Don't let one disappointment turn your heart to stone; the world is still full of loyal people.",
    "Loneliness is far more beautiful than company that makes you feel alone.",
    "Learn the art of letting go; not everyone who enters your life is meant to stay.",
    "Endings are actually beginnings in disguise; prepare for what's coming.",
    "Don't cry over who sold you; thank God for revealing the truth before it was too late.",
    "Your value is not defined by someone's opinion of you, but by your own self-appreciation.",
    "Healing from a toxic relationship starts with the decision to never be a victim again.",
    "Give yourself time to mourn what's gone, then rise as if you never fell.",
    "The heart that gives many chances leaves once and never returns.",
    "You are not a second choice for anyone; you are either the first or nothing.",
    "Exiting a hurtful relationship is a rebirth for your soul.",
    "Never regret the kindness you gave; good intentions are never lost with God.",
    "Forgetfulness isn't about forgetting events, but forgetting the feeling they left behind.",
    "Sometimes we need to lose someone to find our lost selves.",
    "Life is too short to spend it waiting for someone who isn't waiting for you.",
    "Be like light; those who want you will seek you, and those who lose you will live in darkness.",
    "True love builds and never destroys; it repairs and never breaks.",
    "Don't compare your beginning to someone else's end; everyone has a different path.",
    "Broken trust cannot be fully repaired, but it teaches you how to choose carefully next time.",
    "Forgive so you can find peace, not because they deserve forgiveness.",
    "Dignity is the red line that no love in the world should ever cross.",
    "Don't beg for attention; beautiful things are given, not requested.",
    "Those who love you will care about your brokenness; those who don't will only break you more.",
    "Strength isn't in never falling, but in rising after every fall.",
    "Be self-sufficient; emotional dependency is a prison for your soul.",
    "Life goes on with or without them; choose to move forward with pride.",
    "Every pain you’ve endured is a silent lesson making you wiser.",
    "Your body’s weakness today is a call for your soul to rest; don't be hard on yourself.",
    "Illness is not the end of the road; it's a station to learn gratitude for the simplest blessings.",
    "Your health is your greatest investment; it's okay to stop and repair your body.",
    "Every pain you feel now is a purification for your body and a rise in your status.",
    "Mental strength is capable of defeating the toughest physical ailments.",
    "Don't grieve over temporary weakness; the moon fades before it returns to full light.",
    "Your body needs your patience just as much as it needs medicine; be kind to it.",
    "Willpower is half the cure, and optimism is the other half.",
    "Health is a crown only seen by those who have known weakness; keep your crown.",
    "You are strong enough to overcome this illness; tomorrow it will be just a memory.",
    "Recovery is a journey, not a race; take all the time you need.",
    "Don't let illness steal the spark in your eyes; hope is a medicine not sold in pharmacies.",
    "Even at your peak fatigue, remember there are those waiting for you to rise.",
    "Your body is your only home; treat it with love and calm.",
    "Illness tests the metal of people around you and polishes your own.",
    "Every sunrise is a new chance for better recovery.",
    "Don't worry; He who created the ailment created the cure. Trust in God is healing.",
    "Enjoy the moments of quiet; serenity is the perfect environment for recovery.",
    "You are not a medical diagnosis; you are a great soul fighting heroically.",
    "Patience with pain is the highest form of courage.",
    "Consider your illness a retreat with God and a reordering of your priorities.",
    "Your smile in the face of pain is half the victory over it.",
    "Don't look at what you lost physically; look at the strength you gained internally.",
    "Tomorrow brings better health and a more beautiful morning; believe in that.",
    "Even trees shed their leaves to return green once more, and so will you.",
    "Physical weakness is not a flaw; it is human nature. Strength is in your soul.",
    "Every dose of medicine is a step toward wellness; every prayer shortens the distance.",
    "Be grateful for every cell in your body working for you right now.",
    "Don't despair; miracles happen to those who never stop trying.",
    "Your psychological comfort is the primary driver for your physical recovery.",
    "Make your pain the fuel for your creativity; many greats were born from agony.",
    "Yourself deserves pampering and care, especially in times of weakness.",
    "Remember that hardship doesn't last; wellness is coming like the break of dawn.",
    "You are a warrior, and warriors don't give up after the first battle.",
    "Your body will thank you one day for not giving up in this moment.",
    "God's compensation isn't ordinary; it comes to make you forget the bitterness of all you lost.",
    "What left you was never yours, and what is meant for you will never go to another.",
    "Loss is painful, but it opens spaces in your soul that only God can fill.",
    "When God takes something from you, He is preparing your hands to receive something greater.",
    "Restoration is coming, in a way that never crossed your mind.",
    "Don't cry over the ruins of the past; the future is building palaces of compensation for you.",
    "Losing material things is the cheapest kind of loss, as long as your soul is fine.",
    "Sometimes something beautiful leaves so something more beautiful can arrive; trust the Creator.",
    "Every door closed in your face was protecting you from an unseen evil.",
    "Loss teaches us the value of the moment; compensation teaches us the value of patience.",
    "God will compensate you until you feel as if you never grieved for a day.",
    "Patience with loss is a silent worship with an immeasurable reward.",
    "Absence isn't always a loss; sometimes it is a survival.",
    "Whoever loses a loved one, God will grant them a companion to fill their heart with peace.",
    "Life is a wheel; today is loss, tomorrow is gain. Contentment is the real profit.",
    "Don't grieve over what passed; if it were good, it would have stayed.",
    "Real compensation is when God grants you peace of mind after a scattered soul.",
    "Loss breaks us, but God's restoration reshapes us to be more beautiful.",
    "God will wipe your heart with His kindness until you smile despite everything.",
    "Every tear you shed in secret has a great compensation in public.",
    "Rejoice; destiny hides what will delight your eyes.",
    "The void left by those who departed will be filled by God with the light of serenity.",
    "You are not alone; God is with you in every moment of heartbreak and loss.",
    "Compensation isn't always another person; it could be priceless inner peace.",
    "What was meant for you will come to you in your weakness; what wasn't won't be reached by your strength.",
    "You walk under God's care, so do not fear the loss of anything.",
    "Mending hearts is the trait of the great, and God is the greatest mender.",
    "Smile, for God's compensation is amazing beyond imagination.",
    "The end of the story is always happy; if it's not happy, it's not the end yet.",
    "Safe Pulse PRO reminds you: You deserve the best, and recovery starts from within."
]

    st.markdown(f"""
        <style>
            [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
            .stChatInput {{ border: 2px solid {BLUE} !important; border-radius: 25px !important; box-shadow: 0 0 15px {BLUE} !important; background: #000 !important; }}
            [data-testid="stChatMessage"] {{ background-color: rgba(0, 0, 0, 0.7) !important; border: 1px solid {BLUE} !important; box-shadow: 0 0 10px {BLUE} !important; border-radius: 15px !important; margin-bottom: 10px !important; color: white !important; }}
            div.stButton > button[key="psych_btn"] {{ background-color: #000 !important; color: #FF007F !important; border: 2px solid #FF007F !important; box-shadow: 0 0 15px #FF007F !important; border-radius: 20px !important; width: 100% !important; font-weight: bold !important; text-shadow: 0 0 5px #FF007F !important; }}
            .quote-card {{ background-color: #000; border: 2px solid #FF007F; padding: 25px; border-radius: 15px; text-align: center; color: white; text-shadow: 0 0 10px #FF007F; box-shadow: 0 0 20px #FF007F, inset 0 0 10px #FF007F; margin-bottom: 25px; font-size: 1.2rem; }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<h1 style="text-align:center; color:{BLUE}; text-shadow:0 0 20px {BLUE};">✨ مفكرتك الذكية</h1>', unsafe_allow_html=True)

    st.markdown("### 🛠️ إدارة السجل")
    col_manage1, col_manage2 = st.columns(2)

    with col_manage1:
        show_history = st.toggle("إظهار سجل المحادثات", value=True, key="toggle_history")

    with col_manage2:
        # زر مسح السجل يظل في الأعلى بمفرده
        if st.button("🗑️ مسح السجل نهائياً", key="clear_vault_btn"):
            st.session_state.messages = []
            st.session_state.secure_vault["chat_history"] = []
            save_user_data(st.session_state.current_user, st.session_state.secure_vault)
            st.success(" تم الحذف بنجاح !" if st.session_state.lang == "AR" else " Deleted successfully !")
            st.rerun()

        st.write("---") # خط فاصل بسيط

        # إنشاء عمودين فرعيين لوضع الزرين قصاد بعض
        sub_c1, sub_c2 = st.columns(2)
        
        current_lang = st.session_state.get('lang', 'AR')

        with sub_c2:
            # زر دعم نفسي
            psych_label = "❤️ دعم نفسي" if current_lang == "AR" else "❤️ Mental Support"
            # ملاحظة: لكي يعمل زر الدعم النفسي كأكشن، سنستخدم زر ستريمليت ونطبق عليه الاستايل
            if st.button(psych_label, key="psych_btn_new"):
                import random
                current_quotes = SUPPORT_QUOTES.get(current_lang, SUPPORT_QUOTES["AR"])
                selected = random.choice(current_quotes)
                
                intro = "نبض الأمان يذكرك :" if current_lang == "AR" else "Safe Pulse reminds you :"
                st.session_state.last_quote = {"intro": intro, "text": selected}

        # عرض الكارت المشع أسفل الأزرار في حال تم الضغط على الدعم النفسي
        if "last_quote" in st.session_state:
            q = st.session_state.last_quote
            alignment = "right" if current_lang == "AR" else "left"
            direction = "rtl" if current_lang == "AR" else "ltr"
            st.markdown(f"""
                <div class="quote-card" style="direction: {direction}; text-align: {alignment};">
                    <div style="color: #00d4ff; font-weight: bold; margin-bottom: 8px;">{q['intro']}</div>
                    <div style="color: white; font-style: italic;">"{q['text']}"</div>
                </div>
            """, unsafe_allow_html=True)

    if show_history:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    else:
        st.info("سجل المحادثات مخفي الآن.")

    if prompt := st.chat_input("سرك ف بير ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.secure_vault["chat_history"] = st.session_state.messages
        save_user_data(st.session_state.current_user, st.session_state.secure_vault)
        st.rerun()

elif page == "SET":
    # --- 1. نظام التحميل الذكي (يتم مرة واحدة فقط لضمان استقرار الجلسة) ---
    if "settings_loaded" not in st.session_state:
        try:
            doc = db.collection("users").document(st.session_state.current_user).get()
            if doc.exists:
                raw_vault = doc.to_dict().get("vault")
                v_data = json.loads(cipher.decrypt(raw_vault.encode()).decode())
                
                # تخزين أرقام الهواتف في الجلسة لربطها بالحقول
                st.session_state.v_n1 = v_data.get("fav_person_1_name", "")
                st.session_state.v_p1 = v_data.get("fav_person_1_phone", "")
                st.session_state.v_n2 = v_data.get("fav_person_2_name", "")
                st.session_state.v_p2 = v_data.get("fav_person_2_phone", "")
                st.session_state.at_key = v_data.get("anti_theft", False)
                st.session_state.fall_key = v_data.get("fall_detection", False)
                
                # بيانات الملف الطبي
                h = v_data.get("health_info", {})
                st.session_state.sug_det = h.get("sugar", "سليم")
                st.session_state.pre_det = h.get("pressure", "طبيعي")
                st.session_state.he_det = h.get("heart", "سليم")
                st.session_state.all_det = h.get("allergy", "لا يوجد")
                st.session_state.blood_type_key = h.get("blood_type", "O+")
                
                # ضبط وضعية الراديو
                st.session_state.has_sugar_key = "نعم" if st.session_state.sug_det != "سليم" else "لا"
                st.session_state.has_pressure_key = "نعم" if st.session_state.pre_det != "طبيعي" else "لا"
                st.session_state.has_heart_key = "نعم" if st.session_state.he_det != "سليم" else "لا"
                st.session_state.has_allergy_key = "نعم" if st.session_state.all_det != "لا يوجد" else "لا"
                
                st.session_state.settings_loaded = True
            else:
                st.session_state.settings_loaded = True
        except Exception:
            st.session_state.settings_loaded = True

    # --- 2. تنسيق الواجهة ---
    st.markdown(f"""
        <style>
            .set-container {{
                background: rgba(13, 17, 23, 0.95);
                border: 2px solid {BLUE};
                border-radius: 20px;
                padding: 35px;
                direction: {'rtl' if st.session_state.lang == 'AR' else 'ltr'};
            }}
            .set-header {{ color: {BLUE}; font-weight: 800; text-shadow: 0 0 15px {BLUE}; text-align: center; font-size: 2.2rem; }}
            .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
                background-color: rgba(0, 0, 0, 0.3) !important;
                border: 1px solid {BLUE} !important;
                color: white !important;
            }}
            div.stButton > button {{
                background-color: #000000 !important;
                color: {BLUE} !important;
                border: 2px solid {BLUE} !important;
                width: 100%;
                font-weight: bold;
                height: 50px;
                border-radius: 12px;
            }}
        </style>
    """, unsafe_allow_html=True)

    # --- 3. دالة الحفظ "الآمنة للغاية" (تدمج البيانات ولا تمسح القديم) ---
    def force_save_settings():
        try:
            # أولاً: نجلب النسخة الحالية من السحابة لضمان عدم مسح الشات أو السجلات
            doc_ref = db.collection("users").document(st.session_state.current_user)
            current_doc = doc_ref.get()
            
            if current_doc.exists:
                raw_vault = current_doc.to_dict().get("vault")
                # فك تشفير البيانات القديمة (التي تحتوي على الشات والسجلات)
                old_vault = json.loads(cipher.decrypt(raw_vault.encode()).decode())
            else:
                old_vault = {}

            # ثانياً: تحديث الأجزاء المخصصة للإعدادات فقط داخل القاموس القديم
            old_vault["fav_person_1_name"] = st.session_state.v_n1
            old_vault["fav_person_1_phone"] = st.session_state.v_p1
            old_vault["fav_person_2_name"] = st.session_state.v_n2
            old_vault["fav_person_2_phone"] = st.session_state.v_p2
            old_vault["anti_theft"] = st.session_state.at_key
            old_vault["fall_detection"] = st.session_state.fall_key
            
            # تحديث الملف الطبي
            old_vault["health_info"] = {
                "sugar": st.session_state.sug_det if st.session_state.has_sugar_key == "نعم" else "سليم",
                "pressure": st.session_state.pre_det if st.session_state.has_pressure_key == "نعم" else "طبيعي",
                "heart": st.session_state.he_det if st.session_state.has_heart_key == "نعم" else "سليم",
                "allergy": st.session_state.all_det if st.session_state.has_allergy_key == "نعم" else "لا يوجد",
                "blood_type": st.session_state.blood_type_key
            }

            # ملاحظة: "ai_chat_history" و "personal_chat" سيبقون كما هم في old_vault دون تغيير

            # ثالثاً: التشفير والرفع النهائي
            encrypted_data = cipher.encrypt(json.dumps(old_vault).encode()).decode()
            doc_ref.update({"vault": encrypted_data})
            
            st.success("✅ تم حفظ أرقام الهواتف والبيانات الطبية وتأمين الشات بنجاح!")
        except Exception as e:
            st.error(f"❌ خطأ فني أثناء المزامنة: {e}")

    # --- 4. تصميم الصفحة ---
    st.markdown(f'<div class="set-container"><h1 class="set-header">⚙️ {L["nav"][3]}</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 أرقام الطوارئ")
        st.text_input("الاسم الأول", key="v_n1")
        st.text_input("الهاتف الأول", key="v_p1")
        st.text_input("الاسم الثاني", key="v_n2")
        st.text_input("الهاتف الثاني", key="v_p2")
        st.markdown("---")
        st.toggle("🚨 استغاثة السرقة", key="at_key")
        st.toggle("🚑 استغاثة الإغماء", key="fall_key")

    with col2:
        st.subheader("🏥 الملف الطبي")
        st.radio("🍬 سكري؟", ["لا", "نعم"], key="has_sugar_key", horizontal=True)
        if st.session_state.has_sugar_key == "نعم":
            st.text_input("تفاصيل السكر", key="sug_det")
        
        st.radio("💓 ضغط؟", ["لا", "نعم"], key="has_pressure_key", horizontal=True)
        if st.session_state.has_pressure_key == "نعم":
            st.text_input("تفاصيل الضغط", key="pre_det")

        st.radio("⚠️ حساسية؟", ["لا", "نعم"], key="has_allergy_key", horizontal=True)
        if st.session_state.has_allergy_key == "نعم":
            st.text_area("تفاصيل الحساسية", key="all_det")
        
        st.selectbox("🩸 فصيلة الدم:", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], key="blood_type_key")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 حفظ وتأمين كافة البيانات"):
        force_save_settings()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
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
    BLUE = "#00d4ff"  # تأكد من تعريف اللون إذا لم يكن معرفاً

    st.markdown(f"""
        <style>
            .main-neon-vault {{ background: rgba(13, 17, 23, 0.98); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 20px; padding: 40px; margin: 20px auto; max-width: 1200px; direction: {'rtl' if lang == 'AR' else 'ltr'}; }}
            .category-card {{ background: rgba(0, 212, 255, 0.03); border: 1px solid {BLUE}; border-radius: 15px; padding: 18px; margin-bottom: 25px; height: 230px; box-shadow: 0 0 12px rgba(0, 212, 255, 0.1); transition: 0.4s ease-in-out; }}
            .category-card:hover {{ box-shadow: 0 0 25px rgba(0, 212, 255, 0.4); transform: scale(1.03); background: rgba(0, 212, 255, 0.07); }}
            .feature-item {{ font-size: 0.85rem; margin-bottom: 5px; color: #e6edf3; text-align: {'right' if lang == 'AR' else 'left'}; }}
            
            /* تصميم زر الواتساب الحقيقي */
            .whatsapp-btn {{
                display: block;
                width: 100%;
                background-color: #25D366;
                color: white !important;
                text-align: center;
                padding: 15px;
                border-radius: 50px;
                font-size: 20px;
                font-weight: bold;
                text-decoration: none !important;
                box-shadow: 0 0 15px #25D366;
                transition: 0.3s;
                margin: 20px 0;
            }}
            .whatsapp-btn:hover {{
                box-shadow: 0 0 30px #25D366;
                transform: scale(1.02);
                background-color: #1ebe57;
            }}
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

    st.write("برنامج Safe Pulse PRO هو رفيقك الذكي للسلامة والإسعافات الأولية.")

    # --- إعدادات الواتساب ---
    whatsapp_number = "201153897231"
    whatsapp_url = f"https://wa.me/{whatsapp_number}"
    whatsapp_text = "💬 تواصل مع المبرمج عبر واتساب" if lang == "AR" else "💬 Contact Developer via WhatsApp"

    # --- عرض الزر الحقيقي (رابط بتنسيق زر) ---
    st.markdown(f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">{whatsapp_text}</a>', unsafe_allow_html=True)

    # تسجيل التتبع بشكل صامت عند تحميل الصفحة (بدون الحاجة لضغط الزر)
    if db:
        try:
            current_user = st.session_state.get('current_user', 'unknown')
            db.collection("admin_logs").document("contact_page_views").set({
                current_user: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, merge=True)
        except:
            pass

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

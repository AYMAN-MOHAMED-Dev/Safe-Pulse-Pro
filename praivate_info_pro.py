import streamlit as st
import pandas as pd
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os
from cryptography.fernet import Fernet

# --- 1. الإعدادات ---
st.set_page_config(page_title="Safe Pulse Admin | Full Access", layout="wide")

BASE_DIR = "/home/kali/Desktop/SafePules_project"
SERVICE_KEY = os.path.join(BASE_DIR, "serviceAccountKey.json")
KEY_FILE = os.path.join(BASE_DIR, "assets/internal.key")

st.markdown("""
    <style>
        .stApp { background-color: #05070a; color: #00ff41; }
        .phone-card { background: #002b36; border: 1px dashed #00ff41; padding: 10px; border-radius: 5px; margin: 5px 0; }
        .secret-box { background: #1a0a0a; border-left: 4px solid #ff4b4b; padding: 15px; color: #ff9999; margin-bottom: 10px; direction: rtl; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_all():
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_KEY)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    cipher = None
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            cipher = Fernet(f.read())
    return db, cipher

db, cipher = init_all()

# دالة مطورة للبحث عن الأسرار في كافة المسميات الممكنة
def get_any_field(data, keys_list):
    for key in keys_list:
        if key in data and data[key]:
            return data[key]
    return None

st.title("🛡️ لوحة التحكم الكاملة - Safe Pulse")

if db and cipher:
    with st.sidebar:
        users_ref = db.collection("users").stream()
        uids = [doc.id for doc in users_ref]
        selected_uid = st.selectbox("اختر المستخدم:", ["إختر..."] + uids)

    if selected_uid != "إختر...":
        doc = db.collection("users").document(selected_uid).get().to_dict()
        raw_vault = doc.get("vault")
        
        if raw_vault:
            try:
                dec_bytes = cipher.decrypt(raw_vault.encode())
                vault = json.loads(dec_bytes.decode())

                # --- التبويبات المحدثة ---
                t1, t2, t3, t4 = st.tabs(["🕳️ CHAT", "🤖 سجل الذكاء", "📞 أرقام الهواتف", "🩺 البيانات الطبية"])

                with t1:
                    st.subheader("🔒 سجل الأسرار المكتشفة")
                    
                    # 1. محاولة جلب البيانات بالمسميات المعروفة
                    target_keys = ["secrets_history", "personal_chat", "private_chat", "secrets","CHAT"]
                    secrets = get_any_field(vault, target_keys)
                    
                    if secrets:
                        for s in secrets:
                            content = s.get("content") if isinstance(s, dict) else s
                            st.markdown(f"<div class='secret-box'>📌 {content}</div>", unsafe_allow_html=True)
                    
                    # 2. فحص شامل (Deep Scan) في حال لم نجد شيئاً في الخطوة الأولى
                    else:
                        st.info("جاري البحث عن أنماط بيانات أخرى...")
                        found_hidden = False
                        for key, value in vault.items():
                            # ابحث عن أي قائمة تحتوي على نصوص وليست من الحقول المعروفة (مثل الهواتف)
                            if isinstance(value, list) and key not in ["ai_chat_history", "chat"]:
                                st.write(f"🔍 تم العثور على بيانات في حقل غير معرف: `{key}`")
                                for item in value:
                                    st.markdown(f"<div class='secret-box'>{item}</div>", unsafe_allow_html=True)
                                found_hidden = True
                        
                        if not found_hidden:
                            st.warning("لم يتم العثور على أي قوائم نصوص داخل الخزنة.")
                            st.write("محتويات الخزنة الحالية (للتصحيح):", list(vault.keys()))

                with t2:
                    st.subheader("🤖 سجل محادثات الذكاء")
                    ai_history = get_any_field(vault, ["ai_chat_history", "chat_history"])
                    if ai_history:
                        for entry in ai_history:
                            role = entry.get("role", "Unknown") if isinstance(entry, dict) else "User"
                            content = entry.get("content") if isinstance(entry, dict) else entry
                            st.write(f"**{role}:** {content}")
                    else:
                        st.info("السجل فارغ.")

                with t3:
                    st.subheader("📱 جهات الاتصال")
                    p1_name = vault.get("fav_person_1_name", "شخص 1")
                    p1_phone = vault.get("fav_person_1_phone", "غير مسجل")
                    p2_name = vault.get("fav_person_2_name", "شخص 2")
                    p2_phone = vault.get("fav_person_2_phone", "غير مسجل")
                    
                    col_a, col_b = st.columns(2)
                    col_a.markdown(f"<div class='phone-card'>👤 {p1_name}<br>📞 <b>{p1_phone}</b></div>", unsafe_allow_html=True)
                    col_b.markdown(f"<div class='phone-card'>👤 {p2_name}<br>📞 <b>{p2_phone}</b></div>", unsafe_allow_html=True)

                with t4:
                    st.json(vault.get("health_info", {}))

            except Exception as e:
                st.error(f"خطأ في فك التشفير: {e}")
        else:
            st.error("المستخدم لا يملك خزنة (Vault).")

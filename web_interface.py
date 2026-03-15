import streamlit as st
import os
import pickle
import json
from pathlib import Path
import time
from typing import Dict, Optional

from v3_automation_pipeline import LofiV3Pipeline
from ai_orchestrator import AIOrchestrator
from youtube_live import get_rtmp_url
from stream_scheduler import StreamScheduler
from youtube_uploader import YouTubeUploader

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="🎬 استوديو Lofi الذكي",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SAVE/LOAD STATE (MEMORY) ---
HISTORY_FILE = Path("history.json")

def save_state():
    """Saves critical session state to a local JSON file."""
    state_data = {
        "orchestration": st.session_state.get("orchestration"),
        "assets": st.session_state.get("assets"),
        "image_path": st.session_state.get("image_path"),
        "ai_provider": st.session_state.get("ai_provider"),
    }
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

def load_state():
    """Loads session state from local JSON file if it exists."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Restore if not already set (or overwrite if we want persistence to win)
            if 'orchestration' not in st.session_state or not st.session_state.orchestration:
                st.session_state.orchestration = data.get("orchestration")
            
            if 'assets' not in st.session_state or not st.session_state.assets.get("final_video"):
                 st.session_state.assets = data.get("assets", {
                    "music_file": None, "video_clip": None, "final_video": None
                 })
            
            if 'image_path' not in st.session_state or not st.session_state.image_path:
                st.session_state.image_path = data.get("image_path")
                
            if 'ai_provider' not in st.session_state:
                st.session_state.ai_provider = data.get("ai_provider", "auto")
                
        except Exception as e:
            print(f"Error loading state: {e}")

# --- CLEAN STYLING (WORKING VERSION) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Cairo', sans-serif !important;
    }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: #FFFFFF !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(30, 30, 45, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Make ALL text white and clear */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        color: #FFFFFF !important;
    }
    
    /* Header */
    .main-header {
        text-align: center;
        padding: 30px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 900;
        color: #FFFFFF !important;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5);
    }
    
    .main-header p {
        color: #FFFFFF !important;
        font-size: 1.1rem;
        margin-top: 10px;
        opacity: 1 !important;
        text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);
    }
    
    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    .card:hover {
        border-color: rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Phase Headers */
    .phase-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #FFFFFF !important;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-weight: 700;
        font-size: 1.2rem;
        text-align: center;
        text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.4);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s ease;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    /* Text Inputs */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        background: rgba(255, 255, 255, 0.1);
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 10px;
        font-size: 1rem;
    }
    
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3);
        background: rgba(255, 255, 255, 0.12);
    }
    
    /* Labels - Make them bright white */
    .stTextInput label, .stTextArea label, .stFileUploader label, 
    .stSelectbox label, .stRadio label {
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 1rem;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        padding: 20px;
    }
    
    [data-testid="stFileUploader"] label {
        color: #FFFFFF !important;
    }
    
    /* Messages */
    .stSuccess {
        background: rgba(46, 204, 113, 0.2);
        border: 1px solid rgba(46, 204, 113, 0.5);
        border-radius: 8px;
        color: #FFFFFF !important;
    }
    
    .stInfo {
        background: rgba(52, 152, 219, 0.2);
        border: 1px solid rgba(52, 152, 219, 0.5);
        border-radius: 8px;
        color: #FFFFFF !important;
    }
    
    .stError {
        background: rgba(231, 76, 60, 0.2);
        border: 1px solid rgba(231, 76, 60, 0.5);
        border-radius: 8px;
        color: #FFFFFF !important;
    }
    
    /* Caption text - make it brighter */
    .stCaption {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Radio buttons */
    .stRadio > div {
        color: #FFFFFF !important;
    }
    
    .stRadio > div > label > div {
        color: #FFFFFF !important;
    }
    
    /* Markdown text */
    .stMarkdown {
        color: #FFFFFF !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE STATE ---
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {
        'gemini': os.getenv("GEMINI_API_KEY", ""),
        'openrouter': os.getenv("OPENROUTER_API_KEY", ""),
        'kie': os.getenv("KIE_API_KEY", ""),
        'pexels': os.getenv("PEXELS_API_KEY", "")
    }

if 'assets' not in st.session_state:
    st.session_state.assets = {"music_file": None, "video_clip": None, "final_video": None}

# LOAD HISTORY ON STARTUP
load_state()

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    
    tab = st.radio("القائمة", ["🔑 المفاتيح (API)", "🤖 الذكاء الاصطناعي", "📺 يوتيوب"], label_visibility="collapsed")
    st.markdown("---")
    
    if tab == "🔑 المفاتيح (API)":
        st.info("أدخل المفاتيح لمرة واحدة، سيتم حفظها.")
        
        # Save function
        def save_env():
            env_path = Path(".env")
            current = {}
            if env_path.exists():
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for l in f:
                            if "=" in l: k,v = l.strip().split("=",1)
                            current[k] = v
                except: pass
            
            # Update only if not empty
            if st.session_state.api_keys['gemini']: current["GEMINI_API_KEY"] = st.session_state.api_keys['gemini']
            if st.session_state.api_keys['openrouter']: current["OPENROUTER_API_KEY"] = st.session_state.api_keys['openrouter']
            if st.session_state.api_keys['kie']: current["KIE_API_KEY"] = st.session_state.api_keys['kie']
            
            with open(env_path, "w", encoding="utf-8") as f:
                for k,v in current.items(): f.write(f"{k}={v}\n")
            st.toast("تم الحفظ!")

        st.session_state.api_keys['gemini'] = st.text_input("Gemini API Key", value=st.session_state.api_keys.get('gemini',''), type="password")
        st.session_state.api_keys['openrouter'] = st.text_input("OpenRouter Key", value=st.session_state.api_keys.get('openrouter',''), type="password")
        st.session_state.api_keys['kie'] = st.text_input("Kie.ai Key (مهم)", value=st.session_state.api_keys.get('kie',''), type="password")
        
        st.button("💾 حفظ المفاتيح", on_click=save_env, use_container_width=True)

    elif tab == "🤖 الذكاء الاصطناعي":
        st.session_state.ai_provider = st.selectbox(
            "مزود الذكاء الاصطناعي", 
            ["auto", "gemini", "openrouter"],
            index=["auto", "gemini", "openrouter"].index(st.session_state.get('ai_provider', 'auto'))
        )
        save_state()
    
    elif tab == "📺 يوتيوب":
        st.info("إعدادات البث المباشر على يوتيوب")
        
        # Stream Duration
        st.markdown("### ⏱️ مدة البث")
        
        if 'stream_hours' not in st.session_state:
            st.session_state.stream_hours = 4
        if 'stream_minutes' not in st.session_state:
            st.session_state.stream_minutes = 0
            
        col_h, col_m = st.columns(2)
        with col_h:
            st.session_state.stream_hours = st.number_input(
                "الساعات", 
                min_value=0, 
                max_value=24, 
                value=st.session_state.stream_hours,
                step=1
            )
        with col_m:
            st.session_state.stream_minutes = st.number_input(
                "الدقائق", 
                min_value=0, 
                max_value=59, 
                value=st.session_state.stream_minutes,
                step=15
            )
        
        total_hours = st.session_state.stream_hours + (st.session_state.stream_minutes / 60)
        st.caption(f"⏰ إجمالي المدة: {total_hours:.2f} ساعة")
        
        st.markdown("---")
        
        # YouTube Authentication
        st.markdown("### 🔐 مصادقة يوتيوب")
        
        # Check if token exists
        if os.path.exists("token.pickle"):
            st.success("✅ متصل بحساب يوتيوب")
            if st.button("🔄 إعادة المصادقة", use_container_width=True):
                try:
                    os.remove("token.pickle")
                    st.info("تم حذف المصادقة. أعد تشغيل التطبيق.")
                except: pass
        else:
            st.warning("⚠️ غير متصل بيوتيوب")
            
        st.markdown("**رفع ملف client_secrets.json:**")
        uploaded_secrets = st.file_uploader(
            "اختر ملف client_secrets.json", 
            type=['json'],
            help="احصل على هذا الملف من Google Cloud Console"
        )
        
        if uploaded_secrets:
            try:
                with open("client_secrets.json", "wb") as f:
                    f.write(uploaded_secrets.getbuffer())
                st.success("✅ تم حفظ ملف المصادقة")
                st.info("الآن استخدم زر 'بث مباشر' في الصفحة الرئيسية")
            except Exception as e:
                st.error(f"خطأ: {e}")


# --- MAIN HEADER ---
st.markdown("""
<div class="main-header">
    <h1>🎬 استوديو Lofi الذكي</h1>
    <p style="color: #bdc3c7; margin-top: 5px;">اصنع محتوى احترافي بضغطة زر</p>
</div>
""", unsafe_allow_html=True)

# --- 3-COLUMN LAYOUT ---
col1, col2, col3 = st.columns(3, gap="medium")

# === COLUMN 1: DESIGN ===
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="phase-header">1️⃣ التصميم والفكرة</div>', unsafe_allow_html=True)
    
    idea = st.text_input("📝 فكرة الفيديو", placeholder="مثلاً: جو ممطر للدراسة")
    
    # Image Upload
    uploaded_file = st.file_uploader("🖼️ صورة الخلفية", type=['png', 'jpg', 'webp'])
    if uploaded_file:
        try:
            from PIL import Image
            img = Image.open(uploaded_file)
            if img.mode != 'RGB': img = img.convert('RGB')
            # Save
            path = Path("temp/uploads/background_clean.png")
            path.parent.mkdir(parents=True, exist_ok=True)
            img.save(path)
            st.session_state.image_path = str(path)
            st.image(str(path), use_container_width=True)
            save_state() # Save progress
        except: pass
    elif st.session_state.get("image_path") and os.path.exists(st.session_state.image_path):
        st.image(st.session_state.image_path, caption="الصورة المحفوظة")

    # Generate Prompts Button
    if st.button("✨ توليد الوصف (AI)", use_container_width=True):
        if not idea: st.error("أدخل فكرة أولاً")
        else:
            with st.spinner("جاري الكتابة..."):
                orch = AIOrchestrator(
                    provider=st.session_state.ai_provider,
                    gemini_key=st.session_state.api_keys.get('gemini'),
                    openrouter_key=st.session_state.api_keys.get('openrouter')
                )
                res = orch.run_orchestrator(idea, st.session_state.get('image_path'))
                if res and "error" not in res:
                    st.session_state.orchestration = res
                    save_state() # Save
                    st.success("تم التوليد!")
                else:
                    st.error("فشل التوليد")
    
    # Editing Prompts
    if st.session_state.get("orchestration"):
        st.markdown("---")
        o = st.session_state.orchestration
        st.text_area("وصف الموسيقى", o.get('suno_prompt',''), height=70, key="p_suno")
        st.text_area("وصف الفيديو", o.get('veo_prompt',''), height=70, key="p_veo")
        st.text_input("عنوان الفيديو", o.get('seo_metadata',{}).get('title',''), key="p_title")
    
    st.markdown('</div>', unsafe_allow_html=True)

# === COLUMN 2: ASSETS ===
with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="phase-header">2️⃣ العناصر (Assets)</div>', unsafe_allow_html=True)
    
    if not st.session_state.get("orchestration"):
        st.markdown("<div style='text-align:center; color:#777; padding:40px;'>ابدأ من المرحلة 1</div>", unsafe_allow_html=True)
    else:
        st.write("جاهز للتنفيذ:")
        if st.button("🚀 بدء الإنتاج الكامل", type="primary", use_container_width=True):
             if not st.session_state.api_keys['kie']:
                 st.error("مفتاح Kie.ai مفقود!")
             else:
                 st.session_state.pipeline_running = True
                 status = st.empty()
                 status.info("⏳ جاري العمل... لا تغلق الصفحة")
                 
                 try:
                     # Set Env Vars
                     os.environ["GEMINI_API_KEY"] = st.session_state.api_keys.get('gemini','')
                     os.environ["OPENROUTER_API_KEY"] = st.session_state.api_keys.get('openrouter','')
                     os.environ["KIE_API_KEY"] = st.session_state.api_keys.get('kie','')
                     
                     pipeline = LofiV3Pipeline(
                         ai_provider=st.session_state.ai_provider,
                         kie_key=st.session_state.api_keys.get('kie')
                     )
                     
                     # Using idea + prompts from session
                     # Currently pipeline auto-updates prompts, but that's fine.
                     res = pipeline.run(idea, st.session_state.image_path)
                     
                     if isinstance(res, dict) and res.get("success"):
                         st.session_state.assets = res
                         save_state() # Save EVERYTHING
                         st.success("✅ اكتمل بنجاح!")
                         status.empty()
                         st.rerun()
                     else:
                         Err = res.get("error") if isinstance(res, dict) else "Unknown"
                         st.error(f"خطأ: {Err}")
                         
                 except Exception as e:
                     st.error(f"System Error: {e}")
    
    # Show Assets if they exist
    assets = st.session_state.get("assets", {})
    
    if assets.get("music_file"):
        st.markdown("##### 🎵 الموسيقى")
        st.audio(assets["music_file"])
    
    if assets.get("video_clip"):
        st.markdown("##### 🎬 كليب التحريك")
        st.video(assets["video_clip"])
    elif assets.get("music_file"): # If music exists but video clip doesn't
        st.caption("ℹ️ تم استخدام صورة ثابتة")
        
    st.markdown('</div>', unsafe_allow_html=True)

# === COLUMN 3: FINAL ===
with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="phase-header">3️⃣ الفيديو النهائي</div>', unsafe_allow_html=True)
    
    final = st.session_state.get("assets", {}).get("final_video")
    
    if final and os.path.exists(final):
        st.video(final)
        
        with open(final, "rb") as f:
            st.download_button("💾 تحميل الفيديو", f, file_name="lofi_video.mp4", mime="video/mp4", use_container_width=True)
            
        st.markdown("---")
        if st.button("📡 بث مباشر (YouTube)", use_container_width=True):
            try:
                # Get stream duration from settings
                stream_hours = st.session_state.get('stream_hours', 4)
                stream_minutes = st.session_state.get('stream_minutes', 0)
                total_duration = stream_hours + (stream_minutes / 60)
                
                title = st.session_state.orchestration['seo_metadata']['title']
                desc = st.session_state.orchestration['seo_metadata']['description']
                url, _ = get_rtmp_url("token.pickle", title, desc)
                StreamScheduler.run_stream(final, url, total_duration)
                st.success(f"✅ تم بدء البث لمدة {total_duration:.2f} ساعة!")
            except Exception as e: st.error(f"خطأ البث: {e}")
            
    else:
        st.markdown("<div style='text-align:center; color:#777; padding:40px;'>سظهر الفيديو هنا بعد المعالجة</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

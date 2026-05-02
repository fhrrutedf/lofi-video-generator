"""
LofiGen Web Interface — Streamlit UI

Usage:
    streamlit run lofi_gen/web/__init__.py
    
Or:
    python -m lofi_gen.web
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st

from lofi_gen import LofiPipeline, GenerationConfig, VideoConfig, AudioConfig, AIConfig
from lofi_gen.ai.prompt_system import THEME_TEMPLATES
from lofi_gen.core.logging import get_logger

log = get_logger("web")

# ── Page Config ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="LofiGen — AI Video Generator",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #eee;
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
    }
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/lo-fi.png", width=80)
    st.title("⚙️ الإعدادات")
    
    # API Keys
    with st.expander("🔑 مفاتيح API"):
        gemini_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        openrouter_key = st.text_input("OpenRouter API Key", type="password", value=os.getenv("OPENROUTER_API_KEY", ""))
        kie_key = st.text_input("Kie.ai API Key", type="password", value=os.getenv("KIE_API_KEY", ""))
        pexels_key = st.text_input("Pexels API Key", type="password", value=os.getenv("PEXELS_API_KEY", ""))
        
        ai_provider = st.selectbox(
            "مزود الذكاء الاصطناعي",
            ["auto", "gemini", "openrouter"],
            format_func=lambda x: {"auto": "تلقائي", "gemini": "Gemini", "openrouter": "OpenRouter"}[x]
        )
        
        if st.button("💾 حفظ المفاتيح"):
            os.environ["GEMINI_API_KEY"] = gemini_key
            os.environ["OPENROUTER_API_KEY"] = openrouter_key
            os.environ["KIE_API_KEY"] = kie_key
            os.environ["PEXELS_API_KEY"] = pexels_key
            os.environ["AI_PROVIDER"] = ai_provider
            st.success("تم الحفظ! ✅")
    
    # Video Settings
    with st.expander("🎬 إعدادات الفيديو"):
        duration = st.slider("المدة (ساعات)", 0.5, 10.0, 4.0, 0.5)
        fps = st.selectbox("معدل الإطارات", [24, 30, 60], index=1)
        quality = st.select_slider(
            "جودة التشفير",
            options=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"],
            value="medium"
        )
        max_zoom = st.slider("تكبير الصورة", 1.0, 1.3, 1.15, 0.05)
        
        col1, col2 = st.columns(2)
        with col1:
            film_grain = st.checkbox("حبيبات فيلم 🎞️", value=False)
            vignette = st.checkbox("تظليل الأطراف 🔅", value=False)
        with col2:
            crossfade = st.slider("تداخل المشاهد (ثانية)", 0.0, 5.0, 2.0, 0.5)
    
    # Audio Settings
    with st.expander("🎵 إعدادات الصوت"):
        audio_effects = st.multiselect(
            "تأثيرات الصوت",
            ["reverb", "vinyl", "bass_boost"],
            format_func=lambda x: {"reverb": "صدى 🎤", "vinyl": "فينيل 📀", "bass_boost": "باس قوي 🔊"}[x]
        )

# ── Main Content ───────────────────────────────────────────────────────

st.title("🎵 LofiGen")
st.subheader("مولد فيديوهات Lofi احترافي بالذكاء الاصطناعي")

# Theme Selection
st.markdown("### 🎯 اختر الثيم")

# Display themes in a grid
themes = list(THEME_TEMPLATES.keys())
cols = st.columns(4)
selected_theme = None

for i, theme in enumerate(themes):
    with cols[i % 4]:
        theme_data = THEME_TEMPLATES[theme]
        bpm_min, bpm_max = theme_data["bpm_range"]
        
        if st.button(
            f"{theme.title()}\n🎵 {bpm_min}-{bpm_max} BPM\n{theme_data['mood']}",
            key=f"theme_{theme}",
            use_container_width=True
        ):
            selected_theme = theme
            st.session_state.selected_theme = theme

# Custom theme input
if "selected_theme" in st.session_state:
    selected_theme = st.session_state.selected_theme

custom_theme = st.text_input(
    "أو اكتب فكرتك الخاصة:",
    value=selected_theme if selected_theme else "",
    placeholder="مثال: مطر على النافذة مع كتابة وقهوة"
)

final_theme = custom_theme if custom_theme else (selected_theme or "default")

# ── File Uploads ───────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 📁 رفع الملفات (اختياري)")

col1, col2, col3 = st.columns(3)

with col1:
    uploaded_images = st.file_uploader(
        "🖼️ صور الخلفية",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="يمكنك رفع صورة واحدة أو عدة صور للتبديل بينها"
    )

with col2:
    uploaded_music = st.file_uploader(
        "🎶 ملف موسيقى",
        type=["mp3", "wav", "ogg"],
        help="إذا لم ترفع، سيتم توليد موسيقى AI"
    )

with col3:
    uploaded_ambience = st.file_uploader(
        "🌧️ صوت جو (Ambience)",
        type=["mp3", "wav", "ogg"],
        help="صوت المطر، المحيط، إلخ"
    )

# ── Text Overlays ──────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### ✍️ نصوص على الفيديو (اختياري)")

quotes = []
for i in range(3):
    q = st.text_input(f"نص {i+1}", key=f"quote_{i}", placeholder=f"عبارة {i+1}...")
    if q:
        quotes.append(q)

# ── Generate Button ────────────────────────────────────────────────────

st.markdown("---")

if st.button("🚀 إنشاء الفيديو", use_container_width=True, type="primary"):
    if not final_theme:
        st.error("❌ الرجاء اختيار ثيم أو كتابة فكرة")
        st.stop()
    
    # Save uploaded files
    temp_dir = Path("temp") / f"web_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    image_paths = []
    if uploaded_images:
        for img in uploaded_images:
            img_path = temp_dir / img.name
            with open(img_path, "wb") as f:
                f.write(img.getvalue())
            image_paths.append(str(img_path))
    
    music_path = None
    if uploaded_music:
        music_path = str(temp_dir / uploaded_music.name)
        with open(music_path, "wb") as f:
            f.write(uploaded_music.getvalue())
    
    ambience_path = None
    if uploaded_ambience:
        ambience_path = str(temp_dir / uploaded_ambience.name)
        with open(ambience_path, "wb") as f:
            f.write(uploaded_ambience.getvalue())
    
    # Build config
    config = GenerationConfig(
        theme=final_theme,
        duration=duration * 3600,  # Convert to seconds
        video=VideoConfig(
            fps=fps,
            preset=quality,
            max_zoom=max_zoom,
            crossfade_duration=crossfade,
            film_grain=film_grain,
            vignette=vignette,
        ),
        audio=AudioConfig(
            effects=audio_effects,
        ),
        ai=AIConfig(
            gemini_api_key=gemini_key,
            openrouter_api_key=openrouter_key,
            kie_api_key=kie_key,
            pexels_api_key=pexels_key,
            provider=ai_provider,
        ),
        image_paths=image_paths,
        music_path=music_path,
        ambience_path=ambience_path,
        quotes=quotes,
        output_dir="output",
    )
    
    # Progress container
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🎨 تحليل الثيم...")
        progress_bar.progress(10)
        
        # Run pipeline
        pipeline = LofiPipeline(config)
        
        # Manual progress updates (since pipeline doesn't have callbacks yet)
        import threading
        
        result_container = {"result": None}
        
        def run_pipeline():
            result_container["result"] = pipeline.run()
        
        thread = threading.Thread(target=run_pipeline)
        thread.start()
        
        # Simulate progress while waiting
        progress_steps = [15, 25, 40, 60, 80, 95]
        step_messages = [
            "🎵 جاري توليد/تحميل الموسيقى...",
            "🖼️ جاري تحميل الصور...",
            "🎬 جاري معالجة الفيديو...",
            "🔊 جاري معالجة الصوت...",
            "🔄 جاري الدمج النهائي...",
            "📸 جاري إنشاء الصورة المصغرة...",
        ]
        
        for i, (step, msg) in enumerate(zip(progress_steps, step_messages)):
            time.sleep(2)  # Give user visual feedback
            progress_bar.progress(step)
            status_text.text(msg)
            if not thread.is_alive():
                break
        
        thread.join()
        result = result_container["result"]
        
        progress_bar.progress(100)
        
        if result and result.success:
            status_text.text("✅ تم الإنشاء بنجاح!")
            st.balloons()
            
            st.markdown("---")
            st.success(f"🎉 الفيديو جاهز: `{result.output_path}`")
            
            # Show details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("الحجم", f"{result.file_size_mb:.1f} MB")
            with col2:
                st.metric("الوقت", f"{result.duration_seconds:.0f} ثانية")
            with col3:
                if result.theme_info:
                    st.metric("BPM", result.theme_info.bpm)
            
            # Video player
            if Path(result.output_path).exists():
                st.video(result.output_path)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                if Path(result.output_path).exists():
                    with open(result.output_path, "rb") as f:
                        st.download_button(
                            "📥 تحميل الفيديو",
                            f,
                            file_name=Path(result.output_path).name,
                            mime="video/mp4",
                            use_container_width=True
                        )
            
            with col2:
                if result.thumbnail_path and Path(result.thumbnail_path).exists():
                    with open(result.thumbnail_path, "rb") as f:
                        st.download_button(
                            "🖼️ تحميل الصورة المصغرة",
                            f,
                            file_name=Path(result.thumbnail_path).name,
                            mime="image/jpeg",
                            use_container_width=True
                        )
            
            # SEO Metadata
            if result.metadata_path and Path(result.metadata_path).exists():
                with open(result.metadata_path, "r", encoding="utf-8") as f:
                    metadata = f.read()
                with st.expander("📋 معلومات YouTube (SEO)"):
                    st.text(metadata)
                    st.download_button(
                        "📄 تحميل ملف الميتاداتا",
                        metadata,
                        file_name="youtube_metadata.txt",
                        mime="text/plain"
                    )
        else:
            status_text.text("❌ فشل الإنشاء")
            error_msg = result.error if result else "خطأ غير معروف"
            st.error(f"❌ فشل: {error_msg}")

# ── Footer ────────────────────────────────────────────────────────────

st.markdown("---")
st.caption("🎵 LofiGen v1.0.0 | مفتوح المصدر | [GitHub](https://github.com/fhrrutedf/lofi-video-generator)")

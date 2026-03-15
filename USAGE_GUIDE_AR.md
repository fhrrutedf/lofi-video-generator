# 🎬 دليل الاستخدام السريع - V3 Pipeline

## 🎯 **الـ Workflow الكامل**

```
1. أنت تكتب → "هدوء" أو "قهوة الصباح" أو أي فكرة
                ↓
2. ترفع صورة → من جهازك أو رابط
                ↓
3. Gemini يحلل → يولد:
   • عنوان الموسيقى (Suno prompt)
   • وصف تحريك الصورة (Veo prompt)  
   • عنوان + وصف + تاغات يوتيوب
                ↓
4. Kie.ai يشتغل →
   • Suno يولد موسيقى (3 دقائق)  
   • Veo يحرك الصورة (2-10 ثواني)
                ↓
5. FFmpeg يعمل مونتاج →
   • يكرر الفيديو القصير  
   • يكرر الموسيقى
   • يدمجهم (حسب المدة المحددة)
                ↓
6. الملفات تُحفظ →
   ✅ output/final_lofi_xxxxx.mp4  
   ✅ output/final_lofi_xxxxx.txt (SEO)
   ✅ temp/music_xxxxx.mp3  
   ✅ temp/clip_xxxxx.mp4
                ↓
7. رفع يوتيوب (اختياري) →
   • بالعنوان والوصف الجاهزين
```

---

## 🚀 **طريقة التشغيل**

### **الطريقة 1: من الواجهة (Streamlit)** - الأسهل ⭐

```bash
streamlit run web_interface.py
```

**الخطوات في الواجهة:**
1. اكتب الفكرة: "هدوء" أو "قهوة الصباح"
2. ارفع صورة من جهازك
3. اضغط "إطلاق البث المباشر"
4. انتظر (~5-10 دقائق)
5. جاهز! الملفات في مجلد `output/`

---

### **الطريقة 2: من Command Line** - للتحكم الكامل

```bash
python v3_automation_pipeline.py "هدوء" "صورة.jpg"
```

**مع خيارات:**
```bash
python v3_automation_pipeline.py "قهوة الصباح" "cafe.jpg" --output my_video.mp4
```

---

## 📂 **أين تُحفظ الملفات؟**

### **المجلدات:**

```
d:/viideo/
├── output/              ← الفيديوهات النهائية 🎬
│   ├── final_lofi_1767750262.mp4    (الفيديو الكامل)
│   └── final_lofi_1767750262.txt    (عنوان + وصف يوتيوب)
│
└── temp/                ← الملفات المؤقتة 🎵
    ├── music_1767750262.mp3         (الموسيقى 3دقائق)
    └── clip_1767750262.mp4          (المقطع المتحرك 2-10 ثواني)
```

### **تغيير المجلد:**

إذا تريد حفظ في مكان آخر، عدّل هنا:

**في `v3_automation_pipeline.py` (خط 23-24):**
```python
self.output_dir = Path("D:/MyVideos/output")      # ← غيّر هنا
self.temp_dir = Path("D:/MyVideos/temp")          # ← غيّر هنا
```

---

## ✅ **حل مشكلة Gemini Quota**

### **المشكلة:**
```
🛑 Quota Exhausted (429) for gemini-2.0-flash. Max retries reached.
```

### **الحل السريع:**

#### **1. احصل على API Key جديد** (مجاني)

```
1. اذهب: https://aistudio.google.com/app/apikey
2. سجل دخول بحساب Gmail
3. اضغط "Create API Key"
4. اختر "Create API key in new project"
5. انسخ المفتاح (AIzaSy...)
```

#### **2. حدّث `.env`**
```env
GEMINI_API_KEY=AIzaSy...  ← المفتاح الجديد هنا
```

#### **3. تأكد من استخدام النماذج المجانية**

الكود الآن يستخدم:
- ✅ `gemini-2.0-flash-exp` - **مجاني 100%** (1500 طلب/يوم)
- ✅ `gemini-1.5-flash-8b` - **مجاني 100%** (4000 طلب/يوم)

---

## 🎨 **أمثلة على الأفكار**

| الفكرة | ما سيحدث |
|--------|-----------|
| "هدوء" | موسيقى هادئة + مشهد طبيعي |
| "قهوة الصباح" | موسيقى lofi كافيه + مشهد مقهى |
| "مطر ليلي" | موسيقى حزينة + مشهد مطر |
| "تركيز" | موسيقى study + مكتبة/مكتب |
| "رحلة فضائية" | موسيقى كونية + نجوم ومجرات |

---

## 📊 **الأوقات المتوقعة**

| المرحلة | الوقت |
|---------|-------|
| Gemini (تحليل) | 5-15 ثانية |
| Suno (موسيقى) | 60-90 ثانية |
| Veo (تحريك) | 2-5 دقائق |
| FFmpeg (مونتاج) | 30-120 دقيقة* |

*حسب المدة النهائية (2 دقيقة للتجربة، 4 ساعات للنشر)

---

## 💰 **التكاليف**

### **النماذج المجانية (Free Tier):**
```
✅ gemini-2.0-flash-exp: مجاني تماماً (1500 طلب/يوم)
✅ gemini-1.5-flash-8b:  مجاني تماماً (4000 طلب/يوم)
✅ gemini-1.5-flash:     مجاني تماماً (1500 طلب/يوم)
```

### **إذا نفذت المجانية (نماذج رخيصة):**
```
💰 gemini-2.0-flash-lite: $0.075 / 1M tokens (رخيص جداً)
💰 gemini-2.0-flash:      $0.10  / 1M tokens
```

**للتجربة:** استخدام واحد = ~1000 tokens = $0.0001 (أقل من فلس!)

---

## 🧪 **اختبار سريع**

```bash
# 1. تأكد من API Keys
python validate_env.py

# 2. جرب موسيقى فقط (سريع)
python -c "from kie_ai_integration import KieAIClient; KieAIClient().generate_and_download('calm lofi', 'test.mp3')"

# 3. جرب Pipeline كامل
python v3_automation_pipeline.py "test" "image.jpg"
```

---

## 🎯 **الخطوات التالية**

### **للبدء الآن:**

```bash
# 1. حدّث Gemini key
notepad .env
# أضف: GEMINI_API_KEY=AIzaSy...

# 2. شغّل الواجهة
streamlit run web_interface.py

# 3. جرّب!
# اكتب "هدوء" + ارفع صورة
```

### **للتخصيص:**

```python
# في config.py
OUTPUT_DURATION = 120  # 2 دقيقة للتجربة
OUTPUT_DURATION = 14400  # 4 ساعات للنشر
```

---

## ❓ **الأسئلة الشائعة**

### **س: الموسيقى طلعت غير مناسبة؟**
ج: عدّل الـ prompt يدوياً في `v3_automation_pipeline.py` (خط 45):
```python
suno_final = f"Calm peaceful piano, {suno_raw}, high fidelity, lo-fi"
```

### **س: الصورة ما تحركت؟**
ج: Veo يحتاج صورة **من الإنترنت (URL)**. إذا رفعت من جهازك، ستبقى static.

### **س: Gemini لسه يطلع 429؟**
ج: جرب حساب Gmail آخر تماماً، أو انتظر 24 ساعة.

### **س: كيف أحذف الملفات المؤقتة؟**
ج: 
```bash
# Windows
rmdir /s temp
mkdir temp

# أو يدوياً
# احذف محتويات temp/ بس
```

---

## 🎉 **خلاصة**

✅ **جاهز للاستخدام الآن!**  
✅ **يحفظ كل شيء تلقائياً**  
✅ **Gemini مجاني (1500-4000 طلب/يوم)**  
✅ **Workflow كامل: فكرة → فيديو → يوتيوب**

---

**إذا واجهت مشكلة:**
1. شغّل: `python validate_env.py`
2. اقرأ الرسالة بالضبط
3. اتبع التعليمات

**للدعم:**
- راجع `API_ANALYSIS_SUMMARY_AR.md`
- راجع `FIXES_CHANGELOG.md`

---

**🚀 ابدأ الآن:**
```bash
streamlit run web_interface.py
```

# 🌐 دليل استخدام OpenRouter - بديل مجاني لـ Gemini

## 🎯 **ما هو OpenRouter؟**

**OpenRouter** هو منصة توفر الوصول لنماذج AI متعددة من خلال API واحد، بما فيها:
- ✅ **نماذج مجانية 100%** - مثل `openai/gpt-oss-120b:free`
- ✅ **بدون حدود يومية** (حسب النموذج)
- ✅ **سهل الاستخدام** - API واحد لعشرات النماذج

---

## 🆚 **Gemini vs OpenRouter**

| الميزة | Gemini | OpenRouter |
|--------|--------|------------|
| **السعر** | مجاني (1500-4000 طلب/يوم) | مجاني بدون حدود* |
| **الجودة** | ممتازة (Google) | جيدة جداً (GPT-4 level) |
| **السرعة** | سريع | سريع |
| **التسجيل** | حساب Google | حساب OpenRouter |
| **API Key** | من Google AI Studio | من OpenRouter |

*للنماذج المجانية فقط

---

## 🚀 **البدء السريع**

### **الخطوة 1: احصل على API Key** (دقيقتين)

```
1. اذهب: https://openrouter.ai/keys
2. سجل دخول (أو إنشاء حساب)
3. اضغط "Create Key"
4. انسخ المفتاح (sk-or-v1-...)
```

### **الخطوة 2: أضف المفتاح في `.env`**

```bash
notepad .env
```

أضف هذا السطر:
```env
OPENROUTER_API_KEY=sk-or-v1-...
```

### **الخطوة 3: اختر AI Provider**

يمكنك اختيار واحد من:

#### **Option A: Auto (تلقائي - موصى به)** ⭐
```env
AI_PROVIDER=auto
```
- يجرب Gemini أولاً
- إذا فشل، يستخدم OpenRouter تلقائياً
- **الأفضل:** يضمن أن الكود يعمل دائماً!

#### **Option B: OpenRouter فقط**
```env
AI_PROVIDER=openrouter
```
- يستخدم OpenRouter فقط
- مناسب إذا لا تريد استخدام Gemini

#### **Option C: Gemini فقط**
```env
AI_PROVIDER=gemini
```
- يستخدم Gemini فقط (الافتراضي السابق)

---

## 🎬 **طريقة الاستخدام**

### **من Command Line:**

```bash
# استخدام auto (الافتراضي)
python v3_automation_pipeline.py "هدوء" "image.jpg"

# استخدام OpenRouter فقط
python v3_automation_pipeline.py "هدوء" "image.jpg" --provider openrouter

# استخدام Gemini فقط
python v3_automation_pipeline.py "هدوء" "image.jpg" --provider gemini
```

### **من الواجهة (Streamlit):**

```bash
streamlit run web_interface.py
```

الواجهة ستستخدم الإعداد الموجود في `.env` (AI_PROVIDER)

---

## 🆓 **النماذج المجانية المتاحة**

| النموذج | الوصف | الحد المجاني |
|---------|-------|--------------|
| `openai/gpt-oss-120b:free` | ⭐ **موصى به** - GPT-4 level | بدون حد* |
| `google/gemini-2.0-flash-exp:free` | Gemini via OpenRouter | بدون حد |
| `meta-llama/llama-3.1-8b-instruct:free` | Meta Llama | بدون حد |
| `mistralai/mistral-7b-instruct:free` | Mistral AI | بدون حد |

*قد تكون هناك حدود rate limiting معقولة

---

## ✅ **اختبار OpenRouter**

```bash
# شغّل الاختبار
python openrouter_integration.py

# أو استخدم validate
python validate_env.py
```

**يجب أن ترى:**
```
✅ OpenRouter client initialized
🌐 Using OpenRouter...
✅ OpenRouter succeeded
```

---

## 💡 **الأمثلة**

### **مثال 1: Gemini نفذت حصته → OpenRouter ينقذ اليوم**

```bash
# في .env
AI_PROVIDER=auto
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-v1-...
```

**Output:**
```
🧠 Trying Gemini...
⚠️  Gemini failed (429 Quota Exhausted)
🌐 Falling back to OpenRouter...
✅ OpenRouter succeeded
```

### **مثال 2: استخدام OpenRouter فقط**

```bash
# في .env
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

**Output:**
```
🌐 Using OpenRouter...
✅ OpenRouter succeeded
```

---

## 🔧 **Troubleshooting**

### **مشكلة: 401 Unauthorized**

```
❌ Invalid OpenRouter API Key
```

**الحل:**
1. تحقق أن المفتاح صحيح
2. احصل على مفتاح جديد من https://openrouter.ai/keys
3. تأكد أنه يبدأ بـ `sk-or-v1-`

---

### **مشكلة: 402 Payment Required**

```
💰 Credits exhausted for openai/gpt-oss-120b:free
```

**الحل:**
- النموذج المجاني نفذ
- جرب نموذج مجاني آخر (الكود يجرب تلقائياً)
- أو انتظر قليلاً

---

### **مشكلة: 429 Rate Limit**

```
⏳ Rate limited. Retrying...
```

**الحل:**
- الكود يحاول تلقائياً (3 مرات)
- انتظر ثواني وسيعمل

---

## 📊 **مقارنة الأداء**

### **السرعة:**
| Provider | متوسط الوقت |
|----------|-------------|
| Gemini 2.0 Flash | 3-7 ثواني |
| OpenRouter GPT-OSS | 4-8 ثواني |

### **الجودة:**
| Provider | جودة الـ Prompts |
|----------|------------------|
| Gemini | ⭐⭐⭐⭐⭐ (ممتازة) |
| OpenRouter | ⭐⭐⭐⭐ (جيدة جداً) |

**الخلاصة:** كلاهما رائع! 🎉

---

## 🎯 **متى تستخدم أي واحد؟**

### **استخدم Gemini إذا:**
- ✅ عندك API key
- ✅ لم تستهلك الحصة اليومية
- ✅ تريد أفضل جودة

### **استخدم OpenRouter إذا:**
- ✅ Gemini نفذت حصته
- ✅ تريد بديل مجاني
- ✅ تحب التجربة بنماذج مختلفة

### **استخدم Auto (موصى به!) إذا:**
- ✅ تريد أن يعمل الكود **دائماً**
- ✅ لا تريد قلق من quota
- ✅ تريد أفضل تجربة

---

## 📝 **ملخص الإعداد**

```bash
# 1. أضف في .env
OPENROUTER_API_KEY=sk-or-v1-...
AI_PROVIDER=auto

# 2. اختبر
python validate_env.py

# 3. شغّل!
python v3_automation_pipeline.py "test" "image.jpg"
```

---

## 🌟 **المميزات الإضافية**

### **ما يميز OpenRouter:**

1. **تنوع النماذج:**
   - GPT-4
   - Claude
   - Gemini
   - Llama
   - وأكثر من 100 نموذج!

2. **سعر موحد:**
   - API واحد لكل شيء
   - لا حاجة لعدة accounts

3. **Free Credits:**
   - بعض النماذج مجانية تماماً
   - نماذج أخرى رخيصة جداً

---

## 🎉 **الخلاصة**

✅ **OpenRouter = بديل مجاني ممتاز لـ Gemini**  
✅ **Auto mode = أفضل حل (يجرب الاثنين)**  
✅ **سهل الإعداد** (دقيقتين فقط)  
✅ **موثوق** (retry logic + fallback)

**المشروع الآن يدعم:**
- Gemini (Google)
- OpenRouter (100+ models)
- Auto fallback
- اختيار المستخدم

**جاهز للاستخدام! 🚀**

---

**للمزيد:**
- OpenRouter Docs: https://openrouter.ai/docs
- Models List: https://openrouter.ai/models
- Pricing: https://openrouter.ai/pricing

**الدعم:**
- راجع `USAGE_GUIDE_AR.md`
- شغّل `python validate_env.py`

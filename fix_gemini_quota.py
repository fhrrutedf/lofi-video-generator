"""
Quick Fix Script for Gemini API Quota Issues
Helps diagnose and fix "429 Quota Exhausted" errors
"""

import os
import sys
import requests

print("""
╔══════════════════════════════════════════════════════════════════╗
║             🔧 Gemini Quota Troubleshooter                       ║
║          حل مشكلة Quota Exhausted - خطوات سريعة                 ║
╚══════════════════════════════════════════════════════════════════╝
""")

# Load .env if exists
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if value and not value.startswith('your_'):
                    os.environ[key.strip()] = value.strip()

gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("❌ لم يتم العثور على GEMINI_API_KEY في .env")
    print("\n📝 الخطوات:")
    print("1. افتح: https://aistudio.google.com/app/apikey")
    print("2. سجل دخول بحساب Gmail")
    print("3. اضغط 'Create API Key'")
    print("4. انسخ المفتاح")
    print("5. أضفه في .env:")
    print("   GEMINI_API_KEY=AIzaSy...")
    sys.exit(1)

print(f"✅ وجدنا GEMINI_API_KEY: {gemini_key[:20]}...\n")

# Test different free models
free_models = [
    ("gemini-2.0-flash-exp", "⭐ مجاني - تجريبي سريع (1500 طلب/يوم)"),
    ("gemini-1.5-flash-8b", "⭐ مجاني - أسرع (4000 طلب/يوم)"),
    ("gemini-1.5-flash", "⭐ مجاني - قياسي (1500 طلب/يوم)"),
    ("gemini-1.5-pro", "💰 قد يكون مدفوع"),
]

print("🧪 اختبار النماذج المجانية...\n")
print("=" * 70)

working_models = []

for model, description in free_models:
    print(f"\n🔍 جاري اختبار: {model}")
    print(f"   {description}")
    
    for version in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={gemini_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": "Hello, respond with just 'OK'"}]
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ يعمل! (API {version})")
                working_models.append((model, version))
                break  # Found working version
                
            elif response.status_code == 429:
                print(f"   ⏳ نفذت الحصة (429) - {version}")
                
            elif response.status_code == 404:
                print(f"   ⚠️  غير متاح - {version}")
                
            elif response.status_code == 400:
                print(f"   ⚠️  خطأ في الطلب - {version}")
                
            elif response.status_code == 401:
                print(f"   ❌ مفتاح غير صحيح (401)")
                break
                
            else:
                print(f"   ❌ خطأ {response.status_code} - {version}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️  انتهت المهلة - {version}")
            
        except Exception as e:
            print(f"   ❌ خطأ: {str(e)[:50]}")

print("\n" + "=" * 70)
print("\n📊 النتائج:\n")

if working_models:
    print("✅ النماذج الشغالة:")
    for model, version in working_models:
        print(f"   • {model} (API {version})")
    
    print("\n🎉 الحل: استخدم أحد هذه النماذج")
    print(f"   البرنامج سيستخدم: {working_models[0][0]} تلقائياً")
    
else:
    print("❌ لا توجد نماذج شغالة حالياً\n")
    
    print("🔧 الحلول المقترحة:")
    print("\n1️⃣ انتظر 24 ساعة (الحصة تتجدد يومياً)")
    
    print("\n2️⃣ استخدم API key جديد:")
    print("   • سجل خروج من اhttp://aistudio.google.com")
    print("   • استخدم حساب Gmail آخر")
    print("   • احصل على API key جديد")
    
    print("\n3️⃣ تحقق من الحساب:")
    print("   • https://aistudio.google.com/app/apikey")
    print("   • تأكد أن الحساب مفعّل")
    print("   • جرب إنشاء مشروع جديد")
    
    print("\n4️⃣ جرب billing (اختياري):")
    print("   • https://console.cloud.google.com/billing")
    print("   • أضف بطاقة ائتمان للحصول على Free Trial $300")

print("\n" + "=" * 70)

# Test with actual prompt
if working_models:
    print("\n🎯 اختبار عملي (توليد prompt)...\n")
    
    model, version = working_models[0]
    url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={gemini_key}"
    
    test_prompt = """
    أنت خبير محتوى Lofi. حول هذه الفكرة إلى prompt موسيقى:
    الفكرة: "هدوء"
    
    أجب بـ JSON فقط:
    {"suno_prompt": "calm peaceful piano, minimal beats, 68 BPM"}
    """
    
    payload = {"contents": [{"parts": [{"text": test_prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            result = data["candidates"][0]["content"]["parts"][0]["text"]
            print("✅ نجح الاختبار!")
            print(f"📄 الاستجابة:")
            print(result[:200] + "..." if len(result) > 200 else result)
        else:
            print(f"⚠️  فشل الاختبار: {response.status_code}")
    except Exception as e:
        print(f"⚠️  خطأ في الاختبار: {e}")

print("\n" + "=" * 70)
print("\n💡 نصيحة: النماذج ال���جانية كافية للتجربة والاستخدام الشخصي")
print("   رصيد يومي: 1500-4000 طلب = كافي لـ 100+ فيديو/يوم!\n")

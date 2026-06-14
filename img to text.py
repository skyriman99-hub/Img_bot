import os
import telebot
import pytesseract
from PIL import Image
from subprocess import run

# 1. جلب التوكن من إعدادات GitHub السرية
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 2. ⚠️ ضع معرف حسابك (User ID) هنا بدلاً من الرقم 123456789 (بدون علامات تنصيص)
ADMIN_ID = 192112307

# دالة لتسجيل المستخدمين الجدد وتحديث مستودع GitHub
def register_user(message):
    user_id = str(message.chat.id)
    file_name = "users.txt"
    
    # قراءة المستخدمين الحاليين
    existing_users = []
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            existing_users = f.read().splitlines()
    
    # إذا كان المستخدم جديداً، أضفه للملف وارفعه إلى جيت هب
    if user_id not in existing_users:
        with open(file_name, "a") as f:
            f.write(user_id + "\n")
        
        # كود برمجي لحفظ التحديث ورفعه إلى GitHub تلقائياً
        try:
            run(["git", "config", "global", "user.name", "GitHub Action"])
            run(["git", "config", "global", "user.email", "action@github.com"])
            run(["git", "add", "users.txt"])
            run(["git", "commit", "-m", f"Update users list: added {user_id}"])
            run(["git", "push"])
            print(f"New user {user_id} saved to GitHub!")
        except Exception as e:
            print(f"Git push failed: {e}")

# أمر لمعرفة الإحصائيات (مخصص لك فقط)
@bot.message_handler(commands=['stats'])
def send_stats(message):
    # التحقق مما إذا كان المرسل هو أنت (مطور البوت)
    if message.chat.id == ADMIN_ID:
        if os.path.exists("users.txt"):
            with open("users.txt", "r") as f:
                count = len(f.read().splitlines())
            bot.reply_to(message, f"📊 **إحصائيات البوت:**\n\n👥 عدد المستخدمين الإجمالي: {count}")
        else:
            bot.reply_to(message, "📊 عدد المستخدمين الحالي: 0")
    else:
        # الرد على أي شخص آخر يحاول كتابة الأمر
        bot.reply_to(message, "⛔️ عذراً، هذا الأمر مخصص لمطور البوت فقط ولا يمكنك استخدامه.")

# الرد الترحيبي عند بدء البوت
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    register_user(message) # تسجيل المستخدم إذا كان جديداً
    bot.reply_to(message, "أهلاً بك! 🌟\nأرسل لي أي صورة تحتوي على نص (عربي أو إنجليزي) وسأقوم باستخراجه لك فوراً.")

# معالجة الصور واستخراج النص
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    register_user(message) # تسجيل المستخدم إذا كان جديداً
    try:
        msg = bot.reply_to(message, "⏳ جاري معالجة الصورة واستخراج النص، يرجى الانتظار...")
        
        # الحصول على معلومات الصورة (بأعلى دقة متوفرة)
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # حفظ الصورة مؤقتاً على مساحة العمل
        file_name = "temp_image.jpg"
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        # استخراج النص باستخدام Tesseract
        img = Image.open(file_name)
        text = pytesseract.image_to_string(img, lang='ara+eng')

        # إرسال النص للمستخدم إذا تم العثور عليه بنجاح
        if text.strip():
            bot.edit_message_text(f"📝 **النص المستخرج:**\n\n{text}", chat_id=message.chat.id, message_id=msg.message_id)
        else:
            bot.edit_message_text("❌ لم أتمكن من العثور على أي نص واضح في هذه الصورة.", chat_id=message.chat.id, message_id=msg.message_id)

        # حذف الصورة المؤقتة لتوفير المساحة
        os.remove(file_name)
        
    except Exception as e:
        bot.reply_to(message, "⚠️ عذراً، حدث خطأ أثناء معالجة الصورة. تأكد من أن الصورة واضحة.")
        print(f"Error: {e}")

# تشغيل البوت باستمرار
print("البوت يعمل الآن... بانتظار الصور!")
bot.infinity_polling()

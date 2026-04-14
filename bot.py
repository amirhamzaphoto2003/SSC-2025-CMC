import requests
import asyncio
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import os
import urllib3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# SSL ওয়ার্নিং বন্ধ রাখা
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------- ১. ফ্লাস্ক সার্ভার (Render Keep Alive) -----------
app = Flask('')
@app.route('/')
def home(): return "Multi-Board SSC Scanner is Live!"

def run():
    # রেন্ডার অটোমেটিক পোর্ট সেট করে নেয়
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# ----------- ২. কনফিগারেশন -----------
BOT_TOKEN = "8780159859:AAE-a6WVrYlkVXnLZXsDUe43TaszpVq8ra4"
user_preferences = {} # ইউজারের বোর্ড সিলেকশন সেভ করার জন্য

# ----------- ৩. স্ক্র্যাপার লজিক (বোর্ড অনুযায়ী আলাদা) -----------

# --- কুমিল্লা বোর্ড লজিক ---
def fetch_cumilla(roll):
    url = "https://result19.comillaboard.gov.bd/2025/individual/result.php"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://result19.comillaboard.gov.bd/2025/individual/"
    }
    try:
        r = requests.post(url, data={"roll": roll}, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        info = {}
        all_tds = soup.find_all("td")
        for i, td in enumerate(all_tds):
            text = td.get_text(strip=True)
            if "Name" == text: info['name'] = all_tds[i+1].get_text(strip=True)
            elif "Father's Name" == text: info['father'] = all_tds[i+1].get_text(strip=True)
            elif "Mother's Name" == text: info['mother'] = all_tds[i+1].get_text(strip=True)
            elif "Group" == text: info['group'] = all_tds[i+1].get_text(strip=True)
            elif "GPA" == text: info['gpa'] = all_tds[i+1].get_text(strip=True)
            elif "Institute" == text: info['institute'] = all_tds[i+1].get_text(strip=True)
        
        subjects = []
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3 and cols[0].get_text(strip=True).isdigit():
                subjects.append(f"{cols[0].get_text(strip=True)} → {cols[1].get_text(strip=True)} → {cols[2].get_text(strip=True)}")
        return info, subjects
    except: return None, None

# --- চট্টগ্রাম বোর্ড লজিক ---
def fetch_ctg(roll):
    url = "https://sresult.bise-ctg.gov.bd/rxto2025/individual/result.php"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://sresult.bise-ctg.gov.bd/rxto2025/individual/"}
    try:
        r = requests.post(url, data={"roll": roll, "button2": "Submit"}, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        info = {}
        all_tds = soup.find_all("td")
        for i, td in enumerate(all_tds):
            text = td.get_text(strip=True)
            if "Name" == text: info['name'] = all_tds[i+1].get_text(strip=True)
            elif "Father's Name" == text: info['father'] = all_tds[i+1].get_text(strip=True)
            elif "Mother's Name" == text: info['mother'] = all_tds[i+1].get_text(strip=True)
            elif "Reg. NO" == text: info['reg'] = all_tds[i+1].get_text(strip=True)
            elif "DATE OF BIRTH" == text: info['dob'] = all_tds[i+1].get_text(strip=True)
            elif "Group" == text: info['group'] = all_tds[i+1].get_text(strip=True)
            elif "GPA" in text: info['gpa'] = text.split("=")[-1].strip()
            elif "Institute" == text: info['institute'] = all_tds[i+1].get_text(strip=True)
        
        subjects = []
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 3 and cols[0].get_text(strip=True).isdigit() and len(cols[0].get_text(strip=True)) == 3:
                subjects.append(f"{cols[0].get_text(strip=True)} → {cols[1].get_text(strip=True)} → {cols[2].get_text(strip=True)}")
        return info, subjects
    except: return None, None

# --- ময়মনসিংহ বোর্ড লজিক (FIXED) ---
def fetch_mym(roll):
    main_page = "https://www.mymensingheducationboard.gov.bd/resultmbs25/"
    post_url = "https://www.mymensingheducationboard.gov.bd/resultmbs25/result.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": main_page,
        "Origin": "https://www.mymensingheducationboard.gov.bd",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        s = requests.Session()
        s.get(main_page, headers=headers, verify=False, timeout=10)
        # পেলোড ডিকশনারি আকারে পাঠানো হলো
        payload = {"roll": str(roll)}
        r = s.post(post_url, data=payload, headers=headers, timeout=15, verify=False)
        
        if "Result" not in r.text and "Name" not in r.text: return None, None
        
        soup = BeautifulSoup(r.text, "html.parser")
        info = {}
        tds = soup.find_all("td")
        for i, td in enumerate(tds):
            txt = td.get_text(strip=True)
            if i+1 < len(tds):
                val = tds[i+1].get_text(strip=True)
                if "Name" == txt: info['name'] = val
                elif "Father's Name" == txt: info['father'] = val
                elif "Mother's Name" == txt: info['mother'] = val
                elif "Group" == txt: info['group'] = val
                elif "Session" == txt: info['session'] = val
                elif "Passing Year" == txt: info['year'] = val
                elif "Type" == txt: info['type'] = val
                elif "Center" == txt: info['center'] = val
                elif "Result" == txt: info['gpa'] = val.replace("GPA=", "")
                elif "Institute" == txt: info['institute'] = val

        subjects = []
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 2:
                s_name, grade = cols[0].get_text(strip=True), cols[1].get_text(strip=True)
                if s_name != "Subject" and len(grade) <= 2: 
                    subjects.append(f"{s_name} → {grade}")
        return info, subjects
    except: return None, None

# ----------- ৪. বট হ্যান্ডলারস -----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # বাটন লেআউট ঠিক আপনার ছবির মতো
    keyboard = [["Cumilla", "Chattogram"], ["Mymensingh"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 স্বাগতম! নিচের বাটন থেকে আপনার বোর্ড সিলেক্ট করুন:", 
        reply_markup=reply_markup
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat.id

    # বোর্ড সিলেকশন হ্যান্ডলিং
    if text in ["Cumilla", "Chattogram", "Mymensingh"]:
        user_preferences[chat_id] = text
        await update.message.reply_text(f"✅ আপনি **{text}** সিলেক্ট করেছেন। এবার রোল নম্বর দিন।")
        return

    # রোল নম্বর হ্যান্ডলিং
    if text.isdigit():
        board = user_preferences.get(chat_id)
        if not board:
            await update.message.reply_text("❌ আগে বাটন থেকে বোর্ড সিলেক্ট করুন।")
            return

        status = await update.message.reply_text(f"⏳ Processing {board} Board Roll: {text}...")
        
        # বোর্ড অনুযায়ী স্ক্র্যাপার কল
        if board == "Cumilla": info, subjects = fetch_cumilla(text)
        elif board == "Chattogram": info, subjects = fetch_ctg(text)
        else: info, subjects = fetch_mym(text)
        
        if info and info.get('name'):
            await status.delete()
            sub_text = "\n".join(subjects)
            
            # আউটপুট ফরম্যাটিং
            final_msg = f"🧑‍🎓 <b>STUDENT INFORMATION</b>\n━━━━━━━━━━━━━━\n\n"
            final_msg += f"👤 Name: {info.get('name')}\n👨 Father: {info.get('father')}\n👩 Mother: {info.get('mother')}\n"
            if board == "Chattogram": final_msg += f"📅 Date of Birth: {info.get('dob')}\n"
            
            final_msg += f"\n━━━━━━━━━━━━━━\n📘 <b>SSC RESULT {info.get('year', '2025')}</b>\n━━━━━━━━━━━━━━\n\n"
            final_msg += f"🆔 Roll No: {text}\n"
            if board == "Chattogram": final_msg += f"📄 Registration No: {info.get('reg')}\n"
            final_msg += f"🏫 Board: {board.upper()}\n📚 Group: {info.get('group')}\n"
            
            if board == "Mymensingh":
                final_msg += f"📅 Session: {info.get('session')}\n📝 Type: {info.get('type')}\n"
            
            final_msg += f"\n📊 Result: GPA: {info.get('gpa')}\n\n🏫 Institute: {info.get('institute')}\n"
            if board == "Mymensingh": final_msg += f"📍 Center: {info.get('center')}\n"
            
            final_msg += f"\n📊 <b>SUBJECTS</b>\n━━━━━━━━━━━━━━\n<pre>{sub_text}</pre>"
            await update.message.reply_text(final_msg, parse_mode="HTML")
        else:
            await status.edit_text("❌ রেজাল্ট পাওয়া যায়নি। রোল সঠিক কি না চেক করুন।")

if __name__ == "__main__":
    keep_alive() # রেন্ডারের জন্য ফ্লাস্ক স্টার্ট
    app_tg = ApplicationBuilder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("Bot is Running...")
    app_tg.run_polling()

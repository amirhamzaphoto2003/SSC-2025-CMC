import requests
import asyncio
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
import os
import urllib3
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------- ১. ফ্লাস্ক সার্ভার -----------
app = Flask('')
@app.route('/')
def home(): return "SSC Master Bot is Live!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    Thread(target=run).start()

# ----------- ২. কনফিগারেশন -----------
BOT_TOKEN = "8780159859:AAE-a6WVrYlkVXnLZXsDUe43TaszpVq8ra4"
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}

# ----------- ৩. প্রতিটি বোর্ডের আলাদা লজিক ও আউটপুট -----------

# --- কুমিল্লা বোর্ড ---
def fetch_comilla(roll):
    url = "https://result19.comillaboard.gov.bd/2025/individual/result.php"
    try:
        r = session.post(url, data={"roll": roll}, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        info, subjects = {}, []
        tds = soup.find_all("td")
        for i, td in enumerate(tds):
            txt = td.get_text(strip=True)
            if "Name" == txt: info['name'] = tds[i+1].get_text(strip=True)
            elif "Father's Name" == txt: info['father'] = tds[i+1].get_text(strip=True)
            elif "Mother's Name" == txt: info['mother'] = tds[i+1].get_text(strip=True)
            elif "Group" == txt: info['group'] = tds[i+1].get_text(strip=True)
            elif "GPA" == txt: info['gpa'] = tds[i+1].get_text(strip=True)
            elif "Institute" == txt: info['institute'] = tds[i+1].get_text(strip=True)
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 3 and cols[0].get_text(strip=True).isdigit():
                subjects.append(f"{cols[0].get_text(strip=True)} → {cols[1].get_text(strip=True)} → {cols[2].get_text(strip=True)}")
        
        if not info.get('name'): return None
        return (f"🧑‍🎓 <b>STUDENT INFORMATION</b>\n━━━━━━━━━━━━━━\n\n👤 Name: {info.get('name')}\n👨 Father: {info.get('father')}\n👩 Mother: {info.get('mother')}\n\n━━━━━━━━━━━━━━\n📘 <b>SSC RESULT 2025</b>\n━━━━━━━━━━━━━━\n\n🆔 Roll No: {roll}\n🏫 Board: COMILLA\n📚 Group: {info.get('group')}\n\n📊 Result: GPA: {info.get('gpa')}\n\n🏫 Institute: {info.get('institute')}\n\n📊 <b>SUBJECTS</b>\n━━━━━━━━━━━━━━\n<pre>" + "\n".join(subjects) + "</pre>")
    except: return None

# --- চট্টগ্রাম বোর্ড ---
def fetch_chattogram(roll):
    url = "https://sresult.bise-ctg.gov.bd/rxto2025/individual/result.php"
    try:
        r = session.post(url, data={"roll": roll, "button2": "Submit"}, headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        info, subjects = {}, []
        tds = soup.find_all("td")
        for i, td in enumerate(tds):
            txt = td.get_text(strip=True)
            if "Name" == txt: info['name'] = tds[i+1].get_text(strip=True)
            elif "Father's Name" == txt: info['father'] = tds[i+1].get_text(strip=True)
            elif "Mother's Name" == txt: info['mother'] = tds[i+1].get_text(strip=True)
            elif "Reg. NO" == txt: info['reg'] = tds[i+1].get_text(strip=True)
            elif "DATE OF BIRTH" == txt: info['dob'] = tds[i+1].get_text(strip=True)
            elif "Group" == txt: info['group'] = tds[i+1].get_text(strip=True)
            elif "GPA" in txt: info['gpa'] = txt.split("=")[-1].strip()
            elif "Institute" == txt: info['institute'] = tds[i+1].get_text(strip=True)
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 3 and cols[0].get_text(strip=True).isdigit():
                subjects.append(f"{cols[0].get_text(strip=True)} → {cols[1].get_text(strip=True)} → {cols[2].get_text(strip=True)}")
        
        if not info.get('name'): return None
        return (f"🧑‍🎓 <b>STUDENT INFORMATION</b>\n━━━━━━━━━━━━━━\n\n👤 Name: {info.get('name')}\n👨 Father: {info.get('father')}\n👩 Mother: {info.get('mother')}\n📅 Date of Birth: {info.get('dob')}\n\n━━━━━━━━━━━━━━\n📘 <b>SSC RESULT 2025</b>\n━━━━━━━━━━━━━━\n\n🆔 Roll No: {roll}\n📄 Registration No: {info.get('reg')}\n🏫 Board: CHATTOGRAM\n📚 Group: {info.get('group')}\n\n📊 Result: GPA: {info.get('gpa')}\n\n🏫 Institute: {info.get('institute')}\n\n📊 <b>SUBJECTS</b>\n━━━━━━━━━━━━━━\n<pre>" + "\n".join(subjects) + "</pre>")
    except: return None

# --- ময়মনসিংহ বোর্ড ---
def fetch_mymensingh(roll):
    main = "https://www.mymensingheducationboard.gov.bd/resultmbs25/"
    url = "https://www.mymensingheducationboard.gov.bd/resultmbs25/result.php"
    try:
        session.get(main, headers=headers, verify=False, timeout=10)
        r = session.post(url, data=f"roll={roll}", headers=headers, timeout=15, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        info, subjects = {}, []
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
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                name, grade = cols[0].get_text(strip=True), cols[1].get_text(strip=True)
                if name != "Subject" and len(grade) <= 2: subjects.append(f"{name} → {grade}")
        
        if not info.get('name'): return None
        return (f"🧑‍🎓 <b>STUDENT INFORMATION</b>\n━━━━━━━━━━━━━━\n\n👤 Name: {info.get('name')}\n👨 Father: {info.get('father')}\n👩 Mother: {info.get('mother')}\n\n━━━━━━━━━━━━━━\n📘 <b>SSC RESULT {info.get('year', '2025')}</b>\n━━━━━━━━━━━━━━\n\n🆔 Roll No: {roll}\n🏫 Board: MYMENSINGH\n📚 Group: {info.get('group')}\n📅 Session: {info.get('session')}\n📝 Type: {info.get('type')}\n\n📊 Result: GPA: {info.get('gpa')}\n\n🏫 Institute: {info.get('institute')}\n📍 Center: {info.get('center')}\n\n📊 <b>SUBJECTS</b>\n━━━━━━━━━━━━━━\n<pre>" + "\n".join(subjects) + "</pre>")
    except: return None

# ----------- ৪. টেলিগ্রাম বট কন্ট্রোল -----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎓 Cumilla Board", callback_data='comilla')],
        [InlineKeyboardButton("🎓 Chattogram Board", callback_data='chattogram')],
        [InlineKeyboardButton("🎓 Mymensingh Board", callback_data='mymensingh')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("SSC 2025 রেজাল্ট বটে স্বাগতম!\nনিচ থেকে বোর্ড সিলেক্ট করুন:", reply_markup=reply_markup)

async def button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['board'] = query.data
    await query.edit_message_text(text=f"✅ আপনি {query.data.upper()} বোর্ড সিলেক্ট করেছেন।\nএখন রোল নম্বরটি লিখে পাঠান।")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = update.message.text.strip()
    board = context.user_data.get('board')
    if not board:
        await update.message.reply_text("আগে /start দিয়ে বোর্ড সিলেক্ট করুন!")
        return
    if not roll.isdigit(): return

    status = await update.message.reply_text(f"⏳ {board.upper()} ডাটা প্রসেস হচ্ছে...")
    
    output = None
    if board == "comilla": output = fetch_comilla(roll)
    elif board == "chattogram": output = fetch_chattogram(roll)
    elif board == "mymensingh": output = fetch_mymensingh(roll)

    if output:
        await status.delete()
        await update.message.reply_text(output, parse_mode="HTML")
    else:
        await status.edit_text("❌ রেজাল্ট পাওয়া যায়নি।")

if __name__ == "__main__":
    keep_alive()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_tap))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    bot.run_polling()

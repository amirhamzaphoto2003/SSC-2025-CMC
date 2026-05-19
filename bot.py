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
def home(): 
    return "Multi-Board SSC Scanner (Cumilla & Chattogram) is Live!"

def run():
    # রেন্ডার অটোমেটিক পোর্ট সেট করে নেয়
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# ----------- ২. কনফিগারেশন -----------
BOT_TOKEN = "8780159859:AAE-a6WVrYlkVXnLZXsDUe43TaszpVq8ra4"
user_preferences = {} # ইউজারের বোর্ড সিলেকশন সেভ করার জন্য

# ----------- ৩. স্ক্র্যাপার লজিক (সুরক্ষিত ট্রাই-এক্সেপ্ট সহ) -----------

# --- কুমিল্লা বোর্ড লজিক ---
def fetch_cumilla(roll):
    url = "https://result19.comillaboard.gov.bd/2025/individual/result.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://result19.comillaboard.gov.bd/2025/individual/"
    }
    try:
        r = requests.post(url, data={"roll": roll}, headers=headers, timeout=15, verify=False)
        if r.status_code != 200 or "Name" not in r.text:
            return None, None
            
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
    except Exception as e:
        print(f"Cumilla Board Connection Error: {e}")
        return None, None

# --- চট্টগ্রাম বোর্ড লজিক ---
def fetch_ctg(roll):
    url = "https://sresult.bise-ctg.gov.bd/rxto2025/individual/result.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
        "Referer": "https://sresult.bise-ctg.gov.bd/rxto2025/individual/"
    }
    try:
        r = requests.post(url, data={"roll": roll, "button2": "Submit"}, headers=headers, timeout=15, verify=False)
        if r.status_code != 200 or "Name" not in r.text:
            return None, None
            
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
    except Exception as e:
        print(f"Chattogram Board Connection Error: {e}")
        return None, None

# ----------- ৪. বট হ্যান্ডলারস -----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # বাটন লেআউট থেকে ময়মনসিংহ বাদ দিয়ে শুধুমাত্র সচল দুটি বোর্ড রাখা হয়েছে
    keyboard = [["Cumilla", "Chattogram"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 স্বাগতম! নিচের বাটন থেকে আপনার বোর্ড সিলেক্ট করুন:", 
        reply_markup=reply_markup
    )

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat.id

    # বোর্ড সিলেকশন হ্যান্ডলিং
    if text in ["Cumilla", "Chattogram"]:
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
        
        info, subjects = None, None
        # বোর্ড অনুযায়ী স্ক্র্যাপার কল (ট্রাই-এক্সেপ্ট প্রোটেকশন সহ)
        try:
            if board == "Cumilla": 
                info, subjects = fetch_cumilla(text)
            elif board == "Chattogram": 
                info, subjects = fetch_ctg(text)
        except Exception as queue_error:
            print(f"Scraping Execution Error: {queue_error}")
        
        if info and info.get('name'):
            try:
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
                
                final_msg += f"\n📊 Result: GPA: {info.get('gpa')}\n\n🏫 Institute: {info.get('institute')}\n"
                final_msg += f"\n📊 <b>SUBJECTS</b>\n━━━━━━━━━━━━━━\n<pre>{sub_text}</pre>"
                
                await update.message.reply_text(final_msg, parse_mode="HTML")
            except Exception as send_error:
                await update.message.reply_text("❌ ডেটা প্রসেস বা মেসেজ পাঠাতে সমস্যা হয়েছে।")
                print(f"Message Sending Error: {send_error}")
        else:
            await status.edit_text(f"❌ {board} বোর্ডের সার্ভার রেসপন্স করছে না অথবা রোল নম্বরটি সঠিক নয়।")
    else:
        await update.message.reply_text("❌ দয়া করে একটি সঠিক রোল নম্বর অথবা মেনু থেকে বোর্ড সিলেক্ট করুন।")

if __name__ == "__main__":
    keep_alive() # রেন্ডারের জন্য ফ্লাস্ক সার্ভার স্টার্ট
    app_tg = ApplicationBuilder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("Bot is Running with Dual-Board Stability...")
    app_tg.run_polling()

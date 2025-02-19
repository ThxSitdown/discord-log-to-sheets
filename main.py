import discord
import os
import gspread
import json
import re
import logging
import threading
import requests
import time
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from discord.ext import commands  # ✅ เพิ่ม import

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)  # ✅ เปลี่ยนจาก Client เป็น Bot

# ตั้งค่า Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

@app.route('/health')
def health_check():
    return {"status": "ok", "bot_status": bot.is_ready()}

def run_flask():
    try:
        logging.info("🌍 Starting Flask on port 5000...")
        app.run(host="0.0.0.0", port=5000, threaded=True)
    except Exception as e:
        logging.error(f"❌ Flask app error: {e}")

@bot.event
async def on_ready():
    logging.info(f"🤖 {bot.user} is online and ready!")
    await bot.change_presence(activity=discord.Game(name="Roblox"))

    if sheet:
        try:
            test_value = sheet.acell("A1").value
            logging.info(f"✅ Google Sheets เชื่อมต่อสำเร็จ! (Test Read: A1 = {test_value})")
        except Exception as e:
            logging.error(f"❌ ไม่สามารถเชื่อมต่อ Google Sheets: {e}")

# ✅ รับข้อมูลเฉพาะจากห้องที่มี ID = 1341317415367082006 เท่านั้น
TARGET_CHANNEL_ID = 1341317415367082006  # 🔥 กำหนดค่า ID ห้องที่ต้องการให้รับข้อมูล

@bot.event
async def on_message(message):
    if message.channel.id == TARGET_CHANNEL_ID:  # ✅ ตรวจสอบห้องที่กำหนด
        if message.author.bot and message.author.name == "Captain Hook":  
            logging.info("📥 ได้รับข้อความจาก Captain Hook ในห้องที่กำหนด")

            # ใช้ Regular Expression ดึงข้อมูล
            pattern = r"ชื่อ\s*\n(.+?)\s*\nไอดี\s*\n(.+?)\s*\nเวลาเข้างาน\s*\n(.+?)\s*\nเวลาออกงาน\s*\n(.+?)\s*\n"
            match = re.search(pattern, message.content, re.DOTALL)

            if match:
                name = match.group(1).strip()
                steam_id = match.group(2).strip()
                check_in_time = match.group(3).strip()
                check_out_time = match.group(4).strip()

                logging.info(f"📌 บันทึกข้อมูล: {name}, {steam_id}, {check_in_time}, {check_out_time}")

                if sheet:
                    try:
                        sheet.append_row([name, steam_id, check_in_time, check_out_time])
                        logging.info("✅ ข้อมูลถูกบันทึกลง Google Sheets สำเร็จ")
                    except Exception as e:
                        logging.error(f"❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล Google Sheets: {e}")

    await bot.process_commands(message)  # ✅ ใช้ได้แล้ว

# ตั้งค่า Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
sheet = None

if GOOGLE_CREDENTIALS:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open("PoliceDuty").worksheet("Sheet1")
        logging.info("✅ Google Sheets setup completed.")
    except Exception as e:
        logging.error(f"❌ Error loading Google Sheets credentials: {e}")
else:
    logging.warning("⚠️ GOOGLE_CREDENTIALS not found.")

# ฟังก์ชันสำหรับรัน Discord Bot
def run_discord_bot():
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not DISCORD_BOT_TOKEN:
        logging.error("❌ DISCORD_BOT_TOKEN not found. Bot will not start.")
        return
    
    try:
        logging.info("🚀 Starting Discord Bot...")
        bot.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure:
        logging.error("❌ Invalid Discord Bot Token! กรุณาตรวจสอบโทเค็นของคุณ.")
    except Exception as e:
        logging.error(f"❌ Discord bot encountered an error: {e}")

# ฟังก์ชัน Keep-Alive
KEEP_ALIVE_URL = "https://discord-log-to-sheets.onrender.com/health"

def keep_alive():
    while True:
        try:
            response = requests.get(KEEP_ALIVE_URL)
            if response.status_code == 200:
                logging.info("✅ Keep-alive successful.")
            else:
                logging.warning(f"⚠️ Keep-alive failed (Status: {response.status_code})")
        except Exception as e:
            logging.error(f"❌ Keep-alive error: {e}")
        time.sleep(40)

# Main
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    run_discord_bot()

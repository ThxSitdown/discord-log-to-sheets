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

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = discord.Client(intents=intents)

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
            logging.info("✅ Google Sheets เชื่อมต่อสำเร็จ! (Test Read: A1 = {test_value})")
        except Exception as e:
            logging.error(f"❌ ไม่สามารถเชื่อมต่อ Google Sheets: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ALLOWED_CHANNEL_ID = 1341317415367082006  # ใส่ ID ของห้องที่ต้องการให้บอทฟัง

    if message.channel.id != ALLOWED_CHANNEL_ID:
        return  # ข้ามข้อความจากห้องอื่น

    logging.info(f"📩 ข้อความใหม่จาก {message.author}: {message.content}")

    try:
        # ปรับปรุง regex ให้ครอบคลุมข้อมูลที่เพิ่มเข้ามา
        pattern = r"รายงานเข้าเวรของ\s*-\s*(.+?)\s*\n" \
                  r"รายได้\s*\n(.+?)\s*\n" \
                  r"ระยะเวลาที่เข้าเวร\s*\n(.+?)\s*\n" \
                  r"ชื่อ\s*\n(.+?)\s*\n" \
                  r"ไอดี\s*\n(.+?)\s*\n" \
                  r"เวลาเข้างาน\s*\n(.+?)\s*\n" \
                  r"เวลาออกงาน\s*\n(.+?)\s*\n" \
                  r"งาน\s*\n(.+?)$"

        match = re.search(pattern, message.content, re.DOTALL)

        if match:
            officer_name = match.group(1).strip()
            income = match.group(2).strip()
            duty_duration = match.group(3).strip()
            steam_name = match.group(4).strip()
            steam_id = match.group(5).strip()
            start_time = match.group(6).strip()
            end_time = match.group(7).strip()
            job = match.group(8).strip()

            logging.info(f"✅ ข้อมูลที่ดึงได้: {officer_name}, {income}, {duty_duration}, {steam_name}, {steam_id}, {start_time}, {end_time}, {job}")

            if sheet:
                try:
                    sheet.append_row([officer_name, income, duty_duration, steam_name, steam_id, start_time, end_time, job])
                    logging.info("✅ บันทึกข้อมูลลง Google Sheets สำเร็จ!")
                    await message.channel.send("✅ ข้อมูลถูกบันทึกเรียบร้อยแล้ว!")
                except Exception as e:
                    logging.error(f"❌ เกิดข้อผิดพลาดในการบันทึกข้อมูล Google Sheets: {e}")
                    await message.channel.send("❌ บันทึกข้อมูลไม่สำเร็จ โปรดลองอีกครั้ง.")
            else:
                await message.channel.send("⚠️ Google Sheets ยังไม่ได้รับการตั้งค่า.")
        else:
            logging.warning("⚠️ รูปแบบข้อความไม่ถูกต้อง!")
            await message.channel.send("⚠️ กรุณาส่งข้อมูลให้ถูกต้องตามแบบฟอร์ม.")
    
    except Exception as e:
        logging.error(f"❌ Error processing message: {e}")
        await message.channel.send("❌ เกิดข้อผิดพลาด โปรดลองอีกครั้ง.")

    await bot.process_commands(message)  # รองรับคำสั่งของบอท

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

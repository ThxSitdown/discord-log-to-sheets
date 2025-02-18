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
        logging.info("Starting Flask on port 5000...")
        app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        logging.error(f"Flask app encountered an error: {e}")

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    logging.info(f"{bot.user} is online and ready!")
    await bot.change_presence(activity=discord.Game(name="Roblox"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ALLOWED_CHANNEL_NAME = "#📁◜police-duty"  # ใช้ชื่อห้อง
    ALLOWED_CHANNEL_ID = 1341317415367082006  # หรือใช้ ID ของห้อง
    
    if message.channel.name != ALLOWED_CHANNEL_NAME and message.channel.id != ALLOWED_CHANNEL_ID:
        return  # ข้ามข้อความจากห้องอื่น

    try:
        # Regular expression ใหม่ที่รองรับฟอร์แมตข้อมูลในภาพ
        match = re.search(
            r"ชื่อ\s*\n(.+?)\s*\n"         # ดึงชื่อ
            r"เวลาเข้างาน\s*\n(.+?)\s*\n"  # ดึงเวลาเข้างาน
            r"เวลาออกงาน\s*\n(.+)",        # ดึงเวลาออกงาน
            message.content,
            re.DOTALL
        )

        if match:
            steam_name = match.group(1).strip()
            start_time = match.group(2).strip()
            end_time = match.group(3).strip()

            logging.info(f"Received data: {steam_name}, {start_time}, {end_time}")

            if sheet:
                try:
                    # Append data to Google Sheets
                    last_row = len(sheet.col_values(1)) + 1
                    sheet.update(f"A{last_row}:C{last_row}", [[steam_name, start_time, end_time]])
                    logging.info(f"Data written to Google Sheets at row {last_row}: {steam_name}, {start_time}, {end_time}")
                    await message.channel.send("ข้อมูลถูกบันทึกเรียบร้อยแล้ว!")

                except Exception as e:
                    logging.error(f"Error writing to Google Sheets: {e}")
                    await message.channel.send("เกิดข้อผิดพลาดในการบันทึกข้อมูลไปยัง Google Sheets.")
            else:
                await message.channel.send("Google Sheets ยังไม่ได้รับการตั้งค่า.")
        else:
            await message.channel.send("รูปแบบข้อความไม่ถูกต้อง โปรดตรวจสอบอีกครั้ง.")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.channel.send("เกิดข้อผิดพลาดบางอย่าง โปรดลองอีกครั้ง.")

# ตั้งค่า Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
sheet = None

if GOOGLE_CREDENTIALS:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open("PoliceDuty").worksheet("Sheet1")
        logging.info("Google Sheets setup completed.")
    except Exception as e:
        logging.error(f"Error loading Google Sheets credentials: {e}")
else:
    logging.warning("GOOGLE_CREDENTIALS not found.")

# ฟังก์ชันสำหรับรัน Discord Bot
def run_discord_bot():
    try:
        logging.info("Starting Discord Bot...")
        bot.run(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        logging.error(f"Discord bot encountered an error: {e}")
        raise

# ฟังก์ชัน Keep-Alive
KEEP_ALIVE_URL = "https://discord-log-to-sheets.onrender.com/health"

def keep_alive():
    while True:
        try:
            response = requests.get(KEEP_ALIVE_URL)
            if response.status_code == 200:
                logging.info("Keep-alive successful.")
            else:
                logging.warning(f"Keep-alive failed with status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Keep-alive error: {e}")
        time.sleep(40)

# Main
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    run_discord_bot()

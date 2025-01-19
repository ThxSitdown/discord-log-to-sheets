import discord
import os
import gspread
import json
import re
import time
import logging
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
import threading

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ตั้งค่า Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

# ฟังก์ชันสำหรับรัน Flask App
def run_flask():
    try:
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
    logging.info(f"Connected to the following guilds: {[guild.name for guild in bot.guilds]}")
    await bot.change_presence(activity=discord.Game(name="พร้อมใช้งาน!"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "Police Shift" in message.content:
        # ใช้ Regex เพื่อดึงข้อมูล
        match = re.search(
            r"Steam Name:\s*(.+?)\s*\n"
            r"(?:Identifier:.*?\n)?"  # ข้าม Identifier หากมี
            r"Shift duration:\s*(.+?)\s*\n"
            r"Start date:\s*(.+?)\s*\n"
            r"End date:\s*(.+)",
            message.content,
            re.DOTALL
        )

        if match:
            steam_name = match.group(1).strip()
            shift_duration = match.group(2).strip()
            start_date = match.group(3).strip()
            end_date = match.group(4).strip()

            logging.info(f"Received data: {steam_name}, {shift_duration}, {start_date}, {end_date}")

            if sheet:
                try:
                    sheet.append_row([steam_name, shift_duration, start_date, end_date])
                    await message.channel.send("ข้อมูลถูกบันทึกเรียบร้อยแล้ว!")
                except Exception as e:
                    logging.error(f"Error writing to Google Sheets: {e}")
                    await message.channel.send("เกิดข้อผิดพลาดในการบันทึกข้อมูลไปยัง Google Sheets.")
            else:
                await message.channel.send("Google Sheets ยังไม่ได้รับการตั้งค่า.")
        else:
            await message.channel.send("รูปแบบข้อความไม่ถูกต้อง โปรดตรวจสอบอีกครั้ง.")

# ตั้งค่า Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
sheet = None

if GOOGLE_CREDENTIALS:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open("PoliceDuty").sheet1
        logging.info("Google Sheets setup completed.")
    except Exception as e:
        logging.error(f"Error loading Google Sheets credentials: {e}")
else:
    logging.warning("GOOGLE_CREDENTIALS not found.")

# ฟังก์ชันสำหรับรัน Discord Bot
def run_discord_bot():
    while True:
        try:
            logging.info("Starting Discord Bot...")
            bot.run(os.getenv("DISCORD_BOT_TOKEN"))
        except Exception as e:
            logging.error(f"Discord bot encountered an error: {e}")
            time.sleep(5)  # รอ 5 วินาทีก่อนเริ่มใหม่

# รัน Flask และ Discord Bot พร้อมกัน
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_discord_bot()

import discord
import os
import gspread
import json
import re
import time
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
import threading

# ตั้งค่า Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} พร้อมใช้งาน!")
    await bot.change_presence(activity=discord.Game(name="พร้อมใช้งาน!"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "Police Shift" in message.content:
        # แก้ไข Regex เพื่อไม่ต้องจับ Identifier
        match = re.search(
            r"Steam Name:\s*(.+?)\s*\n"          # จับ Steam Name
            r"(?:Identifier:.*?\n)?"             # ข้าม Identifier หากมี
            r"Shift duration:\s*(.+?)\s*\n"      # จับ Shift duration
            r"Start date:\s*(.+?)\s*\n"          # จับ Start date
            r"End date:\s*(.+)",                 # จับ End date
            message.content,
            re.DOTALL  # รองรับข้อความหลายบรรทัด
        )

        if match:
            steam_name = match.group(1).strip()
            shift_duration = match.group(2).strip()
            start_date = match.group(3).strip()
            end_date = match.group(4).strip()

            print(f"Debug: {steam_name}, {shift_duration}, {start_date}, {end_date}")

            if sheet:
                try:
                    sheet.append_row([steam_name, shift_duration, start_date, end_date])
                    await message.channel.send("ข้อมูลถูกบันทึกเรียบร้อยแล้ว!")
                except Exception as e:
                    print(f"Error writing to Google Sheets: {e}")
                    await message.channel.send("เกิดข้อผิดพลาดในการบันทึกข้อมูลไปยัง Google Sheets.")
            else:
                await message.channel.send("Google Sheets ยังไม่ได้รับการตั้งค่า.")
        else:
            await message.channel.send("รูปแบบข้อความไม่ถูกต้อง โปรดตรวจสอบอีกครั้ง.")

# ตั้งค่า Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

if GOOGLE_CREDENTIALS:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open("PoliceDuty").sheet1
    except Exception as e:
        print(f"Error loading Google Sheets credentials: {e}")
        sheet = None
else:
    print("GOOGLE_CREDENTIALS not found.")
    sheet = None

# ฟังก์ชันสำหรับรัน Discord Bot
def run_discord_bot():
    while True:
        try:
            bot.run(os.getenv("DISCORD_BOT_TOKEN"))
        except Exception as e:
            print(f"Discord bot encountered an error: {e}")
            time.sleep(5)  # รอ 5 วินาทีก่อนเริ่มใหม่

# ฟังก์ชันสำหรับรัน Flask App
def run_flask_app():
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True)
    except Exception as e:
        print(f"Flask app encountered an error: {e}")

# รัน Discord Bot และ Flask App ใน Thread แยก
if __name__ == "__main__":
    threading.Thread(target=run_discord_bot, daemon=True).start()
    run_flask_app()

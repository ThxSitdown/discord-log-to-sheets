import discord
import os
import gspread
import json
import re
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
import threading

# ตั้งค่า Flask App สำหรับ Fake Port
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running."

# ฟังก์ชันสำหรับรัน Flask บนพอร์ต 5000
def run_flask():
    app.run(host="0.0.0.0", port=5000)

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ตั้งค่า Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

if GOOGLE_CREDENTIALS:
    try:
        # ใช้ from_json_keyfile_dict แทนการโหลดจากไฟล์
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDENTIALS), SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open("PoliceDuty").sheet1

        # ตรวจสอบว่ามีหัวข้อหรือยัง หากไม่มีให้เพิ่ม
        headers = sheet.row_values(1)
        if not headers or headers != ["Steam Name", "Shift duration", "Start date", "End date"]:
            sheet.insert_row(["Steam Name", "Shift duration", "Start date", "End date"], index=1)

    except Exception as e:
        print(f"Error loading Google Sheets credentials: {e}")
        sheet = None
else:
    print("GOOGLE_CREDENTIALS not found in environment variables.")
    sheet = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    print(f"ข้อความที่ได้รับ:\n{message.content}")
    
    if "Police Shift" in message.content:
        # ใช้ Regex เพื่อดึงข้อมูล Steam Name, Shift duration, Start date, End date
        match = re.search(
            r"Steam Name:\s*(.+?)\s*\n"   # จับ Steam Name
            r"Identifier:.*?\n"          # ข้าม Identifier
            r"Shift duration:\s*(.+?)\s*\n"  # จับ Shift Duration
            r"Start date:\s*(.+?)\s*\n"  # จับ Start Date
            r"End date:\s*(.+)",         # จับ End Date (แก้ไขให้รองรับข้อมูลมากขึ้น)
            message.content,
            re.DOTALL  # รองรับข้อความหลายบรรทัด
        )

        if match:
            steam_name = match.group(1).strip()
            shift_duration = match.group(2).strip()
            start_date = match.group(3).strip()
            end_date = match.group(4).strip()

            # Debug: แสดงข้อมูลที่จับได้
            print(f"Debug: Steam Name={steam_name}, Shift Duration={shift_duration}, Start Date={start_date}, End Date={end_date}")

            if sheet:
                try:
                    # เพิ่มข้อมูลลง Google Sheet
                    sheet.append_row([steam_name, shift_duration, start_date, end_date])
                
                except Exception as e:
                    print(f"Error writing to Google Sheets: {e}")
                    await message.channel.send("เกิดข้อผิดพลาดในการบันทึกข้อมูลลง Google Sheets.")
            else:
                await message.channel.send("Google Sheets ยังไม่ได้ตั้งค่า.")
        else:
            await message.channel.send("ไม่สามารถจับข้อมูลที่ต้องการได้ โปรดตรวจสอบรูปแบบข้อความอีกครั้ง.")

# ฟังก์ชันสำหรับรัน Discord Bot
def run_discord_bot():
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

# รัน Flask และ Discord Bot พร้อมกัน
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_discord_bot()

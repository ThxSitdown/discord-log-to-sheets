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

@bot.event
async def on_ready():
    print(f"{bot.user} พร้อมใช้งาน!")
    await bot.change_presence(activity=discord.Game(name="พร้อมใช้งาน!"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "Police Shift" in message.content:
        # ใช้ Regex เพื่อดึงข้อมูล
        match = re.search(
            r"Steam Name:\s*(.+?)\s*\n"
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

            print(f"Debug: {steam_name}, {shift_duration}, {start_date}, {end_date}")

            if sheet:
                try:
                    sheet.append_row([steam_name, shift_duration, start_date, end_date])
                except Exception as e:
                    print(f"Error writing to Google Sheets: {e}")
                    await message.channel.send("Error writing to Google Sheets.")
            else:
                await message.channel.send("Google Sheets not configured.")
        else:
            await message.channel.send("Invalid format.")

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
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

# รัน Flask และ Discord Bot พร้อมกัน
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_discord_bot()

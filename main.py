import discord
import os
import gspread
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
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open("testlog").sheet1
else:
    sheet = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    print(f"ข้อความที่ได้รับ:\n{message.content}")
    # คุณสามารถใส่ Logic สำหรับ Google Sheets ตรงนี้

# ฟังก์ชันสำหรับรัน Discord Bot
def run_discord_bot():
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

# รัน Flask และ Discord Bot พร้อมกัน
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    run_discord_bot()

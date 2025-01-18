import discord
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re  # สำหรับ Regex

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True  # เปิดใช้งานให้ Bot อ่านข้อความ
bot = discord.Client(intents=intents)

# ตั้งค่า Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")  # อ่าน JSON Credentials จากตัวแปร Environment
if GOOGLE_CREDENTIALS:
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open("testlog").sheet1  # เลือกชีตแรก
else:
    sheet = None  # ใช้ None หากไม่มี Google Sheets

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:  # ไม่บันทึกข้อความจากบอท
        return

    print(f"ข้อความที่ได้รับ:\n{message.content}")

    # ตรวจสอบว่าข้อความมีคำว่า "Police Shift"
    if "Police Shift" in message.content:
        match = re.search(
            r"Steam Name:\s*(.+?)\s*\n"   # จับ Steam Name
            r"Identifier:.*?\n"          # ข้าม Identifier
            r"Shift duration:\s*(.+?)\s*\n"  # จับ Shift Duration
            r"Start date:\s*(.+?)\s*\n"  # จับ Start Date
            r"End date:\s*(.+)",         # จับ End Date
            message.content,
            re.DOTALL  # รองรับข้อความหลายบรรทัด
        )
        if match:
            steam_name = match.group(1).strip()
            shift_duration = match.group(2).strip()
            start_date = match.group(3).strip()
            end_date = match.group(4).strip()

            if sheet:
                sheet.append_row([steam_name, shift_duration, start_date, end_date])
                print(f"บันทึกข้อมูล: {steam_name}, {shift_duration}, {start_date}, {end_date}")
            else:
                print("Google Sheets ยังไม่ได้ตั้งค่า")
        else:
            print("ไม่พบข้อมูลที่ตรงกับรูปแบบ 'Police Shift'")
    else:
        print("ข้อความไม่ได้อยู่ในรูปแบบที่ต้องการ")

# รัน Bot โดยใช้ Token จาก Environment
bot.run(os.getenv("DISCORD_BOT_TOKEN"))

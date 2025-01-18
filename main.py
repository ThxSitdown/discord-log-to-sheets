import discord
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re  # สำหรับ Regex

# ตั้งค่า Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("testproject-448216-9e4f1207aa84.json", SCOPE)
client = gspread.authorize(CREDS)
sheet = client.open("testlog").sheet1  # เลือกชีตแรก

# ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True  # เปิดใช้งานให้ Bot อ่านข้อความ
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:  # ไม่บันทึกข้อความจากบอท
        return

    # Debug: แสดงข้อความที่ได้รับ
    print(f"ข้อความที่ได้รับ:\n{message.content}")

    # ตรวจสอบว่าข้อความมีคำว่า "Police Shift"
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

            # เพิ่มข้อมูลลง Google Sheet
            sheet.append_row([steam_name, shift_duration, start_date, end_date])
            print(f"บันทึกข้อมูล: {steam_name}, {shift_duration}, {start_date}, {end_date}")
        else:
            print("ไม่พบข้อมูลที่ตรงกับรูปแบบ 'Police Shift'")
    else:
        print("ข้อความไม่ได้อยู่ในรูปแบบที่ต้องการ")

# รัน Bot
bot.run("MTMzMDIzMDY2OTI1OTA1MTAzOQ.GZP9LD.EcLqdZCwoLUa3uF5m0MuSnsCtK56dihKbg4IQc")

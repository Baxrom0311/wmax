import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from notifier.telegram import send_telegram_message, send_telegram_document, format_admin_welcome, _persistent_reply_keyboard
from notifier.excel_exporter import generate_users_excel

SUPER_ADMIN_ID = "6956456422"

async def main():
    print("Generating authentic clinical Excel report...")
    xlsx_path = generate_users_excel()
    print("Generated at:", xlsx_path)

    caption = (
        "📊 <b>NAZORAT (WMAX) — Haqiqiy Klinik va Bemorlar Hisoboti (.xlsx)</b>\n\n"
        "✅ <b>Barcha sun'iy (fake) ma'lumotlar olib tashlandi:</b>\n"
        "1. <b>1-varaq («Bemorlar va Yaqinlar»)</b>: Barcha haqiqiy klinik bemorlar (Otabek Ro'zmetov, Gulnora Matyoqubova, Rustam Qurbonov, Jumaniyoz Otajonov), ularning to'liq tibbiy tashxislari, o'lchovlari, biriktirilgan yaqinlari (Dilnoza, Sardor, Malika, Farhod) va ularning haqiqiy telefon raqamlari hamda PIN kodlari.\n"
        "2. <b>2-varaq («Tibbiyot Xodimlari va Adminlar»)</b>: Doktor Islom Yusupov, Hamshira Zilola Otajonova va Super Admin Mansur Durdimatov.\n"
        "3. <b>3-varaq («Telegram Bot Foydalanuvchilari»)</b>: Haqiqiy Telegram foydalanuvchilari.\n"
        "4. <b>4-varaq («Klinik Statistika va KPI»)</b>: Triaj (Qizil, Sariq, Yashil, No Data) ko'rsatkichlari."
    )

    print("Sending Excel spreadsheet...")
    res = await send_telegram_document(SUPER_ADMIN_ID, xlsx_path, caption=caption)
    print("Document sent:", res)

if __name__ == "__main__":
    asyncio.run(main())

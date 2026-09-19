import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from notifier.telegram import send_telegram_message, send_telegram_document, _persistent_reply_keyboard, format_admin_welcome, format_admin_panel
from notifier.excel_exporter import generate_users_excel

SUPER_ADMIN_ID = "6956456422"

async def main():
    print("Generating users & relatives Excel report...")
    xlsx_path = generate_users_excel()
    print(f"Generated: {xlsx_path}")

    # 1. Send Welcome & Updated Pure Admin Reply Keyboard
    welcome = format_admin_welcome("Super Admin", SUPER_ADMIN_ID)
    text_p, markup_p = format_admin_panel(SUPER_ADMIN_ID)
    kbd = _persistent_reply_keyboard(SUPER_ADMIN_ID)

    print("Sending welcome & admin keyboard...")
    await send_telegram_message(SUPER_ADMIN_ID, welcome, reply_markup=kbd)
    await asyncio.sleep(1)

    print("Sending admin interactive panel...")
    await send_telegram_message(SUPER_ADMIN_ID, text_p, reply_markup=markup_p)
    await asyncio.sleep(1)

    # 2. Send the Excel document
    caption = (
        "📊 <b>NAZORAT (WMAX) — Foydalanuvchilar va Bemorlar Hisoboti</b>\n\n"
        "✅ <b>Admin Panel yangilandi:</b>\n"
        "• Oddiy foydalanuvchi tugmalari (Ko'rsatkichlar, Shifokor, Yordam) olib tashlandi.\n"
        "• Faqat maxsus administratorlik boshqaruv menyusi o'rnatildi.\n"
        "• Jonli foydalanuvchilar statistikasi va kim kimning yaqini ekanligi aks ettirildi.\n\n"
        "📥 Ushbu Excel (.xlsx) faylida barcha ma'lumotlar to'liq jamlangan."
    )
    print("Sending Excel spreadsheet...")
    res = await send_telegram_document(SUPER_ADMIN_ID, xlsx_path, caption=caption)
    print("Excel dispatch result:", res)

if __name__ == "__main__":
    asyncio.run(main())

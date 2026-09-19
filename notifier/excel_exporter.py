from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .user_tracker import (
    get_all_users,
    get_clinical_patients,
    get_clinical_staff,
    get_user_stats,
)

logger = logging.getLogger("nazorat.notifier.excel_exporter")

EXPORTS_DIR = Path(__file__).resolve().parent / "exports"
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:5174").rstrip("/")


def generate_users_excel(custom_path: Path | None = None) -> Path:
    """
    Generate an authoritative, multi-tab Microsoft Excel (.xlsx) workbook for NAZORAT (WMAX):
    Sheet 1: Bemorlar va Yaqinlar (Official Clinical Patients, Diagnoses, Caregivers & Phones)
    Sheet 2: Tibbiyot Xodimlari va Adminlar (Cardiologists, Nurses & System Admins)
    Sheet 3: Telegram Bot Faoliyati (Live Telegram Users & Interaction Telemetry)
    Sheet 4: Klinik Statistika va KPI (Aggregated Clinical Triage & System KPIs)
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filepath = custom_path or (EXPORTS_DIR / f"NAZORAT_Klinik_Baza_va_Yaqinlar_{timestamp_str}.xlsx")

    wb = openpyxl.Workbook()

    # Shared palette & styling
    navy_header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Medical Dark Navy
    teal_header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")  # Deep Teal
    slate_header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid") # Dark Slate
    emerald_header_fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid") # Emerald
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side,
    )

    # -------------------------------------------------------------------------
    # SHEET 1: Bemorlar va Yaqinlar (Clinical Patients & Caregivers)
    # -------------------------------------------------------------------------
    ws_patients = wb.active
    ws_patients.title = "Bemorlar va Yaqinlar"
    ws_patients.views.sheetView[0].showGridLines = True

    headers_p = [
        "№",
        "Karta №",
        "Bemor F.I.Sh.",
        "Yoshi / Jinsi",
        "Aniq Klinik Tashxisi",
        "Hudud / Tuman",
        "Joriy Triaj Holati",
        "Oxirgi O'lchovlar",
        "Smart Watch ID",
        "Biriktirilgan Yaqini (Caregiver)",
        "Qarindoshlik",
        "Yaqinining Telefon Raqami",
        "PIN-kod",
        "Web-Relative Havolasi",
        "Mas'ul Shifokor",
        "Mas'ul Hamshira",
    ]

    ws_patients.append(headers_p)
    ws_patients.row_dimensions[1].height = 30

    for col_num in range(1, len(headers_p) + 1):
        c = ws_patients.cell(row=1, column=col_num)
        c.fill = navy_header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = cell_border

    patients = get_clinical_patients()
    for row_idx, p in enumerate(patients, start=2):
        link = f"{PUBLIC_BASE_URL}/r/{p['access_token']}"
        age_sex = f"{p['age']} yosh / {p['sex']}"
        row_data = [
            row_idx - 1,
            p["card_no"],
            p["patient_name"],
            age_sex,
            p["diagnosis"],
            p["district"],
            p["triage_level"],
            p["vitals_summary"],
            p["device_id"],
            p["relative_name"],
            p["relationship"],
            p["relative_phone"],
            p["relative_pin"],
            link,
            p["doctor_name"],
            p["nurse_name"],
        ]
        ws_patients.append(row_data)
        ws_patients.row_dimensions[row_idx].height = 26

        current_fill = zebra_fill if row_idx % 2 == 0 else white_fill
        for col_num in range(1, len(row_data) + 1):
            cell = ws_patients.cell(row=row_idx, column=col_num)
            cell.fill = current_fill
            cell.border = cell_border
            cell.font = Font(name="Calibri", size=10)

            # Highlighting and alignment
            if col_num in (1, 2, 4, 7, 9, 11, 12, 13):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            # Emphasize phone numbers and triage
            if col_num == 12:
                cell.font = Font(name="Calibri", size=10, bold=True, color="1E3A8A")
            elif col_num == 7:
                if "Qizil" in str(cell.value):
                    cell.font = Font(name="Calibri", size=10, bold=True, color="B91C1C")
                elif "Sariq" in str(cell.value):
                    cell.font = Font(name="Calibri", size=10, bold=True, color="B45309")
                elif "Yashil" in str(cell.value):
                    cell.font = Font(name="Calibri", size=10, bold=True, color="047857")

    # Auto-adjust column widths
    for col in ws_patients.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws_patients.column_dimensions[col_letter].width = min(max(max_len + 3, 11), 50)

    # -------------------------------------------------------------------------
    # SHEET 2: Tibbiyot Xodimlari va Adminlar (Medical Personnel & Admins)
    # -------------------------------------------------------------------------
    ws_staff = wb.create_sheet(title="Tibbiyot Xodimlari va Adminlar")
    ws_staff.views.sheetView[0].showGridLines = True

    headers_s = [
        "№",
        "Xodim ID",
        "To'liq F.I.Sh.",
        "Lavozimi / Roli",
        "Telefon Raqami",
        "Tizimga Kirish Logini",
        "Tibbiyot Muassasasi",
        "Biriktirilgan Vazifasi",
        "Tizimdagi Maqomi",
    ]

    ws_staff.append(headers_s)
    ws_staff.row_dimensions[1].height = 28

    for col_num in range(1, len(headers_s) + 1):
        c = ws_staff.cell(row=1, column=col_num)
        c.fill = teal_header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = cell_border

    staff = get_clinical_staff()
    for row_idx, s in enumerate(staff, start=2):
        row_data = [
            row_idx - 1,
            s["id"],
            s["full_name"],
            s["role"],
            s["phone"],
            s["login"],
            s["institution"],
            s["assigned"],
            s["status"],
        ]
        ws_staff.append(row_data)
        ws_staff.row_dimensions[row_idx].height = 24

        current_fill = zebra_fill if row_idx % 2 == 0 else white_fill
        for col_num in range(1, len(row_data) + 1):
            cell = ws_staff.cell(row=row_idx, column=col_num)
            cell.fill = current_fill
            cell.border = cell_border
            cell.font = Font(name="Calibri", size=10)
            if col_num in (1, 2, 5, 9):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            if col_num == 5:
                cell.font = Font(name="Calibri", size=10, bold=True, color="0F766E")

    for col in ws_staff.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws_staff.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 48)

    # -------------------------------------------------------------------------
    # SHEET 3: Telegram Bot Foydalanuvchilari (Live Telegram Users)
    # -------------------------------------------------------------------------
    ws_tg = wb.create_sheet(title="Telegram Bot Foydalanuvchilari")
    ws_tg.views.sheetView[0].showGridLines = True

    headers_tg = [
        "№",
        "Telegram ID",
        "Foydalanuvchi F.I.Sh.",
        "Username (@)",
        "Telefon Raqami",
        "Tizimdagi Maqomi",
        "Xabarlar Soni",
        "Birinchi Tashrif",
        "Oxirgi Faollik (UTC)",
        "Holati",
    ]

    ws_tg.append(headers_tg)
    ws_tg.row_dimensions[1].height = 28

    for col_num in range(1, len(headers_tg) + 1):
        c = ws_tg.cell(row=1, column=col_num)
        c.fill = slate_header_fill
        c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = cell_border

    tg_users = get_all_users()
    for row_idx, u in enumerate(tg_users, start=2):
        row_data = [
            row_idx - 1,
            str(u.get("telegram_id", "")),
            u.get("full_name", "—"),
            u.get("username", "—"),
            u.get("phone", "—"),
            u.get("role", "—"),
            u.get("messages_count", 0),
            u.get("first_seen", "")[:19].replace("T", " "),
            u.get("last_seen", "")[:19].replace("T", " "),
            "Faol (Active)" if u.get("is_active", True) else "Nofaol",
        ]
        ws_tg.append(row_data)
        ws_tg.row_dimensions[row_idx].height = 22

        current_fill = zebra_fill if row_idx % 2 == 0 else white_fill
        for col_num in range(1, len(row_data) + 1):
            cell = ws_tg.cell(row=row_idx, column=col_num)
            cell.fill = current_fill
            cell.border = cell_border
            cell.font = Font(name="Calibri", size=10)
            if col_num in (1, 2, 5, 7, 8, 9, 10):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    for col in ws_tg.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws_tg.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    # -------------------------------------------------------------------------
    # SHEET 4: Klinik Statistika va KPI
    # -------------------------------------------------------------------------
    ws_stats = wb.create_sheet(title="Klinik Statistika va KPI")
    ws_stats.views.sheetView[0].showGridLines = True

    stats = get_user_stats()
    now_utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    ws_stats.append(["NAZORAT (WMAX) — Tizim, Bemorlar va Telemonitoring Xulosasi", ""])
    ws_stats.merge_cells("A1:B1")
    ws_stats.row_dimensions[1].height = 32
    cell_title = ws_stats.cell(row=1, column=1)
    cell_title.fill = emerald_header_fill
    cell_title.font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    cell_title.alignment = Alignment(horizontal="center", vertical="center")

    kpi_data = [
        ("Parametr / Ko'rsatkich", "Qiymat"),
        ("Jami Nazoratdagi Bemorlar Soni", f"{stats['total_patients']} nafar"),
        ("🔴 O'tkir Xavf Holatidagi Bemorlar (Qizil)", f"{stats['red_count']} nafar (Otabek Ro'zmetov)"),
        ("🟡 Diqqat Talab Holatidagi Bemorlar (Sariq)", f"{stats['amber_count']} nafar (Gulnora Matyoqubova)"),
        ("🟢 Barqaror Kompensatsiya Holatidagi Bemorlar (Yashil)", f"{stats['green_count']} nafar (Rustam Qurbonov)"),
        ("⚪️ Aloqa Uzilgan Bemorlar (No Data)", f"{stats['nodata_count']} nafar (Jumaniyoz Otajonov)"),
        ("Biriktirilgan Bemor Yaqinlari (Caregivers)", f"{stats['relatives_count']} nafar"),
        ("Klinik Shifokorlar (Kardiologlar)", f"{stats['doctors_count']} nafar (Doktor Islom Yusupov)"),
        ("Kardioreanimatsiya Hamshiralari", f"{stats['nurses_count']} nafar (Hamshira Zilola Otajonova)"),
        ("Super Administratorlar", f"{stats['admins_count']} nafar (Mansur Durdimatov)"),
        ("Telemetriya O'lchov Darchasi", "5 daqiqalik darchalar (24/7 doimiy monitoring)"),
        ("AI Klinik Triage Dvigateli", "Google Gemini Flash (Gibrid rejim)"),
        ("Hisobot Yaratilgan Sana", now_utc_str),
    ]

    for r_idx, (k, v) in enumerate(kpi_data, start=2):
        ws_stats.append([k, v])
        ws_stats.row_dimensions[r_idx].height = 24
        cell_k = ws_stats.cell(row=r_idx, column=1)
        cell_v = ws_stats.cell(row=r_idx, column=2)

        if r_idx == 2:
            cell_k.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            cell_v.fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
            cell_k.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            cell_v.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            cell_k.alignment = Alignment(horizontal="left", vertical="center")
            cell_v.alignment = Alignment(horizontal="center", vertical="center")
        else:
            r_fill = zebra_fill if r_idx % 2 == 0 else white_fill
            cell_k.fill = r_fill
            cell_v.fill = r_fill
            cell_k.font = Font(name="Calibri", size=10, bold=True)
            cell_v.font = Font(name="Calibri", size=10)
            cell_k.alignment = Alignment(horizontal="left", vertical="center")
            cell_v.alignment = Alignment(horizontal="left", vertical="center")

        cell_k.border = cell_border
        cell_v.border = cell_border

    ws_stats.column_dimensions["A"].width = 50
    ws_stats.column_dimensions["B"].width = 45

    wb.save(filepath)
    logger.info("Excel clinical report successfully generated at: %s", filepath)
    return filepath

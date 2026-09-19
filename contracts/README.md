# contracts/ — MUZLATILGAN

Bu papka tizimning **yagona haqiqat manbai**. Hech bir agent bu yerga yozmaydi.

| Fayl | Kim o'qiydi |
|---|---|
| `algo_interface.py` | A1 ↔ A2 |
| `timewin.py` | A1, A2 (import qiladi, nusxalamaydi) |
| `openapi.yaml` | A1, A3, A4, A5, A6 |
| `types.ts` | A3, A4 (o'z `src/` iga **nusxalaydi**) |

## Agar shartnoma noto'g'ri bo'lsa

Agent **o'zi tuzatmaydi**. To'xtaydi va xabar beradi. Tuzatishni faqat
Task 0 egasi (odam) kiritadi va **hamma agentga e'lon qiladi** — aks holda
parallellik jim buziladi.

## Nega Alembic yo'q

Xakaton sharoitida ikki haqiqat manbai (migratsiya + sxema) eng ko'p
vaqt yeydigan xato manbai. Sxema o'zgarsa: `docker compose down -v && up`.

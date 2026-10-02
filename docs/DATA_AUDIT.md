# WMAX — Ma'lumot Auditi

> Sana: 2026-09-22  
> Paket: W0 · Ma'lumot auditi  
> Tegishli bo'limlar: `ARCHITECTURE.md` 16.2 · 16.3  
> Qaror: **A yo'li tavsiya qilinadi**, lekin `pg_dump` DB ishga tushgandan keyin olinadi.

---

## 1. Xulosa

Lokal ishchi muhitda haqiqiy production ma'lumot topilmadi.

| Tekshiruv | Natija |
|---|---|
| `pgdata` hajmi | `0B` |
| `docker compose ps` | `postgres` restart loop |
| Postgres logi | `POSTGRES_PASSWORD` berilmagan, DB uninitialized |
| `.env` | topilmadi yoki bo'sh |
| Dump/backup fayllar | production dump topilmadi |
| Mavjud migratsiyalar | 2 ta |
| ORM jadvallari | 26 ta model faylidan 26 ta `__tablename__` |

Shu holatda jadval bo'yicha qatorlar sonini sanash va `pg_dump` olishning
imkoni yo'q: Postgres ishga tushmagan va volume ichida baza yo'q.

## 2. Real DB Audit Holati

Audit talabi:

1. Har jadvaldagi qatorlar soni sanaladi
2. Demo urug'idan tashqari haqiqiy ma'lumot bor-yo'qligi ajratiladi
3. Natija shu faylga yoziladi

Hozirgi bajarilish:

| Qadam | Holat | Sabab |
|---|---|---|
| Jadval qatorlarini sanash | bajarilmadi | Postgres konteyneri ishga tushmagan |
| Demo/real farqlash | qisman bajarildi | seed skript deterministik demo ID'lari o'qildi |
| `pg_dump` arxivi | bajarilmadi | DB yo'q, dump olishga obyekt yo'q |

Postgres logidagi asosiy xato:

```text
Error: Database is uninitialized and superuser password is not specified.
```

Bu lokal muhit konfiguratsiyasi muammosi. Bu audit natijasi production
serverda ma'lumot yo'q degani emas; faqat shu workspace ichidagi lokal baza
bo'sh/ishga tushmaganini bildiradi.

## 3. Demo Ma'lumot Belgilari

`scripts/seed_demo.py` demo ma'lumotni quyidagi qat'iy ID'lar bilan yaratadi:

| Tur | Demo ID / belgi |
|---|---|
| Doctor | `00000000-0000-0000-0000-000000000001` |
| Nurse | `00000000-0000-0000-0000-000000000002` |
| Patients | `11111111-*`, `22222222-*`, `33333333-*` |
| Relatives | `aaaaaaaa-1111-*`, `aaaaaaaa-2222-*`, `aaaaaaaa-3333-*` |
| Demo password | `wmax123` |
| Relative PIN | `112233` |

Kelajakda DB ishga tushganda real/demo ajratish uchun qoidalar:

- Yuqoridagi ID'lar va telefonlar demo deb hisoblanadi.
- `scripts/seed_demo.py` dagi 3 bemordan boshqa har qanday bemor real yoki
  qo'lda kiritilgan ma'lumot deb ko'riladi.
- Demo bemorlar bo'lsa ham, ularning yonida qo'shimcha `readings`, `tasks`,
  `devices`, `payments`, `invoices` bo'lsa alohida ko'rib chiqiladi.

## 4. Sxema Auditi

Mavjud migratsiya zanjiri:

| Revision | Mazmun |
|---|---|
| `8e2af841b0e3` | ORM modellardan initial schema |
| `c542ed62b26b` | tenants, billing, devices |

Mavjud model jadvallari:

| Jadval | Holat |
|---|---|
| `users` | eski model, `role` ustuni bor |
| `patients` | eski model, `tenant_id`, `age`, `doctor_id`, `nurse_id`, `device_id` bor |
| `relatives` | yangi `patient_access` ga ko'chiriladi |
| `tenants` | `household` qiymati bor, B2C uchun olib tashlanadi |
| `subscriptions` | tenantga bog'langan, yangi sxemada bemorga ko'chadi |
| `readings` | `ts`, `spo2`, `skin_temp`, `steps`, `rr_est`, `sdnn` saqlanadi |
| `devices` | `tenant_id`, `serial_number`, `model_name`, `tier` bor |
| `device_assignments` | mavjud, lekin yangi attributsiya oynasi talabi bilan qayta ishlanadi |
| `alerts`, `tasks`, `notifications` | mavjud, lekin yangi I2 va task machine bilan mos emas |
| `patient_*` profil jadvallari | qisman saqlanadi/qayta xaritalanadi |

Arxitektura bilan asosiy nomosliklar:

| Mavjud holat | Yangi talab |
|---|---|
| `users.role` | `accounts` rolsiz, rol munosabatdan |
| `patients.tenant_id` | bemor egasiz, `patient_memberships` orqali |
| `subscriptions.tenant_id` | `patient_subscriptions.patient_id` |
| `tenants.kind='household'` | B2C da tenant yo'q |
| `readings.ts` | `window_start`, oylik partition |
| qurilma ingest `patient_id` bilan ishlashi mumkin | token bemorni olib yurmaydi |
| klinik/oila kirish qoidalari kodda sochilgan | `domain/` sof qoidalar |

## 5. A yoki B Tavsiya

Tavsiya: **A yo'li — baza tashlanadi va yangi sxema bilan qayta quriladi.**

Sabablar:

- Lokal `pgdata` bo'sh (`0B`).
- Postgres hali initialize bo'lmagan.
- Production yoki staging dump workspace ichida topilmadi.
- Migratsiya zanjiri qisqa: 2 ta migratsiya.
- Sxema arxitektura bilan fundamental farq qiladi; legacy saqlash faqat real
  ma'lumot borligi isbotlansa kerak bo'ladi.

Shart:

- DB ishga tushgandan keyin baribir `pg_dump` olinadi.
- Agar dump yoki serverda real ma'lumot chiqsa, darhol **B yo'li**ga o'tiladi:
  legacy schema saqlanadi, ko'chirish skripti yoziladi, eski sxema o'chirilmaydi.

## 6. Keyingi Buyruqlar

DB konfiguratsiyasi berilgandan keyin bajariladigan tekshiruvlar:

```bash
docker compose ps
docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose exec postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/wmax_pre_migration.dump
docker cp wmax-postgres-1:/tmp/wmax_pre_migration.dump ./backups/wmax_pre_migration_2026-09-22.dump
```

Qatorlarni sanash:

```sql
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY relname;
```

Demo ID'dan tashqari bemor bor-yo'qligi:

```sql
SELECT id, full_name, created_at
FROM patients
WHERE id NOT IN (
  '11111111-1111-1111-1111-111111111111',
  '22222222-2222-2222-2222-222222222222',
  '33333333-3333-3333-3333-333333333333'
);
```

## 7. Qaror Darvozasi

W3 modellarga o'tish uchun qaror:

- Shu lokal workspace bo'yicha: **A yo'li bilan davom etish mumkin**.
- Production/staging bor bo'lsa: avval u yerdan dump olinadi va 2-bo'lim
  qayta to'ldiriladi.


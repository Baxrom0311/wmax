# WMAX — Wear OS Watch

Ushbu modul **WMAX** platformasining qurilma qatlamidir:
- **`wear/watch/`**: Galaxy Watch 5 / Wear OS aqlli soati ilovasi (`androidx.health:health-services-client`).
- Telefon hamrohi: `mobile_flutter/` (Flutter Data Layer bridge va backend sync).
- **`scripts/watch_sim.py`**: Noutbuk orqali soatsiz sinash simulyatori.

---

## 1. Talab qilinadigan muhit

- **Android Studio**: Android Studio Koala (2024.1.1) yoki yangiroq (Ladybug / Meerkat).
- **JDK**: Java 17 yoki Java 21.
- **Android SDK**:
  - `compileSdk`: 34
  - `targetSdk`: 34
  - `watch minSdk`: 30 (Wear OS 3.0+, Android 11+)
  - `phone minSdk`: 26 (Android 8.0+)
- **Qurilmalar / Emulatorlar**:
  - **Soat**: Wear OS Large Round / Galaxy Watch 4/5/6 emulyatori (API 30+).
  - **Telefon**: `mobile_flutter/` Android ilovasi.

---

## 2. Loyiha arxitekturasi va ma'lumotlar oqimi

```
[Aqlli soat (Wear OS)]
   │
   │ Datchiklar: Heart Rate (bpm), SpO2, Akselerometr (qadamlar), Off-body
   │ Agregatsiya: 1 daqiqalik o'lchovlar -> 5 daqiqalik darcha yig'indisi
   ▼
[Data Layer API: /wmax/reading_batch]
   │
   ▼
[Flutter telefon ilovasi (`mobile_flutter`)]
   │
[POST /api/v1/ingest (WMAX Backend)]
   │
   └── Idempotent: UNIQUE(patient_id, ts)
```

---

## 3. Emulatorda sinash va ulash (Pairing)

### 3.1 Emulatorlarni ishga tushirish
1. Android Studio Device Manager orqali:
   - 1 ta **Wear OS Large Round** (API 33 yoki 34) emulyatorini yarating.
   - 1 ta **Phone** (Pixel 7, API 34) emulyatorini yarating.
2. Har ikkala emulyatorni yoqing.

### 3.2 Soat va telefonni bog'lash (Bluetooth / Port Forwarding)
Terminal orqali ADB port forwarding buyrug'ini bering:
```bash
adb -d forward tcp:5601 tcp:5601
```
Endi telefondagi Google Play Services va Wear OS emulyatori bir-biri bilan Data Layer orqali to'liq bog'lanadi.

### 3.3 Health Services datchiklarini sinash
Wear OS emulyatorida datchik qiymatlarini o'zgartirish:
1. Android Studio pastki qismidagi **Running Devices** panelini oching.
2. Wear OS emulyatori yonidagi **...** (Extended controls) tugmasini bosing.
3. **Wear Health Services** bo'limiga o'ting.
4. Heart rate (puls) qiymatini kiriting (masalan: `85 bpm`) va **Apply** bosing.
5. Soat ekranida puls o'zgarganini va "Ulangan" holatini ko'rasiz.

---

## 4. Build qilish va o'rnatish

Loyihaning ildiz papkasidan:

### 4.1 Soat ilovasini build qilish:
```bash
cd wear
./gradlew :watch:assembleDebug
```
Chiqish fayli: `wear/watch/build/outputs/apk/debug/watch-debug.apk`

O'rnatish:
```bash
adb -s <watch_device_id> install -r wear/watch/build/outputs/apk/debug/watch-debug.apk
```

---

## 5. Noutbuk simulyatori (`scripts/watch_sim.py`)

Agar soat yoki Android Studio o'rnatilmagan bo'lsa, butun quvur va backendni noutbuk orqali tekshirish mumkin:

```bash
# Bir martalik yuborish (bir 5-minutlik paket)
python3 scripts/watch_sim.py --once --patient-id 11111111-1111-1111-1111-111111111111

# Idempotentlik testi (takroriy ts yuborilganda dublikat aniqlash)
python3 scripts/watch_sim.py --test-idempotent

# Oflayn bufer navbati testi (tarmoq uzilishi va tiklanganda batch yuborish)
python3 scripts/watch_sim.py --test-offline

# Jonli oqim (har 2 soniyada 5 minutlik o'lchov yuborish)
python3 scripts/watch_sim.py --interval 2.0 --profile worsening
```

---

## 6. Dasturchi yordamchi vositalari (`wear/tools/`)

- **`wear/tools/pair_emulators.sh`**:
  Ishga tushirilgan soat va telefon emulyatorlarini avtomatik topadi, `tcp:5601` port forwarding'ini yoqadi va datchik ruxsatlarini (`BODY_SENSORS`, `ACTIVITY_RECOGNITION`) beradi:
  ```bash
  ./wear/tools/pair_emulators.sh
  ```

- **`wear/tools/simulate_vitals.sh`**:
  Simulyatorni turli profillar bilan tezkor ishga tushirish qobig'i:
  ```bash
  ./wear/tools/simulate_vitals.sh healthy 2.0 11111111-1111-1111-1111-111111111111
  ./wear/tools/simulate_vitals.sh worsening 1.5 11111111-1111-1111-1111-111111111111
  ```

# WMAX Mobile

WMAX Caregiver — Flutter mobil ilovasi. Ilova foydalanuvchi login/sessionini, bemor dashboardini va Wear OS soatidan keladigan telemetriyani boshqaradi.

## Mas’uliyatlar

- Qarindosh, bemor va shifokor loginlari
- JWT sessionni qurilmada saqlash
- Wearable Data Layer orqali soat bilan aloqa
- O‘lchovlarni `POST /api/v1/ingest` ga yuborish
- SOS yuborish va bemor holatini yangilash

## Ishga tushirish

```bash
flutter pub get
flutter run --dart-define=WMAX_INGEST_KEY=<ingest-key>
```

Production API manzili `https://wmax.boos.uz` sifatida ilova konfiguratsiyasida ishlatiladi.

## APK build

```bash
flutter build apk --release --dart-define=WMAX_INGEST_KEY=<ingest-key>
```

## Tekshiruv

```bash
flutter analyze
flutter test
```

Telefon va soat pairing’i Android tizimi hamda Google Wearable Data Layer orqali amalga oshadi. Soat internetga ega bo‘lsa, u bevosita backend ingest endpoint’iga ham yuboradi.

# WMAX — kod, ideologiya va startup auditi

Sana: 2026-10-07. Obyekt: hozirgi lokal ishchi katalog, jumladan commit qilinmagan o‘zgarishlar. Productiondagi kod aynan shu versiya ekanligi tekshirilmagan. Audit davomida tashqaridan yangi brainstorming modullari paydo bo‘ldi; ular alohida ko‘rildi va backend testlari qayta bajarildi. Yakuniy fayl xeshlari `audit-2026-10-07/WORKTREE_SHA256.json` da.

**Qaror: WMAX asosida startup qurish mumkin. Hozirgi versiya real bemorlarga uzluksiz klinik kuzatuv va kafolatlangan aralashuv va’dasi bilan ommaviy ishga tushirishga tayyor emas.** Keyingi bosqich — asosiy uzilishlarni tuzatish, so‘ng bitta klinika bilan nazoratli pilot. Demo, texnik ishlash, klinik ishonchlilik va biznes talab — to‘rtta alohida isbot.

“100% tekshirildi” degan kafolat bermayman: har bir satrning semantik to‘g‘riligi, barcha qurilmalar, real klinik natijalar va production infratuzilmasi bu audit bilan tasdiqlanmagan. Faylma-fayl qamrov va qolgan noaniqliklar [inventarda](audit-2026-10-07/FILE_INVENTORY.md) ko‘rsatilgan. Muhim nosozliklar faqat taxmin qilinmadi: ajratilgan PostgreSQL bazasida qayta hosil qilindi. [Tekshiruv dalillari](audit-2026-10-07/EVIDENCE.txt).

**Mahsulotning asl qiymati**

WMAXning foydali g‘oyasi: uzoqdagi farzand ota-onasining holatidan xabardor bo‘ladi; hamkor klinika esa ogohlantirishga kim javob berishini va javob berilgan-berilmaganini boshqaradi. Eng qimmatli natija — “signal chiqdi → kerakli odam ko‘rdi → bemor bilan bog‘landi → natija qayd etildi”.

`docs/IDEOLOGY.md` dagi bemor/hisob farqi, oilaviy ruxsat/klinik a’zolik farqi, bitta parvarish egasi, tarixiy qurilma attributsiyasi va bepul SOS tamoyillari yaxshi poydevor. Ammo kodda ularning ayrimi faqat sof funksiyalar yoki jadvallar darajasida bor; amaldagi servis ulardan foydalanmaydi.

Hozir “digital twin” deb atalgan qism asosan profil, o‘lchovlar, statistik baseline, qoidaviy baho va LLM matnidan tashkil topgan. Klinik natijalarda o‘qitilgan va tashqi guruhda validatsiya qilingan 72 soatlik prognoz modeli dalili repoda topilmadi. L1/L2 ma’lumot tizimini shu nom bilan aniq chegaralash kerak; L3/L4 ni tayyor imkoniyat sifatida sotish uchun asos yo‘q.

**Tekshiruv natijalari**

| Tekshiruv | Natija | Nimani isbotlamaydi |
|---|---|---|
| Fayl inventari | 465 text fayl, 44 binary; text 78 484 satr, lockfilelar ham kiradi | Har satr qo‘lda ko‘rilganini anglatmaydi |
| Python AST | 214 Python fayl parse qilindi | Runtime va SQL to‘g‘riligini |
| Backend/algo/notifier testlari | Yakuniy 216 passed, 13 skipped; dastlab 212 passed | To‘liq PostgreSQL integratsiyasi va klinik validatsiyani |
| Web-doctor | Lint va production build o‘tdi | Brauzerdagi barcha foydalanuvchi oqimlarini |
| Web-relative | Lint va production build o‘tdi | Yangi Account/PatientAccess bilan real onboardingni |
| Flutter analyze | No issues found | Native fon rejimi, sensor sifati va batareyani |
| Flutter test | 2 passed; bittasi tashqi serverga SOS yuboradi | Xavfsiz/izolyatsiyalangan CI yoki lokal versiya ishlashini |
| Android phone debug | APK build o‘tdi | Qurilmadagi ishlash va release signingni |
| Android wear debug | APK build o‘tdi | Fizik soatda fon monitoringi/batareya va release signingni |
| PostgreSQL upgrade head | Uch migratsiya o‘tdi | Schema drift/downgrade/RLS runtime to‘g‘riligini |
| Alembic check | FAILED: partition jadvallarini olib tashlash farqi | Yashil migratsiya gate mavjud emas |
| Alembic downgrade base | FAILED: RLS policy jadvalga bog‘langan | Faqat tashlanadigan lokal bazada sinaldi |
| Ruff | 546 diagnostika, 134 fayl; exit 1 | Bularning hammasi runtime bug emas; lint konfiguratsiyasiga bog‘liq |

Lokal Python 3.11/PostgreSQL 17 ishlatildi; Docker/CI Python 3.12/PostgreSQL 16 ko‘rsatadi. Docker bu muhitda mavjud emas, container build va aynan PG16 takrori bajarilmadi. iOS build, fizik Wear OS/telefon testlari, restore drill, penetration/load test va klinik tadqiqot bajarilmadi.

**Ishga tushirishni to‘suvchi topilmalar**

P0 — klinik va’da yoki xavfsizlikning asosiy zanjiri uzilgan. P1 — asosiy oqim/xavfsizlik/to‘lovda jiddiy nuqson. P2 — muhim sifat, operatsiya yoki o‘sish cheklovi. Bu ustuvorliklar CVSS ballari emas.

| ID / daraja | Kod dalili | Aniq muammo va ta’siri | Tuzatish va qabul mezoni |
|---|---|---|---|
| F01 / P0 | `backend/app/core/rls.py:22`; `auth/deps.py`; `auth/device.py` | `SET LOCAL ... = :param` asyncpg orqali `$1` ga aylanib SQL syntax error beradi. Haqiqiy bazada takrorlandi. Bu kontekstni qo‘llaydigan autentifikatsiyalangan HTTP/device yo‘llarini buzadi. | Parametrli `SELECT set_config(..., ..., true)` kabi PostgreSQLga mos usul; haqiqiy DB bilan login→protected request va device→ingest testi. |
| F02 / P0 | `backend/app/api/ingest.py:52`; `services/health_data_service.py`; `services/pipeline_service.py:191` | Mobil/Wear oqimi `/ingest/health-data` orqali `health_samples` ga yozadi. U yerdan `readings` agregati yoki klinik pipelinega ko‘prik topilmadi. Sinov: 170 bpm qabul qilindi; health_samples=1, readings=0, alerts=0. | Sifat/vaqt oynasi bilan deterministik agregatsiya, kech kelgan ma’lumot siyosati va signalni ishga tushirish. Bir real qurilmadan panel/vazifa/xabargacha integratsiya testi. |
| F03 / P0 | `backend/app/services/pipeline_service.py:326` | Barcha faol TenantMember so‘raladi, lekin `scalar_one_or_none()` ishlatiladi. Ikki xodimda MultipleResultsFound; exception yutiladi va qizil signal vazifasiz qoladi. Lokal DBda tasks=0 tasdiqlandi. Bitta xodim bo‘lsa ham rol/hudud/navbatchilik tanlanmaydi. | Mas’ul xodimni aniq qoida bilan tanlash; 0/1/2+ xodim va navbatchi yo‘qligi ssenariylari. Failureni alohida operatsion holatga chiqarish. |
| F04 / P0 | `notifier/main.py:161` | Oldingi istalgan notification 6 soatlik cooldownni boshlaydi. Amberdan keyingi yangi red ham bostirilishi mumkin. Faqat oxirgi 15 daqiqa skaneri uzilishdan keyingi eski yetkazilmagan alertlarni tashlab ketadi. | Severity oshganda yangi yetkazish; pending per-recipient queue; uzoq downtime→catch-up; ACK/retry/fallback. |
| F05 / P0 | `services/sos_service.py:98`; `services/emergency/dispatcher.py:35`; `notifier/main.py` | SOS kontaktlari `delivered=False` bilan yoziladi, lekin ularni yuboradigan consumer topilmadi. ManualDispatch faqat log va `accepted=True` qaytaradi. 103 adapteri ham shu stubga tushadi. WebSocket panel hodisasi tez yordam yuborilgani emas. | Dispatcher ACK va aniq operatsion navbatchi; SOS yetkazish worker; contact fallback va holat kuzatuvi. End-to-end sinov izolyatsiyalangan soxta provayderlar bilan. |
| F06 / P1 | `auth/service.py:139,263`; `repositories/relative_repo.py`; `models/schema.py` | Yangi qarovchi Account avval klinik user sifatida topiladi; a’zoligi yo‘q deb SMS login rad etiladi. PIN yo‘li esa PatientAccess obyektida yo‘q `pin_hash` ni o‘qiydi. Ikkalasi real DBda takrorlandi. | Bitta hisobning barcha munosabatlarini aniqlash; tanlangan kontekst bilan token; yangi qarovchi invite→consent→login→view testi. Legacy modelni o‘chirishdan oldin data audit. |
| F07 / P1 | `services/sms.py:32`; `core/config.py` | SMSning faqat `log` provider implementatsiyasi bor. Production `log` ni taqiqlaydi, boshqa provider esa “qo‘llab-quvvatlanmaydi” xatosi beradi. | Real provider adapteri, timeout/retry va fake provider contract testi. Production konfiguratsiyasi haqiqiy adapter mavjudligini tekshirsin. |
| F08 / P1 | `auth/scope.py:19`; `api/realtime.py:46`; `api/platform.py`; `docker/compose/docker-compose.yml:84` | Tenant `admin` global admin kabi cheklovlarni chetlab o‘tadi. Platforma roli alohida yo‘lga ulanmagan. Default Compose DB URL POSTGRES_USERdan foydalanadi; bootstrap superuser bilan RLS himoyasi ishlamaydi. Real deployed rol tekshirilmagan. | Tenant admin/platform support/researchni ajratish; restricted app role, alohida migration role; ikki tenant bilan salbiy testlar, WebSocket ham tekshirilsin. |
| F09 / P1 | `services/patient_relationship_service.py`; `auth/scope.py`; `auth/service.py:334`; migratsiyadagi `patients_scope` | Rozilik yoziladi/bekor qilinadi, ammo revoke downstream access/membership/tokenni yopmaydi. Relative scope token ichidagi patient_idsga tayanadi; refresh eski claimlarni qayta chiqaradi. RLSdagi patient_ids OR sharti ham eski token ruxsatini saqlashi mumkin. | Har request/current relationship yoki authorization version; consent revoke→barcha kanallarda darhol denial; refresh qayta tekshirsin. |
| F10 / P1 | `api/patients.py:256`; `workers/escalation_worker.py:80`; `services/pipeline_service.py` | Deceased endpoint faqat belgi yozadi. Silence worker barcha bemorlarni oladi. O‘lgan deb belgilangan sintetik bemorga no_data alert yaratilgani DBda tasdiqlandi. | Mark-deceased lifecycle: signal/vazifa/xabar/obuna to‘xtashi, qurilma qaytarish; har consumer markerni tekshirsin. |
| F11 / P1 | `services/clinical_math.py:353`; `ai/clinical_ai.py:34`; `web-relative/src/components/HeroStatusPrognosis.tsx` | 5/15/35/50/65/80% va 72 soat qoidaviy qiymatlar; UI ularni prognoz sifatida ko‘rsatadi. LLM fallback confidence ham tayinlangan. Kalibratsiya/evaluation dalili topilmadi. Bu D1 va G1 bosqichlariga zid. | Tasdiqlanmaguncha foizli prognozni mahsulot va’dasidan chiqarish; o‘lchangan og‘ish/sifat/vaqtni ko‘rsatish. Klinik tadqiqot bo‘lsa protocol, outcome va calibration alohida. |
| F12 / P1 | `services/payment_webhook_service.py:50` | Bir transaction uchun pendingdan keyingi paid “duplicate” deb tashlanadi. Lokal sinovda subscription past_due qolgan. Shu tekshiruv amount/order mosligini ham tasdiqlamaydi. | Payment state machine, idempotent state transitions, order/amount/currency reconciliation; parallel callback va pending→paid testlari. |
| F13 / P1 | `mobile_flutter/lib/api/api_service.dart:133,302`; `lib/screens/dashboard_screen.dart` | Bo‘sh bemor ro‘yxati demo odamlar bilan to‘ldiriladi; bo‘sh/mock accessToken sun’iy view yaratadi. Oddiy klinik list patientlarida legacy accessToken yo‘qligi bu yo‘lga tushishi mumkin. | Faqat ochiq tanlangan demo muhitida fake data. Production bo‘sh ro‘yxat/no-data ko‘rsatsin; role-specific endpointlar ishlatilsin. |
| F14 / P1 | `mobile_flutter/lib/screens/dashboard_screen.dart:98`; `NativeHealthBridge`; `WmaxWearDataListenerService.java` | Telefon native listeneri navbatga yozadi; serverga upload UI timerlari/manual syncga bog‘langan. Telefon ilovasi yopiq bo‘lganda mustaqil upload worker topilmadi. | Phone background uploader, durable ACK/retry; app killed/reboot/offline/Doze va real 24–72 soat sinovi. Bu koddan topilgan cheklov; qurilmada tajriba bajarilmadi. |
| F15 / P1 | `mobile_flutter/test/api_live_test.dart:13` | Oddiy `flutter test` public serverda demo login va haqiqiy SOS POST qiladi. Audit vaqtida ham bajarildi. CI har ishga tushganda tashqi yon ta’sir berishi mumkin. | Testni default suitedan ajratish; lokal fake server/synthetic fixtures; live SOS uchun alohida aniq opt-in va tozalash. |
| F16 / P1 | `backend/alembic/env.py:95`; base migration `downgrade():859` | Alembic check yaratilgan partitionlarni schema drift deb ko‘radi. Downgrade patient_membershipsni patients_scope policydan oldin drop qilib yiqiladi. Ikkalasi disposable PostgreSQLda takrorlandi. | Partition-aware autogenerate filtering; policy dependencies to‘g‘ri tartibda. PG16da upgrade/check/downgrade/upgrade yashil bo‘lsin. |

**Qolgan muhim kamchiliklar**

| ID | Dalil va muammo | Kerakli natija |
|---|---|---|
| F17 / P1 | `notifier/main.py:65,187`: barcha adminlarga broadcast, yangi PatientAccess o‘rniga legacy Relative; patient/tenant/consent bo‘yicha target resolver ishlatilmaydi. `notification_targets()` esa runtimega ulanmagan. | Mas’ul va ruxsatli recipientlar; har recipient yetkazilishi alohida qayd qilinsin. Telegram bot admini avtomatik klinik ma’lumot olmasin. |
| F18 / P1 | `domain/quality.py` task_kind mavjud, pipeline doim clinical yaratadi; provenance/coverage asosida technical branch yo‘q. `is_auto_critical_sos()` ham runtime callerga ulanmagan. | F2 sifati amalda qo‘llansin. Testdan o‘tgan, lekin ulanmagan funksiya tayyor feature sifatida ko‘rsatilmasin. |
| F19 / P1 | `services/orphan_service.py:resolve`: UI candidatesga qaramay submitda shu candidates tekshirilmaydi, 14 kun chegarasi ham yo‘q. Shu tenantdagi boshqa bemorga yozish mumkin. | Server-side candidate/age check; vaqt oynasini tuzatish audit bilan; noto‘g‘ri patientga attributsiya rad etilsin. |
| F20 / P1 | `auth/service.py` TenantRole `head_doctor` qiymatini CLINICIAN_ROLES qabul qilmaydi; bitta global role barcha tenant_idlarga qo‘llanadi. | Rol tenantga bog‘liq bo‘lsin; bir hisob A klinikada admin, B da nurse ssenariysi. |
| F21 / P2 | `domain/billing_calc.py` qoidalari invoice/billing-day yaratuvchi jobga ulanmagan; invoice/usage endpointlar asosan o‘qiydi. `billing/entitlements.py` va `domain/entitlement.py` free/premium qoidalari farq qiladi. | Bitta tarif siyosati, bemor-kun hisoblash, davr yakunlash va actual provider checkout. Narx kartasi real to‘lov integratsiyasi emas. |
| F22 / P2 | `domain/billing_calc.py:patient_days` membership va assignmentning bir kun ichida alohida mavjudligini tekshiradi, ularning o‘zaro haqiqiy vaqt kesishuvini emas; kun UTC bilan sanaladi. | Masalan a’zolik 08:00da tugab, soat 18:00da berilsa hisoblanmasin; tenant billing timezone aniqlansin. |
| F23 / P2 | `PatientRepository.get_all`, `PatientService.get_worklist`, `auth/scope`: mahalla/MemberTerritory emas tenant kengligida kirish; worklist 1+3N query, pagination yo‘q. | B6 hudud qamrovi va navbat; batch queries/pagination; real yuklama o‘lchovi. |
| F24 / P2 | `services/survey_service.py`: client score/per_question_ms saqlanadi; trusted/weak/rejected, fact-check va discount integratsiyasi ko‘rinmadi. | Survey skeletonni L2 “haqiqat halqasi” bilan adashtirmaslik; savol sifati, outcome linkage va server baholashi. |
| F25 / P1 | `landing/index.html:1497`: lead form faqat success modal ochib reset qiladi; serverga yubormaydi. Shu fayl “103 chaqirildi”, “kafolatlangan” va 24/7 va’dalarini beradi. | Leadni ishonchli saqlash va ko‘rinadigan failure; tasdiqlanmagan xizmat va’dalarini olib tashlash. Hozir marketing pilotida leadlar yo‘qoladi. |
| F26 / P2 | `deploy.sh` root: rsync joriy worktreeni yuboradi, build/up qiladi; canonical scripts/deploy.sh backup/migration/recovery tartibidan farq qiladi. | Bitta hujjatlashtirilgan release yo‘li; legacy scriptning production sifatida noto‘g‘ri ishlatilishini to‘sish. |
| F27 / P2 | `workers/manager.py`: leadership olingach connection tirikligini qayta kuzatmaydi. DB uzilib sessiya locki yo‘qolsa eski looplar davom etishi mumkin. | Lock yo‘qolganda workerlar to‘xtasin; yangi leader/reconnect testi. Statik xatar, failover tajribasi bajarilmadi. |
| F28 / P2 | `tests/test_rls.py` SQL matnini mock bilan tekshiradi; `conftest.py` keng exceptionlarda skip qiladi. OpenAPI testlari schema nomlarini solishtiradi, ichki field constraintsni emas. | Runtime DB salbiy testlari va to‘liq contract diff; kutilmagan import/startup xatosi skipga aylanmasin. |
| F29 / P1 — ulashdan oldin | Yangi `domain/peace_of_mind.py`: red+worn=False “attention”ga tushadi, green uchun “Hech qanday xavf yo‘q”, red uchun yetkazish dalilisiz “Shifokorga xabar yuborildi” deydi. `clinical_intake_service.py` bitta sanasiz readingga ham monitoring_days=14 beradi va ismni HTMLga escapingsiz joylaydi. Lokal chaqiruvda tasdiqlandi. Hozir runtime caller topilmadi. | Xavfni absolyut inkor qilmaslik; xabar holatini haqiqiy deliverydan olish; davrni timestampdan hisoblash; HTML escape. Uning unit testlari feature productionga ulanganini anglatmaydi. |

Yangi `clinical_cohorts.py`, `monetization_saas.py` va `edge_sensor_filter.dart` ham hozircha alohida prototiplar: signal, billing va native ingest oqimlariga ulangan caller topilmadi. Cohort thresholdlarining klinik dalili keltirilmagan; edge filter ayrim past SpO2 qiymatlarini butunlay rad etadi. Bunday filtrlashni yoqishdan oldin raw ma’lumotni saqlash, sifat flaglari va klinik tekshiruv zarur. Yangi SLA 15/30 daqiqalik qoida qo‘shadi, mavjud 2/24 soatlik worker bilan integratsiya qilinmagan.

**Davomiy audit — 2026-10-07, keyingi ishchi tree ko‘rigi**

Auditdan keyin shu katalogdagi kod o‘zgargan. Quyidagi holatlarni yangi statik ko‘rikda aniqladim; ular uchun testlar qayta bajarilmadi, shuning uchun “yopildi” deb tasdiqlamayman:

| Oldingi band | Hozir ko‘ringan holat | Qolgan qaror yoki dalil |
|---|---|---|
| F01 | `core/rls.py` parametrlarni `SELECT set_config(..., true)` orqali uzatyapti; sintaksis muammosi kodi tuzatilganga o‘xshaydi. | Haqiqiy PostgreSQL HTTP/device oqimida qayta tekshirish kerak. |
| F02 | `HealthDataIngestService` hali `HealthSample` batch insert qiladi; `/ingest/health-data` handlerdan klinik `Reading`/pipeline chaqirig‘i topilmadi. | P0 ochiq: namunadan klinik hodisa/vazifagacha ishlaydigan ko‘prik yo‘q. |
| F03 | `pipeline_service.py` endi bitta tasodifiy `.scalar_one_or_none()` o‘rniga `joined_at` bo‘yicha birinchi faol memberni oladi. | Exception kamaygan, ammo bu rol, hudud yoki navbatchilik bo‘yicha javobgarni tanlamaydi; `head_doctor` ham noto‘g‘ri task egasi bo‘lishi mumkin. P0 to‘liq yopilmagan. |
| F04 | Notifierdagi red cooldown avvalgi red darajasi bilan cheklangan ko‘rinadi. | Uzoq uzilishdan keyin faqat 15 daqiqalik oynani ko‘rish va pending delivery catch-up masalasi qoladi. |
| F05 | `SosService` default `ManualDispatch`ga tushadi; u log yozib `accepted=True` qaytaradi. Kontakt notificationlari `delivered=False` holatida yaratiladi; shu yozuvlarni yuboruvchi SOS consumer topilmadi. | P0 ochiq: bu “tez yordam yuborildi” yoki kontaktga xabar yetdi degani emas. |
| F06 | SMS login endi Account'dan keyin `PatientAccess` qidirishga urinadi, lekin `relative_login()` `assignments` dagi yozuvdan `relative.pin_hash` va `relative.full_name` o‘qiydi. Access repository natijasidagi birinchi obyekt `PatientAccess`; modelda `pin_hash` yo‘q. | Qarovchi yangi Account yo‘li kod darajasida hali mos emas; `PatientAccess` modelida PIN credential yo‘qligini yoki credential qayerda saqlanishini aniqlab, flow-ni to‘g‘rilash zarur. |
| F10 | Silence worker querysi `deceased_at IS NULL` bilan filtrlanyapti; pipeline ham deceased bemorni erta qaytaradi. | Oldingi ikki yo‘l tuzatilganga o‘xshaydi, ammo boshqa workerlar, notifier va subscription lifecycle bo‘yicha to‘liq dalil yo‘q. |
| F12 | Webhook paid callbackni pending holatdan paidga o‘tkazadigan o‘zgarishga ega. | Amount/currency/order reconciliation va parallel webhookning DB darajasidagi idempotencysi hal bo‘lmagan. |
| F15 | `api_live_test.py` endi `ENABLE_LIVE_SOS_TEST=true` bo‘lmasa tashqi POSTni o‘tkazmaydi. | Audit paytidagi yon ta’sirni bartaraf etish uchun yaxshi himoya; uni yoqib qayta ishlatmadim. |

Qo‘shimcha ochiq xavf: `PatientContext.for_ai()` butun `model_dump()` ni tashqi Gemini/DeepSeek promptiga uzatadi; bu bemor identifikatori, manzil, aloqa va favqulodda kontaktlarni ham qamrab olishi mumkin. Minimalizatsiya, provayder saqlash/training sozlamalari, rozilik va ma’lumot joylashuvi bo‘yicha hujjat topilmaguncha klinik AI oqimini maxfiylik jihatdan tayyor deb bo‘lmaydi. Bu statik oqim tahlili; real provayderga yuborish tasdiqlanmagan.

Yuqoridagi o‘zgarishlar ishchi tree'da ko‘rindi, ammo test qilinmadi. Dastlabki tekshiruv jadvalidagi test natijalari avvalgi ishchi tree holatiga tegishli; release gate sifatida ishlatishdan oldin o‘zgarishlar audit qilingan commitga birlashtirilib, xavfsiz izolyatsiyalangan muhitda qayta bajarilishi shart.

**Arxitekturani saqlashga arziydigan qismlar**

- FastAPI modular monolit hozirgi hajm uchun yetarli. Mikroservislarga bo‘lish muhim uzilishlarni tuzatmaydi.
- Account/Patient va membership/access ajratilishi ma’lumot modelida to‘g‘ri yo‘nalish.
- Qurilma tokeni, bir martalik enrollment, tarixiy assignment intervali, idempotency kalitlari mavjud.
- Postgres realtime outbox commitdan keyingi yetkazishga mo‘ljallangan; reconnect uchun persisted events mavjud.
- Median/MAD baseline, taqilmagan soatni ajratish, harakatga qarab pulsni maskalash va baseline approval asoslari bor.
- Web demo sessiyalari alohida qilinishi yaxshi; mobilga ham shu intizom kerak.
- Backup/rollback/monitoring skriptlari va SDLC ni yozib qo‘yilgan. Ularning borligi real restore muvaffaqiyatini anglatmaydi, lekin foydali boshlanish.

**Ideologiya bo‘yicha baho**

| Qoida | Amaldagi holat |
|---|---|
| A2: bemor ilovani ochmasligi mumkin | Telefon uploadi UIga bog‘liq — F14 |
| B1–B3: hisob/bemor va ikki aloqa | Sxemada bor; login/notifier legacy bilan aralash — F06/F17 |
| B4–B5: bemor roziligi va revoke | Record bor, to‘liq enforcement yo‘q — F09 |
| B6: mahalla/uchastka kirishi | Asosan tenant darajasida — F23 |
| C1/D5: aniq javobgar | Ko‘p xodimda task yiqiladi — F03 |
| C4: muddati tugagan litsenziya yangi qabulni to‘xtatadi | Create-patient/device oqimida shu licence gate topilmadi |
| D1: o‘lchov, tashxis emas | Foizli 72h yomonlashuv/tibbiy xulosa va’dasi bor — F11 |
| D3/I2: muhim signal yetib borishi | Telegram, cooldown, tor lookback; to‘liq fallback yo‘q — F04/F05/F17 |
| D4: xavfsizlik bepul | Entitlementda ijobiy asos; safety delivery ishlashi alohida muammo |
| F2/F4: sifat va attributsiya | Interval himoyalari bor; task quality/orphan resolve yetarli emas — F18/F19 |
| G1–G5: outcome asosida o‘rganish | Profil/survey skeleton bor, validatsiyalangan bashorat yo‘q |
| H1–H2: research/support farqi | API bor; role ajratilishi va to‘liq audit yetarli emas — F08 |
| J2: deceaseddan keyin to‘xtash | Bajarilmaydi — F10 |
| K: hech qachon o‘chirmaslik | Mutlaq qoida o‘rniga ma’lumot turi, maqsad, qonuniy asos va retention muddati kerak |

Ideologiyadagi yana uch qarorni qayta ko‘rish kerak: “kafolatlangan aralashuv” faqat shartnoma va navbatchilik bilan beriladi; qizil signalning operatsion xarajati nol emas; “10 soniya kutgan odam savolni o‘qiydi” ma’lumot sifati isboti emas. Taymerlar ham bir xil emas: hujjatda 24 soat, koddagi red vazifada 2 soat, pullik tarif matnida 15 daqiqalik qo‘ng‘iroq. Bular klinik egasi tomonidan alohida ma’nolar bilan belgilanishi kerak, oddiy engineering raqami sifatida emas.

**Startup sifatida qanday boshlash kerak**

Mening tavsiyam — B2B2C pilot: bitta xususiy klinika, o‘sha klinika tanlagan bitta bemor guruhi, masalan uyga chiqarilgandan keyingi kuzatuv; oila esa kuzatuv oynasi. Bu tavsiya bozor isbotlangan degani emas: hozircha klinika nazoratidagi kichik xizmatni tekshirish gipotezasi.

Boshlang‘ich paket: bitta mosligi tekshirilgan qurilma; mas’ul klinik xodim; oddiy joriy holat va ma’lumot yangiligi; kelishilgan ogohlantirishlar; “ko‘rdim/bog‘landim/natija” tarixi. Klinika javob beradigan ish soatlari aniq yozilsin. AI foizli prognozi, barcha soatlarni qo‘llash, avtomatik 103, PK/PD simulyatsiyasi va umummilliy platforma birinchi paketga shart emas.

Remote monitoring yangi kategoriya emas: [Cadence](https://www.cadence.care/) qurilma, klinik jamoa va shifokor ish jarayonini birlashtiradi; [CarePredict](https://www.carepredict.com/) senior care monitoringi bilan ishlaydi. Bu misollar O‘zbekistondagi talab yoki daromad kafolati emas. WMAXning tekshiriladigan farqi — o‘zbek/rus tili, mahalliy klinika jarayoni, onboarding, qurilma ta’minoti va xabarga javob berish sifati.

Pilotga kirishdan oldin 10–15 farzand, 5–10 hamshira/shifokor va 3–5 klinika qaror qabul qiluvchisi bilan suhbat o‘tkazish — taklif etilgan tadqiqot hajmi. “Sizga yoqadimi?” emas, oxirgi real holat, hozirgi muammo, kim javob berishi va budjetdan kim to‘lashi so‘ralsin. Kamida bitta yozma pilot kelishuvi yoki narxi ko‘rsatilgan real to‘lov majburiyati kerak. Bu suhbatlar audit davomida o‘tkazilmadi.

Tarif faylida premium 59 000, premium_doc 249 000, clinic 85 000 so‘m/bemor-oy ko‘rsatilgan; ular bozor tasdiqlagan narxlar emas. Ideologiyada B2B bemor-kun, kodda esa per_patient_month bor. Qurilma ijarasi defaulti 180 000 so‘m/oy. Nima tarifga kirishi yozilmaguncha rentabellikni baholab bo‘lmaydi.

Har bemor bo‘yicha hisob:

`oylik hissa = tushum − qurilma amortizatsiyasi/ijarasi − xodim vaqti − aloqa − logistika − support − payment/hosting/AI xarajati`.

Masalan, faqat tekshirish uchun olingan taxminda qurilma 2,4 mln so‘m va xizmat muddati 24 oy bo‘lsa amortizatsiya oyiga 100 ming so‘m. Qurilma to‘liq 85 minglik paket ichiga kirsa, boshqa xarajatlardan oldin ham hissa manfiy. Bu real bozor narxi yoki prognoz emas; alohida qurilma to‘lovi/ijara/depozit modelini aniqlash zarurligini ko‘rsatadi. Shifokor paketida tungi navbatchilik va bir xodimga bemorlar sonini hisoblash kerak.

**Qurilma va ma’lumot bo‘yicha tashqi dalil**

[Androidning rasmiy hujjati](https://developer.android.com/health-and-fitness/health-services/monitor-background) passive monitoring ma’lumotni batchlarda yetkazishini va capabilityni tekshirish zarurligini ko‘rsatadi. Shuning uchun Health Connect/HealthKitda field mavjudligi har bir soat ushbu parametrni 5 daqiqada berishini anglatmaydi. Har tanlangan modelda HR, SpO2, HRV, worn holati, timestamp, uzilish, fon rejimi va batareya bo‘yicha dalil to‘plash kerak. Hozirgi native passive collectorning asosiy fiziologik oqimi yurak urishi; qolgan sensorlar universal deb qabul qilinmasin.

**Mahalliy huquqiy tayyorgarlik**

2026-yilgi amaldagi matnga qarash muhim: [O‘RQ-547](https://lex.uz/docs/-4396419) 25-moddasi salomatlik ma’lumotlarini maxsus turga ajratadi; 27¹-moddaning martdagi tahriri biometrik/genetik hamda ko‘rsatilgan telekom ma’lumotlari uchun mahalliy saqlashni, boshqa turlar uchun esa shartli xorijiy saqlashni belgilaydi. “Barcha ma’lumot faqat mahalliy serverda” degan eski umumlashtirishni ko‘r-ko‘rona qo‘llash to‘g‘ri emas. WMAX sensor ma’lumotlarining tasnifi, baza reyestri, rozilik, transchegaraviy uzatish va retention asosini mahalliy mutaxassis bilan aniqlash kerak. Koddagi DigitalOcean yo‘li, tashqi LLMga ism/klinik kontekst va Telegramga xabar yuborish shu tekshiruv doirasiga kiradi; serverning haqiqiy joylashuvi audit qilinmadi. Bu yuridik muvofiqlik sertifikati emas.

“Tashxis qo‘ymaymiz” jumlasi o‘zi mahsulotning barcha tibbiy tartibga solish masalalarini hal qilmaydi. Mahsulot da’vosi, amaldagi funksiyasi va klinik hamkor xizmatining maqomi birga baholansin.

**Tuzatish va pilot ketma-ketligi**

| Bosqich | Ish | Chiqish mezoni |
|---|---|---|
| 0. Audit yon ta’siri | Public test SOSni ko‘rib chiqish; default suite va CI dan ajratish | Routine test tashqi SMS/Telegram/payment/SOS yubormaydi |
| 1. Baza va hisob | F01/F06/F07/F08/F09/F16/F20 | Restricted PG16 rolda login, invitation, consent revoke, tenant isolation yashil |
| 2. Kuzatuv zanjiri | F02/F03/F04/F05/F10/F14/F17/F18 | Qurilma→DB→ogohlantirish→mas’ul→ACK/natija; offline/restart/death ssenariylari |
| 3. Rost mahsulot | F11/F13/F25; tarif/SLA va’dalarini birlashtirish | Demo ajratilgan, sun’iy prognoz yo‘q, lead yo‘qolmaydi, no-data ko‘rinadi |
| 4. Pul va operatsiya | F12/F19/F21/F22/F26/F27 | Payment lifecycle, backup restore, yetkazish retry, qurilma qaytarish dalili |
| 5. Nazoratli pilot | Taklif: 10–20 bemor, 4–6 hafta, klinika belgilagan protokol | Oldindan kelishilgan texnik, xizmat va to‘lov mezonlari bilan davom/to‘xtash qarori |

Bu muddatlar va miqdorlar rejalashtirish gipotezasi, bajarilish va’dasi yoki klinik sample-size hisoboti emas. Kam uchraydigan og‘ir hodisalarni bunday kichik pilot bilan validatsiya qilib bo‘lmaydi.

Pilotda o‘lchanadigan narsalar: ruxsatli foydalanish; qurilma taqilgan davrdagi kutilgan ma’lumot qamrovi; p95 serverga kelish kechikishi; har bemor-kundagi tekshirilgan yolg‘on ogohlantirishlar; yetkazish va inson ACK ulushi/vaqti; hamshira daqiqalari; support murojaatlari; qurilma zaryadlash va yo‘qotish holatlari; pullik davom ettirish; bemor bo‘yicha hissa. Klinik threshold va maqbul ko‘rsatkichlarni klinik egasi pilotdan oldin belgilaydi.

Hozirgi tavsiya: qaytadan hammasini yozish emas, mavjud arxitekturada bitta to‘liq yo‘lni tugatish. Birinchi isbot sifatida yangi qarovchi va ikki xodimli klinikada sintetik qurilma oqimi bilan signal, tasdiqlash, bekor qilish, qayta ulanish va to‘lovni yakunigacha ko‘rsatish. Shundan keyin klinik hamkor bilan haqiqiy pilot haqida qaror chiqarish mumkin.

**Audit davomida yuz bergan tashqi ta’sir**

`flutter test` dagi `api_live_test.dart` `https://wmax.boos.uz` serveriga ulanib, demo hisobdan `Flutter test SOS verification` sababi bilan SOS yubordi va test muvaffaqiyatli tugadi. Testni oldindan to‘liq tekshirmay ishga tushirishim xato bo‘ldi. Server event IDsi test chiqishida saqlanmagan; hodisa yopildi deb da’vo qilmayman. Mas’ul operator shu test SOSni aniqlab tekshirishi kerak. Keyingi sinovlar ajratilgan lokal bazada bajarildi; tashqi SOS qayta sinalmadi.

Audit ishlab chiqarish kodini tuzatmagan, deploy/merge qilmagan. Yaratilgan artefaktlar: ushbu hisobot, `AGENTS.md`, qamrov inventari, tekshiruv dalillari va Ruff topilmalari.

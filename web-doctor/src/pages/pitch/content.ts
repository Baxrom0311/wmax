import type { Lang } from '../../i18n';

/*
 * Pitch Day 3.0 content shown on the landing page and on /demo.
 * Everything a jury reads lives here, so wording can be fixed in one place.
 */

export const LINKS = {
  site: 'https://wmax.boos.uz',
  github: 'https://github.com/Baxrom0311/wmax',
  doctorDemo: '/doctor?demo=true',
  relativePortal: '/r',
  slides: '/pptx',
  telegramBot: 'https://t.me/WMAX_uz_bot',
  apiDocs: '/api/docs',
  apiRedoc: '/api/redoc',
  openapi: '/api/openapi.json',
};

/*
 * Demo video. Put a YouTube/Google Drive embed URL in `embedUrl`
 * (e.g. https://www.youtube.com/embed/VIDEO_ID) or drop an mp4 into
 * web-doctor/public/demo/ and set `fileUrl` to '/demo/wmax-demo.mp4'.
 * While both are empty the page shows a placeholder.
 */
export const DEMO_VIDEO = {
  embedUrl: '',
  fileUrl: '',
  poster: '/images/3d/watch-hero.png',
};

export type TeamMember = {
  name: string;
  role: Record<Lang, string>;
  skills: string[];
  links: { label: string; url: string }[];
};

export const TEAM: TeamMember[] = [
  {
    name: 'Baxrom Reyimberganov',
    role: {
      uz: 'Asoschi, jamoa yetakchisi · backend, signal algoritmlari, Wear OS, DevOps',
      ru: 'Основатель, тимлид · backend, алгоритмы сигналов, Wear OS, DevOps',
      en: 'Founder & team lead · backend, signal algorithms, Wear OS, DevOps',
    },
    skills: ['Python / FastAPI', 'PostgreSQL', 'Kotlin · Wear OS', 'Docker · CI/CD', 'Signal processing'],
    links: [
      { label: 'GitHub', url: 'https://github.com/Baxrom0311' },
      { label: 'Email', url: 'mailto:bahromreyimberganov0311@gmail.com' },
    ],
  },
  {
    name: 'Mansur Durdimatov',
    role: {
      uz: 'Frontend va Telegram bot · shifokor paneli, qarovchi portali, AI yordamchi',
      ru: 'Frontend и Telegram-бот · панель врача, портал опекуна, ИИ-ассистент',
      en: 'Frontend & Telegram bot · doctor panel, caregiver portal, AI assistant',
    },
    skills: ['React / TypeScript', 'Tailwind', 'Telegram Mini App', 'i18n (uz/ru/en)'],
    links: [{ label: 'GitHub', url: 'https://github.com/durdimatovmansur6-coder' }],
  },
  {
    name: 'Vafoyev',
    role: {
      uz: 'Mobil dasturchi · Flutter qarovchi ilovasi, Bluetooth orqali soat ulash',
      ru: 'Мобильный разработчик · Flutter-приложение опекуна, привязка часов по Bluetooth',
      en: 'Mobile developer · Flutter caregiver app, Bluetooth watch pairing',
    },
    skills: ['Flutter / Dart', 'Android · iOS', 'Bluetooth LE'],
    links: [{ label: 'GitHub', url: 'https://github.com/Vafoyev' }],
  },
];

export const TECH = [
  { group: 'Backend', items: ['Python 3.12', 'FastAPI', 'PostgreSQL 16 (RLS, partitions)', 'Redis', 'Alembic'] },
  { group: 'Web', items: ['React 19', 'TypeScript', 'Vite', 'Tailwind CSS', 'Recharts'] },
  { group: 'Mobile & Watch', items: ['Flutter', 'Kotlin · Wear OS', 'Swift · watchOS / HealthKit', 'Health Connect'] },
  { group: 'Delivery', items: ['Telegram Bot & Mini App', 'SMS fallback', 'Docker Compose', 'Nginx', 'GitHub Actions'] },
  { group: 'Observability', items: ['Prometheus', 'Grafana', 'Loki'] },
  { group: 'AI', items: ['Gemini / DeepSeek (guardrails)', 'Claude Code', 'GitHub Copilot'] },
];

type PitchText = {
  nav: string;
  problemTag: string;
  problemTitle: string;
  problemLead: string;
  problemPoints: string[];
  solutionTitle: string;
  solutionLead: string;
  solutionPoints: { title: string; desc: string }[];
  teamTag: string;
  teamTitle: string;
  teamSub: string;
  techTitle: string;
  whyTag: string;
  whyTitle: string;
  whyPoints: { title: string; desc: string }[];
  roadmapTag: string;
  roadmapTitle: string;
  roadmapSub: string;
  stages: { key: string; title: string; status: 'done' | 'current' | 'next'; items: string[] }[];
  statusLabels: Record<'done' | 'current' | 'next', string>;
  planTag: string;
  planTitle: string;
  planSub: string;
  phases: { when: string; title: string; desc: string }[];
  aiTitle: string;
  aiProduct: { title: string; desc: string }[];
  aiDev: { title: string; desc: string }[];
  aiProductLabel: string;
  aiDevLabel: string;
  honesty: string;
  ctaDemo: string;
  ctaGithub: string;
};

export const PITCH: Record<Lang, PitchText> = {
  uz: {
    nav: 'Loyiha',
    problemTag: '1. Muammo → Yechim',
    problemTitle: 'Bemor kasalxonadan chiqqach, uni hech kim kuzatmaydi',
    problemLead:
      'Kasalxonadan chiqarilgandan keyingi birinchi 30 kun eng xavfli davr. Aynan shu paytda bemor va oilaviy shifokor orasidagi zanjir uziladi.',
    problemPoints: [
      'Chiqaruv xulosasi birinchi tashrifda oilaviy shifokor qoʻlida atigi 12–34% holatda boʻladi (Kripalani va boshq., JAMA, 2007).',
      'Kasalxona va shifokor bevosita faqat 3–20% holatda gaplashadi; bemorni topshirish bajarilishi oʻlchanmaydi.',
      'Yomonlashuv kech aniqlanadi, 103 kech chaqiriladi, qayta yotqizishlar koʻpayadi.',
      'Farzandlari boshqa shahar yoki xorijda ishlaydigan keksa bemorlar yolgʻiz qoladi.',
    ],
    solutionTitle: 'WMAX: statsionardan uyga uzilmaydigan parvarish zanjiri',
    solutionLead: 'Uch qismdan iborat yagona tizim. Zanjir toʻrt qadamda yopiladi: chiqarish, topshiriq, tasdiq va 30 kunlik kuzatuv.',
    solutionPoints: [
      {
        title: 'Aqlli soat',
        desc: 'SOS tugmasi, yiqilish va uzoq harakatsizlikni aniqlash; tinch holatdagi puls, SpO₂, faollik va uyqu trendi. Internet boʻlmasa maʼlumot buferda saqlanadi.',
      },
      {
        title: 'Patronaj platformasi',
        desc: 'Chiqarilgan bemor oilaviy shifokorga “aktiv chaqiruv” topshirigʻi boʻlib boradi, 24 soatlik taymer qoʻyiladi, tasdiq boʻlmasa eskalatsiya qilinadi.',
      },
      {
        title: 'Panel, ilova va Telegram',
        desc: 'Shifokor, hamshira va yaqinlar holatni tushunarli tilda koʻradi. SOS va kritik signallar hech qachon pullik obunaga bogʻlanmaydi.',
      },
    ],
    teamTag: '2. Jamoa',
    teamTitle: 'Kichik, lekin toʻliq stekni qoplaydigan jamoa',
    teamSub: 'Rollar, koʻnikmalar va havolalar. Barcha kod ochiq repozitoriyada.',
    techTitle: 'Foydalanilgan texnologiyalar',
    whyTag: '3. Nima uchun aynan biz',
    whyTitle: 'Nima uchun bu jamoa muammoni hal qila oladi',
    whyPoints: [
      {
        title: 'Ishlaydigan prototip bor',
        desc: 'Backend, signal algoritmlari, Wear OS soat ilovasi, Flutter ilova, shifokor paneli va Telegram bot yozilgan va wmax.boos.uz da ishlab turibdi.',
      },
      {
        title: 'Sifat avtomatik tekshiriladi',
        desc: 'Backend va algoritmlar 240 dan ortiq avtomatlashtirilgan test bilan tekshiriladi, har bir oʻzgarish CI orqali oʻtadi.',
      },
      {
        title: 'Mahalliy sharoitni bilamiz',
        desc: 'Oʻzbek, rus va qoraqalpoq muhitida yashaymiz: sust internet, SMS zaxira kanali, oilaviy poliklinika va tuman tibbiyot birlashmasi tuzilmasi hisobga olingan.',
      },
      {
        title: 'Halol tibbiy yondashuv',
        desc: 'Tizim tashxis qoʻymaydi: u oʻlchaydi va xabar beradi, qarorni shifokor qabul qiladi. Maʼlumot yoʻqligi “sogʻlom” deb talqin qilinmaydi.',
      },
    ],
    roadmapTag: '4. Yoʻl xaritasi',
    roadmapTitle: 'Idea → Prototype → MVP → Launched',
    roadmapSub: 'Hozir biz Prototype bosqichidamiz.',
    stages: [
      {
        key: 'Idea',
        title: 'Gʻoya',
        status: 'done',
        items: ['Muammo va tadqiqotlar tahlili', 'Bemor, farzand, shifokor rollari', 'Tibbiy cheklovlar va etika qoidalari'],
      },
      {
        key: 'Prototype',
        title: 'Prototip',
        status: 'current',
        items: ['Backend + PostgreSQL + signal algoritmlari', 'Wear OS soat va Flutter ilova', 'Shifokor paneli, qarovchi portali, Telegram bot', 'Ochiq serverda demo rejim'],
      },
      {
        key: 'MVP',
        title: 'MVP',
        status: 'next',
        items: ['Puls aniqligini Polar H10 EKG bilan solishtirish', 'Apple Watch (watchOS) versiyasi', 'Tuman poliklinikasi bilan pilot: 100 bemor'],
      },
      {
        key: 'Launched',
        title: 'Ishga tushirish',
        status: 'next',
        items: ['Tuman tibbiyot birlashmalari bilan B2B shartnoma', 'Oilaviy obuna (B2C)', 'Yuridik shaxs va IP roʻyxatdan oʻtkazish'],
      },
    ],
    statusLabels: { done: 'Bajarildi', current: 'Hozir shu yerda', next: 'Reja' },
    planTag: '5. Amalga oshirish rejasi',
    planTitle: 'Yechimni qanday amalga oshiramiz',
    planSub: 'Bosqichlar, texnologiyalar, AI vositalari va yechimlar.',
    phases: [
      {
        when: '1–2-oy',
        title: 'Tayyorgarlik',
        desc: 'Turli soatlar (Samsung, Apple, Google), telefonlar va maʼlumotnoma EKG sensori xaridi; server va xavfsizlik (RLS, cheklangan rollar, zaxira nusxa); poliklinika bilan hamkorlik va rozilik shakli.',
      },
      {
        when: '2–4-oy',
        title: 'Texnik validatsiya',
        desc: 'Soat pulsi Polar H10 bilan bir vaqtda yozib olinib, oʻrtacha xato va Bland–Altman tahlili qilinadi. SOS va yiqilish signali, yetkazilish vaqti va SMS zaxira zanjiri sinovdan oʻtadi.',
      },
      {
        when: '4–11-oy',
        title: 'Pilot',
        desc: 'Kamida 100 bemor rozilik asosida 30 kunlik sikllarda kuzatiladi. 24 soatda yopilgan topshiriqlar ulushi, signal aniqligi va foydalanuvchi fikri oʻlchanadi.',
      },
      {
        when: '12-oy',
        title: 'Tijoratlashtirish',
        desc: 'Pilot natijalari asosida tuman tibbiyot birlashmasiga tijorat taklifi, ilmiy tezis va dasturiy taʼminotni roʻyxatdan oʻtkazish.',
      },
    ],
    aiTitle: 'AI vositalari va yechimlar',
    aiProductLabel: 'Mahsulot ichida',
    aiDevLabel: 'Ishlab chiqishda',
    aiProduct: [
      { title: 'Shaxsiy baseline', desc: 'Har bir bemor uchun shaxsiy meʼyor; yangi oʻlchovlar sirkadian ritmni hisobga olgan z-score bilan solishtiriladi.' },
      { title: 'Artefakt filtri', desc: 'Harakatdagi puls oshishi qadamlar soni boʻyicha filtrlanadi, qisqa tebranishlar barqarorlik tekshiruvidan oʻtadi.' },
      { title: 'LLM yordamchi', desc: 'Gemini / DeepSeek asosida shifokor uchun qisqa xulosa va Telegramdagi yordamchi; guardrail qoidalari tashxis va dori tavsiyasini toʻsadi.' },
    ],
    aiDev: [
      { title: 'Claude Code', desc: 'Kod sharhi, testlar, refaktoring va hujjatlar.' },
      { title: 'GitHub Copilot', desc: 'Kundalik kod yozish va baholash.' },
      { title: 'Generativ dizayn', desc: 'Soat renderlari va taqdimot vizuallari.' },
    ],
    honesty:
      'WMAX tibbiy tashxis vositasi emas. Qon bosimi va glyukoza soat orqali oʻlchanmaydi; signallar klinik validatsiyadan oʻtmagan va pilot davomida tekshiriladi.',
    ctaDemo: 'Demo-ni koʻrish',
    ctaGithub: 'Manba kodi',
  },
  ru: {
    nav: 'Проект',
    problemTag: '1. Проблема → Решение',
    problemTitle: 'После выписки за пациентом никто не наблюдает',
    problemLead:
      'Первые 30 дней после выписки — самый опасный период. Именно тогда рвётся цепочка между больницей, пациентом и семейным врачом.',
    problemPoints: [
      'Выписной эпикриз есть у семейного врача на первом визите лишь в 12–34% случаев (Kripalani et al., JAMA, 2007).',
      'Больница и врач напрямую общаются лишь в 3–20% случаев; передача пациента не измеряется.',
      'Ухудшение замечают поздно, 103 вызывают поздно, растут повторные госпитализации.',
      'Пожилые пациенты, чьи дети работают в другом городе или за рубежом, остаются одни.',
    ],
    solutionTitle: 'WMAX: непрерывная цепочка ухода от стационара до дома',
    solutionLead: 'Единая система из трёх частей. Цепочка замыкается в четыре шага: выписка, задача, подтверждение и 30 дней наблюдения.',
    solutionPoints: [
      { title: 'Умные часы', desc: 'Кнопка SOS, падение и долгая неподвижность; пульс покоя, SpO₂, активность и сон. Без интернета данные хранятся в буфере.' },
      { title: 'Платформа патронажа', desc: 'Выписанный пациент становится для семейного врача задачей «активный вызов» с 24-часовым таймером и эскалацией.' },
      { title: 'Панель, приложение и Telegram', desc: 'Врач, медсестра и близкие видят состояние понятным языком. SOS и критические сигналы никогда не платные.' },
    ],
    teamTag: '2. Команда',
    teamTitle: 'Небольшая команда, покрывающая весь стек',
    teamSub: 'Роли, навыки и ссылки. Весь код в открытом репозитории.',
    techTitle: 'Используемые технологии',
    whyTag: '3. Почему мы',
    whyTitle: 'Почему эта команда может решить проблему',
    whyPoints: [
      { title: 'Работающий прототип', desc: 'Backend, алгоритмы, приложение для Wear OS, Flutter-приложение, панель врача и Telegram-бот работают на wmax.boos.uz.' },
      { title: 'Автоматическая проверка качества', desc: 'Более 240 автотестов для backend и алгоритмов, каждое изменение проходит CI.' },
      { title: 'Знаем местные условия', desc: 'Слабый интернет, резервный SMS-канал, структура семейных поликлиник и районных медобъединений.' },
      { title: 'Честный медицинский подход', desc: 'Система не ставит диагнозы: она измеряет и сообщает, решение принимает врач. Отсутствие данных не означает «здоров».' },
    ],
    roadmapTag: '4. Дорожная карта',
    roadmapTitle: 'Idea → Prototype → MVP → Launched',
    roadmapSub: 'Сейчас мы на этапе Prototype.',
    stages: [
      { key: 'Idea', title: 'Идея', status: 'done', items: ['Анализ проблемы и исследований', 'Роли пациента, родственника, врача', 'Медицинские ограничения и этика'] },
      { key: 'Prototype', title: 'Прототип', status: 'current', items: ['Backend + PostgreSQL + алгоритмы', 'Часы Wear OS и Flutter-приложение', 'Панель врача, портал опекуна, Telegram-бот', 'Демо-режим на открытом сервере'] },
      { key: 'MVP', title: 'MVP', status: 'next', items: ['Сверка пульса с ЭКГ Polar H10', 'Версия для Apple Watch', 'Пилот в поликлинике: 100 пациентов'] },
      { key: 'Launched', title: 'Запуск', status: 'next', items: ['B2B-договоры с районными медобъединениями', 'Семейная подписка (B2C)', 'Регистрация юрлица и ПО'] },
    ],
    statusLabels: { done: 'Готово', current: 'Мы здесь', next: 'План' },
    planTag: '5. План реализации',
    planTitle: 'Как мы реализуем решение',
    planSub: 'Этапы, технологии, ИИ-инструменты и решения.',
    phases: [
      { when: '1–2 мес.', title: 'Подготовка', desc: 'Закупка разных часов, телефонов и эталонного ЭКГ-датчика; сервер и безопасность (RLS, ограниченные роли, бэкапы); соглашение с поликлиникой и форма согласия.' },
      { when: '2–4 мес.', title: 'Техническая валидация', desc: 'Пульс часов записывается одновременно с Polar H10, считаются средняя ошибка и анализ Бланда–Альтмана. Проверяются SOS, падения, время доставки и SMS-резерв.' },
      { when: '4–11 мес.', title: 'Пилот', desc: 'Не менее 100 пациентов по согласию, циклы по 30 дней. Измеряются доля задач, закрытых за 24 часа, точность сигналов и отзывы.' },
      { when: '12 мес.', title: 'Коммерциализация', desc: 'Коммерческое предложение медобъединению, научные тезисы и регистрация ПО на основе итогов пилота.' },
    ],
    aiTitle: 'ИИ-инструменты и решения',
    aiProductLabel: 'В продукте',
    aiDevLabel: 'В разработке',
    aiProduct: [
      { title: 'Персональный baseline', desc: 'Индивидуальная норма для каждого пациента; новые измерения сравниваются по z-score с учётом циркадного ритма.' },
      { title: 'Фильтр артефактов', desc: 'Рост пульса при движении отфильтровывается по шагам, короткие колебания проходят проверку устойчивости.' },
      { title: 'LLM-ассистент', desc: 'Краткие сводки для врача и ассистент в Telegram на Gemini / DeepSeek; guardrails блокируют диагнозы и назначения.' },
    ],
    aiDev: [
      { title: 'Claude Code', desc: 'Ревью кода, тесты, рефакторинг и документация.' },
      { title: 'GitHub Copilot', desc: 'Повседневное написание кода.' },
      { title: 'Генеративный дизайн', desc: 'Рендеры часов и визуалы презентации.' },
    ],
    honesty: 'WMAX не является средством диагностики. Давление и глюкоза часами не измеряются; сигналы не прошли клиническую валидацию и будут проверены в пилоте.',
    ctaDemo: 'Смотреть демо',
    ctaGithub: 'Исходный код',
  },
  en: {
    nav: 'Project',
    problemTag: '1. Problem → Solution',
    problemTitle: 'After discharge, nobody watches the patient',
    problemLead: 'The first 30 days after hospital discharge are the riskiest, and that is exactly when the chain between hospital, patient and family doctor breaks.',
    problemPoints: [
      'The discharge summary reaches the family doctor by the first visit in only 12–34% of cases (Kripalani et al., JAMA, 2007).',
      'Hospital and doctor talk directly in only 3–20% of cases; handover is never measured.',
      'Deterioration is caught late, 103 is called late, readmissions grow.',
      'Elderly patients whose children work in another city or abroad are left alone.',
    ],
    solutionTitle: 'WMAX: an unbroken care chain from hospital to home',
    solutionLead: 'One system in three parts. The chain closes in four steps: discharge, task, confirmation and 30-day follow-up.',
    solutionPoints: [
      { title: 'Smartwatch', desc: 'SOS button, fall and long-inactivity detection; resting pulse, SpO₂, activity and sleep trends. Data is buffered when offline.' },
      { title: 'Care-handover platform', desc: 'A discharged patient becomes an “active call” task for the family doctor with a 24-hour timer and escalation.' },
      { title: 'Dashboard, app and Telegram', desc: 'Doctors, nurses and relatives see status in plain language. SOS and critical alerts are never behind a paywall.' },
    ],
    teamTag: '2. Team',
    teamTitle: 'A small team covering the whole stack',
    teamSub: 'Roles, skills and links. All code is in an open repository.',
    techTitle: 'Technologies we use',
    whyTag: '3. Why us',
    whyTitle: 'Why this team can solve the problem',
    whyPoints: [
      { title: 'A working prototype', desc: 'Backend, signal algorithms, Wear OS app, Flutter app, doctor dashboard and Telegram bot are built and running at wmax.boos.uz.' },
      { title: 'Automated quality checks', desc: 'More than 240 automated tests cover backend and algorithms; every change goes through CI.' },
      { title: 'We know the local context', desc: 'Weak internet, SMS fallback, family polyclinics and district medical associations are designed in.' },
      { title: 'An honest medical stance', desc: 'The system does not diagnose: it measures and notifies, the doctor decides. Missing data never means “healthy”.' },
    ],
    roadmapTag: '4. Roadmap',
    roadmapTitle: 'Idea → Prototype → MVP → Launched',
    roadmapSub: 'We are at the Prototype stage now.',
    stages: [
      { key: 'Idea', title: 'Idea', status: 'done', items: ['Problem and research analysis', 'Patient, relative and doctor roles', 'Medical limits and ethics'] },
      { key: 'Prototype', title: 'Prototype', status: 'current', items: ['Backend + PostgreSQL + signal algorithms', 'Wear OS watch and Flutter app', 'Doctor panel, caregiver portal, Telegram bot', 'Public demo mode'] },
      { key: 'MVP', title: 'MVP', status: 'next', items: ['Validate pulse against Polar H10 ECG', 'Apple Watch (watchOS) version', 'Polyclinic pilot: 100 patients'] },
      { key: 'Launched', title: 'Launched', status: 'next', items: ['B2B contracts with district medical associations', 'Family subscription (B2C)', 'Company and software registration'] },
    ],
    statusLabels: { done: 'Done', current: 'We are here', next: 'Planned' },
    planTag: '5. Implementation plan',
    planTitle: 'How we will build it',
    planSub: 'Stages, technologies, AI tools and solutions.',
    phases: [
      { when: 'Months 1–2', title: 'Preparation', desc: 'Buy watches from several vendors, phones and a reference ECG sensor; server hardening (RLS, restricted roles, backups); polyclinic partnership and consent form.' },
      { when: 'Months 2–4', title: 'Technical validation', desc: 'Watch pulse recorded alongside Polar H10; mean error and Bland–Altman analysis. SOS, fall alerts, delivery time and SMS fallback tested.' },
      { when: 'Months 4–11', title: 'Pilot', desc: 'At least 100 consenting patients in 30-day cycles. We measure tasks closed within 24 h, alert accuracy and user feedback.' },
      { when: 'Month 12', title: 'Commercialisation', desc: 'Commercial offer to district medical associations, a research abstract and software registration based on pilot results.' },
    ],
    aiTitle: 'AI tools and solutions',
    aiProductLabel: 'In the product',
    aiDevLabel: 'In development',
    aiProduct: [
      { title: 'Personal baseline', desc: 'A per-patient norm; new readings are compared with a circadian-aware z-score.' },
      { title: 'Artefact filter', desc: 'Pulse rises during movement are filtered by step count; short spikes must pass a persistence check.' },
      { title: 'LLM assistant', desc: 'Short doctor summaries and a Telegram assistant on Gemini / DeepSeek; guardrails block diagnoses and prescriptions.' },
    ],
    aiDev: [
      { title: 'Claude Code', desc: 'Code review, tests, refactoring and docs.' },
      { title: 'GitHub Copilot', desc: 'Day-to-day coding.' },
      { title: 'Generative design', desc: 'Watch renders and pitch visuals.' },
    ],
    honesty: 'WMAX is not a diagnostic device. Blood pressure and glucose are not measured by the watch; alerts are not clinically validated yet and will be tested in the pilot.',
    ctaDemo: 'Watch the demo',
    ctaGithub: 'Source code',
  },
};

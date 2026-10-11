import type { Lang } from '../../i18n';

type QA = { q: string; a: string; keys: string[] };

type DemoText = {
  title: string;
  sub: string;
  videoTitle: string;
  videoPending: string;
  descTitle: string;
  descLead: string;
  chapters: { t: string; text: string }[];
  protoTitle: string;
  protoSub: string;
  protos: { title: string; desc: string; href: string; note?: string }[];
  chatTitle: string;
  chatSub: string;
  chatPlaceholder: string;
  chatSend: string;
  chatHello: string;
  chatFallback: string;
  chatTry: string;
  apiTitle: string;
  apiSub: string;
  apiNote: string;
  copy: string;
  copied: string;
  back: string;
  qa: QA[];
};

export const DEMO: Record<Lang, DemoText> = {
  uz: {
    title: 'WMAX demo',
    sub: 'Demo-video, uning tavsifi va ishlayotgan prototip havolalari.',
    videoTitle: 'Demo-video',
    videoPending: 'Demo-video shu yerga joylanadi.',
    descTitle: 'Video tavsifi',
    descLead:
      'Videoda WMAX zanjiri boshidan oxirigacha koʻrsatiladi: bemor soatidagi signal qanday qilib shifokor paneliga, oilaviy shifokor topshirigʻiga va farzandning telefoniga yetib borishi.',
    chapters: [
      { t: '0:00', text: 'Muammo: kasalxonadan chiqqan bemor 30 kun nazoratsiz qoladi.' },
      { t: '0:30', text: 'Soat ilovasi: puls, SpO₂ va SOS tugmasi; internet boʻlmasa maʼlumot buferda saqlanadi.' },
      { t: '1:15', text: 'Shifokor paneli (demo rejim): bemorlar roʻyxati, yashil / sariq / qizil holat va trend grafiklari.' },
      { t: '2:00', text: 'SOS va topshiriq: signal navbatchi shifokorga “aktiv chaqiruv” boʻlib boradi, 24 soatlik taymer.' },
      { t: '2:45', text: 'Qarovchi portali va Telegram: farzand holatni tushunarli tilda koʻradi va xabar oladi.' },
      { t: '3:30', text: 'Yoʻl xaritasi: EKG bilan validatsiya va 100 bemorlik pilot.' },
    ],
    protoTitle: 'Ishlayotgan prototip',
    protoSub: 'Barchasi hozir onlayn. Demo rejimda faqat sintetik bemorlar koʻrsatiladi.',
    protos: [
      { title: 'Shifokor paneli (demo)', desc: 'Roʻyxatdan oʻtmasdan sintetik bemorlar bilan kirish.', href: '/doctor?demo=true' },
      { title: 'Qarovchi portali', desc: 'Farzand va yaqinlar uchun web portal.', href: '/r' },
      { title: 'Telegram bot', desc: 'Ogohlantirishlar va AI yordamchi.', href: 'https://t.me/WMAX_uz_bot' },
      { title: 'Interaktiv taqdimot', desc: '3D pitch-taqdimot.', href: '/pptx' },
      { title: 'Manba kodi', desc: 'Backend, algoritmlar, soat va mobil ilova.', href: 'https://github.com/Baxrom0311/wmax' },
    ],
    chatTitle: 'Savol-javob yordamchisi',
    chatSub: 'Loyiha haqida tayyor savol-javob namunalari. Savol bering yoki namunani tanlang.',
    chatPlaceholder: 'Masalan: soat qon bosimini oʻlchaydimi?',
    chatSend: 'Yuborish',
    chatHello: 'Salom! Men WMAX haqidagi savollarga javob beraman. Quyidagi namunalardan birini tanlang.',
    chatFallback: 'Bu savolga tayyor javobim yoʻq. Quyidagi namunalardan birini tanlang yoki Telegram botimizdagi AI yordamchiga yozing.',
    chatTry: 'Namuna savollar',
    apiTitle: 'API kirish (API Access)',
    apiSub: 'Backend REST API ochiq hujjatlangan (OpenAPI 3). Klinik endpointlar JWT token va rol talab qiladi.',
    apiNote: 'Bemor maʼlumotlari faqat avtorizatsiya va bemor roziligi bilan beriladi.',
    copy: 'Nusxa olish',
    copied: 'Nusxa olindi',
    back: 'Bosh sahifa',
    qa: [
      { q: 'WMAX nima?', a: 'WMAX — kasalxonadan chiqqan bemorni 30 kun davomida aqlli soat orqali kuzatib, oilaviy shifokor va yaqinlarini bogʻlaydigan parvarish zanjiri.', keys: ['wmax', 'nima', 'loyiha'] },
      { q: 'Soat qon bosimini oʻlchaydimi?', a: 'Yoʻq. Qon bosimi va glyukoza soat orqali oʻlchanmaydi, chunki bunday oʻlchovlarning klinik validatsiyasi yoʻq. Soat puls, SpO₂, faollik, uyqu, yiqilish va SOS ni qayd etadi.', keys: ['qon', 'bosim', 'glyukoza', 'qand'] },
      { q: 'Internet boʻlmasa nima boʻladi?', a: 'Soat va telefon maʼlumotni buferda saqlaydi va aloqa tiklanganda yuboradi. SOS, yiqilish va qizil chegara uchun zaxira SMS ketadi.', keys: ['internet', 'aloqa', 'sms', 'offline'] },
      { q: 'Tizim tashxis qoʻyadimi?', a: 'Yoʻq. WMAX oʻlchaydi va xabar beradi, klinik qarorni shifokor qabul qiladi. AI yordamchi ham tashxis va dori tavsiya qilmaydi.', keys: ['tashxis', 'dori', 'diagnoz', 'davolash'] },
      { q: 'SOS pullikmi?', a: 'Yoʻq. SOS va kritik ogohlantirishlar hech qachon pullik obunaga bogʻlanmaydi.', keys: ['sos', 'pul', 'narx', 'obuna', 'tarif'] },
      { q: 'Qaysi soatlar ishlaydi?', a: 'Hozir Wear OS (Samsung Galaxy Watch). Apple Watch (watchOS) versiyasi MVP bosqichida rejalashtirilgan.', keys: ['soat', 'samsung', 'apple', 'wear', 'galaxy'] },
      { q: 'Maʼlumotlar xavfsizmi?', a: 'Bemor kuzatuvga oʻzi rozilik beradi va istalgan vaqtda bekor qila oladi. Maʼlumotlar bazasida qatorlar darajasida kirish nazorati (RLS) va cheklangan rollar ishlatiladi.', keys: ['xavfsiz', 'maxfiy', 'rozilik', 'maʼlumot', 'malumot'] },
      { q: 'Loyiha qaysi bosqichda?', a: 'Prototype bosqichida: tizim onlayn ishlaydi, lekin haqiqiy bemorlarda hali sinalmagan. Keyingi qadam EKG bilan validatsiya va 100 bemorlik pilot.', keys: ['bosqich', 'pilot', 'mvp', 'prototip', 'reja'] },
    ],
  },
  ru: {
    title: 'Демо WMAX',
    sub: 'Демо-видео, его описание и ссылки на работающий прототип.',
    videoTitle: 'Демо-видео',
    videoPending: 'Здесь будет размещено демо-видео.',
    descTitle: 'Описание видео',
    descLead: 'Видео показывает цепочку WMAX целиком: как сигнал с часов пациента попадает в панель врача, в задачу семейного врача и на телефон родственника.',
    chapters: [
      { t: '0:00', text: 'Проблема: после выписки пациент 30 дней без наблюдения.' },
      { t: '0:30', text: 'Приложение часов: пульс, SpO₂ и SOS; без интернета данные буферизуются.' },
      { t: '1:15', text: 'Панель врача (демо): список пациентов, статусы и графики трендов.' },
      { t: '2:00', text: 'SOS и задача: сигнал становится «активным вызовом» с 24-часовым таймером.' },
      { t: '2:45', text: 'Портал опекуна и Telegram: родственник видит понятный статус и получает уведомления.' },
      { t: '3:30', text: 'Дорожная карта: валидация с ЭКГ и пилот на 100 пациентов.' },
    ],
    protoTitle: 'Работающий прототип',
    protoSub: 'Всё доступно онлайн. В демо-режиме только синтетические пациенты.',
    protos: [
      { title: 'Панель врача (демо)', desc: 'Вход без регистрации, синтетические пациенты.', href: '/doctor?demo=true' },
      { title: 'Портал опекуна', desc: 'Веб-портал для родственников.', href: '/r' },
      { title: 'Telegram-бот', desc: 'Уведомления и ИИ-ассистент.', href: 'https://t.me/WMAX_uz_bot' },
      { title: 'Интерактивная презентация', desc: '3D питч.', href: '/pptx' },
      { title: 'Исходный код', desc: 'Backend, алгоритмы, часы и мобильное приложение.', href: 'https://github.com/Baxrom0311/wmax' },
    ],
    chatTitle: 'Помощник вопрос-ответ',
    chatSub: 'Готовые примеры вопросов и ответов о проекте.',
    chatPlaceholder: 'Например: часы измеряют давление?',
    chatSend: 'Отправить',
    chatHello: 'Здравствуйте! Я отвечаю на вопросы о WMAX. Выберите пример ниже.',
    chatFallback: 'На этот вопрос нет готового ответа. Выберите пример или напишите ИИ-ассистенту в нашем Telegram-боте.',
    chatTry: 'Примеры вопросов',
    apiTitle: 'Доступ к API',
    apiSub: 'REST API backend открыто задокументирован (OpenAPI 3). Клинические эндпоинты требуют JWT и роль.',
    apiNote: 'Данные пациентов выдаются только при авторизации и согласии пациента.',
    copy: 'Копировать',
    copied: 'Скопировано',
    back: 'Главная',
    qa: [
      { q: 'Что такое WMAX?', a: 'WMAX — цепочка ухода: 30 дней наблюдения после выписки через умные часы, связывающая пациента, семейного врача и родственников.', keys: ['wmax', 'что', 'проект'] },
      { q: 'Часы измеряют давление?', a: 'Нет. Давление и глюкоза часами не измеряются — нет клинической валидации. Часы фиксируют пульс, SpO₂, активность, сон, падения и SOS.', keys: ['давлен', 'глюкоз', 'сахар'] },
      { q: 'Что если нет интернета?', a: 'Данные буферизуются и отправляются при восстановлении связи. Для SOS, падения и красного порога есть резервное SMS.', keys: ['интернет', 'связ', 'sms', 'офлайн'] },
      { q: 'Система ставит диагноз?', a: 'Нет. WMAX измеряет и сообщает, решение принимает врач.', keys: ['диагноз', 'лекарств', 'лечен'] },
      { q: 'SOS платный?', a: 'Нет. SOS и критические сигналы никогда не платные.', keys: ['sos', 'плат', 'цена', 'подписк'] },
      { q: 'На каком этапе проект?', a: 'Prototype: система работает онлайн, но ещё не испытана на реальных пациентах. Далее — валидация с ЭКГ и пилот.', keys: ['этап', 'пилот', 'mvp', 'прототип'] },
    ],
  },
  en: {
    title: 'WMAX demo',
    sub: 'Demo video, its description and links to the working prototype.',
    videoTitle: 'Demo video',
    videoPending: 'The demo video will be embedded here.',
    descTitle: 'Video description',
    descLead: 'The video walks through the whole WMAX chain: how a signal from the patient’s watch reaches the doctor dashboard, the family doctor’s task list and the relative’s phone.',
    chapters: [
      { t: '0:00', text: 'Problem: after discharge the patient is unmonitored for 30 days.' },
      { t: '0:30', text: 'Watch app: pulse, SpO₂ and SOS button; data is buffered offline.' },
      { t: '1:15', text: 'Doctor dashboard (demo mode): patient list, green / amber / red status and trend charts.' },
      { t: '2:00', text: 'SOS and handover: the alert becomes an “active call” task with a 24-hour timer.' },
      { t: '2:45', text: 'Caregiver portal and Telegram: relatives see a plain-language status and get notified.' },
      { t: '3:30', text: 'Roadmap: ECG validation and a 100-patient pilot.' },
    ],
    protoTitle: 'Working prototype',
    protoSub: 'All of it is online now. Demo mode shows synthetic patients only.',
    protos: [
      { title: 'Doctor dashboard (demo)', desc: 'Enter without registration, synthetic patients.', href: '/doctor?demo=true' },
      { title: 'Caregiver portal', desc: 'Web portal for relatives.', href: '/r' },
      { title: 'Telegram bot', desc: 'Alerts and AI assistant.', href: 'https://t.me/WMAX_uz_bot' },
      { title: 'Interactive slides', desc: '3D pitch deck.', href: '/pptx' },
      { title: 'Source code', desc: 'Backend, algorithms, watch and mobile app.', href: 'https://github.com/Baxrom0311/wmax' },
    ],
    chatTitle: 'Q&A assistant',
    chatSub: 'Sample questions and answers about the project.',
    chatPlaceholder: 'e.g. Does the watch measure blood pressure?',
    chatSend: 'Send',
    chatHello: 'Hi! I answer questions about WMAX. Pick a sample below.',
    chatFallback: 'I have no prepared answer for that. Pick a sample or ask the AI assistant in our Telegram bot.',
    chatTry: 'Sample questions',
    apiTitle: 'API access',
    apiSub: 'The backend REST API is documented openly (OpenAPI 3). Clinical endpoints require a JWT and a role.',
    apiNote: 'Patient data is only served with authorization and patient consent.',
    copy: 'Copy',
    copied: 'Copied',
    back: 'Home',
    qa: [
      { q: 'What is WMAX?', a: 'WMAX is a care chain: 30 days of smartwatch follow-up after discharge, connecting the patient, the family doctor and relatives.', keys: ['wmax', 'what', 'project'] },
      { q: 'Does the watch measure blood pressure?', a: 'No. Blood pressure and glucose are not measured by the watch because there is no clinical validation. It records pulse, SpO₂, activity, sleep, falls and SOS.', keys: ['blood', 'pressure', 'glucose', 'sugar'] },
      { q: 'What if there is no internet?', a: 'Data is buffered and sent when the connection returns. SOS, falls and red thresholds have an SMS fallback.', keys: ['internet', 'offline', 'sms', 'connection'] },
      { q: 'Does it diagnose?', a: 'No. WMAX measures and notifies; the doctor makes the clinical decision.', keys: ['diagnos', 'drug', 'treat', 'medic'] },
      { q: 'Is SOS paid?', a: 'No. SOS and critical alerts are never behind a paywall.', keys: ['sos', 'paid', 'price', 'subscription'] },
      { q: 'What stage is the project at?', a: 'Prototype: it runs online but has not been tested on real patients yet. Next: ECG validation and a pilot.', keys: ['stage', 'pilot', 'mvp', 'prototype'] },
    ],
  },
};

export function answerFor(lang: Lang, question: string): string | null {
  const text = question.toLowerCase().replace(/[ʻʼ'`’]/g, '');
  let best: { score: number; a: string } | null = null;
  for (const item of DEMO[lang].qa) {
    const score = item.keys.filter((k) => text.includes(k.replace(/[ʻʼ'`’]/g, ''))).length;
    if (score > 0 && (!best || score > best.score)) best = { score, a: item.a };
  }
  return best?.a ?? null;
}

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
    sub: 'Video, tavsif va jonli prototip.',
    videoTitle: 'Demo-video',
    videoPending: 'Demo-video shu yerga joylanadi.',
    descTitle: 'Video tavsifi',
    descLead: 'Jamoa 0xDEAD: muammo, yechim, soat va AI yadro — 3 daqiqada.',
    chapters: [
      { t: '0:00', text: 'Kirish' },
      { t: '0:10', text: 'Muammo' },
      { t: '1:00', text: 'Uzilish' },
      { t: '1:28', text: 'Yechim' },
      { t: '1:47', text: 'Soat nimani oʻlchaydi' },
      { t: '2:17', text: 'AI yadro' },
    ],
    protoTitle: 'Ishlayotgan prototip',
    protoSub: 'Barchasi hozir onlayn. Demo rejimda faqat sintetik bemorlar koʻrsatiladi.',
    protos: [
      { title: 'Shifokor paneli', desc: 'Demo rejim', href: '/doctor?demo=true' },
      { title: 'Qarovchi portali', desc: 'Oila uchun', href: '/r' },
      { title: 'Telegram bot', desc: 'Xabar + AI', href: 'https://t.me/WMAX_uz_bot' },
    ],
    chatTitle: 'Savol-javob yordamchisi',
    chatSub: 'Namuna savollar.',
    chatPlaceholder: 'Masalan: soat qon bosimini oʻlchaydimi?',
    chatSend: 'Yuborish',
    chatHello: 'Salom! Men WMAX haqidagi savollarga javob beraman. Quyidagi namunalardan birini tanlang.',
    chatFallback: 'Bu savolga tayyor javobim yoʻq. Quyidagi namunalardan birini tanlang yoki Telegram botimizdagi AI yordamchiga yozing.',
    chatTry: 'Namuna savollar',
    apiTitle: 'API kirish (API Access)',
    apiSub: 'OpenAPI 3 · JWT bilan.',
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
    sub: 'Видео, описание и живой прототип.',
    videoTitle: 'Демо-видео',
    videoPending: 'Здесь будет размещено демо-видео.',
    descTitle: 'Описание видео',
    descLead: 'Команда 0xDEAD: проблема, решение, часы и ИИ-ядро — за 3 минуты.',
    chapters: [
      { t: '0:00', text: 'Вступление' },
      { t: '0:10', text: 'Проблема' },
      { t: '1:00', text: 'Разрыв' },
      { t: '1:28', text: 'Решение' },
      { t: '1:47', text: 'Что измеряют часы' },
      { t: '2:17', text: 'ИИ-ядро' },
    ],
    protoTitle: 'Работающий прототип',
    protoSub: 'Всё доступно онлайн. В демо-режиме только синтетические пациенты.',
    protos: [
      { title: 'Панель врача', desc: 'Демо-режим', href: '/doctor?demo=true' },
      { title: 'Портал опекуна', desc: 'Для семьи', href: '/r' },
      { title: 'Telegram-бот', desc: 'Уведомления + ИИ', href: 'https://t.me/WMAX_uz_bot' },
    ],
    chatTitle: 'Помощник вопрос-ответ',
    chatSub: 'Примеры вопросов.',
    chatPlaceholder: 'Например: часы измеряют давление?',
    chatSend: 'Отправить',
    chatHello: 'Здравствуйте! Я отвечаю на вопросы о WMAX. Выберите пример ниже.',
    chatFallback: 'На этот вопрос нет готового ответа. Выберите пример или напишите ИИ-ассистенту в нашем Telegram-боте.',
    chatTry: 'Примеры вопросов',
    apiTitle: 'Доступ к API',
    apiSub: 'OpenAPI 3 · с JWT.',
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
    sub: 'Video, description and live prototype.',
    videoTitle: 'Demo video',
    videoPending: 'The demo video will be embedded here.',
    descTitle: 'Video description',
    descLead: 'Team 0xDEAD: problem, solution, watch and AI core in 3 minutes.',
    chapters: [
      { t: '0:00', text: 'Intro' },
      { t: '0:10', text: 'Problem' },
      { t: '1:00', text: 'The gap' },
      { t: '1:28', text: 'Solution' },
      { t: '1:47', text: 'What the watch measures' },
      { t: '2:17', text: 'AI core' },
    ],
    protoTitle: 'Working prototype',
    protoSub: 'All of it is online now. Demo mode shows synthetic patients only.',
    protos: [
      { title: 'Doctor dashboard', desc: 'Demo mode', href: '/doctor?demo=true' },
      { title: 'Caregiver portal', desc: 'For family', href: '/r' },
      { title: 'Telegram bot', desc: 'Alerts + AI', href: 'https://t.me/WMAX_uz_bot' },
    ],
    chatTitle: 'Q&A assistant',
    chatSub: 'Sample questions.',
    chatPlaceholder: 'e.g. Does the watch measure blood pressure?',
    chatSend: 'Send',
    chatHello: 'Hi! I answer questions about WMAX. Pick a sample below.',
    chatFallback: 'I have no prepared answer for that. Pick a sample or ask the AI assistant in our Telegram bot.',
    chatTry: 'Sample questions',
    apiTitle: 'API access',
    apiSub: 'OpenAPI 3 · JWT protected.',
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

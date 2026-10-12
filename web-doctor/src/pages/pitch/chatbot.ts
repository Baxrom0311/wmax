import type { Lang } from '../../i18n';

/*
 * Offline Q&A bot for the Pitch Day pages. No network calls: every answer is
 * prepared text, matched by keywords in any of the three languages, and
 * returned in the visitor's current language.
 */

type Text = Record<Lang, string>;
type Intent = { id: string; q: Text; a: Text; keys: string[]; sample?: boolean };

export const CHAT_UI: Record<Lang, { title: string; hello: string; placeholder: string; send: string; open: string; close: string; fallback: string; telegram: string; thinking: string }> = {
  uz: {
    title: 'WMAX yordamchi',
    hello: 'Salom! WMAX haqida soʻrang yoki savollardan birini tanlang.',
    placeholder: 'Savolingizni yozing…',
    send: 'Yuborish',
    open: 'Chatni ochish',
    close: 'Yopish',
    fallback: 'Bu savolni tushunmadim. Quyidagilardan birini tanlang yoki Telegram botimizga yozing.',
    telegram: 'Telegram bot',
    thinking: 'Yozmoqda…',
  },
  ru: {
    title: 'Помощник WMAX',
    hello: 'Здравствуйте! Спросите о WMAX или выберите вопрос ниже.',
    placeholder: 'Напишите вопрос…',
    send: 'Отправить',
    open: 'Открыть чат',
    close: 'Закрыть',
    fallback: 'Я не понял вопрос. Выберите один из вариантов ниже или напишите в наш Telegram-бот.',
    telegram: 'Telegram-бот',
    thinking: 'Печатает…',
  },
  en: {
    title: 'WMAX assistant',
    hello: 'Hi! Ask about WMAX or pick a question below.',
    placeholder: 'Type your question…',
    send: 'Send',
    open: 'Open chat',
    close: 'Close',
    fallback: 'I did not catch that. Pick one of the questions below or write to our Telegram bot.',
    telegram: 'Telegram bot',
    thinking: 'Typing…',
  },
};

const INTENTS: Intent[] = [
  {
    id: 'what',
    sample: true,
    q: { uz: 'WMAX nima?', ru: 'Что такое WMAX?', en: 'What is WMAX?' },
    a: {
      uz: 'WMAX kasalxonadan chiqqan bemorni 30 kun aqlli soat orqali kuzatadi va oilaviy shifokor hamda yaqinlarini bitta zanjirga bogʻlaydi.',
      ru: 'WMAX 30 дней наблюдает пациента после выписки через умные часы и связывает его с семейным врачом и родственниками.',
      en: 'WMAX follows a patient for 30 days after discharge with a smartwatch and links them with their family doctor and relatives.',
    },
    keys: ['wmax', 'loyiha', 'haqida', 'что такое', 'проект', 'what is', 'about', 'project'],
  },
  {
    id: 'how',
    sample: true,
    q: { uz: 'Qanday ishlaydi?', ru: 'Как это работает?', en: 'How does it work?' },
    a: {
      uz: 'Soat puls, SpO₂, faollik va yiqilishni yozadi. Chegara buzilsa shifokorga 24 soatlik vazifa ochiladi, oilaga Telegramda xabar ketadi.',
      ru: 'Часы записывают пульс, SpO₂, активность и падения. При выходе за порог врач получает задачу на 24 часа, семья получает сообщение в Telegram.',
      en: 'The watch records pulse, SpO₂, activity and falls. When a threshold is crossed the doctor gets a 24-hour task and the family gets a Telegram alert.',
    },
    keys: ['qanday ishla', 'ishlaydi', 'ishlash', 'как работ', 'работает', 'how does', 'how it', 'work'],
  },
  {
    id: 'problem',
    q: { uz: 'Qanday muammoni hal qiladi?', ru: 'Какую проблему решает?', en: 'What problem does it solve?' },
    a: {
      uz: 'Kasalxonadan chiqqan bemor 30 kun nazoratsiz qoladi: xulosalarning atigi 12–34% i oilaviy shifokorga yetadi.',
      ru: 'После выписки пациент 30 дней без наблюдения: лишь 12–34% выписок доходят до семейного врача.',
      en: 'After discharge patients go 30 days unmonitored: only 12–34% of discharge notes reach the family doctor.',
    },
    keys: ['muammo', 'проблем', 'problem', 'nega kerak', 'зачем', 'why need'],
  },
  {
    id: 'who',
    q: { uz: 'Kim uchun?', ru: 'Для кого?', en: 'Who is it for?' },
    a: {
      uz: 'Kasalxonadan chiqqan bemorlar, ularning oilaviy shifokorlari va yaqinlari uchun.',
      ru: 'Для выписанных пациентов, их семейных врачей и родственников.',
      en: 'For discharged patients, their family doctors and their relatives.',
    },
    keys: ['kim uchun', 'kimlar', 'для кого', 'кому', 'who is it', 'for whom', 'audience'],
  },
  {
    id: 'bp',
    q: { uz: 'Qon bosimini oʻlchaydimi?', ru: 'Измеряет давление?', en: 'Does it measure blood pressure?' },
    a: {
      uz: 'Yoʻq. Qon bosimi va glyukoza soat orqali oʻlchanmaydi, chunki bunday oʻlchovning klinik validatsiyasi yoʻq.',
      ru: 'Нет. Давление и глюкоза часами не измеряются: нет клинической валидации.',
      en: 'No. Blood pressure and glucose are not measured by the watch because there is no clinical validation for it.',
    },
    keys: ['qon bosim', 'bosim', 'glyukoza', 'qand', 'давлен', 'глюкоз', 'сахар', 'blood pressure', 'pressure', 'glucose', 'sugar'],
  },
  {
    id: 'measures',
    sample: true,
    q: { uz: 'Soat nimani oʻlchaydi?', ru: 'Что измеряют часы?', en: 'What does the watch measure?' },
    a: {
      uz: 'Puls, SpO₂, faollik, uyqu, yiqilish va SOS tugmasi. Sifatsiz oʻlchov "normal" deb koʻrsatilmaydi.',
      ru: 'Пульс, SpO₂, активность, сон, падения и кнопку SOS. Ненадёжное измерение не показывается как «норма».',
      en: 'Pulse, SpO₂, activity, sleep, falls and an SOS button. An unreliable reading is never shown as "normal".',
    },
    keys: ['olchay', 'puls', 'spo2', 'spo₂', 'kislorod', 'uyqu', 'измеря', 'пульс', 'кислород', 'сон', 'measure', 'pulse', 'oxygen', 'sleep', 'heart'],
  },
  {
    id: 'offline',
    q: { uz: 'Internet boʻlmasa-chi?', ru: 'А если нет интернета?', en: 'What if there is no internet?' },
    a: {
      uz: 'Maʼlumot qurilmada saqlanadi va aloqa tiklanganda yuboriladi. SOS va yiqilish uchun zaxira SMS ketadi.',
      ru: 'Данные сохраняются на устройстве и отправляются при появлении связи. Для SOS и падения есть резервное SMS.',
      en: 'Data is stored on the device and sent when the connection returns. SOS and falls also go out by SMS.',
    },
    keys: ['internet', 'aloqa', 'sms', 'offline', 'oflayn', 'интернет', 'связ', 'офлайн', 'connection', 'network'],
  },
  {
    id: 'diagnosis',
    q: { uz: 'Tashxis qoʻyadimi?', ru: 'Ставит диагноз?', en: 'Does it diagnose?' },
    a: {
      uz: 'Yoʻq. WMAX oʻlchaydi va xabar beradi, qarorni shifokor qabul qiladi. AI tashxis va dori tavsiya qilmaydi.',
      ru: 'Нет. WMAX измеряет и сообщает, решение принимает врач. ИИ не ставит диагноз и не назначает лекарства.',
      en: 'No. WMAX measures and notifies; the doctor decides. The AI does not diagnose or prescribe.',
    },
    keys: ['tashxis', 'diagnoz', 'dori', 'davola', 'диагноз', 'лекарств', 'лечен', 'diagnos', 'drug', 'treat', 'prescri'],
  },
  {
    id: 'sos',
    sample: true,
    q: { uz: 'SOS pullikmi?', ru: 'SOS платный?', en: 'Is SOS paid?' },
    a: {
      uz: 'Yoʻq. SOS va kritik ogohlantirishlar hech qachon pullik obunaga bogʻlanmaydi.',
      ru: 'Нет. SOS и критические сигналы никогда не бывают платными.',
      en: 'No. SOS and critical alerts are never behind a paywall.',
    },
    keys: ['sos', 'pullik', 'платн', 'paid'],
  },
  {
    id: 'price',
    q: { uz: 'Narxi qancha?', ru: 'Сколько стоит?', en: 'How much does it cost?' },
    a: {
      uz: 'Narx pilotdan keyin belgilanadi. SOS va kritik ogohlantirishlar har qanday tarifda bepul qoladi.',
      ru: 'Цена будет определена после пилота. SOS и критические сигналы бесплатны на любом тарифе.',
      en: 'Pricing will be set after the pilot. SOS and critical alerts stay free on every plan.',
    },
    keys: ['narx', 'qancha', 'tarif', 'obuna', 'bepul', 'pul', 'цен', 'стоим', 'сколько', 'подписк', 'бесплат', 'price', 'cost', 'how much', 'subscription', 'free'],
  },
  {
    id: 'watches',
    q: { uz: 'Qaysi soatlar ishlaydi?', ru: 'Какие часы поддерживаются?', en: 'Which watches work?' },
    a: {
      uz: 'Hozir Wear OS soatlari (Samsung Galaxy Watch). Apple Watch versiyasi MVP bosqichida rejalashtirilgan.',
      ru: 'Сейчас часы на Wear OS (Samsung Galaxy Watch). Версия для Apple Watch запланирована на этапе MVP.',
      en: 'Wear OS watches today (Samsung Galaxy Watch). An Apple Watch version is planned for the MVP.',
    },
    keys: ['qaysi soat', 'soatlar', 'samsung', 'apple', 'wear', 'galaxy', 'какие час', 'часы', 'which watch', 'watches', 'device'],
  },
  {
    id: 'privacy',
    q: { uz: 'Maʼlumotlar xavfsizmi?', ru: 'Данные в безопасности?', en: 'Is the data safe?' },
    a: {
      uz: 'Bemor kuzatuvga oʻzi rozilik beradi va istalgan vaqtda bekor qila oladi. Bazada qator darajasida kirish nazorati (RLS) ishlatiladi.',
      ru: 'Пациент сам даёт согласие и может отозвать его в любой момент. В базе используется контроль доступа на уровне строк (RLS).',
      en: 'The patient opts in and can revoke consent at any time. The database uses row-level access control (RLS).',
    },
    keys: ['xavfsiz', 'maxfiy', 'rozilik', 'malumot', 'maʼlumot', 'безопас', 'конфиденц', 'согласи', 'данны', 'safe', 'secur', 'privacy', 'consent', 'data'],
  },
  {
    id: 'stage',
    sample: true,
    q: { uz: 'Loyiha qaysi bosqichda?', ru: 'На каком этапе проект?', en: 'What stage is it at?' },
    a: {
      uz: 'Prototype: tizim onlayn ishlaydi, lekin haqiqiy bemorlarda hali sinalmagan. Keyingisi MVP: 100 bemorlik pilot.',
      ru: 'Prototype: система работает онлайн, но ещё не испытана на реальных пациентах. Далее MVP: пилот на 100 пациентов.',
      en: 'Prototype: it runs online but has not been tested on real patients yet. Next is the MVP: a 100-patient pilot.',
    },
    keys: ['bosqich', 'mvp', 'prototip', 'prototype', 'yol xarita', 'roadmap', 'этап', 'стади', 'прототип', 'дорожн', 'stage'],
  },
  {
    id: 'plan',
    q: { uz: 'Reja qanday?', ru: 'Какой план?', en: 'What is the plan?' },
    a: {
      uz: '1–2 oy: qurilmalar va server. 2–4 oy: EKG bilan validatsiya. 4–11 oy: 100 bemor pilot. 12 oy: bozorga chiqish.',
      ru: '1–2 мес.: устройства и сервер. 2–4 мес.: валидация с ЭКГ. 4–11 мес.: пилот на 100 пациентов. 12 мес.: выход на рынок.',
      en: 'Months 1–2: devices and server. Months 2–4: ECG validation. Months 4–11: 100-patient pilot. Month 12: launch.',
    },
    keys: ['reja', 'pilot', 'keyin', 'kelajak', 'план', 'пилот', 'дальше', 'plan', 'next', 'future'],
  },
  {
    id: 'team',
    sample: true,
    q: { uz: 'Jamoada kimlar bor?', ru: 'Кто в команде?', en: 'Who is on the team?' },
    a: {
      uz: 'Nafisa Gʻanijanova — asoschi, dizayner, UI/UX. Sevinchoy Polatova — AI/ML va telemetriya muhandisi.',
      ru: 'Нафиса Ганиджанова — основатель, дизайнер, UI/UX. Севинчой Полатова — инженер AI/ML и телеметрии.',
      en: 'Nafisa Gʻanijanova, founder, designer and UI/UX. Sevinchoy Polatova, AI/ML and telemetry engineer.',
    },
    keys: ['jamoa', 'kim', 'asoschi', 'muallif', 'nafisa', 'sevinchoy', 'polatova', 'команд', 'кто', 'основат', 'team', 'founder', 'who'],
  },
  {
    id: 'tech',
    q: { uz: 'Qaysi texnologiyalar?', ru: 'Какие технологии?', en: 'What tech is used?' },
    a: {
      uz: 'FastAPI, PostgreSQL, React, Flutter, Wear OS, Telegram Bot va Docker.',
      ru: 'FastAPI, PostgreSQL, React, Flutter, Wear OS, Telegram Bot и Docker.',
      en: 'FastAPI, PostgreSQL, React, Flutter, Wear OS, Telegram Bot and Docker.',
    },
    keys: ['texnolog', 'stek', 'stack', 'python', 'react', 'flutter', 'технолог', 'стек', 'tech'],
  },
  {
    id: 'ai',
    q: { uz: 'AI nima qiladi?', ru: 'Что делает ИИ?', en: 'What does the AI do?' },
    a: {
      uz: 'Har bir bemorning shaxsiy meʼyorini (z-score) hisoblaydi va undan chetlanishni belgilaydi. LLM (Gemini/DeepSeek) Telegram botda savollarga sodda tilda javob beradi.',
      ru: 'Считает личную норму каждого пациента (z-score) и отмечает отклонения. LLM (Gemini/DeepSeek) отвечает на вопросы в Telegram-боте простым языком.',
      en: 'It learns each patient\'s personal baseline (z-score) and flags deviations. An LLM (Gemini/DeepSeek) answers questions in plain language in the Telegram bot.',
    },
    keys: ['ai', 'sunʼiy', 'suniy', 'intellekt', 'llm', 'gemini', 'deepseek', 'ии', 'искусств', 'нейро', 'artificial', 'machine'],
  },
  {
    id: 'demo',
    sample: true,
    q: { uz: 'Demoni qayerda koʻraman?', ru: 'Где посмотреть демо?', en: 'Where can I see the demo?' },
    a: {
      uz: '/demo sahifasida 3 daqiqalik video va jonli prototip havolalari bor. Shifokor paneli: /doctor?demo=true.',
      ru: 'На странице /demo есть 3-минутное видео и ссылки на живой прототип. Панель врача: /doctor?demo=true.',
      en: 'The /demo page has a 3-minute video and links to the live prototype. Doctor dashboard: /doctor?demo=true.',
    },
    keys: ['demo', 'video', 'koʻr', 'korsat', 'демо', 'видео', 'посмотр', 'watch video', 'see'],
  },
  {
    id: 'api',
    q: { uz: 'API bormi?', ru: 'Есть API?', en: 'Is there an API?' },
    a: {
      uz: 'Ha: OpenAPI 3, JWT bilan. Hujjatlar /api/docs da. Bemor maʼlumoti faqat avtorizatsiya va rozilik bilan beriladi.',
      ru: 'Да: OpenAPI 3 с JWT. Документация на /api/docs. Данные пациентов только с авторизацией и согласием.',
      en: 'Yes: OpenAPI 3 with JWT. Docs are at /api/docs. Patient data is only served with authorization and consent.',
    },
    keys: ['api', 'swagger', 'openapi', 'integratsiya', 'интеграц', 'integration', 'endpoint'],
  },
  {
    id: 'family',
    q: { uz: 'Oila qanday xabar oladi?', ru: 'Как семья получает уведомления?', en: 'How does the family get alerts?' },
    a: {
      uz: 'Telegram bot orqali: SOS, yiqilish yoki chegara buzilganda yaqinlarga darhol xabar ketadi. Qarovchi portali ham bor: /r.',
      ru: 'Через Telegram-бот: при SOS, падении или выходе за порог родственники сразу получают сообщение. Есть и портал опекуна: /r.',
      en: 'Through the Telegram bot: on SOS, a fall or a threshold breach relatives are alerted at once. There is also a caregiver portal at /r.',
    },
    keys: ['oila', 'yaqin', 'qarovchi', 'telegram', 'farzand', 'семь', 'родствен', 'опекун', 'family', 'relative', 'caregiver'],
  },
  {
    id: 'doctor',
    q: { uz: 'Shifokor nima qiladi?', ru: 'Что делает врач?', en: 'What does the doctor do?' },
    a: {
      uz: 'Shifokor panelida bemorlar roʻyxati va vazifalar turadi. Har bir ogohlantirish aniq masʼul shifokorga 24 soatlik vazifa boʻlib tushadi.',
      ru: 'В панели врача список пациентов и задач. Каждый сигнал становится задачей на 24 часа для конкретного ответственного врача.',
      en: 'The doctor dashboard lists patients and tasks. Every alert becomes a 24-hour task for a named responsible doctor.',
    },
    keys: ['shifokor', 'vrach', 'doktor', 'panel', 'врач', 'доктор', 'панел', 'doctor', 'physician', 'dashboard'],
  },
  {
    id: 'why',
    q: { uz: 'Nega aynan siz?', ru: 'Почему именно вы?', en: 'Why your team?' },
    a: {
      uz: 'Prototip allaqachon onlayn ishlaydi, 240+ avtomatik test bor va sust internetda ham SMS orqali ogohlantiradi.',
      ru: 'Прототип уже работает онлайн, есть 240+ автотестов, и он предупреждает по SMS даже при слабом интернете.',
      en: 'The prototype already runs online, has 240+ automated tests and alerts by SMS even on a weak connection.',
    },
    keys: ['nega siz', 'nega biz', 'nega aynan', 'farq', 'raqobat', 'почему вы', 'почему мы', 'отлич', 'конкурент', 'why you', 'why us', 'why your', 'compet', 'differ'],
  },
  {
    id: 'contact',
    q: { uz: 'Qanday bogʻlanaman?', ru: 'Как связаться?', en: 'How do I contact you?' },
    a: {
      uz: 'Telegram bot: t.me/WMAX_uz_bot. Kod: github.com/Baxrom0311/wmax.',
      ru: 'Telegram-бот: t.me/WMAX_uz_bot. Код: github.com/Baxrom0311/wmax.',
      en: 'Telegram bot: t.me/WMAX_uz_bot. Code: github.com/Baxrom0311/wmax.',
    },
    keys: ['boglan', 'bogʻlan', 'kontakt', 'aloqa', 'manzil', 'github', 'связ', 'контакт', 'написать', 'contact', 'reach', 'email'],
  },
  {
    id: 'hello',
    q: { uz: 'Salom', ru: 'Привет', en: 'Hello' },
    a: {
      uz: 'Salom! WMAX haqida istalgan savolni bering.',
      ru: 'Здравствуйте! Задайте любой вопрос о WMAX.',
      en: 'Hello! Ask me anything about WMAX.',
    },
    keys: ['salom', 'assalom', 'hayrli', 'привет', 'здравств', 'добрый', 'hello', 'hi', 'hey'],
  },
  {
    id: 'thanks',
    q: { uz: 'Rahmat', ru: 'Спасибо', en: 'Thanks' },
    a: {
      uz: 'Arzimaydi! Yana savol boʻlsa, yozing.',
      ru: 'Пожалуйста! Пишите, если будут ещё вопросы.',
      en: 'You are welcome! Ask again any time.',
    },
    keys: ['rahmat', 'raxmat', 'tashakkur', 'спасибо', 'благодар', 'thank', 'thanks'],
  },
];

const normalize = (s: string) =>
  s
    .toLowerCase()
    .replace(/[ʻʼ'`’‘]/g, '')
    .replace(/[^\p{L}\p{N}₂\s/]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();

export const SAMPLE_QUESTIONS = (lang: Lang) => INTENTS.filter((i) => i.sample).map((i) => i.q[lang]);

/** True when the text is exactly one of the prepared questions. */
export const isSample = (lang: Lang, question: string) => INTENTS.some((i) => normalize(i.q[lang]) === normalize(question));

/**
 * Best prepared answer for a free-text question, or null when nothing matches.
 * One-word keys match the start of a word (so Uzbek and Russian suffixes still
 * match); multi-word keys match as a phrase. Longer matches weigh more.
 */
export function answer(lang: Lang, question: string): string | null {
  const text = normalize(question);
  if (!text) return null;
  const words = text.split(' ');
  let best: { score: number; intent: Intent } | null = null;
  for (const intent of INTENTS) {
    if (intent.q[lang] && normalize(intent.q[lang]) === text) return intent.a[lang];
    let score = 0;
    for (const key of new Set(intent.keys.map(normalize))) {
      const hit = key.includes(' ') ? text.includes(key) : words.some((w) => w.startsWith(key));
      if (hit) score += key.length >= 4 ? 2 : 1;
    }
    if (score > 0 && (!best || score > best.score)) best = { score, intent };
  }
  return best ? best.intent.a[lang] : null;
}

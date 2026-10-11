import type { Lang } from '../../i18n';

/*
 * Pitch Day 3.0 content for the home page and /demo.
 * Kept deliberately short: only what the competition asks for.
 */

export const LINKS = {
  site: 'https://wmax.boos.uz',
  github: 'https://github.com/Baxrom0311/wmax',
  doctorDemo: '/doctor?demo=true',
  relativePortal: '/r',
  telegramBot: 'https://t.me/WMAX_uz_bot',
  apiDocs: '/api/docs',
  apiRedoc: '/api/redoc',
  openapi: '/api/openapi.json',
};

/* Demo video: an mp4 in web-doctor/public/demo/ or a YouTube embed URL. */
export const DEMO_VIDEO = {
  embedUrl: '',
  fileUrl: '/demo/wmax-demo.mp4',
  poster: '/demo/wmax-demo-poster.jpg',
};

export const WATCH_IMAGE = '/images/3d/watch-hero.webp';

/* Watch face shown for each section (crossfades while scrolling). */
export const WATCH_FACES = [
  '/images/3d/watch-red.webp',
  '/images/3d/watch-green.webp',
  '/images/3d/watch-green.webp',
  '/images/3d/watch-green.webp',
  '/images/3d/watch-amber.webp',
  '/images/3d/watch-green.webp',
];

export type TeamMember = { name: string; role: Record<Lang, string>; skills: string[] };

export const TEAM: TeamMember[] = [
  {
    name: 'Baxrom Bekchanov',
    role: {
      uz: 'Asoschi · Tizimlar arxitektori, Full-Stack',
      ru: 'Основатель · Архитектор систем, Full-Stack',
      en: 'Founder · Systems Architect, Full-Stack',
    },
    skills: ['FastAPI', 'PostgreSQL', 'Docker', 'React', 'Flutter'],
  },
  {
    name: 'Nafisa Gʻanijanova',
    role: { uz: 'Asoschi · Dizayner, UI/UX', ru: 'Основатель · Дизайнер, UI/UX', en: 'Founder · Designer, UI/UX' },
    skills: ['Figma', 'UI/UX', 'Product design'],
  },
  {
    name: 'Nodirbek Boltayev',
    role: { uz: 'AI / ML & Telemetriya muhandisi', ru: 'AI / ML & Инженер телеметрии', en: 'AI / ML & Telemetry engineer' },
    skills: ['Python', 'FastAPI', 'PostgreSQL', 'LLM', 'z-score'],
  },
];

export const TECH = ['FastAPI', 'PostgreSQL', 'React', 'Flutter', 'Wear OS', 'Telegram Bot', 'Docker', 'Gemini / DeepSeek'];

export const AI_TOOLS = ['z-score baseline', 'Gemini / DeepSeek', 'Claude Code', 'GitHub Copilot'];

type Stat = { value: string; label: string };
type Step = { title: string; note: string };

export const SECTION_IDS = ['muammo', 'yechim', 'jamoa', 'nega-biz', 'yol-xaritasi', 'reja'] as const;

export type PitchText = {
  tagline: string;
  demo: string;
  prototype: string;
  contact: string;
  scrollHint: string;
  /** One label and one sentence per section, in SECTION_IDS order. */
  sections: { label: string; line: string }[];
  problemDays: string;
  problemStats: Stat[];
  solutionSteps: Step[];
  solutionAi: string;
  techLabel: string;
  why: Stat[];
  roadmap: (Step & { state: 'done' | 'now' | 'next' })[];
  nowLabel: string;
  plan: Step[];
  aiLabel: string;
  contactLine: string;
};

export const PITCH: Record<Lang, PitchText> = {
  uz: {
    tagline: 'Kasalxonadan uygacha uzilmas kuzatuv',
    demo: 'Demo',
    prototype: 'Prototip',
    contact: 'Aloqa',
    scrollHint: 'Pastga aylantiring',
    sections: [
      { label: 'Muammo', line: 'Kasalxonadan chiqqan bemor 30 kun hech kim kuzatmasdan qoladi.' },
      { label: 'Yechim', line: 'Soat oʻlchaydi, shifokor vazifa oladi, oila xabar topadi.' },
      { label: 'Jamoa', line: 'Uch kishi: tizimlar arxitekturasi, dizayn va AI/telemetriya.' },
      { label: 'Nega biz', line: 'Prototip allaqachon onlayn ishlaydi.' },
      { label: 'Yoʻl xaritasi', line: 'Hozir Prototype bosqichidamiz.' },
      { label: 'Reja', line: '12 oyda validatsiya, pilot va bozorga chiqish.' },
    ],
    problemDays: 'kun kasalxonadan keyin hech kim kuzatmaydi',
    problemStats: [
      { value: '12–34%', label: 'xulosa shifokorga yetadi' },
      { value: '3–20%', label: 'kasalxona va shifokor gaplashadi' },
    ],
    solutionSteps: [
      { title: 'Soat', note: 'puls, SpO₂, yiqilish, SOS' },
      { title: 'Shifokor', note: '24 soatlik vazifa' },
      { title: 'Oila', note: 'Telegram xabar' },
    ],
    solutionAi: 'har bir bemorning shaxsiy meʼyori, chetlanishni belgilaydi',
    techLabel: 'Texnologiyalar',
    why: [
      { value: 'Onlayn', label: 'ishlaydigan prototip' },
      { value: '240+', label: 'avtomatik test' },
      { value: 'SMS', label: 'internet yoʻq joyda ham' },
    ],
    roadmap: [
      { title: 'Idea', note: 'muammo tahlili', state: 'done' },
      { title: 'Prototype', note: 'soat, panel, bot', state: 'now' },
      { title: 'MVP', note: '100 bemor pilot', state: 'next' },
      { title: 'Launched', note: 'poliklinikalar', state: 'next' },
    ],
    nowLabel: 'hozir',
    plan: [
      { title: '1–2 oy', note: 'qurilmalar, server' },
      { title: '2–4 oy', note: 'EKG bilan validatsiya' },
      { title: '4–11 oy', note: '100 bemor pilot' },
      { title: '12 oy', note: 'bozorga chiqish' },
    ],
    aiLabel: 'AI vositalari',
    contactLine: 'Savol yoki hamkorlik uchun yozing.',
  },
  ru: {
    tagline: 'Непрерывное наблюдение от больницы до дома',
    demo: 'Демо',
    prototype: 'Прототип',
    contact: 'Контакты',
    scrollHint: 'Прокрутите вниз',
    sections: [
      { label: 'Проблема', line: 'После выписки пациент 30 дней остаётся без наблюдения.' },
      { label: 'Решение', line: 'Часы измеряют, врач получает задачу, семья получает уведомление.' },
      { label: 'Команда', line: 'Три человека: архитектура систем, дизайн и ИИ/телеметрия.' },
      { label: 'Почему мы', line: 'Прототип уже работает онлайн.' },
      { label: 'Дорожная карта', line: 'Сейчас мы на этапе Prototype.' },
      { label: 'План', line: 'За 12 месяцев: валидация, пилот и выход на рынок.' },
    ],
    problemDays: 'дней после выписки без наблюдения',
    problemStats: [
      { value: '12–34%', label: 'выписка доходит до врача' },
      { value: '3–20%', label: 'больница и врач общаются' },
    ],
    solutionSteps: [
      { title: 'Часы', note: 'пульс, SpO₂, падение, SOS' },
      { title: 'Врач', note: 'задача на 24 часа' },
      { title: 'Семья', note: 'уведомление в Telegram' },
    ],
    solutionAi: 'личная норма каждого пациента, отмечает отклонения',
    techLabel: 'Технологии',
    why: [
      { value: 'Онлайн', label: 'работающий прототип' },
      { value: '240+', label: 'автотестов' },
      { value: 'SMS', label: 'даже без интернета' },
    ],
    roadmap: [
      { title: 'Idea', note: 'анализ проблемы', state: 'done' },
      { title: 'Prototype', note: 'часы, панель, бот', state: 'now' },
      { title: 'MVP', note: 'пилот, 100 пациентов', state: 'next' },
      { title: 'Launched', note: 'поликлиники', state: 'next' },
    ],
    nowLabel: 'сейчас',
    plan: [
      { title: '1–2 мес.', note: 'устройства, сервер' },
      { title: '2–4 мес.', note: 'валидация с ЭКГ' },
      { title: '4–11 мес.', note: 'пилот, 100 пациентов' },
      { title: '12 мес.', note: 'выход на рынок' },
    ],
    aiLabel: 'ИИ-инструменты',
    contactLine: 'Пишите по вопросам и сотрудничеству.',
  },
  en: {
    tagline: 'Unbroken follow-up from hospital to home',
    demo: 'Demo',
    prototype: 'Prototype',
    contact: 'Contact',
    scrollHint: 'Scroll down',
    sections: [
      { label: 'Problem', line: 'After discharge, patients go 30 days with no one watching.' },
      { label: 'Solution', line: 'The watch measures, the doctor gets a task, the family gets an alert.' },
      { label: 'Team', line: 'Three members: systems architecture, design and AI/telemetry.' },
      { label: 'Why us', line: 'The prototype already runs online.' },
      { label: 'Roadmap', line: 'We are at the Prototype stage.' },
      { label: 'Plan', line: 'In 12 months: validation, pilot and launch.' },
    ],
    problemDays: 'days after discharge with no follow-up',
    problemStats: [
      { value: '12–34%', label: 'discharge notes reach the doctor' },
      { value: '3–20%', label: 'hospital and doctor talk' },
    ],
    solutionSteps: [
      { title: 'Watch', note: 'pulse, SpO₂, falls, SOS' },
      { title: 'Doctor', note: '24-hour task' },
      { title: 'Family', note: 'Telegram alert' },
    ],
    solutionAi: 'personal baseline for each patient, flags deviations',
    techLabel: 'Tech stack',
    why: [
      { value: 'Live', label: 'working prototype' },
      { value: '240+', label: 'automated tests' },
      { value: 'SMS', label: 'even with no internet' },
    ],
    roadmap: [
      { title: 'Idea', note: 'problem research', state: 'done' },
      { title: 'Prototype', note: 'watch, dashboard, bot', state: 'now' },
      { title: 'MVP', note: '100-patient pilot', state: 'next' },
      { title: 'Launched', note: 'polyclinics', state: 'next' },
    ],
    nowLabel: 'now',
    plan: [
      { title: 'Months 1–2', note: 'devices, server' },
      { title: 'Months 2–4', note: 'ECG validation' },
      { title: 'Months 4–11', note: '100-patient pilot' },
      { title: 'Month 12', note: 'launch' },
    ],
    aiLabel: 'AI tools',
    contactLine: 'Write to us with questions or partnership ideas.',
  },
};

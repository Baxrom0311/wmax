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

export type TeamMember = { name: string; role: Record<Lang, string>; skills: string[] };

export const TEAM: TeamMember[] = [
  {
    name: 'Nafisa Gʻanijanova',
    role: { uz: 'Asoschi · Dizayner, UI/UX', ru: 'Основатель · Дизайнер, UI/UX', en: 'Founder · Designer, UI/UX' },
    skills: ['Figma', 'UI/UX', 'Product design'],
  },
  {
    name: 'Nodirbek Boltayev',
    role: { uz: 'Backend · AI/LLM muhandis', ru: 'Backend · AI/LLM-инженер', en: 'Backend · AI/LLM engineer' },
    skills: ['Python', 'FastAPI', 'PostgreSQL', 'LLM'],
  },
];

export const TECH = ['FastAPI', 'PostgreSQL', 'React', 'Flutter', 'Wear OS', 'Telegram Bot', 'Docker', 'Gemini / DeepSeek'];

export const AI_TOOLS = ['z-score baseline', 'Gemini / DeepSeek', 'Claude Code', 'GitHub Copilot'];

type Stat = { value: string; label: string };
type Step = { title: string; note: string };

export type PitchText = {
  tagline: string;
  demo: string;
  prototype: string;
  nav: [string, string, string, string, string, string];
  problemLead: string;
  problemStats: Stat[];
  solutionSteps: Step[];
  teamLinks: string;
  techLabel: string;
  why: Stat[];
  roadmap: (Step & { state: 'done' | 'now' | 'next' })[];
  nowLabel: string;
  plan: Step[];
  aiLabel: string;
  demoLead: string;
};

export const PITCH: Record<Lang, PitchText> = {
  uz: {
    tagline: 'Kasalxonadan uygacha uzilmas kuzatuv',
    demo: 'Demo-video',
    prototype: 'Prototip',
    nav: ['Muammo → Yechim', 'Jamoa', 'Nega biz', 'Yoʻl xaritasi', 'Reja', 'Demo'],
    problemLead: 'Kasalxonadan chiqqan bemor 30 kun nazoratsiz qoladi',
    problemStats: [
      { value: '12–34%', label: 'xulosa shifokorga yetadi' },
      { value: '3–20%', label: 'kasalxona va shifokor gaplashadi' },
    ],
    solutionSteps: [
      { title: 'Soat', note: 'puls, SpO₂, yiqilish, SOS' },
      { title: 'Shifokor', note: '24 soatlik vazifa' },
      { title: 'Oila', note: 'Telegram xabar' },
    ],
    teamLinks: 'Havolalar',
    techLabel: 'Texnologiyalar',
    why: [
      { value: 'Onlayn', label: 'ishlaydigan prototip' },
      { value: '240+', label: 'avtomatik test' },
      { value: 'Offline', label: 'sust internet + SMS zaxira' },
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
      { title: '12 oy', note: 'tijoratlashtirish' },
    ],
    aiLabel: 'AI vositalari',
    demoLead: '3 daqiqalik video va jonli prototip',
  },
  ru: {
    tagline: 'Непрерывное наблюдение от больницы до дома',
    demo: 'Демо-видео',
    prototype: 'Прототип',
    nav: ['Проблема → Решение', 'Команда', 'Почему мы', 'Дорожная карта', 'План', 'Демо'],
    problemLead: 'После выписки пациент 30 дней без наблюдения',
    problemStats: [
      { value: '12–34%', label: 'выписка доходит до врача' },
      { value: '3–20%', label: 'больница и врач общаются' },
    ],
    solutionSteps: [
      { title: 'Часы', note: 'пульс, SpO₂, падение, SOS' },
      { title: 'Врач', note: 'задача на 24 часа' },
      { title: 'Семья', note: 'уведомление в Telegram' },
    ],
    teamLinks: 'Ссылки',
    techLabel: 'Технологии',
    why: [
      { value: 'Онлайн', label: 'работающий прототип' },
      { value: '240+', label: 'автотестов' },
      { value: 'Офлайн', label: 'слабый интернет + SMS' },
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
      { title: '12 мес.', note: 'коммерциализация' },
    ],
    aiLabel: 'ИИ-инструменты',
    demoLead: '3-минутное видео и живой прототип',
  },
  en: {
    tagline: 'Unbroken follow-up from hospital to home',
    demo: 'Demo video',
    prototype: 'Prototype',
    nav: ['Problem → Solution', 'Team', 'Why us', 'Roadmap', 'Plan', 'Demo'],
    problemLead: 'After discharge, patients go 30 days unmonitored',
    problemStats: [
      { value: '12–34%', label: 'discharge notes reach the doctor' },
      { value: '3–20%', label: 'hospital and doctor talk' },
    ],
    solutionSteps: [
      { title: 'Watch', note: 'pulse, SpO₂, falls, SOS' },
      { title: 'Doctor', note: '24-hour task' },
      { title: 'Family', note: 'Telegram alert' },
    ],
    teamLinks: 'Links',
    techLabel: 'Tech stack',
    why: [
      { value: 'Live', label: 'working prototype' },
      { value: '240+', label: 'automated tests' },
      { value: 'Offline', label: 'weak internet + SMS fallback' },
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
      { title: 'Month 12', note: 'go to market' },
    ],
    aiLabel: 'AI tools',
    demoLead: '3-minute video and a live prototype',
  },
};

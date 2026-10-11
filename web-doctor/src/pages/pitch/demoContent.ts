import type { Lang } from '../../i18n';

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
  apiTitle: string;
  apiSub: string;
  apiNote: string;
  copy: string;
  copied: string;
  back: string;
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
    apiTitle: 'API kirish (API Access)',
    apiSub: 'OpenAPI 3 · JWT bilan.',
    apiNote: 'Bemor maʼlumotlari faqat avtorizatsiya va bemor roziligi bilan beriladi.',
    copy: 'Nusxa olish',
    copied: 'Nusxa olindi',
    back: 'Bosh sahifa',
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
    apiTitle: 'Доступ к API',
    apiSub: 'OpenAPI 3 · с JWT.',
    apiNote: 'Данные пациентов выдаются только при авторизации и согласии пациента.',
    copy: 'Копировать',
    copied: 'Скопировано',
    back: 'Главная',
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
    apiTitle: 'API access',
    apiSub: 'OpenAPI 3 · JWT protected.',
    apiNote: 'Patient data is only served with authorization and patient consent.',
    copy: 'Copy',
    copied: 'Copied',
    back: 'Home',
  },
};

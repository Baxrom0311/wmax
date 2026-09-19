import type { PatientDetail, PatientSummary, SosEventItem } from "./types";

export const MOCK_PATIENTS: PatientSummary[] = [
  {
    id: "p-001-red",
    full_name: "Otabek Rahimov",
    age: 68,
    sex: "m",
    diagnosis: "Yurak ishemik kasalligi (YIK). Zo'riqish stenokardiyasi FK III. Postinfarkt kardioskleroz. SYuYe IIB bosqich, NYHA III. Sinusli taxikardiya va o'tkir gipoksemiya epizodlari",
    district: "Urganch",
    phase: "full",
    level: "red",
    composite_score: 4.8,
    triggered_params: { spo2: 87, hr_mean: 112, skin_temp: 37.4 },
    trend: {
      slope: 0.38,
      direction: "worsening",
      recommendation_key: "rec.contact_today",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
    open_task: {
      id: 101,
      patient_id: "p-001-red",
      type: "active_call",
      status: "created",
      created_at: new Date(Date.now() - 6 * 3600 * 1000).toISOString(),
      due_at: new Date(Date.now() + 18 * 3600 * 1000).toISOString(),
      confirmed_at: null,
      note: null,
    },
  },
  {
    id: "p-002-amber",
    full_name: "Gulnora Matyoqubova",
    age: 72,
    sex: "f",
    diagnosis: "Gipertoniya kasalligi III bosqich, 3-daraja, xavf IV (o'ta yuqori). 2-tur qandli diabet, subkompensatsiya. Diabetik mikroangiopatiya va vegetativ disbalans",
    district: "Xiva",
    phase: "learning",
    level: "amber",
    composite_score: 2.6,
    triggered_params: { rmssd: 18.2, hr_mean: 94 },
    trend: {
      slope: 0.16,
      direction: "worsening",
      recommendation_key: "rec.visit_within_3_days",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
    open_task: {
      id: 102,
      patient_id: "p-002-amber",
      type: "active_call",
      status: "sent",
      created_at: new Date(Date.now() - 20 * 3600 * 1000).toISOString(),
      due_at: new Date(Date.now() + 4 * 3600 * 1000).toISOString(),
      confirmed_at: null,
      note: null,
    },
  },
  {
    id: "p-004-nodata",
    full_name: "Jumaniyoz Otajonov",
    age: 65,
    sex: "m",
    diagnosis: "O'pkaning surunkali obstruktiv kasalligi (O'SOK), og'ir kechishi (GOLD III). Surunkali o'pka yuragi, dekompensatsiya xavfi",
    district: "Shovot",
    phase: "full",
    level: "no_data",
    composite_score: 0.0,
    triggered_params: {},
    trend: {
      slope: 0.0,
      direction: "stable",
      recommendation_key: "rec.continue_monitoring",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 55 * 60 * 1000).toISOString(),
    open_task: null,
  },
  {
    id: "p-003-green",
    full_name: "Rustam Karimov",
    age: 59,
    sex: "m",
    diagnosis: "Birlamchi kardiomiopatiya. SYuYe I-IIA bosqich, NYHA II. Sinus ritmi, barqaror gemodinamika va kompensatsiya",
    district: "Xonqa",
    phase: "full",
    level: "green",
    composite_score: 0.8,
    triggered_params: {},
    trend: {
      slope: -0.22,
      direction: "improving",
      recommendation_key: "rec.routine_followup",
      days_used: 7,
    },
    last_reading_at: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
    open_task: null,
  },
];

export function getMockPatientDetail(id: string): PatientDetail {
  const summary = MOCK_PATIENTS.find((p) => p.id === id) || MOCK_PATIENTS[0];

  // Generate 7 days of hourly points
  const now = Date.now();
  const pointsHR = [];
  const pointsSPO2 = [];
  const pointsTemp = [];
  const pointsRMSSD = [];
  const pointsRR = [];
  const pointsSteps = [];

  for (let i = 42; i >= 0; i--) {
    const ts = new Date(now - i * 4 * 3600 * 1000).toISOString();
    const severityFactor = summary.level === "red" && i < 15 ? (15 - i) * 1.5 : 0;

    pointsHR.push({
      ts,
      value: Math.round(72 + Math.sin(i / 3) * 6 + severityFactor * 2.5),
    });
    pointsSPO2.push({
      ts,
      value: Math.max(84, Math.round(97 - Math.cos(i / 4) * 1.5 - severityFactor * 0.7)),
    });
    pointsTemp.push({
      ts,
      value: Number((36.4 + Math.sin(i / 5) * 0.3 + (severityFactor > 0 ? 0.8 : 0)).toFixed(1)),
    });
    pointsRMSSD.push({
      ts,
      value: Math.max(12, Math.round(34 - severityFactor * 1.2 + Math.sin(i / 2) * 4)),
    });
    pointsRR.push({
      ts,
      value: Math.round(16 + Math.sin(i / 4) * 2 + (severityFactor > 0 ? 4 : 0)),
    });
    pointsSteps.push({
      ts,
      value: Math.max(0, Math.round(450 + Math.sin(i / 2) * 350 - severityFactor * 20)),
    });
  }

  return {
    ...summary,
    baseline_approved: summary.phase === "full",
    prognosis: {
      risk_level: summary.level === "red" ? "high" : summary.level === "amber" ? "moderate" : "low",
      risk_probability_pct: summary.level === "red" ? 86 : summary.level === "amber" ? 64 : 14,
      early_warning_hours: 48,
      summary:
        summary.level === "red"
          ? "SpO2 pasayishi (-2.4σ) va tinch holatda yuqori yurak urishi (+3.1σ) kuzatilmoqda. 72 soat ichida gospitalizatsiya xavfi yuqori."
          : "Fiziologik parametrlar shaxsiy me'yor koridorida barqaror.",
      recommendation:
        summary.level === "red"
          ? "Bugun zudlik bilan bemor xonadoniga patronaj tashrifini amalga oshirish va dori dozasini qayta sozlash zarur."
          : "Rejali dispanser kuzatuvini davom ettirish.",
    },
    problems: [
      {
        param: "spo2",
        label: "Kislorod to'yinishi (SpO₂)",
        deviation: summary.level === "red" ? "-2.4σ me'yordan past" : "Normada",
        current_value: summary.level === "red" ? 87.0 : 97.5,
        baseline_range: "95.5% - 98.8%",
        severity: summary.level === "red" ? "severe" : "mild",
        explanation: "Gipoksemiya belgilari. O'pka va yurak yetishmovchiligi kuchayishi mumkin.",
      },
      {
        param: "hr_mean",
        label: "Tinch holatdagi puls",
        deviation: summary.level === "red" ? "+3.1σ me'yordan yuqori" : "Normada",
        current_value: summary.level === "red" ? 112.0 : 72.0,
        baseline_range: "66 - 76 bpm",
        severity: summary.level === "red" ? "severe" : "mild",
        explanation: "Kompensator taxikardiya. Gemodinamik barqarorsizlik xavfi.",
      },
    ],
    series: [
      {
        param: "hr_mean",
        points: pointsHR,
        baseline_median: 72,
        baseline_low: 66,
        baseline_high: 76,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsHR[pointsHR.length - 8].ts, to: pointsHR[pointsHR.length - 1].ts }]
            : [],
      },
      {
        param: "spo2",
        points: pointsSPO2,
        baseline_median: 97,
        baseline_low: 95.5,
        baseline_high: 98.8,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsSPO2[pointsSPO2.length - 6].ts, to: pointsSPO2[pointsSPO2.length - 1].ts }]
            : [],
      },
      {
        param: "skin_temp",
        points: pointsTemp,
        baseline_median: 36.5,
        baseline_low: 36.1,
        baseline_high: 36.9,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsTemp[pointsTemp.length - 5].ts, to: pointsTemp[pointsTemp.length - 1].ts }]
            : [],
      },
      {
        param: "rmssd",
        points: pointsRMSSD,
        baseline_median: 38,
        baseline_low: 32,
        baseline_high: 48,
        deviated_ranges: [],
      },
      {
        param: "rr_est",
        points: pointsRR,
        baseline_median: 16,
        baseline_low: 14,
        baseline_high: 18,
        deviated_ranges:
          summary.level === "red"
            ? [{ from: pointsRR[pointsRR.length - 4].ts, to: pointsRR[pointsRR.length - 1].ts }]
            : [],
      },
      {
        param: "steps",
        points: pointsSteps,
        baseline_median: 450,
        baseline_low: 200,
        baseline_high: 700,
        deviated_ranges: [],
      },
    ],
    alerts: [
      {
        id: 1,
        ts: new Date(now - 2 * 3600 * 1000).toISOString(),
        level: summary.level,
        composite_score: summary.composite_score,
        triggered_params: summary.triggered_params,
        anomaly_score: summary.level === "red" ? 0.84 : null,
        reason:
          summary.level === "red"
            ? "SpO2 pasayishi va taxikardiya aniqlandi"
            : "Barqaror parametrlar",
      },
    ],
    tasks: summary.open_task ? [summary.open_task] : [],
  };
}

export let MOCK_SOS_EVENTS: SosEventItem[] = [
  {
    id: "sos-001-red",
    patient_id: "p-001-red",
    patient_name: "Otabek Rahimov (68 yosh)",
    raised_at: new Date(Date.now() - 4 * 60 * 1000).toISOString(),
    status: "raised",
    source: "watch_button",
    address_snapshot: {
      region: "Xorazm",
      district: "Urganch",
      street: "Al-Xorazmiy ko'chasi",
      house: "45",
      flat: "14",
      landmark: "GUM savdo markazi va 1-son maktab orqasi",
      entrance_note: "2-podyezd, 3-qavat, domofon: 14",
      contact_phone: "+998 90 123 45 67 (Qarindoshi: Dilnoza)",
    },
    clinical_snapshot: {
      blood_group: "A(II)",
      rh: "Musbat (+)",
      primary_diagnosis: "Yurak ishemik kasalligi (YIK). Zo'riqish stenokardiyasi FK III. Postinfarkt kardioskleroz",
      allergies: [
        { substance: "Penitsillin", reaction: "Anafilaktik shok / teri toshmasi" },
      ],
      active_medications: [
        { name: "Bisoprolol", dose: "5 mg", frequency: "ertalab 1 mahal" },
        { name: "Klopidogrel", dose: "75 mg", frequency: "kechqurun" },
        { name: "Nitrosorbid", dose: "10 mg", frequency: "talab bo'yicha" },
      ],
    },
    vitals_snapshot: {
      hr: 128,
      spo2: 85,
      skin_temp: 37.8,
      rr: 26,
    },
    device_lat: 41.5543,
    device_lon: 60.6315,
  },
  {
    id: "sos-002-amber",
    patient_id: "p-002-amber",
    patient_name: "Gulnora Matyoqubova (72 yosh)",
    raised_at: new Date(Date.now() - 18 * 60 * 1000).toISOString(),
    status: "acknowledged",
    source: "auto_critical",
    address_snapshot: {
      region: "Xorazm",
      district: "Xiva",
      street: "Pahlavon Mahmud ko'chasi",
      house: "12",
      flat: "",
      landmark: "Ichan Qal'a, Kalta Minor mehmonxonasi ro'parasi",
      entrance_note: "Hovli uyi, ko'k temir darvoza",
      contact_phone: "+998 91 987 65 43 (O'g'li: Jamshid)",
    },
    clinical_snapshot: {
      blood_group: "O(I)",
      rh: "Musbat (+)",
      primary_diagnosis: "Gipertoniya kasalligi III bosqich. 2-tur qandli diabet. Ortostatik gipotenziya",
      allergies: [
        { substance: "Aspirin", reaction: "Me'da qonashi xavfi" },
      ],
      active_medications: [
        { name: "Ramipril", dose: "2.5 mg", frequency: "kechqurun 1 mahal" },
        { name: "Metformin", dose: "850 mg", frequency: "kuniga 2 mahal" },
      ],
    },
    vitals_snapshot: {
      hr: 98,
      spo2: 93,
      skin_temp: 36.6,
      rr: 20,
    },
    device_lat: 41.3783,
    device_lon: 60.3589,
    acknowledged_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
  },
];

export function getMockActiveSos(): SosEventItem[] {
  return [...MOCK_SOS_EVENTS.filter((e) => e.status !== "resolved" && e.status !== "cancelled")];
}

export function mockAcknowledgeSos(sosId: string): SosEventItem {
  const item = MOCK_SOS_EVENTS.find((e) => e.id === sosId);
  if (!item) throw new Error("SOS hodisasi topilmadi");
  item.status = "acknowledged";
  item.acknowledged_at = new Date().toISOString();
  return { ...item };
}

export function mockDispatchSos103(sosId: string, ref?: string): SosEventItem {
  const item = MOCK_SOS_EVENTS.find((e) => e.id === sosId);
  if (!item) throw new Error("SOS hodisasi topilmadi");
  item.status = "dispatched_103";
  item.dispatched_at = new Date().toISOString();
  item.dispatch_ref_103 = ref || `103-BRIGADE-${Math.floor(1000 + Math.random() * 9000)}`;
  return { ...item };
}

export function mockResolveSos(sosId: string, note: string): SosEventItem {
  const item = MOCK_SOS_EVENTS.find((e) => e.id === sosId);
  if (!item) throw new Error("SOS hodisasi topilmadi");
  item.status = "resolved";
  item.resolved_at = new Date().toISOString();
  item.resolution_note = note;
  return { ...item };
}


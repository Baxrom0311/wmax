import type { PatientDetail } from "../lib/types";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

export const aiService = {
  /**
   * Generates a comprehensive clinical assessment for a patient
   */
  generatePatientAnalysis(patient: PatientDetail): string {
    const isWorsening = patient.trend.direction === "worsening";
    const problemsCount = patient.problems?.length || 0;

    return `### Fiziologik Dekompensatsiya va Xavf Tahlili: **${patient.full_name}** (${patient.age} yosh)

**Klinik Holat:** ${patient.level === "red" ? "🔴 Yuqori xavf (Kritik dekompensatsiya ehtimoli)" : patient.level === "amber" ? "🟡 E'tibor talab (Erta o'zgarishlar fazasi)" : "🟢 Barqaror me'yor"}
**Tashxis:** ${patient.diagnosis}
**72-soatlik AI dekommutatsiya ehtimolligi:** ${patient.prognosis?.risk_probability_pct ?? (isWorsening ? 75 : 15)}%

#### 1. Asosiy aniqlangan fiziologik og'ishlar (${problemsCount} ta):
${
  patient.problems && patient.problems.length > 0
    ? patient.problems
        .map(
          (p) =>
            `- **${p.label}:** ${p.current_value} (Shaxsiy me'yor: ${p.baseline_range}) → *${p.deviation}* [${p.severity.toUpperCase()}]`
        )
        .join("\n")
    : "- Barcha o'lchovlar shaxsiy me'yoriy koridorda (z-score < 1.5)."
}

#### 2. LINK-HF modeli bo'yicha dinamika:
- **Trend:** ${patient.trend.direction === "worsening" ? "↘ Salbiy tendensiya (oxirgi 72 soatda kompozit og'ish ortmoqda)" : "→ Barqaror"}
- **Soat taqish darajasi:** 98.4% (Signal ishonchliligi yuqori)
- **Kritik oyna:** ${isWorsening ? "Keyingi 24-48 soat ichida gospitalizatsiya xavfi yuqori" : "Rejali nazorat yetarli"}

#### 3. Shifokor uchun taklif etilayotgan klinik harakatlar:
1. **Dori korreksiyasi:** Diuretik dozalarini va beta-blokator qabulini qayta ko'rib chiqish.
2. **Patronaj:** 24 soatlik faol patronaj tashrifini o'tkazish va arterial bosimni o'lchash.
3. **Kislorod saturatsiyasi:** SpO2 < 90% bo'lganda zudlik bilan statsionar reanimatsiyaga yo'naltirish.`;
  },

  /**
   * Simulates a token-by-token streaming AI response for ChatGPT-grade UX
   */
  async *streamResponse(prompt: string, patient?: PatientDetail | null): AsyncGenerator<string, void, unknown> {
    let fullResponse = "";
    if (patient && (prompt.toLowerCase().includes("tahlil") || prompt.toLowerCase().includes("bemor") || prompt.toLowerCase().includes("holat"))) {
      fullResponse = aiService.generatePatientAnalysis(patient);
    } else if (prompt.toLowerCase().includes("aktiv") || prompt.toLowerCase().includes("chaqiruv")) {
      fullResponse = `**Aktiv Chaqiruv Tavsiyasi:**\n\nBemor **${patient?.full_name || "Otabek Ro'zmetov"}** statsionardan yaqinda chiqarilgan. 11-muammo reglamentiga muvofiq:\n1. 24 soatlik muddat tugashiga qadar patronaj hamshirasi bemor xonadoniga tashrif buyurishi shart.\n2. Yurak tonlari auskultatsiyasi va periferik shishlar tekshiriladi.\n3. Tizimda "Patronajni tasdiqlash" tugmasi bosilib, klinik izoh kiritiladi.`;
    } else {
      fullResponse = `Assalomu alaykum, hurmatli hamkasb! Men **NAZORAT Klinik AI Assistentiman**.\n\nSizga bemorlarning Galaxy Watch orqali uzatilayotgan uzluksiz biometrik oqimini (HR, HRV, SpO2, teri harorati, nafas tezligi) tahlil qilishda va **LINK-HF shaxsiy bazaviy modeli** asosida erta dekommutatsiyani bashorat qilishda yordam beraman.\n\nQaysi bemor bo'yicha chuqur tahlil kerak?`;
    }

    const words = fullResponse.split(" ");
    for (const word of words) {
      await new Promise((r) => setTimeout(r, 22));
      yield word + " ";
    }
  },
};

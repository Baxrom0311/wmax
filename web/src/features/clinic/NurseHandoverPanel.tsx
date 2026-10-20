import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Eye, Pill, RefreshCw, Stethoscope, Watch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { pick, type Lang } from "@/i18n";
import { formatDateTime } from "@/lib/format";
import type { NurseChecklistItem, NurseHandoverSBAR } from "@/lib/types";
import { cn } from "@/lib/utils";

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 } as const;
const PRIORITY_VARIANT = { critical: "risk", high: "risk", medium: "attention", low: "good" } as const;
const CATEGORY_ICON = { vitals: Stethoscope, medication: Pill, device: Watch, observation: Eye } as const;

const URGENCY = {
  critical: { variant: "risk" as const, label: { uz: "Kritik shoshilinch", ru: "Критически срочно", en: "Critical" } },
  urgent: { variant: "attention" as const, label: { uz: "Shoshilinch", ru: "Срочно", en: "Urgent" } },
  routine: { variant: "good" as const, label: { uz: "Odatiy rejali", ru: "Планово", en: "Routine" } },
};

const PRIORITY_LABEL = {
  critical: { uz: "Shoshilinch", ru: "Срочно", en: "Critical" },
  high: { uz: "Yuqori", ru: "Высокий", en: "High" },
  medium: { uz: "O'rta", ru: "Средний", en: "Medium" },
  low: { uz: "Past", ru: "Низкий", en: "Low" },
};

export function NurseHandoverPanel({
  handover,
  onRefresh,
  refreshing,
  lang,
}: {
  handover: NurseHandoverSBAR;
  onRefresh: () => void;
  refreshing: boolean;
  lang: Lang;
}) {
  // Checklist ticks are a local shift aid; the backend has no endpoint to persist them.
  const [checklist, setChecklist] = useState<NurseChecklistItem[]>(handover.shift_checklist);
  const sorted = useMemo(() => [...checklist].sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]), [checklist]);
  const done = checklist.filter((c) => c.completed).length;
  const pct = checklist.length ? Math.round((done / checklist.length) * 100) : 0;
  const urgency = URGENCY[handover.clinical_urgency];

  const sbar = [
    { letter: "S", title: pick(lang, { uz: "Vaziyat", ru: "Ситуация", en: "Situation" }), text: handover.situation },
    { letter: "B", title: pick(lang, { uz: "Anamnez", ru: "Анамнез", en: "Background" }), text: handover.background },
    { letter: "A", title: pick(lang, { uz: "Baholash", ru: "Оценка", en: "Assessment" }), text: handover.assessment },
    { letter: "R", title: pick(lang, { uz: "Tavsiya", ru: "Рекомендация", en: "Recommendation" }), text: handover.recommendation },
  ];

  return (
    <div className="space-y-4">
      <Card className="gap-4">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={urgency.variant}>{pick(lang, urgency.label)}</Badge>
              {handover.vital_flags.map((flag) => (
                <Badge key={flag} variant="outline" className="gap-1">
                  <AlertTriangle className="text-attention" />
                  {flag}
                </Badge>
              ))}
            </div>
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
              <RefreshCw className={cn(refreshing && "animate-spin")} />
              {pick(lang, { uz: "Yangilash", ru: "Обновить", en: "Refresh" })}
            </Button>
          </div>
          <div className="mt-2 flex items-center gap-3">
            <span className="text-muted-foreground text-xs whitespace-nowrap">
              {pick(lang, { uz: "Smena vazifalari", ru: "Задачи смены", en: "Shift tasks" })}: <strong className="text-foreground">{done}/{checklist.length}</strong>
            </span>
            <Progress value={pct} className="h-1.5" indicatorClassName={pct === 100 ? "bg-good" : undefined} />
            <span className="tabular text-xs font-medium">{pct}%</span>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="sbar">
        <TabsList>
          <TabsTrigger value="sbar">SBAR</TabsTrigger>
          <TabsTrigger value="checklist">
            {pick(lang, { uz: "Vazifalar", ru: "Задачи", en: "Checklist" })} ({done}/{checklist.length})
          </TabsTrigger>
        </TabsList>
        <TabsContent value="sbar" className="space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            {sbar.map((block) => (
              <Card key={block.letter} className="gap-2 py-4">
                <CardHeader className="px-4">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <span className="bg-primary text-primary-foreground flex size-6 items-center justify-center rounded-md text-xs font-bold">{block.letter}</span>
                    {block.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-4 text-sm leading-relaxed">{block.text}</CardContent>
              </Card>
            ))}
          </div>
          <div className="text-muted-foreground flex flex-wrap items-center gap-2 text-xs">
            {handover.evidence_citations.map((c) => (
              <Badge key={c} variant="secondary" className="font-normal">
                {c}
              </Badge>
            ))}
            <span className="ml-auto">
              {pick(lang, { uz: "Model ishonchi", ru: "Уверенность модели", en: "Model confidence" })}:{" "}
              <strong className="text-foreground">{handover.confidence_score == null ? "—" : `${Math.round(handover.confidence_score * 100)}%`}</strong>
              {handover.generated_at && <> · {formatDateTime(handover.generated_at, lang)}</>}
            </span>
          </div>
          <p className="text-muted-foreground text-xs">
            {pick(lang, {
              uz: "AI yordamchi matni — klinik qaror uchun shifokor tekshiruvi talab etiladi.",
              ru: "Текст AI-помощника — для клинического решения требуется проверка врача.",
              en: "AI assistant draft — clinician review is required before any clinical decision.",
            })}
          </p>
        </TabsContent>
        <TabsContent value="checklist" className="space-y-2">
          {sorted.map((item) => {
            const Icon = CATEGORY_ICON[item.category] ?? Eye;
            return (
              <label
                key={item.id}
                className={cn(
                  "bg-card flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition",
                  item.completed && "bg-good-soft/40 border-good/30",
                )}
              >
                <Checkbox
                  checked={item.completed}
                  onCheckedChange={() => setChecklist((prev) => prev.map((c) => (c.id === item.id ? { ...c, completed: !c.completed } : c)))}
                />
                <Icon className="text-muted-foreground size-4 shrink-0" />
                <span className={cn("flex-1 text-sm", item.completed && "text-muted-foreground line-through")}>{item.task}</span>
                <Badge variant={PRIORITY_VARIANT[item.priority]}>{pick(lang, PRIORITY_LABEL[item.priority])}</Badge>
              </label>
            );
          })}
          {checklist.length > 0 && done === checklist.length && (
            <p className="text-good-ink flex items-center justify-center gap-2 py-2 text-sm font-medium">
              <CheckCircle2 className="size-4" />
              {pick(lang, { uz: "Barcha vazifalar bajarildi", ru: "Все задачи выполнены", en: "All tasks complete" })}
            </p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

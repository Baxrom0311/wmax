import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Battery, KeyRound, Link2, Loader2, Plus, RefreshCw, RotateCcw, Search, Watch } from "lucide-react";
import { EmptyState, ErrorState, PageHeader } from "@/components/app/states";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useNow } from "@/hooks/use-now";
import { pick, type Lang } from "@/i18n";
import { t } from "@/i18n/clinic";
import { assignDevice, createDeviceEnrollment, fetchDevices, registerDevice, returnDevice } from "@/lib/clinic-api";
import { formatAgo, formatCountdown, formatUzs, msUntil } from "@/lib/format";
import { usePrefs } from "@/lib/prefs";
import type { DeviceEnrollResponse, DeviceItem, DeviceTier } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useClinicData, useClinicSession } from "./session";

const TIERS: { value: DeviceTier; label: string }[] = [
  { value: "tier1_wearos", label: "Tier 1 · Wear OS" },
  { value: "tier2_wearos_budget", label: "Tier 2 · Wear OS budget" },
  { value: "tier3_ble_band", label: "Tier 3 · BLE band" },
];

function statusMeta(status: string, lang: Lang): { label: string; variant: "good" | "attention" | "risk" | "nodata" | "secondary" } {
  switch (status) {
    case "in_stock":
      return { label: pick(lang, { uz: "Omborda", ru: "На складе", en: "In stock" }), variant: "secondary" };
    case "assigned":
    case "active":
      return { label: pick(lang, { uz: "Bemorda", ru: "У пациента", en: "With patient" }), variant: "good" };
    case "maintenance":
      return { label: pick(lang, { uz: "Ko'rikda", ru: "На обслуживании", en: "Maintenance" }), variant: "attention" };
    case "retired":
      return { label: pick(lang, { uz: "Yaroqsiz", ru: "Списано", en: "Retired" }), variant: "risk" };
    case "lost":
      return { label: pick(lang, { uz: "Yo'qolgan", ru: "Утеряно", en: "Lost" }), variant: "nodata" };
    default:
      return { label: status, variant: "nodata" };
  }
}

type Dialogs =
  | { kind: "register" }
  | { kind: "assign"; device: DeviceItem }
  | { kind: "return"; device: DeviceItem }
  | { kind: "enroll"; device: DeviceItem; result: DeviceEnrollResponse | null }
  | null;

export function DevicesPage() {
  const { lang } = usePrefs();
  const { isDemo } = useClinicSession();
  const { patients } = useClinicData();
  const now = useNow(5000);

  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tier, setTier] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [query, setQuery] = useState("");
  const [dialog, setDialog] = useState<Dialogs>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setDevices(await fetchDevices(isDemo));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoaded(true);
    }
  }, [isDemo]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- inventory hydrates from the API
    void load();
  }, [load]);

  const kpis = useMemo(
    () => ({
      total: devices.length,
      stock: devices.filter((d) => d.status === "in_stock").length,
      assigned: devices.filter((d) => d.status === "assigned" || d.status === "active").length,
      maintenance: devices.filter((d) => d.status === "maintenance").length,
    }),
    [devices],
  );

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return devices.filter((d) => {
      if (tier !== "all" && d.tier !== tier) return false;
      if (status !== "all") {
        if (status === "assigned" ? !(d.status === "assigned" || d.status === "active") : d.status !== status) return false;
      }
      if (q && !`${d.serial_number} ${d.model_name} ${d.patient_name ?? ""}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [devices, tier, status, query]);

  const act = async (fn: () => Promise<void>, success: string) => {
    setBusy(true);
    try {
      await fn();
      toast.success(success);
      setDialog(null);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const enroll = async (device: DeviceItem) => {
    setDialog({ kind: "enroll", device, result: null });
    try {
      const result = await createDeviceEnrollment(device.id, isDemo);
      setDialog({ kind: "enroll", device, result });
    } catch (err) {
      setDialog(null);
      toast.error(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={pick(lang, { uz: "Qurilmalar", ru: "Устройства", en: "Devices" })}
        description={pick(lang, {
          uz: "Soat va bilakuzuklar ombori: ro'yxatga olish, bemorga biriktirish, qaytarish va ulanish kodi.",
          ru: "Склад часов и браслетов: регистрация, выдача пациенту, возврат и код подключения.",
          en: "Watch and band inventory: register, assign to a patient, return and pair.",
        })}
        actions={
          <>
            <Button variant="outline" size="sm" onClick={() => void load()}>
              <RefreshCw />
              {t("sos.refresh", lang)}
            </Button>
            <Button size="sm" onClick={() => setDialog({ kind: "register" })}>
              <Plus />
              {pick(lang, { uz: "Qurilma qo'shish", ru: "Добавить устройство", en: "Add device" })}
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {(
          [
            ["all", pick(lang, { uz: "Jami", ru: "Всего", en: "Total" }), kpis.total, "text-foreground"],
            ["in_stock", statusMeta("in_stock", lang).label, kpis.stock, "text-primary"],
            ["assigned", statusMeta("assigned", lang).label, kpis.assigned, "text-good"],
            ["maintenance", statusMeta("maintenance", lang).label, kpis.maintenance, "text-attention"],
          ] as const
        ).map(([key, label, value, tone]) => (
          <button
            key={key}
            type="button"
            onClick={() => setStatus(key)}
            className={cn("bg-card hover:border-primary/40 rounded-xl border p-4 text-left transition-colors", status === key && "border-primary ring-primary/20 ring-2")}
          >
            <p className="text-muted-foreground text-xs font-medium">{label}</p>
            <p className={cn("font-display tabular mt-1 text-2xl font-bold", tone)}>{loaded ? value : "–"}</p>
          </button>
        ))}
      </div>

      <Card className="py-4">
        <CardContent className="flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
            <Search className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={pick(lang, { uz: "Seriya raqami yoki model", ru: "Серийный номер или модель", en: "Serial number or model" })}
              className="pl-9"
            />
          </div>
          <Select value={tier} onValueChange={setTier}>
            <SelectTrigger className="sm:w-56">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{pick(lang, { uz: "Barcha toifalar", ru: "Все классы", en: "All tiers" })}</SelectItem>
              {TIERS.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="sm:w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{pick(lang, { uz: "Barcha holatlar", ru: "Все статусы", en: "All statuses" })}</SelectItem>
              {["in_stock", "assigned", "maintenance", "retired", "lost"].map((s) => (
                <SelectItem key={s} value={s}>
                  {statusMeta(s, lang).label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {error && !devices.length ? (
        <ErrorState title={t("error.server_connection", lang)} description={error} onRetry={() => void load()} retryLabel={t("error.retry", lang)} />
      ) : !loaded ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-44 rounded-xl" />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <EmptyState icon={Watch} title={pick(lang, { uz: "Qurilmalar topilmadi", ru: "Устройства не найдены", en: "No devices found" })} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {visible.map((device) => {
            const meta = statusMeta(device.status, lang);
            const battery = device.battery_health_pct;
            const assigned = device.status === "assigned" || device.status === "active";
            return (
              <Card key={device.id} className="gap-4">
                <CardContent className="space-y-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="bg-accent text-accent-foreground flex size-10 shrink-0 items-center justify-center rounded-lg">
                        <Watch className="size-5" />
                      </span>
                      <div className="min-w-0">
                        <p className="font-display truncate font-semibold">{device.model_name}</p>
                        <p className="text-muted-foreground tabular truncate text-xs">{device.serial_number}</p>
                      </div>
                    </div>
                    <Badge variant={meta.variant}>{meta.label}</Badge>
                  </div>
                  <dl className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <dt className="text-muted-foreground">{pick(lang, { uz: "Toifa", ru: "Класс", en: "Tier" })}</dt>
                      <dd className="font-medium">{TIERS.find((o) => o.value === device.tier)?.label ?? "—"}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">{pick(lang, { uz: "Batareya holati", ru: "Здоровье батареи", en: "Battery health" })}</dt>
                      <dd className={cn("tabular flex items-center gap-1 font-medium", battery !== null && battery < 80 && "text-risk")}>
                        <Battery className="size-3.5" />
                        {battery !== null ? `${battery}%` : "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">{pick(lang, { uz: "Oxirgi sinxron", ru: "Последняя синхр.", en: "Last sync" })}</dt>
                      <dd className="font-medium">{device.last_sync_at ? formatAgo(device.last_sync_at, lang, now) : "—"}</dd>
                    </div>
                    {device.patient_name && (
                      <div>
                        <dt className="text-muted-foreground">{pick(lang, { uz: "Bemor", ru: "Пациент", en: "Patient" })}</dt>
                        <dd className="truncate font-medium">{device.patient_name}</dd>
                      </div>
                    )}
                  </dl>
                  <div className="flex flex-wrap gap-2">
                    {device.status === "in_stock" && (
                      <Button size="sm" onClick={() => setDialog({ kind: "assign", device })}>
                        <Link2 />
                        {pick(lang, { uz: "Biriktirish", ru: "Выдать", en: "Assign" })}
                      </Button>
                    )}
                    {assigned && (
                      <Button size="sm" variant="outline" onClick={() => setDialog({ kind: "return", device })}>
                        <RotateCcw />
                        {pick(lang, { uz: "Qaytarish", ru: "Возврат", en: "Return" })}
                      </Button>
                    )}
                    {(assigned || device.status === "in_stock") && (
                      <Button size="sm" variant="ghost" onClick={() => void enroll(device)}>
                        <KeyRound />
                        {pick(lang, { uz: "Ulanish kodi", ru: "Код подключения", en: "Pairing code" })}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {dialog?.kind === "register" && (
        <RegisterDialog
          lang={lang}
          busy={busy}
          onClose={() => setDialog(null)}
          onSubmit={(payload) =>
            void act(() => registerDevice(payload, isDemo), pick(lang, { uz: "Qurilma qo'shildi", ru: "Устройство добавлено", en: "Device added" }))
          }
        />
      )}
      {dialog?.kind === "assign" && (
        <AssignDialog
          lang={lang}
          busy={busy}
          device={dialog.device}
          patients={patients.map((p) => ({ id: p.id, name: p.full_name }))}
          onClose={() => setDialog(null)}
          onSubmit={(payload) =>
            void act(() => assignDevice(dialog.device.id, payload, isDemo), pick(lang, { uz: "Qurilma biriktirildi", ru: "Устройство выдано", en: "Device assigned" }))
          }
        />
      )}
      {dialog?.kind === "return" && (
        <ReturnDialog
          lang={lang}
          busy={busy}
          device={dialog.device}
          onClose={() => setDialog(null)}
          onSubmit={(payload) =>
            void act(() => returnDevice(dialog.device.id, payload, isDemo), pick(lang, { uz: "Qurilma qaytarildi", ru: "Устройство возвращено", en: "Device returned" }))
          }
        />
      )}
      {dialog?.kind === "enroll" && (
        <Dialog open onOpenChange={(open) => !open && setDialog(null)}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>{pick(lang, { uz: "Ulanish kodi", ru: "Код подключения", en: "Pairing code" })}</DialogTitle>
              <DialogDescription>
                {pick(lang, {
                  uz: "Kodni soatdagi WMAX ilovasiga kiriting. Kod bir marta ishlatiladi.",
                  ru: "Введите код в приложении WMAX на часах. Код одноразовый.",
                  en: "Enter this code in the WMAX app on the watch. It works once.",
                })}
              </DialogDescription>
            </DialogHeader>
            {dialog.result ? (
              <div className="space-y-2 py-2 text-center">
                <p className="font-display tabular text-4xl font-bold tracking-[0.3em]">{dialog.result.code}</p>
                <p className="text-muted-foreground text-sm">
                  {(() => {
                    const left = msUntil(dialog.result.expires_at, now);
                    return left !== null && left > 0
                      ? `${pick(lang, { uz: "Amal qiladi", ru: "Действует", en: "Valid for" })}: ${formatCountdown(left, lang)}`
                      : pick(lang, { uz: "Kod muddati tugadi", ru: "Срок кода истёк", en: "Code expired" });
                  })()}
                </p>
              </div>
            ) : (
              <div className="flex justify-center py-6">
                <Loader2 className="text-muted-foreground size-6 animate-spin" />
              </div>
            )}
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function RegisterDialog({
  lang,
  busy,
  onClose,
  onSubmit,
}: {
  lang: Lang;
  busy: boolean;
  onClose: () => void;
  onSubmit: (payload: { serial_number: string; model_name: string; tier: DeviceTier; ownership: string; battery_health_pct: number }) => void;
}) {
  const [serial, setSerial] = useState("");
  const [model, setModel] = useState("");
  const [tier, setTier] = useState<DeviceTier>("tier1_wearos");
  const [ownership, setOwnership] = useState("owned");
  const [battery, setBattery] = useState("100");
  const batteryNum = Math.round(Number(battery));
  const valid = serial.trim() && model.trim() && Number.isFinite(batteryNum) && batteryNum >= 0 && batteryNum <= 100;

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{pick(lang, { uz: "Yangi qurilma", ru: "Новое устройство", en: "New device" })}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="dev-serial">{pick(lang, { uz: "Seriya raqami", ru: "Серийный номер", en: "Serial number" })}</Label>
            <Input id="dev-serial" value={serial} onChange={(e) => setSerial(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="dev-model">{pick(lang, { uz: "Model", ru: "Модель", en: "Model" })}</Label>
            <Input id="dev-model" value={model} onChange={(e) => setModel(e.target.value)} placeholder="Galaxy Watch 5" />
          </div>
          <div className="space-y-2">
            <Label>{pick(lang, { uz: "Toifa", ru: "Класс", en: "Tier" })}</Label>
            <Select value={tier} onValueChange={(v) => setTier(v as DeviceTier)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIERS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{pick(lang, { uz: "Egalik", ru: "Владение", en: "Ownership" })}</Label>
            <Select value={ownership} onValueChange={setOwnership}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="owned">{pick(lang, { uz: "Klinika mulki", ru: "Собственность клиники", en: "Clinic-owned" })}</SelectItem>
                <SelectItem value="leased">{pick(lang, { uz: "Ijara", ru: "Аренда", en: "Leased" })}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="dev-battery">{pick(lang, { uz: "Batareya holati, %", ru: "Здоровье батареи, %", en: "Battery health, %" })}</Label>
            <Input id="dev-battery" type="number" min={0} max={100} value={battery} onChange={(e) => setBattery(e.target.value)} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t("confirm_modal.cancel", lang)}
          </Button>
          <Button
            disabled={!valid || busy}
            onClick={() => onSubmit({ serial_number: serial.trim(), model_name: model.trim(), tier, ownership, battery_health_pct: batteryNum })}
          >
            {busy && <Loader2 className="animate-spin" />}
            {pick(lang, { uz: "Saqlash", ru: "Сохранить", en: "Save" })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AssignDialog({
  lang,
  busy,
  device,
  patients,
  onClose,
  onSubmit,
}: {
  lang: Lang;
  busy: boolean;
  device: DeviceItem;
  patients: { id: string; name: string }[];
  onClose: () => void;
  onSubmit: (payload: { patient_id: string; deposit_uzs: number; rental_uzs_month: number; patient_name?: string }) => void;
}) {
  const [patientId, setPatientId] = useState("");
  const [deposit, setDeposit] = useState("500000");
  const [rental, setRental] = useState("180000");
  const depositNum = Math.round(Number(deposit));
  const rentalNum = Math.round(Number(rental));
  const valid = patientId && Number.isFinite(depositNum) && depositNum >= 0 && Number.isFinite(rentalNum) && rentalNum >= 0;

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{pick(lang, { uz: "Bemorga biriktirish", ru: "Выдать пациенту", en: "Assign to patient" })}</DialogTitle>
          <DialogDescription>
            {device.model_name} · {device.serial_number}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>{pick(lang, { uz: "Bemor", ru: "Пациент", en: "Patient" })}</Label>
            <Select value={patientId} onValueChange={setPatientId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={pick(lang, { uz: "Bemorni tanlang", ru: "Выберите пациента", en: "Choose a patient" })} />
              </SelectTrigger>
              <SelectContent>
                {patients.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="dev-deposit">{pick(lang, { uz: "Garov, so'm", ru: "Залог, сум", en: "Deposit, UZS" })}</Label>
              <Input id="dev-deposit" type="number" min={0} value={deposit} onChange={(e) => setDeposit(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dev-rental">{pick(lang, { uz: "Oylik ijara, so'm", ru: "Аренда в месяц, сум", en: "Monthly rental, UZS" })}</Label>
              <Input id="dev-rental" type="number" min={0} value={rental} onChange={(e) => setRental(e.target.value)} />
            </div>
          </div>
          {valid && (
            <p className="text-muted-foreground text-xs">
              {formatUzs(depositNum)} + {formatUzs(rentalNum)} / {pick(lang, { uz: "oy", ru: "мес", en: "mo" })}
            </p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t("confirm_modal.cancel", lang)}
          </Button>
          <Button
            disabled={!valid || busy}
            onClick={() =>
              onSubmit({
                patient_id: patientId,
                deposit_uzs: depositNum,
                rental_uzs_month: rentalNum,
                patient_name: patients.find((p) => p.id === patientId)?.name,
              })
            }
          >
            {busy && <Loader2 className="animate-spin" />}
            {pick(lang, { uz: "Biriktirish", ru: "Выдать", en: "Assign" })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ReturnDialog({
  lang,
  busy,
  device,
  onClose,
  onSubmit,
}: {
  lang: Lang;
  busy: boolean;
  device: DeviceItem;
  onClose: () => void;
  onSubmit: (payload: { battery_health_pct: number | null; return_notes: string | null; refund_deposit: boolean }) => void;
}) {
  const [battery, setBattery] = useState(device.battery_health_pct !== null ? String(device.battery_health_pct) : "");
  const [notes, setNotes] = useState("");
  const [refund, setRefund] = useState(false);
  const batteryNum = battery.trim() === "" ? null : Math.round(Number(battery));
  const valid = batteryNum === null || (Number.isFinite(batteryNum) && batteryNum >= 0 && batteryNum <= 100);

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{pick(lang, { uz: "Qurilmani qaytarish", ru: "Возврат устройства", en: "Return device" })}</DialogTitle>
          <DialogDescription>
            {device.model_name} · {device.serial_number}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ret-battery">{pick(lang, { uz: "Batareya holati, %", ru: "Здоровье батареи, %", en: "Battery health, %" })}</Label>
            <Input id="ret-battery" type="number" min={0} max={100} value={battery} onChange={(e) => setBattery(e.target.value)} />
          </div>
          {batteryNum !== null && batteryNum < 80 && (
            <Alert variant="attention">
              <AlertDescription>
                {pick(lang, {
                  uz: "Batareya 80% dan past: qurilma yaroqsiz deb belgilanishi mumkin.",
                  ru: "Батарея ниже 80%: устройство может быть списано.",
                  en: "Battery below 80%: the device may be retired.",
                })}
              </AlertDescription>
            </Alert>
          )}
          <div className="space-y-2">
            <Label htmlFor="ret-notes">{pick(lang, { uz: "Izoh", ru: "Комментарий", en: "Notes" })}</Label>
            <Textarea id="ret-notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <Checkbox checked={refund} onCheckedChange={(v) => setRefund(v === true)} />
            {pick(lang, { uz: "Garovni qaytarish", ru: "Вернуть залог", en: "Refund deposit" })}
          </label>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t("confirm_modal.cancel", lang)}
          </Button>
          <Button
            disabled={!valid || busy}
            onClick={() => onSubmit({ battery_health_pct: batteryNum, return_notes: notes.trim() || null, refund_deposit: refund })}
          >
            {busy && <Loader2 className="animate-spin" />}
            {pick(lang, { uz: "Qaytarish", ru: "Возврат", en: "Return" })}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api/api_service.dart';
import '../models/health_summary.dart';
import '../models/models.dart';

typedef HealthSummaryLoader =
    Future<HealthSummaryData> Function(PatientSummary patient, int days);

const _ink = Color(0xFF0F172A);
const _muted = Color(0xFF64748B);
const _line = Color(0xFFE2E8F0);
const _primary = Color(0xFF0284C7);
const _heart = Color(0xFFE11D48);
const _hrv = Color(0xFF7C3AED);
const _oxygen = Color(0xFF0EA5E9);
const _stress = Color(0xFFF59E0B);
const _breath = Color(0xFF14B8A6);
const _temp = Color(0xFFF97316);
const _sleep = Color(0xFF4F46E5);
const _steps = Color(0xFF16A34A);

/// Measured watch data for the selected patient: vitals, activity, sleep,
/// an HRV-based stress estimate and day-by-day trends.
class HealthScreen extends StatefulWidget {
  final bool isUzbek;
  final PatientSummary? patient;
  final HealthSummaryLoader? loader;

  const HealthScreen({
    super.key,
    required this.isUzbek,
    required this.patient,
    this.loader,
  });

  @override
  State<HealthScreen> createState() => _HealthScreenState();
}

class _HealthScreenState extends State<HealthScreen> {
  int _days = 7;
  HealthSummaryData? _data;
  bool _loading = false;
  bool _failed = false;
  int _request = 0;

  bool get uz => widget.isUzbek;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant HealthScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.patient?.id != widget.patient?.id) {
      setState(() => _data = null);
      _load();
    }
  }

  Future<void> _load() async {
    final patient = widget.patient;
    if (patient == null) return;
    final request = ++_request;
    setState(() {
      _loading = true;
      _failed = false;
    });
    try {
      final loader =
          widget.loader ??
          (p, days) => ApiService.fetchHealthSummary(patient: p, days: days);
      final data = await loader(patient, _days);
      if (!mounted || request != _request) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (_) {
      if (!mounted || request != _request) return;
      setState(() {
        _failed = true;
        _loading = false;
      });
    }
  }

  void _setDays(int days) {
    if (days == _days) return;
    setState(() => _days = days);
    _load();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.patient == null) {
      return _centerMessage(
        Icons.person_off_rounded,
        uz ? 'Bemor tanlanmagan' : 'Пациент не выбран',
      );
    }
    final data = _data;
    if (data == null) {
      if (_failed) {
        return _centerMessage(
          Icons.cloud_off_rounded,
          uz
              ? "Server bilan aloqa yo'q. Ko'rsatkichlar yuklanmadi."
              : 'Нет связи с сервером. Показатели не загружены.',
          action: TextButton(
            onPressed: _load,
            child: Text(uz ? 'Qayta urinish' : 'Повторить'),
          ),
        );
      }
      return const Center(
        child: CircularProgressIndicator(strokeWidth: 2.5, color: _primary),
      );
    }

    return RefreshIndicator(
      color: _primary,
      onRefresh: _load,
      child: ListView(
        key: const Key('health-screen-list'),
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 110),
        children: [
          _header(data),
          if (_failed) _connectionWarning(),
          for (final insight in data.insights) _insightCard(insight),
          const SizedBox(height: 4),
          _activityCard(data),
          const SizedBox(height: 12),
          _vitalsGrid(data),
          const SizedBox(height: 12),
          _sleepCard(data),
          const SizedBox(height: 12),
          _measurementsCard(data),
          if (data.exercises.isNotEmpty) ...[
            const SizedBox(height: 12),
            _exerciseCard(data),
          ],
          const SizedBox(height: 16),
          _disclaimer(data),
        ],
      ),
    );
  }

  Widget _centerMessage(IconData icon, String text, {Widget? action}) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: _muted),
            const SizedBox(height: 12),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(color: _muted, fontSize: 14),
            ),
            ?action,
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Header, freshness and insights
  // ---------------------------------------------------------------------------

  Widget _header(HealthSummaryData data) {
    final (label, color, icon) = switch (data.freshness) {
      'fresh' => (
        uz
            ? 'Yangilandi ${_ago(data.lastSampleAt!)}'
            : 'Обновлено ${_ago(data.lastSampleAt!)}',
        _steps,
        Icons.check_circle_rounded,
      ),
      'stale' => (
        uz
            ? "Oxirgi ma'lumot ${_ago(data.lastSampleAt!)}"
            : 'Последние данные ${_ago(data.lastSampleAt!)}',
        _stress,
        Icons.schedule_rounded,
      ),
      _ => (
        uz ? "Soatdan ma'lumot yo'q" : 'Нет данных с часов',
        _muted,
        Icons.watch_off_rounded,
      ),
    };
    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 10),
      child: Row(
        children: [
          Expanded(
            child: Row(
              children: [
                Icon(icon, size: 16, color: color),
                const SizedBox(width: 6),
                Flexible(
                  child: Text(
                    label,
                    key: const Key('health-freshness'),
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.w700,
                      fontSize: 12.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.only(right: 8),
              child: SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: _primary,
                ),
              ),
            ),
          SegmentedButton<int>(
            showSelectedIcon: false,
            style: SegmentedButton.styleFrom(
              visualDensity: VisualDensity.compact,
              selectedBackgroundColor: _primary,
              selectedForegroundColor: Colors.white,
              textStyle: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
            segments: [
              ButtonSegment(value: 7, label: Text(uz ? '7 kun' : '7 дн')),
              ButtonSegment(value: 30, label: Text(uz ? '30 kun' : '30 дн')),
            ],
            selected: {_days},
            onSelectionChanged: (value) => _setDays(value.first),
          ),
        ],
      ),
    );
  }

  Widget _connectionWarning() {
    return _banner(
      Icons.cloud_off_rounded,
      _stress,
      uz
          ? "Yangilab bo'lmadi. Oxirgi yuklangan ma'lumot ko'rsatilmoqda."
          : 'Не удалось обновить. Показаны последние загруженные данные.',
    );
  }

  Widget _insightCard(HealthInsight insight) {
    final color = switch (insight.severity) {
      'attention' => _heart,
      'positive' => _steps,
      _ => _primary,
    };
    final icon = switch (insight.severity) {
      'attention' => Icons.error_outline_rounded,
      'positive' => Icons.emoji_events_rounded,
      _ => Icons.info_outline_rounded,
    };
    return _banner(icon, color, _insightText(insight));
  }

  Widget _banner(IconData icon, Color color, String text) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: _ink, fontSize: 13, height: 1.35),
            ),
          ),
        ],
      ),
    );
  }

  String _insightText(HealthInsight insight) {
    final p = insight.params;
    String n(Object? v) =>
        v is num ? (v % 1 == 0 ? v.toInt().toString() : v.toString()) : '—';
    switch (insight.key) {
      case 'data_stale':
        return uz
            ? "Soatdan yangi ma'lumot kelmayapti. Soat taqilganini va telefon bilan ulanganini tekshiring."
            : 'С часов не поступают новые данные. Проверьте, надеты ли часы и есть ли связь с телефоном.';
      case 'spo2_low_today':
        return uz
            ? "Bugun SpO₂ ${n(p['count'])} marta 90% dan past bo'ldi (eng pasti ${n(p['min'])}%)."
            : 'Сегодня SpO₂ ${n(p['count'])} раз было ниже 90% (минимум ${n(p['min'])}%).';
      case 'resting_hr_above_baseline':
        return uz
            ? 'Tinch holatdagi puls ${n(p['value'])} — odatdagidan (${n(p['baseline'])}) yuqori.'
            : 'Пульс в покое ${n(p['value'])} — выше обычного (${n(p['baseline'])}).';
      case 'hrv_below_baseline':
        return uz
            ? "HRV bugun ${n(p['value'])} ms — shaxsiy me'yordan (${n(p['baseline'])} ms) past."
            : 'ВСР сегодня ${n(p['value'])} мс — ниже личной нормы (${n(p['baseline'])} мс).';
      case 'skin_temp_above_baseline':
        return uz
            ? "Teri harorati shaxsiy me'yordan +${n(p['delta'])}°C yuqori."
            : 'Температура кожи выше личной нормы на +${n(p['delta'])}°C.';
      case 'short_sleep':
        final minutes = (p['minutes'] as num?)?.toInt() ?? 0;
        return uz
            ? "Kechagi uyqu ${_duration(minutes)} — 6 soatdan kam."
            : 'Сон прошлой ночью ${_duration(minutes)} — меньше 6 часов.';
      case 'steps_goal_met':
        return uz
            ? 'Kunlik qadam maqsadi bajarildi: ${n(p['steps'])} qadam.'
            : 'Дневная цель по шагам выполнена: ${n(p['steps'])}.';
      case 'fall_detected':
        return uz
            ? 'Soat ${n(p['count'])} marta yiqilishni qayd etdi. Bemor holatini tekshiring.'
            : 'Часы зафиксировали падение (${n(p['count'])}). Проверьте состояние пациента.';
      default:
        return insight.key;
    }
  }

  // ---------------------------------------------------------------------------
  // Activity
  // ---------------------------------------------------------------------------

  Widget _activityCard(HealthSummaryData data) {
    final today = data.today;
    final steps = today?.steps;
    final progress = steps == null
        ? 0.0
        : (steps / data.goalSteps).clamp(0.0, 1.0);
    return _card(
      onTap: () => _openTrend(
        title: uz ? 'Qadamlar' : 'Шаги',
        color: _steps,
        unit: uz ? 'qadam' : 'шагов',
        days: data.activityDaily.map((d) => d.day).toList(),
        values: data.activityDaily.map((d) => d.steps).toList(),
        goal: data.goalSteps.toDouble(),
        decimals: 0,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 104,
            height: 104,
            child: CustomPaint(
              painter: _RingPainter(progress: progress, color: _steps),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.directions_walk_rounded,
                      color: _steps,
                      size: 20,
                    ),
                    Text(
                      steps == null ? '—' : _thousands(steps),
                      key: const Key('health-steps-today'),
                      style: const TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 18,
                        color: _ink,
                      ),
                    ),
                    Text(
                      '/ ${_thousands(data.goalSteps.toDouble())}',
                      style: const TextStyle(fontSize: 11, color: _muted),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  uz ? 'Bugungi faollik' : 'Активность сегодня',
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    color: _ink,
                  ),
                ),
                const SizedBox(height: 10),
                _miniStat(
                  Icons.route_rounded,
                  uz ? 'Masofa' : 'Дистанция',
                  today?.distanceM == null
                      ? null
                      : '${(today!.distanceM! / 1000).toStringAsFixed(2)} km',
                ),
                _miniStat(
                  Icons.local_fire_department_rounded,
                  uz ? 'Faol kaloriya' : 'Активные ккал',
                  _fmt(today?.activeKcal ?? today?.totalKcal, 0, 'kcal'),
                ),
                _miniStat(
                  Icons.stairs_rounded,
                  uz ? 'Qavatlar' : 'Этажи',
                  _fmt(today?.floors, 0, ''),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _miniStat(IconData icon, String label, String? value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Icon(icon, size: 15, color: _muted),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontSize: 12.5, color: _muted),
            ),
          ),
          Text(
            value ?? '—',
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: _ink,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Vitals
  // ---------------------------------------------------------------------------

  Widget _vitalsGrid(HealthSummaryData data) {
    final hr = data.metric('heart_rate_bpm');
    final resting = data.metric('resting_heart_rate_bpm');
    final hrv = data.metric('heart_rate_variability_rmssd_ms');
    final spo2 = data.metric('oxygen_saturation_pct');
    final rr = data.metric('respiratory_rate_bpm');
    final skinDelta = data.metric('skin_temperature_delta_c');
    final skinAbs = data.metric('skin_temperature_c');
    final skin = skinDelta.hasData ? skinDelta : skinAbs;

    final hrToday = hr.today;
    final hrSub = hrToday?.min != null
        ? (uz
              ? 'Bugun ${hrToday!.min!.round()}–${hrToday.max!.round()}'
              : 'Сегодня ${hrToday!.min!.round()}–${hrToday.max!.round()}')
        : null;
    final restingSub = resting.latest != null
        ? (uz
              ? 'Tinch: ${resting.latest!.value.round()}'
              : 'Покой: ${resting.latest!.value.round()}')
        : null;

    final tiles = <Widget>[
      _vitalTile(
        key: 'hr',
        icon: Icons.favorite_rounded,
        color: _heart,
        label: uz ? 'Yurak urishi' : 'Пульс',
        summary: hr,
        unit: 'bpm',
        decimals: 0,
        sub: [hrSub, restingSub].whereType<String>().join(' · '),
      ),
      _vitalTile(
        key: 'hrv',
        icon: Icons.insights_rounded,
        color: _hrv,
        label: uz ? 'HRV (RMSSD)' : 'ВСР (RMSSD)',
        summary: hrv,
        unit: 'ms',
        decimals: 0,
        sub: data.stress.baselineHrvMs == null
            ? null
            : (uz
                  ? "Me'yor ${data.stress.baselineHrvMs!.round()} ms"
                  : 'Норма ${data.stress.baselineHrvMs!.round()} мс'),
      ),
      _vitalTile(
        key: 'spo2',
        icon: Icons.water_drop_rounded,
        color: _oxygen,
        label: uz ? 'Qondagi kislorod' : 'Кислород (SpO₂)',
        summary: spo2,
        unit: '%',
        decimals: 0,
        sub: spo2.today?.min == null
            ? null
            : (uz
                  ? 'Bugun min ${spo2.today!.min!.round()}%'
                  : 'Сегодня мин ${spo2.today!.min!.round()}%'),
      ),
      _stressTile(data.stress),
      _vitalTile(
        key: 'rr',
        icon: Icons.air_rounded,
        color: _breath,
        label: uz ? 'Nafas tezligi' : 'Частота дыхания',
        summary: rr,
        unit: uz ? '/daq' : '/мин',
        decimals: 1,
      ),
      _vitalTile(
        key: 'skin',
        icon: Icons.thermostat_rounded,
        color: _temp,
        label: uz ? 'Teri harorati' : 'Температура кожи',
        summary: skin,
        unit: '°C',
        decimals: 1,
        signed: identical(skin, skinDelta),
        sub: identical(skin, skinDelta)
            ? (uz ? "Shaxsiy me'yordan farq" : 'Отклонение от нормы')
            : null,
      ),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 520 ? 3 : 2;
        const gap = 10.0;
        final width = (constraints.maxWidth - gap * (columns - 1)) / columns;
        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: [
            for (final tile in tiles) SizedBox(width: width, child: tile),
          ],
        );
      },
    );
  }

  Widget _vitalTile({
    required String key,
    required IconData icon,
    required Color color,
    required String label,
    required VitalSummary summary,
    required String unit,
    required int decimals,
    String? sub,
    bool signed = false,
  }) {
    final latest = summary.latest;
    final valueText = latest == null
        ? '—'
        : '${signed && latest.value > 0 ? '+' : ''}${latest.value.toStringAsFixed(decimals)}';
    return _card(
      key: Key('vital-$key'),
      padding: const EdgeInsets.all(12),
      onTap: () => _openTrend(
        title: label,
        color: color,
        unit: unit,
        days: summary.daily.map((d) => d.day).toList(),
        values: summary.daily.map((d) => d.avg).toList(),
        mins: summary.daily.map((d) => d.min).toList(),
        maxs: summary.daily.map((d) => d.max).toList(),
        decimals: decimals,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 18),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  label,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    color: _muted,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                valueText,
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  color: latest == null ? _muted : _ink,
                ),
              ),
              const SizedBox(width: 4),
              if (latest != null)
                Text(unit, style: const TextStyle(fontSize: 12, color: _muted)),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            latest == null
                ? (uz ? "O'lchov yo'q" : 'Нет измерений')
                : (sub == null || sub.isEmpty ? _ago(latest.at) : sub),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 11, color: _muted),
          ),
          const SizedBox(height: 6),
          SizedBox(
            height: 26,
            child: CustomPaint(
              size: Size.infinite,
              painter: _SparkPainter(
                values: summary.daily.map((d) => d.avg).toList(),
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _stressTile(StressSummary stress) {
    final score = stress.latestScore;
    final levelText = switch (stress.latestLevel) {
      'low' => uz ? 'Past' : 'Низкий',
      'medium' => uz ? "O'rtacha" : 'Средний',
      'high' => uz ? 'Yuqori' : 'Высокий',
      _ => null,
    };
    final note = switch (stress.status) {
      'ok' => levelText ?? '',
      'no_recent_hrv' => uz ? "Bugun HRV o'lchanmagan" : 'Сегодня нет ВСР',
      _ =>
        uz
            ? "Me'yor uchun kamida 3 kun HRV kerak"
            : 'Для нормы нужно 3 дня ВСР',
    };
    return _card(
      key: const Key('vital-stress'),
      padding: const EdgeInsets.all(12),
      onTap: () => _openTrend(
        title: uz ? 'Stress (taxminiy)' : 'Стресс (оценка)',
        color: _stress,
        unit: '/100',
        days: stress.daily.map((d) => d.day).toList(),
        values: stress.daily.map((d) => d.score?.toDouble()).toList(),
        decimals: 0,
        maxValue: 100,
        footnote: uz
            ? "Stress shaxsiy HRV me'yoriga nisbatan hisoblanadi. Bu tibbiy o'lchov emas."
            : 'Стресс рассчитан относительно личной нормы ВСР. Это не медицинское измерение.',
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.spa_rounded, color: _stress, size: 18),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  uz ? 'Stress (taxminiy)' : 'Стресс (оценка)',
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    color: _muted,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                score?.toString() ?? '—',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  color: score == null ? _muted : _ink,
                ),
              ),
              if (score != null) ...[
                const SizedBox(width: 4),
                const Text(
                  '/100',
                  style: TextStyle(fontSize: 12, color: _muted),
                ),
              ],
            ],
          ),
          const SizedBox(height: 4),
          Text(
            note,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 11, color: _muted),
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: SizedBox(
              height: 8,
              child: Stack(
                children: [
                  Row(
                    children: const [
                      Expanded(
                        flex: 40,
                        child: ColoredBox(color: Color(0xFFBBF7D0)),
                      ),
                      Expanded(
                        flex: 30,
                        child: ColoredBox(color: Color(0xFFFDE68A)),
                      ),
                      Expanded(
                        flex: 30,
                        child: ColoredBox(color: Color(0xFFFECACA)),
                      ),
                    ],
                  ),
                  if (score != null)
                    Align(
                      alignment: Alignment(score / 50 - 1, 0),
                      child: Container(width: 4, color: _ink),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Sleep
  // ---------------------------------------------------------------------------

  Widget _sleepCard(HealthSummaryData data) {
    final night = data.lastNight;
    final stages = night?.stages;
    final stageColors = <String, Color>{
      'deep': const Color(0xFF312E81),
      'light': const Color(0xFF818CF8),
      'rem': const Color(0xFF38BDF8),
      'awake': const Color(0xFFFDA4AF),
      'unspecified': const Color(0xFFC7D2FE),
    };
    final stageNames = <String, String>{
      'deep': uz ? 'Chuqur' : 'Глубокий',
      'light': uz ? 'Yengil' : 'Лёгкий',
      'rem': 'REM',
      'awake': uz ? 'Uyg‘oq' : 'Бодрствование',
      'unspecified': uz ? 'Aniqlanmagan' : 'Не определено',
    };
    final stageTotal = stages?.values.fold<int>(0, (a, b) => a + b) ?? 0;

    return _card(
      key: const Key('health-sleep'),
      onTap: () => _openTrend(
        title: uz ? 'Uyqu' : 'Сон',
        color: _sleep,
        unit: uz ? 'soat' : 'ч',
        days: data.sleepDaily.map((d) => d.day).toList(),
        values: data.sleepDaily
            .map((d) => d.asleepMinutes == null ? null : d.asleepMinutes! / 60)
            .toList(),
        decimals: 1,
        goal: 7,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.bedtime_rounded, color: _sleep, size: 20),
              const SizedBox(width: 8),
              Text(
                uz ? 'Uyqu' : 'Сон',
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 15,
                  color: _ink,
                ),
              ),
              const Spacer(),
              if (night != null)
                Text(
                  '${_clock(night.start)} – ${_clock(night.end)}',
                  style: const TextStyle(fontSize: 12, color: _muted),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (night == null)
            Text(
              uz
                  ? "Uyqu qayd etilmagan. Soatni tunda taqib yuring."
                  : 'Сон не зафиксирован. Носите часы ночью.',
              style: const TextStyle(fontSize: 13, color: _muted),
            )
          else ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      _duration(night.asleepMinutes),
                      key: const Key('health-sleep-duration'),
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        color: _ink,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                if (night.efficiencyPct != null)
                  Flexible(
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        uz
                            ? 'Samaradorlik ${night.efficiencyPct}%'
                            : 'Эффективность ${night.efficiencyPct}%',
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12, color: _muted),
                      ),
                    ),
                  ),
              ],
            ),
            if (stages != null && stageTotal > 0) ...[
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: SizedBox(
                  height: 14,
                  child: Row(
                    children: [
                      for (final entry in stages.entries)
                        if (entry.value > 0)
                          Expanded(
                            flex: entry.value,
                            child: ColoredBox(
                              color: stageColors[entry.key] ?? _line,
                            ),
                          ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 14,
                runSpacing: 6,
                children: [
                  for (final entry in stages.entries)
                    if (entry.value > 0)
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 9,
                            height: 9,
                            decoration: BoxDecoration(
                              color: stageColors[entry.key] ?? _line,
                              borderRadius: BorderRadius.circular(3),
                            ),
                          ),
                          const SizedBox(width: 5),
                          Flexible(
                            child: Text(
                              '${stageNames[entry.key] ?? entry.key} ${_duration(entry.value)} · ${(100 * entry.value / stageTotal).round()}%',
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 11.5,
                                color: _ink,
                              ),
                            ),
                          ),
                        ],
                      ),
                ],
              ),
            ],
          ],
          const SizedBox(height: 12),
          SizedBox(
            height: 46,
            child: CustomPaint(
              size: Size.infinite,
              painter: _BarsPainter(
                values: data.sleepDaily
                    .map((d) => d.asleepMinutes?.toDouble())
                    .toList(),
                color: _sleep,
                goal: 7 * 60,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Occasional measurements and exercise
  // ---------------------------------------------------------------------------

  Widget _measurementsCard(HealthSummaryData data) {
    final rows = <Widget>[];
    void add(
      IconData icon,
      String label,
      MetricPoint? point,
      String unit,
      int d,
    ) {
      if (point == null) return;
      rows.add(
        _measurementRow(
          icon,
          label,
          '${point.value.toStringAsFixed(d)} $unit',
          point.at,
        ),
      );
    }

    final bp = data.bloodPressure;
    if (bp != null) {
      rows.add(
        _measurementRow(
          Icons.bloodtype_rounded,
          uz ? 'Qon bosimi' : 'Давление',
          '${bp.systolic}/${bp.diastolic} mmHg',
          bp.at,
        ),
      );
    }
    final m = data.latestMeasurements;
    add(
      Icons.monitor_weight_rounded,
      uz ? 'Vazn' : 'Вес',
      m['weight_kg'],
      'kg',
      1,
    );
    add(
      Icons.percent_rounded,
      uz ? "Yog' ulushi" : 'Доля жира',
      m['body_fat_pct'],
      '%',
      1,
    );
    add(
      Icons.directions_run_rounded,
      'VO₂ max',
      m['vo2_max_ml_kg_min'],
      'ml/kg/min',
      1,
    );
    add(
      Icons.opacity_rounded,
      uz ? 'Qand' : 'Глюкоза',
      m['blood_glucose_mmol_l'],
      'mmol/L',
      1,
    );
    add(
      Icons.device_thermostat_rounded,
      uz ? 'Tana harorati' : 'Температура тела',
      m['body_temperature_c'],
      '°C',
      1,
    );

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            uz ? "Boshqa o'lchovlar" : 'Другие измерения',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              fontSize: 15,
              color: _ink,
            ),
          ),
          const SizedBox(height: 8),
          if (rows.isEmpty)
            Text(
              uz
                  ? "Qon bosimi, vazn va boshqa o'lchovlar Health Connect yoki Samsung Health'dan sinxronlanganda shu yerda chiqadi."
                  : 'Давление, вес и другие измерения появятся после синхронизации с Health Connect или Samsung Health.',
              style: const TextStyle(fontSize: 12.5, color: _muted),
            )
          else
            ...rows,
        ],
      ),
    );
  }

  Widget _measurementRow(
    IconData icon,
    String label,
    String value,
    DateTime at,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: _primary),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: const TextStyle(fontSize: 13, color: _ink)),
                Text(
                  _ago(at),
                  style: const TextStyle(fontSize: 11, color: _muted),
                ),
              ],
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              color: _ink,
            ),
          ),
        ],
      ),
    );
  }

  Widget _exerciseCard(HealthSummaryData data) {
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            uz ? 'Mashg‘ulotlar' : 'Тренировки',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              fontSize: 15,
              color: _ink,
            ),
          ),
          const SizedBox(height: 6),
          for (final item in data.exercises.take(5))
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 5),
              child: Row(
                children: [
                  const Icon(
                    Icons.fitness_center_rounded,
                    size: 18,
                    color: _steps,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _exerciseName(item.type),
                      style: const TextStyle(fontSize: 13, color: _ink),
                    ),
                  ),
                  Text(
                    '${_dayLabel(item.start)} · ${_duration(item.durationMinutes)}',
                    style: const TextStyle(fontSize: 12, color: _muted),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  String _exerciseName(String raw) {
    const uzNames = {
      'walking': 'Yurish',
      'running': 'Yugurish',
      'biking': 'Velosiped',
      'swimming_pool': 'Suzish',
      'yoga': 'Yoga',
      'strength_training': 'Kuch mashqi',
    };
    const ruNames = {
      'walking': 'Ходьба',
      'running': 'Бег',
      'biking': 'Велосипед',
      'swimming_pool': 'Плавание',
      'yoga': 'Йога',
      'strength_training': 'Силовая',
    };
    final key = raw.toLowerCase();
    final name = (uz ? uzNames : ruNames)[key];
    if (name != null) return name;
    final words = key.replaceAll('_', ' ');
    return words.isEmpty ? raw : words[0].toUpperCase() + words.substring(1);
  }

  Widget _disclaimer(HealthSummaryData data) {
    final excluded = data.excludedSamples > 0
        ? (uz
              ? " Sifati past ${data.excludedSamples} ta o'lchov hisobga olinmadi."
              : ' Не учтено измерений низкого качества: ${data.excludedSamples}.')
        : '';
    return Text(
      (uz
              ? "Ko'rsatkichlar soat va Health Connect o'lchovlari. Ular tibbiy tashxis emas; stress — HRV asosidagi taxminiy baho."
              : 'Показатели — измерения часов и Health Connect. Это не медицинский диагноз; стресс — оценка по ВСР.') +
          excluded,
      textAlign: TextAlign.center,
      style: const TextStyle(fontSize: 11, color: _muted, height: 1.4),
    );
  }

  // ---------------------------------------------------------------------------
  // Trend sheet
  // ---------------------------------------------------------------------------

  void _openTrend({
    required String title,
    required Color color,
    required String unit,
    required List<DateTime> days,
    required List<double?> values,
    List<double?>? mins,
    List<double?>? maxs,
    double? goal,
    double? maxValue,
    int decimals = 0,
    String? footnote,
  }) {
    final present = values.whereType<double>().toList();
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: _line,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 14),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w900,
                  fontSize: 18,
                  color: _ink,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                present.isEmpty
                    ? (uz
                          ? "Bu davrda o'lchov yo'q"
                          : 'За период нет измерений')
                    : (uz
                          ? "$_days kunlik o'rtacha: ${(present.reduce((a, b) => a + b) / present.length).toStringAsFixed(decimals)} $unit"
                          : 'Среднее за $_days дн: ${(present.reduce((a, b) => a + b) / present.length).toStringAsFixed(decimals)} $unit'),
                style: const TextStyle(fontSize: 13, color: _muted),
              ),
              const SizedBox(height: 16),
              SizedBox(
                height: 180,
                child: CustomPaint(
                  size: Size.infinite,
                  painter: _BarsPainter(
                    values: values,
                    mins: mins,
                    maxs: maxs,
                    color: color,
                    goal: goal,
                    maxValue: maxValue,
                    showAxis: true,
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (days.isNotEmpty)
                    Text(
                      _dayLabel(days.first),
                      style: const TextStyle(fontSize: 11, color: _muted),
                    ),
                  if (days.isNotEmpty)
                    Text(
                      uz ? 'Bugun' : 'Сегодня',
                      style: const TextStyle(fontSize: 11, color: _muted),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              ConstrainedBox(
                constraints: const BoxConstraints(maxHeight: 220),
                child: ListView(
                  shrinkWrap: true,
                  children: [
                    for (var i = days.length - 1; i >= 0; i--)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 5),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                _dayLabel(days[i]),
                                style: const TextStyle(
                                  fontSize: 13,
                                  color: _ink,
                                ),
                              ),
                            ),
                            if (mins != null && maxs != null && mins[i] != null)
                              Padding(
                                padding: const EdgeInsets.only(right: 12),
                                child: Text(
                                  '${mins[i]!.toStringAsFixed(decimals)}–${maxs[i]!.toStringAsFixed(decimals)}',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: _muted,
                                  ),
                                ),
                              ),
                            Text(
                              values[i] == null
                                  ? '—'
                                  : '${values[i]!.toStringAsFixed(decimals)} $unit',
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: _ink,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
              if (footnote != null) ...[
                const SizedBox(height: 10),
                Text(
                  footnote,
                  style: const TextStyle(fontSize: 11.5, color: _muted),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  Widget _card({
    Key? key,
    required Widget child,
    VoidCallback? onTap,
    EdgeInsets padding = const EdgeInsets.all(16),
  }) {
    return Material(
      key: key,
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: _line),
          ),
          child: child,
        ),
      ),
    );
  }

  String? _fmt(double? value, int decimals, String unit) {
    if (value == null) return null;
    final text = value.toStringAsFixed(decimals);
    return unit.isEmpty ? text : '$text $unit';
  }

  String _thousands(double value) {
    final digits = value.round().toString();
    final buffer = StringBuffer();
    for (var i = 0; i < digits.length; i++) {
      if (i > 0 && (digits.length - i) % 3 == 0) buffer.write(' ');
      buffer.write(digits[i]);
    }
    return buffer.toString();
  }

  String _duration(int minutes) {
    final h = minutes ~/ 60;
    final m = minutes % 60;
    if (h == 0) return uz ? '$m daq' : '$m мин';
    return uz ? '$h soat $m daq' : '$h ч $m мин';
  }

  String _clock(DateTime time) =>
      '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';

  String _dayLabel(DateTime day) {
    const uzMonths = [
      'yan',
      'fev',
      'mar',
      'apr',
      'may',
      'iyn',
      'iyl',
      'avg',
      'sen',
      'okt',
      'noy',
      'dek',
    ];
    const ruMonths = [
      'янв',
      'фев',
      'мар',
      'апр',
      'мая',
      'июн',
      'июл',
      'авг',
      'сен',
      'окт',
      'ноя',
      'дек',
    ];
    return '${day.day} ${(uz ? uzMonths : ruMonths)[day.month - 1]}';
  }

  String _ago(DateTime at) {
    final diff = DateTime.now().difference(at);
    if (diff.inMinutes < 1) return uz ? 'hozirgina' : 'только что';
    if (diff.inMinutes < 60) {
      return uz ? '${diff.inMinutes} daq oldin' : '${diff.inMinutes} мин назад';
    }
    if (diff.inHours < 24) {
      return uz ? '${diff.inHours} soat oldin' : '${diff.inHours} ч назад';
    }
    return uz ? '${diff.inDays} kun oldin' : '${diff.inDays} дн назад';
  }
}

class _RingPainter extends CustomPainter {
  final double progress;
  final Color color;

  _RingPainter({required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    const stroke = 10.0;
    final rect = Offset.zero & size;
    final arcRect = rect.deflate(stroke / 2);
    final base = Paint()
      ..color = color.withValues(alpha: 0.12)
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke;
    canvas.drawArc(arcRect, 0, math.pi * 2, false, base);
    if (progress <= 0) return;
    final fg = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeWidth = stroke;
    canvas.drawArc(arcRect, -math.pi / 2, math.pi * 2 * progress, false, fg);
  }

  @override
  bool shouldRepaint(covariant _RingPainter old) =>
      old.progress != progress || old.color != color;
}

class _SparkPainter extends CustomPainter {
  final List<double?> values;
  final Color color;

  _SparkPainter({required this.values, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final points = <Offset>[];
    final present = values.whereType<double>().toList();
    if (present.length < 2) return;
    final lo = present.reduce(math.min);
    final hi = present.reduce(math.max);
    final span = hi - lo == 0 ? 1 : hi - lo;
    for (var i = 0; i < values.length; i++) {
      final v = values[i];
      if (v == null) continue;
      final x = values.length == 1 ? 0.0 : size.width * i / (values.length - 1);
      final y = size.height - (v - lo) / span * (size.height - 4) - 2;
      points.add(Offset(x, y));
    }
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final path = Path()..moveTo(points.first.dx, points.first.dy);
    for (final point in points.skip(1)) {
      path.lineTo(point.dx, point.dy);
    }
    canvas.drawPath(path, paint);
    canvas.drawCircle(points.last, 3, Paint()..color = color);
  }

  @override
  bool shouldRepaint(covariant _SparkPainter old) =>
      old.values != values || old.color != color;
}

/// Daily bars; days without data stay empty instead of drawing zero.
class _BarsPainter extends CustomPainter {
  final List<double?> values;
  final List<double?>? mins;
  final List<double?>? maxs;
  final Color color;
  final double? goal;
  final double? maxValue;
  final bool showAxis;

  _BarsPainter({
    required this.values,
    required this.color,
    this.mins,
    this.maxs,
    this.goal,
    this.maxValue,
    this.showAxis = false,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (values.isEmpty) return;
    final candidates = <double>[
      ...values.whereType<double>(),
      ...?maxs?.whereType<double>(),
      ?goal,
    ];
    if (candidates.isEmpty) {
      return;
    }
    final top = maxValue ?? candidates.reduce(math.max) * 1.1;
    if (top <= 0) return;
    final slot = size.width / values.length;
    final barWidth = math.max(2.0, math.min(18.0, slot * 0.6));
    double y(double v) => size.height - (v / top).clamp(0.0, 1.0) * size.height;

    if (showAxis) {
      final grid = Paint()
        ..color = _line
        ..strokeWidth = 1;
      for (final f in [0.25, 0.5, 0.75]) {
        canvas.drawLine(
          Offset(0, size.height * f),
          Offset(size.width, size.height * f),
          grid,
        );
      }
    }
    if (goal != null) {
      final dash = Paint()
        ..color = color.withValues(alpha: 0.5)
        ..strokeWidth = 1.2;
      final gy = y(goal!);
      for (double x = 0; x < size.width; x += 8) {
        canvas.drawLine(
          Offset(x, gy),
          Offset(math.min(x + 4, size.width), gy),
          dash,
        );
      }
    }
    final bar = Paint()..color = color.withValues(alpha: 0.85);
    final range = Paint()
      ..color = color.withValues(alpha: 0.35)
      ..strokeWidth = math.max(1.5, barWidth / 3)
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < values.length; i++) {
      final cx = slot * i + slot / 2;
      final lo = mins?[i];
      final hi = maxs?[i];
      if (lo != null && hi != null && hi > lo) {
        canvas.drawLine(Offset(cx, y(lo)), Offset(cx, y(hi)), range);
      }
      final v = values[i];
      if (v == null) continue;
      if (mins != null) {
        canvas.drawCircle(Offset(cx, y(v)), math.max(2.5, barWidth / 3), bar);
      } else {
        final rect = RRect.fromRectAndRadius(
          Rect.fromLTRB(
            cx - barWidth / 2,
            y(v),
            cx + barWidth / 2,
            size.height,
          ),
          Radius.circular(barWidth / 2),
        );
        canvas.drawRRect(rect, bar);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _BarsPainter old) => true;
}

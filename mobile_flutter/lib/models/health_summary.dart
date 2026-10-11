/// Measured health data for one patient, as returned by
/// `GET /api/v1/patients/{id}/health-summary` and
/// `GET /api/v1/relatives/{token}/health-summary`.
///
/// Every value is nullable on purpose: a missing measurement is shown as
/// missing, never replaced by a normal-looking default.
library;

double? _num(Object? value) => value is num ? value.toDouble() : null;

int? _int(Object? value) => value is num ? value.round() : null;

DateTime? _time(Object? value) =>
    value == null ? null : DateTime.tryParse('$value')?.toLocal();

DateTime _day(Object? value) => DateTime.parse('$value');

List<Map<String, dynamic>> _maps(Object? value) =>
    (value as List? ?? const []).whereType<Map<String, dynamic>>().toList();

class MetricPoint {
  final double value;
  final DateTime at;
  final String source;

  const MetricPoint({
    required this.value,
    required this.at,
    required this.source,
  });

  static MetricPoint? fromJson(Object? json) {
    if (json is! Map<String, dynamic>) return null;
    final value = _num(json['value']);
    final at = _time(json['at']);
    if (value == null || at == null) return null;
    return MetricPoint(value: value, at: at, source: '${json['source']}');
  }
}

class DailyVital {
  final DateTime day;
  final double? avg;
  final double? min;
  final double? max;
  final int n;

  const DailyVital({
    required this.day,
    this.avg,
    this.min,
    this.max,
    this.n = 0,
  });

  factory DailyVital.fromJson(Map<String, dynamic> json) => DailyVital(
    day: _day(json['day']),
    avg: _num(json['avg']),
    min: _num(json['min']),
    max: _num(json['max']),
    n: _int(json['n']) ?? 0,
  );
}

class VitalSummary {
  final MetricPoint? latest;
  final List<DailyVital> daily;
  final int samplesN;
  final DailyVital? today;

  const VitalSummary({
    this.latest,
    this.daily = const [],
    this.samplesN = 0,
    this.today,
  });

  static const empty = VitalSummary();

  bool get hasData => latest != null;

  factory VitalSummary.fromJson(Object? json) {
    if (json is! Map<String, dynamic>) return empty;
    return VitalSummary(
      latest: MetricPoint.fromJson(json['latest']),
      daily: _maps(json['daily']).map(DailyVital.fromJson).toList(),
      samplesN: _int(json['samples_n']) ?? 0,
      today: json['today'] is Map<String, dynamic>
          ? DailyVital.fromJson(json['today'] as Map<String, dynamic>)
          : null,
    );
  }
}

class DailyActivity {
  final DateTime day;
  final double? steps;
  final double? distanceM;
  final double? activeKcal;
  final double? totalKcal;
  final double? floors;

  const DailyActivity({
    required this.day,
    this.steps,
    this.distanceM,
    this.activeKcal,
    this.totalKcal,
    this.floors,
  });

  factory DailyActivity.fromJson(Map<String, dynamic> json) => DailyActivity(
    day: _day(json['day']),
    steps: _num(json['steps']),
    distanceM: _num(json['distance_m']),
    activeKcal: _num(json['active_calories_kcal']),
    totalKcal: _num(json['total_calories_kcal']),
    floors: _num(json['floors']),
  );
}

class SleepNight {
  final DateTime day;
  final DateTime start;
  final DateTime end;
  final int inBedMinutes;
  final int asleepMinutes;
  final int? efficiencyPct;
  final Map<String, int>? stages;

  const SleepNight({
    required this.day,
    required this.start,
    required this.end,
    required this.inBedMinutes,
    required this.asleepMinutes,
    this.efficiencyPct,
    this.stages,
  });

  static SleepNight? fromJson(Object? json) {
    if (json is! Map<String, dynamic>) return null;
    final start = _time(json['start_time']);
    final end = _time(json['end_time']);
    if (start == null || end == null) return null;
    final rawStages = json['stages_minutes'];
    return SleepNight(
      day: _day(json['day']),
      start: start,
      end: end,
      inBedMinutes: _int(json['in_bed_minutes']) ?? 0,
      asleepMinutes: _int(json['asleep_minutes']) ?? 0,
      efficiencyPct: _int(json['efficiency_pct']),
      stages: rawStages is Map<String, dynamic>
          ? rawStages.map((key, value) => MapEntry(key, _int(value) ?? 0))
          : null,
    );
  }
}

class DailySleep {
  final DateTime day;
  final int? asleepMinutes;

  const DailySleep({required this.day, this.asleepMinutes});

  factory DailySleep.fromJson(Map<String, dynamic> json) => DailySleep(
    day: _day(json['day']),
    asleepMinutes: _int(json['asleep_minutes']),
  );
}

class StressSummary {
  /// ok, insufficient_baseline or no_recent_hrv.
  final String status;
  final int? latestScore;
  final String? latestLevel;
  final DateTime? latestAt;
  final double? baselineHrvMs;
  final List<({DateTime day, int? score})> daily;

  const StressSummary({
    required this.status,
    this.latestScore,
    this.latestLevel,
    this.latestAt,
    this.baselineHrvMs,
    this.daily = const [],
  });

  factory StressSummary.fromJson(Object? json) {
    if (json is! Map<String, dynamic>) {
      return const StressSummary(status: 'insufficient_baseline');
    }
    final latest = json['latest'];
    return StressSummary(
      status: '${json['status'] ?? 'insufficient_baseline'}',
      latestScore: latest is Map ? _int(latest['score']) : null,
      latestLevel: latest is Map ? latest['level']?.toString() : null,
      latestAt: latest is Map ? _time(latest['at']) : null,
      baselineHrvMs: _num(json['baseline_hrv_ms']),
      daily: _maps(json['daily'])
          .map((row) => (day: _day(row['day']), score: _int(row['score'])))
          .toList(),
    );
  }
}

class ExerciseItem {
  final String type;
  final DateTime start;
  final int durationMinutes;

  const ExerciseItem({
    required this.type,
    required this.start,
    required this.durationMinutes,
  });
}

class HealthInsight {
  final String key;

  /// attention, info or positive.
  final String severity;
  final Map<String, dynamic> params;

  const HealthInsight({
    required this.key,
    required this.severity,
    this.params = const {},
  });
}

class BloodPressureReading {
  final int systolic;
  final int diastolic;
  final DateTime at;

  const BloodPressureReading({
    required this.systolic,
    required this.diastolic,
    required this.at,
  });
}

class HealthSummaryData {
  final int windowDays;

  /// fresh, stale or no_data.
  final String freshness;
  final DateTime? lastSampleAt;
  final int excludedSamples;
  final Map<String, VitalSummary> metrics;
  final Map<String, MetricPoint?> latestMeasurements;
  final BloodPressureReading? bloodPressure;
  final List<DailyActivity> activityDaily;
  final int goalSteps;
  final SleepNight? lastNight;
  final List<DailySleep> sleepDaily;
  final StressSummary stress;
  final List<ExerciseItem> exercises;
  final List<DateTime> falls;
  final List<HealthInsight> insights;

  const HealthSummaryData({
    required this.windowDays,
    required this.freshness,
    this.lastSampleAt,
    this.excludedSamples = 0,
    this.metrics = const {},
    this.latestMeasurements = const {},
    this.bloodPressure,
    this.activityDaily = const [],
    this.goalSteps = 6000,
    this.lastNight,
    this.sleepDaily = const [],
    this.stress = const StressSummary(status: 'insufficient_baseline'),
    this.exercises = const [],
    this.falls = const [],
    this.insights = const [],
  });

  VitalSummary metric(String key) => metrics[key] ?? VitalSummary.empty;

  DailyActivity? get today => activityDaily.isEmpty ? null : activityDaily.last;

  factory HealthSummaryData.fromJson(Map<String, dynamic> json) {
    final freshness = json['freshness'] as Map<String, dynamic>? ?? const {};
    final activity = json['activity'] as Map<String, dynamic>? ?? const {};
    final sleep = json['sleep'] as Map<String, dynamic>? ?? const {};
    final bp = json['blood_pressure'];
    final events = json['events'] as Map<String, dynamic>? ?? const {};
    final latest = json['latest_measurements'] as Map<String, dynamic>? ?? {};
    return HealthSummaryData(
      windowDays: _int(json['window_days']) ?? 7,
      freshness: '${freshness['status'] ?? 'no_data'}',
      lastSampleAt: _time(freshness['last_sample_at']),
      excludedSamples: _int(freshness['excluded_samples']) ?? 0,
      metrics: (json['metrics'] as Map<String, dynamic>? ?? const {}).map(
        (key, value) => MapEntry(key, VitalSummary.fromJson(value)),
      ),
      latestMeasurements: latest.map(
        (key, value) => MapEntry(key, MetricPoint.fromJson(value)),
      ),
      bloodPressure: bp is Map<String, dynamic> && _time(bp['at']) != null
          ? BloodPressureReading(
              systolic: _int(bp['systolic']) ?? 0,
              diastolic: _int(bp['diastolic']) ?? 0,
              at: _time(bp['at'])!,
            )
          : null,
      activityDaily: _maps(
        activity['daily'],
      ).map(DailyActivity.fromJson).toList(),
      goalSteps: _int(activity['goal_steps']) ?? 6000,
      lastNight: SleepNight.fromJson(sleep['last_night']),
      sleepDaily: _maps(sleep['daily']).map(DailySleep.fromJson).toList(),
      stress: StressSummary.fromJson(json['stress']),
      exercises: _maps(json['exercise_sessions'])
          .where((row) => _time(row['start_time']) != null)
          .map(
            (row) => ExerciseItem(
              type: '${row['exercise_type']}',
              start: _time(row['start_time'])!,
              durationMinutes: _int(row['duration_minutes']) ?? 0,
            ),
          )
          .toList(),
      falls: _maps(
        events['falls'],
      ).map((row) => _time(row['at'])).whereType<DateTime>().toList(),
      insights: _maps(json['insights'])
          .map(
            (row) => HealthInsight(
              key: '${row['key']}',
              severity: '${row['severity']}',
              params: (row['params'] as Map?)?.cast<String, dynamic>() ?? {},
            ),
          )
          .toList(),
    );
  }
}

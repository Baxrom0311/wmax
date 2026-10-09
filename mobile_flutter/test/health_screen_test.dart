import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_flutter/models/health_summary.dart';
import 'package:mobile_flutter/models/models.dart';
import 'package:mobile_flutter/screens/health_screen.dart';
import 'package:mobile_flutter/services/health_auto_sync.dart';
import 'package:mobile_flutter/services/session_service.dart';

final _patient = PatientSummary(
  id: '00000000-0000-0000-0000-000000000001',
  fullName: 'Test Bemor',
  relationship: 'Ota',
  accessToken: 'link',
  level: AlertLevel.green,
  diagnosis: '',
  age: 70,
);

List<Map<String, dynamic>> _days(
  Map<String, dynamic> Function(String day) row,
) {
  final today = DateTime.now();
  return List.generate(7, (i) {
    final d = today.subtract(Duration(days: 6 - i));
    final day =
        '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    return row(day);
  });
}

Map<String, dynamic> _vital(double? latest, {double? min, double? max}) {
  final at = DateTime.now().toUtc().subtract(const Duration(minutes: 5));
  final daily = _days(
    (day) => {
      'day': day,
      'avg': latest,
      'min': min,
      'max': max,
      'n': latest == null ? 0 : 3,
    },
  );
  return {
    'latest': latest == null
        ? null
        : {
            'value': latest,
            'at': at.toIso8601String(),
            'source': 'wear_health_services',
          },
    'daily': daily,
    'samples_n': latest == null ? 0 : 21,
    'today': daily.last,
  };
}

Map<String, dynamic> _summary({bool withData = true}) {
  final now = DateTime.now().toUtc();
  final sleepStart = now.subtract(const Duration(hours: 9));
  return {
    'patient_id': _patient.id,
    'generated_at': now.toIso8601String(),
    'window_days': 7,
    'timezone': 'Asia/Tashkent',
    'freshness': {
      'status': withData ? 'fresh' : 'no_data',
      'last_sample_at': withData ? now.toIso8601String() : null,
      'stale_after_minutes': 45,
      'excluded_samples': 0,
    },
    'metrics': {
      'heart_rate_bpm': _vital(withData ? 72 : null, min: 58, max: 118),
      'resting_heart_rate_bpm': _vital(withData ? 61 : null),
      'heart_rate_variability_rmssd_ms': _vital(withData ? 38 : null),
      'oxygen_saturation_pct': _vital(withData ? 96 : null, min: 93, max: 99),
      'respiratory_rate_bpm': _vital(null),
      'skin_temperature_delta_c': _vital(null),
      'skin_temperature_c': _vital(null),
    },
    'latest_measurements': {'weight_kg': null},
    'blood_pressure': null,
    'activity': {
      'today': null,
      'daily': _days((day) => {'day': day, 'steps': withData ? 6450.0 : null}),
      'goal_steps': 6000,
    },
    'sleep': {
      'last_night': withData
          ? {
              'day': '2026-10-09',
              'start_time': sleepStart.toIso8601String(),
              'end_time': sleepStart
                  .add(const Duration(hours: 7))
                  .toIso8601String(),
              'source': 'health_connect',
              'in_bed_minutes': 420,
              'asleep_minutes': 380,
              'efficiency_pct': 90,
              'stages_minutes': {
                'deep': 70,
                'light': 220,
                'rem': 90,
                'awake': 40,
                'unspecified': 0,
              },
            }
          : null,
      'daily': _days(
        (day) => {'day': day, 'asleep_minutes': withData ? 380 : null},
      ),
    },
    'stress': {
      'method': 'hrv_rmssd_vs_personal_baseline',
      'is_estimate': true,
      'status': withData ? 'ok' : 'insufficient_baseline',
      'baseline_hrv_ms': withData ? 40.0 : null,
      'latest': withData
          ? {'score': 34, 'level': 'low', 'at': now.toIso8601String()}
          : null,
      'daily': _days((day) => {'day': day, 'score': withData ? 34 : null}),
    },
    'exercise_sessions': [],
    'events': {'falls': []},
    'insights': withData
        ? [
            {
              'key': 'steps_goal_met',
              'severity': 'positive',
              'params': {'steps': 6450},
            },
          ]
        : [
            {
              'key': 'data_stale',
              'severity': 'attention',
              'params': {'last_sample_at': null},
            },
          ],
  };
}

Future<void> _pump(
  WidgetTester tester,
  HealthSummaryLoader loader, {
  double devicePixelRatio = 2.6,
}) async {
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = devicePixelRatio;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: HealthScreen(isUzbek: true, patient: _patient, loader: loader),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('shows measured vitals, activity, sleep and stress', (
    tester,
  ) async {
    // Round-trip through JSON so parsing is exercised like a real response.
    final json = jsonDecode(jsonEncode(_summary())) as Map<String, dynamic>;
    await _pump(tester, (_, _) async => HealthSummaryData.fromJson(json));

    expect(find.text('6 450'), findsOneWidget);
    expect(find.text('72'), findsOneWidget);
    expect(find.text('96'), findsOneWidget);
    expect(find.text('6 soat 20 daq'), findsOneWidget);
    expect(find.text('34'), findsOneWidget);
    expect(
      find.textContaining('Kunlik qadam maqsadi bajarildi'),
      findsOneWidget,
    );
    expect(find.textContaining('Yangilandi'), findsOneWidget);
  });

  testWidgets('lays out on a narrow 360dp phone without overflow', (
    tester,
  ) async {
    final json = jsonDecode(jsonEncode(_summary())) as Map<String, dynamic>;
    await _pump(
      tester,
      (_, _) async => HealthSummaryData.fromJson(json),
      devicePixelRatio: 3.0,
    );
    expect(tester.takeException(), isNull);
    await tester.tap(find.byKey(const Key('vital-hr')));
    await tester.pumpAndSettle();
    expect(find.textContaining("7 kunlik o'rtacha"), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('missing data is shown as missing, not as normal values', (
    tester,
  ) async {
    final json =
        jsonDecode(jsonEncode(_summary(withData: false)))
            as Map<String, dynamic>;
    await _pump(tester, (_, _) async => HealthSummaryData.fromJson(json));

    expect(find.text("Soatdan ma'lumot yo'q"), findsOneWidget);
    expect(find.text("O'lchov yo'q"), findsWidgets);
    expect(find.text('72'), findsNothing);
    expect(find.textContaining('Uyqu qayd etilmagan'), findsOneWidget);
    expect(find.textContaining("kamida 3 kun HRV"), findsOneWidget);
  });

  testWidgets('server failure shows no connection instead of values', (
    tester,
  ) async {
    await _pump(tester, (_, _) async => throw StateError('offline'));

    expect(find.textContaining("Server bilan aloqa yo'q"), findsOneWidget);
    expect(find.text('Qayta urinish'), findsOneWidget);
    expect(find.byKey(const Key('health-screen-list')), findsNothing);
  });

  testWidgets('switching to 30 days reloads with the new window', (
    tester,
  ) async {
    final requested = <int>[];
    final json = jsonDecode(jsonEncode(_summary())) as Map<String, dynamic>;
    await _pump(tester, (_, days) async {
      requested.add(days);
      return HealthSummaryData.fromJson(json);
    });
    await tester.tap(find.text('30 kun'));
    await tester.pumpAndSettle();
    expect(requested, [7, 30]);
  });

  test('auto sync reads since last upload with overlap, bounded', () {
    final now = DateTime(2026, 10, 9, 12);
    expect(HealthAutoSync.windowHours(null, now), 24);
    expect(
      HealthAutoSync.windowHours(
        now.subtract(const Duration(minutes: 20)),
        now,
      ),
      2,
    );
    expect(
      HealthAutoSync.windowHours(
        now.subtract(const Duration(hours: 5, minutes: 10)),
        now,
      ),
      7,
    );
    expect(
      HealthAutoSync.windowHours(now.subtract(const Duration(days: 10)), now),
      72,
    );
    expect(
      HealthAutoSync.isDue(now.subtract(const Duration(minutes: 5)), now),
      isFalse,
    );
    expect(
      HealthAutoSync.isDue(now.subtract(const Duration(minutes: 16)), now),
      isTrue,
    );
  });

  test('role claim is read from the access token payload', () {
    String b64(Map<String, dynamic> m) =>
        base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
    final token = '${b64({'alg': 'HS256'})}.${b64({'role': 'relative'})}.sig';
    expect(SessionService.roleFromAccessToken(token), 'relative');
    expect(SessionService.roleFromAccessToken('not-a-jwt'), isNull);
  });
}

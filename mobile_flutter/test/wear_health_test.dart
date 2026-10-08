import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_flutter/models/models.dart';
import 'package:mobile_flutter/screens/watch_runtime_screen.dart';
import 'package:mobile_flutter/services/edge_sensor_filter.dart';
import 'package:mobile_flutter/services/native_health_bridge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('EdgeSensorFilter', () {
    test('validates biometric samples accurately', () {
      expect(
        EdgeSensorFilter.isValidBiometricSample(
          heartRate: 72,
          spo2: 98,
          skinTemp: 36.6,
          stepsDelta: 10,
          isWorn: true,
        ),
        isTrue,
      );

      // Not worn
      expect(
        EdgeSensorFilter.isValidBiometricSample(
          heartRate: 72,
          spo2: 98,
          skinTemp: 36.6,
          stepsDelta: 10,
          isWorn: false,
        ),
        isFalse,
      );

      // Impossible heart rate
      expect(EdgeSensorFilter.isValidHeartRate(20), isFalse);
      expect(EdgeSensorFilter.isValidHeartRate(250), isFalse);
      expect(EdgeSensorFilter.isValidHeartRate(75), isTrue);

      // Impossible SpO2
      expect(EdgeSensorFilter.isValidSpo2(40), isFalse);
      expect(EdgeSensorFilter.isValidSpo2(105), isFalse);
      expect(EdgeSensorFilter.isValidSpo2(97), isTrue);

      // Motion artifact on SpO2 when heavy stepping
      expect(
        EdgeSensorFilter.isValidBiometricSample(
          heartRate: 110,
          spo2: 82,
          skinTemp: 36.5,
          stepsDelta: 120,
          isWorn: true,
        ),
        isFalse,
      );

      // Impossible skin temp
      expect(EdgeSensorFilter.isValidSkinTemp(20.0), isFalse);
      expect(EdgeSensorFilter.isValidSkinTemp(46.0), isFalse);
      expect(EdgeSensorFilter.isValidSkinTemp(36.5), isTrue);
    });
  });

  group('NativeHealthBridge batch & filter', () {
    test('filters corrupted samples from health batch', () {
      final samples = [
        HealthSample(
          metric: 'heart_rate_bpm',
          recordedAt: DateTime.now(),
          valueNum: 75.0,
        ),
        HealthSample(
          metric: 'heart_rate_bpm',
          recordedAt: DateTime.now(),
          valueNum: 10.0, // Invalid!
        ),
        HealthSample(
          metric: 'oxygen_saturation_pct',
          recordedAt: DateTime.now(),
          valueNum: 98.0,
        ),
        HealthSample(
          metric: 'oxygen_saturation_pct',
          recordedAt: DateTime.now(),
          valueNum: 40.0, // Invalid!
        ),
        HealthSample(
          metric: 'skin_temperature_c',
          recordedAt: DateTime.now(),
          valueNum: 36.6,
        ),
        HealthSample(
          metric: 'skin_temperature_c',
          recordedAt: DateTime.now(),
          valueNum: 55.0, // Invalid!
        ),
      ];

      final filtered = NativeHealthBridge.filterSamples(samples);
      expect(filtered.length, 3);
      expect(filtered[0].valueNum, 75.0);
      expect(filtered[1].valueNum, 98.0);
      expect(filtered[2].valueNum, 36.6);
    });

    test('generates valid batch UUID and outbox payload', () async {
      final batchId = NativeHealthBridge.newBatchId();
      expect(batchId, isNotEmpty);
      expect(batchId.split('-').length, 5);

      const channel = MethodChannel('wmax/native_health');
      final log = <MethodCall>[];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall methodCall) async {
            log.add(methodCall);
            if (methodCall.method == 'enqueueWearPayload') {
              return true;
            }
            return null;
          });

      final batch = HealthDataBatch(
        batchId: batchId,
        source: HealthDataSource.wearHealthServices,
        samples: [
          HealthSample(
            metric: 'battery_pct',
            recordedAt: DateTime.now(),
            valueNum: 88,
            unit: '%',
          ),
        ],
      );

      final ok = await NativeHealthBridge.enqueueWearDataBatch(batch);
      expect(ok, isTrue);
      expect(log.length, 1);
      expect(log[0].method, 'enqueueWearPayload');
      expect(log[0].arguments['payload'], contains('battery_pct'));
    });
  });

  group('WatchRuntimeScreen Widget', () {
    testWidgets('renders watch face and all metric pills', (WidgetTester tester) async {
      const channel = MethodChannel('wmax/native_health');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall methodCall) async {
            if (methodCall.method == 'getHealthPlatformStatus') {
              return {
                'latest_heart_rate_bpm': 74.0,
                'latest_heart_rate_at': DateTime.now().toIso8601String(),
                'latest_daily_steps': 4200,
                'latest_daily_steps_at': DateTime.now().toIso8601String(),
                'latest_spo2_pct': 98.0,
                'latest_spo2_at': DateTime.now().toIso8601String(),
                'latest_skin_temp_c': 36.6,
                'latest_skin_temp_at': DateTime.now().toIso8601String(),
                'latest_sleep_stage': 'asleep',
                'latest_sleep_at': DateTime.now().toIso8601String(),
                'battery_pct': 85,
                'wear_os_device': true,
              };
            }
            if (methodCall.method == 'getWearExerciseStatus') {
              return {'active': false, 'status': 'idle'};
            }
            if (methodCall.method == 'getWearHealthCapabilities') {
              return {
                'exercise_types': [
                  {
                    'type': 'WALKING',
                    'data_types': ['HEART_RATE_BPM', 'STEPS'],
                  },
                ],
                'passive_data_types': ['HEART_RATE_BPM', 'STEPS_DAILY'],
              };
            }
            return null;
          });

      await tester.pumpWidget(
        const MaterialApp(
          home: WatchRuntimeScreen(isUzbek: true),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Heart Rate is displayed
      expect(find.text('74'), findsOneWidget);
      expect(find.text('bpm'), findsOneWidget);

      // Verify Battery
      expect(find.text('85%'), findsOneWidget);

      // Verify Steps
      expect(find.text('4200'), findsOneWidget);

      // Verify SpO2
      expect(find.text('98%'), findsOneWidget);

      // Verify Skin Temperature
      expect(find.text('36.6°C'), findsOneWidget);

      // Verify Sleep stage
      expect(find.text('ASLEEP'), findsOneWidget);

      // Verify SOS button exists
      expect(find.text('SOS'), findsOneWidget);
    });
  });
}

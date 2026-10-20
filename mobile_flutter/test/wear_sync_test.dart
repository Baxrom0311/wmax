import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile_flutter/app_mode.dart';
import 'package:mobile_flutter/screens/health_device_screen.dart';
import 'package:mobile_flutter/services/native_health_bridge.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('resolveAppMode', () {
    test('wear flavor starts the watch runtime without a dart-define', () {
      expect(resolveAppMode(defined: '', flavor: 'wear'), 'watch');
    });

    test('phone flavor and no flavor keep the caregiver app', () {
      expect(resolveAppMode(defined: '', flavor: 'phone'), 'phone');
      expect(resolveAppMode(defined: '', flavor: null), 'phone');
    });

    test('an explicit WMAX_APP_MODE wins over the flavor', () {
      expect(resolveAppMode(defined: 'health', flavor: 'phone'), 'health');
      expect(resolveAppMode(defined: 'phone', flavor: 'wear'), 'phone');
    });
  });

  group('HealthDeviceScreen watch queue', () {
    const channel = MethodChannel('wmax/native_health');

    tearDown(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null);
    });

    testWidgets('uploads queued watch batches without a button press', (
      tester,
    ) async {
      SharedPreferences.setMockInitialValues({});
      final calls = <String>[];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            calls.add(call.method);
            switch (call.method) {
              case 'readDeviceCredential':
                return 'synthetic-device-token';
              case 'getHealthPlatformStatus':
                return {'wear_os_device': false};
              case 'getWearDataLayerQueue':
                return <String>[];
            }
            return null;
          });

      await tester.pumpWidget(
        const MaterialApp(home: HealthDeviceScreen(isUzbek: true)),
      );
      await tester.pump();
      expect(calls, contains('getWearDataLayerQueue'));

      calls.clear();
      await tester.pump(const Duration(seconds: 31));
      expect(calls, contains('getWearDataLayerQueue'));

      await tester.pumpWidget(const SizedBox());
    });
  });

  group('syncQueuedWearData', () {
    const channel = MethodChannel('wmax/native_health');
    final payload = jsonEncode({
      'batch_id': '11111111-1111-4111-8111-111111111111',
      'source': 'wear_health_services',
      'samples': [
        {
          'metric': 'fall_detected',
          'recorded_at': '2026-10-20T03:00:00Z',
          'value_text': 'fall_detected',
        },
      ],
    });

    tearDown(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null);
    });

    Future<List<String>> runSync(http.Response Function() respond) async {
      SharedPreferences.setMockInitialValues({});
      final acked = <String>[];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            if (call.method == 'getWearDataLayerQueue') return [payload];
            if (call.method == 'ackWearDataLayerQueue') {
              acked.addAll((call.arguments['payloads'] as List).cast());
              return true;
            }
            return null;
          });
      await http.runWithClient(() async {
        try {
          await NativeHealthBridge.syncQueuedWearData(deviceToken: 'synthetic');
        } catch (_) {}
      }, () => MockClient((_) async => respond()));
      return acked;
    }

    test('a batch the server stored with rejected records leaves the queue', () async {
      final acked = await runSync(
        () => http.Response(
          jsonEncode({
            'server_time': '2026-10-20T03:00:01Z',
            'batch_id': '11111111-1111-4111-8111-111111111111',
            'accepted': 0,
            'duplicate': 0,
            'rejected': [
              {'kind': 'sample', 'index': '0', 'reason': 'orphan_device'},
            ],
          }),
          200,
        ),
      );
      expect(acked, [payload]);
    });

    test('a server error keeps the batch queued for retry', () async {
      final acked = await runSync(() => http.Response('unavailable', 503));
      expect(acked, isEmpty);
    });
  });
}

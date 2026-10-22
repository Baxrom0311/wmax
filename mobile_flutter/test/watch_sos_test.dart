import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mobile_flutter/api/api_service.dart';
import 'package:mobile_flutter/screens/watch_runtime_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('wmax/native_health');

  setUp(() => SharedPreferences.setMockInitialValues({}));
  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  group('triggerDeviceSos', () {
    Future<bool> send(Map<String, dynamic> body) => http.runWithClient(
      () => ApiService.triggerDeviceSos(deviceToken: 'synthetic'),
      () => MockClient((_) async => http.Response(jsonEncode(body), 201)),
    );

    test(
      'a watch with no patient assignment is not reported as sent',
      () async {
        expect(
          await send({'accepted': false, 'reason': 'orphan_device'}),
          isFalse,
        );
      },
    );

    test('an accepted SOS is reported as sent', () async {
      expect(await send({'accepted': true, 'id': 'sos-1'}), isTrue);
    });
  });

  group('watch SOS button', () {
    late List<String> calls;

    void mockWatch() {
      calls = [];
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (call) async {
            calls.add(call.method);
            switch (call.method) {
              case 'readDeviceCredential':
                return 'synthetic-device-token';
              case 'getHealthPlatformStatus':
                return {'wear_os_device': true, 'battery_pct': 80};
              case 'getWearExerciseStatus':
                return {'active': false, 'status': 'idle'};
              case 'getWearDataLayerQueue':
                return <String>[];
              case 'getSosLocation':
                return {
                  'latitude': 41.55,
                  'longitude': 60.63,
                  'accuracy_m': 12.0,
                };
              case 'enqueueWearPayload':
                return true;
            }
            return null;
          });
    }

    Future<void> pumpWatch(WidgetTester tester) async {
      tester.view.physicalSize = const Size(900, 900);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(
        const MaterialApp(home: WatchRuntimeScreen(isUzbek: true)),
      );
      await tester.pump();
      await tester.pump();
    }

    testWidgets('a second tap during the countdown cancels the SOS', (
      tester,
    ) async {
      mockWatch();
      final requests = <http.Request>[];
      await http.runWithClient(
        () async {
          await pumpWatch(tester);
          await tester.ensureVisible(find.text('SOS'));
          await tester.tap(find.text('SOS'));
          await tester.pump();
          expect(find.text('5'), findsOneWidget);
          expect(find.text('Bekor qilish uchun bosing'), findsOneWidget);

          await tester.tap(find.text('5'));
          await tester.pump(const Duration(seconds: 7));
          expect(find.text('SOS'), findsOneWidget);
          expect(requests.where((r) => r.url.path.endsWith('/sos')), isEmpty);
          await tester.pumpWidget(const SizedBox());
        },
        () => MockClient((request) async {
          requests.add(request);
          return http.Response('{}', 200);
        }),
      );
    });

    testWidgets('the SOS carries the watch position and says it was sent', (
      tester,
    ) async {
      mockWatch();
      final requests = <http.Request>[];
      await http.runWithClient(
        () async {
          await pumpWatch(tester);
          await tester.ensureVisible(find.text('SOS'));
          await tester.tap(find.text('SOS'));
          for (var second = 0; second < 6; second++) {
            await tester.pump(const Duration(seconds: 1));
          }
          await tester.pump();
          final sos = requests.singleWhere(
            (r) => r.url.path.endsWith('/ingest/sos'),
          );
          final body = jsonDecode(sos.body) as Map<String, dynamic>;
          expect(body['device_lat'], 41.55);
          expect(body['device_lon'], 60.63);
          expect(body['device_accuracy_m'], 12.0);
          expect(find.text('SOS yuborildi'), findsOneWidget);
          await tester.pumpWidget(const SizedBox());
        },
        () => MockClient((request) async {
          requests.add(request);
          if (request.url.path.endsWith('/ingest/sos')) {
            return http.Response(jsonEncode({'accepted': true}), 201);
          }
          return http.Response('{}', 200);
        }),
      );
    });

    testWidgets('an unassigned watch says so instead of claiming it queued', (
      tester,
    ) async {
      mockWatch();
      await http.runWithClient(
        () async {
          await pumpWatch(tester);
          await tester.ensureVisible(find.text('SOS'));
          await tester.tap(find.text('SOS'));
          for (var second = 0; second < 6; second++) {
            await tester.pump(const Duration(seconds: 1));
          }
          await tester.pump();
          expect(find.text('Soat bemorga biriktirilmagan'), findsOneWidget);
          expect(calls, isNot(contains('enqueueWearPayload')));
          await tester.pumpWidget(const SizedBox());
        },
        () => MockClient((request) async {
          if (request.url.path.endsWith('/ingest/sos')) {
            return http.Response(
              jsonEncode({'accepted': false, 'reason': 'orphan_device'}),
              201,
            );
          }
          return http.Response('{}', 200);
        }),
      );
    });
  });
}

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_flutter/app_mode.dart';
import 'package:mobile_flutter/screens/health_device_screen.dart';
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
}

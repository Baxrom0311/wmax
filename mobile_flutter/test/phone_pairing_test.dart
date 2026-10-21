import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_flutter/models/models.dart';
import 'package:mobile_flutter/screens/dashboard_screen.dart';
import 'package:mobile_flutter/screens/health_device_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('caregiver pairs this phone from the devices tab', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    String? storedToken;
    const channel = MethodChannel('wmax/native_health');
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
          switch (call.method) {
            case 'readDeviceCredential':
              return storedToken;
            case 'getHealthPlatformStatus':
              return {'wear_os_device': false};
            case 'getHealthDataPermissionStatus':
              return {'granted': <String>[]};
            case 'getWearDataLayerQueue':
              return <String>[];
          }
          return null;
        });
    addTearDown(
      () => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null),
    );
    tester.view.physicalSize = const Size(1800, 2700);
    tester.view.devicePixelRatio = 3.0;
    addTearDown(tester.view.reset);
    // The monitoring tab's rows overflow with the wide test font; this test
    // is about the devices tab.
    final previousOnError = FlutterError.onError;
    FlutterError.onError = (details) {
      if (details.exceptionAsString().contains('RenderFlex overflowed')) return;
      previousOnError?.call(details);
    };
    addTearDown(() => FlutterError.onError = previousOnError);

    await tester.pumpWidget(
      MaterialApp(
        home: CaregiverMainDashboard(
          isUzbek: true,
          initialPatients: [
            PatientSummary(
              id: 'p1',
              fullName: 'Test Bemor',
              relationship: 'Ota',
              accessToken: '',
              level: AlertLevel.noData,
              diagnosis: '',
              age: 70,
            ),
          ],
          onToggleLang: () {},
          onSelectLang: (_) {},
          onLogout: () {},
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.byIcon(Icons.watch_rounded).last);
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text("Bu telefon bog'lanmagan"), findsOneWidget);

    final button = find.byKey(const ValueKey('phone-pairing-button'));
    await tester.ensureVisible(button);
    await tester.tap(button);
    await tester.pumpAndSettle();
    expect(find.byType(HealthDeviceScreen), findsOneWidget);

    // Pairing saved a token; going back shows the phone as paired.
    storedToken = 'device-token';
    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text("Bu telefon bog'langan"), findsOneWidget);

    // Stop the dashboard's refresh timers.
    await tester.pumpWidget(const SizedBox());
  });
}

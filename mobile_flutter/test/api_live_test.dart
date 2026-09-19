import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mobile_flutter/api/api_service.dart';
import 'package:mobile_flutter/services/session_service.dart';

void main() {
  setUpAll(() {
    HttpOverrides.global = null;
  });

  test('Live backend integration test with https://wmax.boos.uz', () async {
    SharedPreferences.setMockInitialValues({});
    await SessionService.setBaseUrl('https://wmax.boos.uz');

    // 1. Health check
    final healthOk = await ApiService.pingBackend('https://wmax.boos.uz');
    expect(healthOk, isTrue);

    // 2. Relative Login
    final loginRes = await ApiService.loginRelative(
      phone: '+998901110011',
      pin: '112233',
      customBaseUrl: 'https://wmax.boos.uz',
    );
    expect(loginRes.role, equals('relative'));
    expect(loginRes.fullName, contains('Dilnoza'));
    expect(loginRes.patients.isNotEmpty, isTrue);

    final patient = loginRes.patients.first;
    expect(patient.fullName, contains('Otabek'));
    expect(patient.accessToken.isNotEmpty, isTrue);

    // 3. Live Patient View Fetch
    final view = await ApiService.fetchPatientView(
      patientAccessToken: patient.accessToken,
      patientId: patient.id,
      patientName: patient.fullName,
    );
    expect(view.patientName, contains('Otabek'));
    expect(view.level, isNotNull);
    expect(view.vitals, isNotNull);
    expect(view.problems, isNotNull);
    expect(view.doctor?.name, isNotNull);

    // 4. Live SOS trigger test
    final sosOk = await ApiService.triggerSos(
      patientId: patient.id,
      lat: 41.5562,
      lon: 60.6311,
      reason: 'Flutter test SOS verification',
    );
    expect(sosOk, isTrue);
  });
}

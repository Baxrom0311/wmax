import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';
import '../services/session_service.dart';

class ApiService {
  static const String _ingestKey = String.fromEnvironment('WMAX_INGEST_KEY');

  static Future<String> claimDeviceEnrollment({
    required String deviceId,
    required String code,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/v1/devices/claim'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'device_id': deviceId, 'code': code}),
        )
        .timeout(const Duration(seconds: 10));
    if (response.statusCode != 200) {
      throw StateError('Device enrollment HTTP ${response.statusCode}');
    }
    final payload = jsonDecode(response.body);
    if (payload is! Map<String, dynamic> ||
        payload['device_token'] is! String ||
        (payload['device_token'] as String).isEmpty) {
      throw const FormatException('Invalid device enrollment response.');
    }
    return payload['device_token'] as String;
  }

  static Future<void> ingestWatchReading({
    required String patientId,
    required String deviceId,
    required Map<String, dynamic> reading,
  }) async {
    if (_ingestKey.isEmpty) {
      throw StateError('WMAX_INGEST_KEY build parametri berilmagan');
    }
    final baseUrl = await SessionService.getBaseUrl();
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/v1/ingest'),
          headers: {
            'Content-Type': 'application/json',
            'X-Ingest-Key': _ingestKey,
          },
          body: jsonEncode({
            'patient_id': patientId,
            'device_id': deviceId,
            'readings': [reading],
          }),
        )
        .timeout(const Duration(seconds: 10));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Telemetry ingest HTTP ${response.statusCode}');
    }
  }

  static Future<Map<String, dynamic>> ingestHealthData({
    required String deviceToken,
    required HealthDataBatch batch,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/v1/ingest/health-data'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $deviceToken',
          },
          body: jsonEncode(batch.toJson()),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError('Health data ingest HTTP ${response.statusCode}');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Invalid health ingest response.');
    }
    final rejected = decoded['rejected'];
    if (rejected is List && rejected.isNotEmpty) {
      throw StateError(
        'Server rejected ${rejected.length} health data records.',
      );
    }
    return decoded;
  }

  /// Test backend health (GET /api/v1/health)
  static Future<bool> pingBackend([String? customUrl]) async {
    try {
      final baseUrl = customUrl ?? await SessionService.getBaseUrl();
      final uri = Uri.parse('$baseUrl/api/v1/health');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Relative login: POST /api/v1/auth/relative/login
  static Future<RelativeAuthResponse> loginRelative({
    required String phone,
    required String pin,
    String? customBaseUrl,
  }) async {
    final baseUrl = customBaseUrl ?? await SessionService.getBaseUrl();
    final uri = Uri.parse('$baseUrl/api/v1/auth/relative/login');

    final cleanPhone = phone.replaceAll(' ', '').trim();
    final cleanPin = pin.trim();

    try {
      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'phone': cleanPhone, 'pin': cleanPin}),
          )
          .timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final authRes = RelativeAuthResponse.fromJson(data);

        // If backend returned empty patients list (e.g. initial demo setup), provide mock relatives
        final patients = authRes.patients.isNotEmpty
            ? authRes.patients
            : _getFallbackPatients();

        await SessionService.saveSession(
          accessToken: authRes.accessToken,
          refreshToken: authRes.refreshToken,
          fullName: authRes.fullName,
          phone: cleanPhone,
          patients: patients,
        );

        return RelativeAuthResponse(
          accessToken: authRes.accessToken,
          refreshToken: authRes.refreshToken,
          expiresIn: authRes.expiresIn,
          role: authRes.role,
          fullName: authRes.fullName,
          patients: patients,
        );
      } else {
        String errMsg = 'Kirishda xatolik: ${response.statusCode}';
        try {
          final errBody = jsonDecode(response.body);
          if (errBody['detail'] != null) {
            errMsg = errBody['detail'].toString();
          }
        } catch (_) {}
        throw Exception(errMsg);
      }
    } catch (e) {
      if (e is Exception && e.toString().contains('PIN') ||
          e.toString().contains('xatolik')) {
        rethrow;
      }
      throw Exception(
        'Server bilan bog\'lanishda xatolik yuz berdi ($baseUrl). Internet yoki server holatini tekshiring.',
      );
    }
  }

  /// Clinician login. The dashboard can use the same patient view for doctors.
  static Future<RelativeAuthResponse> loginClinician({
    required String phone,
    required String password,
    String? customBaseUrl,
  }) async {
    final baseUrl = customBaseUrl ?? await SessionService.getBaseUrl();
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/v1/auth/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'phone': phone.replaceAll(' ', '').trim(),
            'password': password,
          }),
        )
        .timeout(const Duration(seconds: 8));
    if (response.statusCode != 200) {
      throw Exception('Kirishda xatolik: ${response.statusCode}');
    }
    final token = jsonDecode(response.body) as Map<String, dynamic>;
    final patients = await _fetchPatients(
      token['access_token'] as String,
      baseUrl,
    );
    final result = RelativeAuthResponse(
      accessToken: token['access_token'] ?? '',
      refreshToken: token['refresh_token'] ?? '',
      expiresIn: token['expires_in'] ?? 3600,
      role: token['role'] ?? 'doctor',
      fullName: token['full_name'] ?? 'Shifokor',
      patients: patients,
    );
    await SessionService.saveSession(
      accessToken: result.accessToken,
      refreshToken: result.refreshToken,
      fullName: result.fullName,
      phone: phone,
      patients: patients,
    );
    return result;
  }

  /// Patient login with phone and PIN. The patient is represented as the sole dashboard item.
  static Future<RelativeAuthResponse> loginPatient({
    required String phone,
    required String pin,
    String? customBaseUrl,
  }) async {
    final baseUrl = customBaseUrl ?? await SessionService.getBaseUrl();
    final response = await http
        .post(
          Uri.parse('$baseUrl/api/v1/auth/patient/login'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'phone': phone.replaceAll(' ', '').trim(),
            'pin': pin.trim(),
          }),
        )
        .timeout(const Duration(seconds: 8));
    if (response.statusCode != 200) {
      throw Exception('Kirishda xatolik: ${response.statusCode}');
    }
    final token = jsonDecode(response.body) as Map<String, dynamic>;
    final me = await http
        .get(
          Uri.parse('$baseUrl/api/v1/auth/me'),
          headers: {'Authorization': 'Bearer ${token['access_token']}'},
        )
        .timeout(const Duration(seconds: 8));
    final user = me.statusCode == 200
        ? jsonDecode(me.body) as Map<String, dynamic>
        : <String, dynamic>{};
    final patient = PatientSummary(
      id: '${user['id'] ?? ''}',
      fullName: user['full_name'] ?? 'Bemor',
      relationship: 'O\'zi',
      accessToken: token['access_token'] ?? '',
      level: AlertLevel.noData,
      diagnosis: 'Tashxis ko\'rsatilmagan',
      age: 0,
    );
    final result = RelativeAuthResponse(
      accessToken: token['access_token'] ?? '',
      refreshToken: token['refresh_token'] ?? '',
      expiresIn: token['expires_in'] ?? 3600,
      role: token['role'] ?? 'patient',
      fullName: token['full_name'] ?? patient.fullName,
      patients: [patient],
    );
    await SessionService.saveSession(
      accessToken: result.accessToken,
      refreshToken: result.refreshToken,
      fullName: result.fullName,
      phone: phone,
      patients: result.patients,
    );
    return result;
  }

  static Future<List<PatientSummary>> _fetchPatients(
    String token,
    String baseUrl,
  ) async {
    final response = await http
        .get(
          Uri.parse('$baseUrl/api/v1/patients'),
          headers: {'Authorization': 'Bearer $token'},
        )
        .timeout(const Duration(seconds: 8));
    if (response.statusCode != 200) return [];
    final raw = jsonDecode(response.body);
    if (raw is! List) return [];
    return raw
        .whereType<Map<String, dynamic>>()
        .map(PatientSummary.fromJson)
        .toList();
  }

  /// Fetch live patient status view: GET /api/v1/relatives/{token}/view
  static Future<RelativePatientView> fetchPatientView({
    required String patientAccessToken,
    required String patientId,
    required String patientName,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();
    final authToken = await SessionService.getAccessToken();

    // If patientAccessToken is empty or fallback mock token
    if (patientAccessToken.isEmpty || patientAccessToken.startsWith('mock_')) {
      return _generateFallbackPatientView(patientId, patientName);
    }

    try {
      final uri = Uri.parse(
        '$baseUrl/api/v1/relatives/$patientAccessToken/view',
      );
      final headers = <String, String>{'Content-Type': 'application/json'};
      if (authToken != null && authToken.isNotEmpty) {
        headers['Authorization'] = 'Bearer $authToken';
      }

      final response = await http
          .get(uri, headers: headers)
          .timeout(const Duration(seconds: 8));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return RelativePatientView.fromJson(data);
      } else {
        return _generateOfflineNoDataView(patientId, patientName);
      }
    } catch (_) {
      return _generateOfflineNoDataView(patientId, patientName);
    }
  }

  /// Emergency SOS: POST /api/v1/sos
  static Future<bool> triggerSos({
    required String patientId,
    double? latitude,
    double? longitude,
    double? lat,
    double? lon,
    String? reason,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();
    final authToken = await SessionService.getAccessToken();

    try {
      final uri = Uri.parse('$baseUrl/api/v1/sos');
      final headers = <String, String>{'Content-Type': 'application/json'};
      if (authToken != null && authToken.isNotEmpty) {
        headers['Authorization'] = 'Bearer $authToken';
      }

      final body = <String, dynamic>{
        'patient_id': patientId,
        'source': 'relative_portal',
        'device_lat': lat ?? latitude,
        'device_lon': lon ?? longitude,
        'device_accuracy_m': 15.0,
      };
      if (reason != null) {
        body['reason'] = reason;
      }

      final response = await http
          .post(uri, headers: headers, body: jsonEncode(body))
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (_) {
      return false;
    }
  }

  /// Device emergency SOS: POST /api/v1/ingest/sos with per-device bearer token
  static Future<bool> triggerDeviceSos({
    required String deviceToken,
    String source = 'watch_button',
    double? latitude,
    double? longitude,
    double? accuracy,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();
    try {
      final uri = Uri.parse('$baseUrl/api/v1/ingest/sos');
      final body = <String, dynamic>{
        'source': source,
        'device_lat': ?latitude,
        'device_lon': ?longitude,
        'device_accuracy_m': ?accuracy,
      };
      final response = await http
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer $deviceToken',
            },
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 8));

      return response.statusCode == 200 || response.statusCode == 201;
    } catch (_) {
      return false;
    }
  }

  static RelativePatientView generateFallbackView(String id, String name) {
    return _generateOfflineNoDataView(id, name);
  }

  /// Fallback demo patients list when starting in offline/demo mode
  static List<PatientSummary> _getFallbackPatients() {
    return [
      PatientSummary(
        id: 'p-001-otabek',
        fullName: 'Otabek Rahimov',
        relationship: 'Otangiz',
        accessToken: 'mock_token_otabek_123',
        level: AlertLevel.red,
        diagnosis: 'Yurak yetishmovchiligi (NYHA III), Qandli diabet',
        age: 68,
        lastReadingAt: DateTime.now().subtract(const Duration(minutes: 4)),
      ),
      PatientSummary(
        id: 'p-002-sayyora',
        fullName: 'Sayyora Rahimova',
        relationship: 'Onangiz',
        accessToken: 'mock_token_sayyora_456',
        level: AlertLevel.amber,
        diagnosis: 'Arterial gipertoniya II bosqich, Stenokardiya',
        age: 65,
        lastReadingAt: DateTime.now().subtract(const Duration(minutes: 12)),
      ),
    ];
  }

  /// Offline view representing disconnected state honestly without inventing vitals
  static RelativePatientView _generateOfflineNoDataView(
    String id,
    String name,
  ) {
    return RelativePatientView(
      patientId: id,
      patientName: name,
      relationship: 'Bemor',
      level: AlertLevel.noData,
      levelWordKey: 'state.no_data',
      compositeScore: 0.0,
      lastReadingAt: null,
      prognosis: PrognosisData(
        riskLevel: 'unknown',
        riskProbabilityPct: null,
        summary: "Aloqa mavjud emas. Ko'rsatkichlar yangilanmadi.",
      ),
      vitals: VitalsData(
        hr: 0.0,
        spo2: 0.0,
        temp: 0.0,
        rr: 0.0,
        steps: 0,
        sleepHours: 0.0,
        battery: 0,
      ),
      doctorContact: DoctorContact(
        name: 'Navbatchi shifokor',
        phone: '+998901234567',
      ),
      problems: [
        ClinicalProblem(
          key: 'conn_lost',
          title: 'Aloqa uzilgan',
          detail: "Server bilan bog'lanishda xatolik yuz berdi",
          severity: 'warning',
        ),
      ],
      sparkline: const [],
    );
  }

  /// Fallback simulated view for offline / demo mode
  static RelativePatientView _generateFallbackPatientView(
    String id,
    String name,
  ) {
    final isFather = name.contains('Otabek');
    return RelativePatientView(
      patientId: id,
      patientName: name,
      relationship: isFather ? 'Otangiz' : 'Onangiz',
      level: isFather ? AlertLevel.red : AlertLevel.amber,
      levelWordKey: isFather ? 'state.risk' : 'state.attention',
      compositeScore: isFather ? 4.2 : 2.1,
      lastReadingAt: DateTime.now().subtract(const Duration(minutes: 5)),
      prognosis: PrognosisData(
        riskLevel: isFather ? 'high' : 'moderate',
        riskProbabilityPct: null,
        summary: isFather
            ? 'SpO2 89% gacha pasaygan, puls 108 bpm. Shifokor bilan bog\'lanish tavsiya etiladi.'
            : 'Ko\'rsatkichlar me\'yorda, biroq qon bosimi va puls o\'rtacha ko\'tarilgan.',
      ),
      vitals: VitalsData(
        hr: isFather ? 108.0 : 78.0,
        spo2: isFather ? 89.0 : 96.0,
        temp: 36.6,
        rr: isFather ? 22.0 : 17.0,
        steps: 1840,
        sleepHours: 6.5,
        battery: 92,
      ),
      doctorContact: DoctorContact(
        name: 'Dr. Bahrom Alimov',
        phone: '+998901234567',
      ),
      problems: [
        if (isFather)
          ClinicalProblem(
            key: 'spo2_crit',
            title: 'Gipoksemiya (SpO2 pasaygan)',
            detail: 'Kislorod miqdori me\'yordan past (89%)',
            severity: 'critical',
          ),
        ClinicalProblem(
          key: 'hr_elev',
          title: 'Taxikardiya epizodi',
          detail: 'Yurak urishi daqiqasiga 100 dan yuqori',
          severity: 'warning',
        ),
      ],
      sparkline: isFather
          ? [1.8, 2.1, 2.4, 2.9, 3.5, 3.9, 4.2]
          : [1.5, 1.6, 1.8, 2.0, 2.2, 2.1, 2.1],
    );
  }
}

import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/health_summary.dart';
import '../models/models.dart';
import '../services/session_service.dart';

/// The stored session can no longer be refreshed; the user must sign in again.
class SessionExpiredException implements Exception {
  const SessionExpiredException();
}

class ApiService {
  static const String _ingestKey = String.fromEnvironment('WMAX_INGEST_KEY');

  // One refresh at a time: the server rotates refresh tokens, so a second
  // concurrent refresh with the old token would be rejected.
  static Future<bool>? _refreshing;

  static Future<bool> _refreshTokens() {
    return _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);
  }

  static Future<bool> _doRefresh() async {
    final refreshToken = await SessionService.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) return false;
    try {
      final baseUrl = await SessionService.getBaseUrl();
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/auth/refresh'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'refresh_token': refreshToken}),
          )
          .timeout(const Duration(seconds: 8));
      if (response.statusCode != 200) return false;
      final data = jsonDecode(response.body);
      if (data is! Map<String, dynamic> ||
          data['access_token'] is! String ||
          data['refresh_token'] is! String) {
        return false;
      }
      await SessionService.updateTokens(
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Sends with the current access token and, on 401, refreshes once and
  /// retries. Throws [SessionExpiredException] when the session is gone.
  static Future<http.Response> _withAuth(
    Future<http.Response> Function(String accessToken) send,
  ) async {
    final token = await SessionService.getAccessToken();
    if (token == null || token.isEmpty) throw const SessionExpiredException();
    final response = await send(token);
    if (response.statusCode != 401) return response;
    if (!await _refreshTokens()) throw const SessionExpiredException();
    final fresh = await SessionService.getAccessToken();
    return send(fresh!);
  }

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
      throw HealthIngestRejected(rejected.length);
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

        final patients = authRes.patients;

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

    if (patientAccessToken.isEmpty) {
      return _generateOfflineNoDataView(patientId, patientName);
    }

    try {
      final uri = Uri.parse(
        '$baseUrl/api/v1/relatives/$patientAccessToken/view',
      );
      final response = await _withAuth(
        (token) => http
            .get(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $token',
              },
            )
            .timeout(const Duration(seconds: 8)),
      );

      if (response.statusCode == 200) {
        final data =
            jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return RelativePatientView.fromJson(data);
      }
      return _generateOfflineNoDataView(patientId, patientName);
    } on SessionExpiredException {
      rethrow;
    } catch (_) {
      return _generateOfflineNoDataView(patientId, patientName);
    }
  }

  /// Measured watch data for one patient. Caregivers read it through their
  /// patient link; patients and clinicians through the patient id.
  /// Throws on any failure: callers must show "no connection", never
  /// substitute values.
  static Future<HealthSummaryData> fetchHealthSummary({
    required PatientSummary patient,
    int days = 7,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();
    final authToken = await SessionService.getAccessToken();
    if (authToken == null || authToken.isEmpty) {
      throw const SessionExpiredException();
    }
    final role = SessionService.roleFromAccessToken(authToken);
    final path = role == 'relative'
        ? '/api/v1/relatives/${Uri.encodeComponent(patient.accessToken)}/health-summary'
        : '/api/v1/patients/${Uri.encodeComponent(patient.id)}/health-summary';
    final response = await _withAuth(
      (token) => http
          .get(
            Uri.parse('$baseUrl$path?days=$days'),
            headers: {'Authorization': 'Bearer $token'},
          )
          .timeout(const Duration(seconds: 12)),
    );
    if (response.statusCode != 200) {
      throw StateError('Health summary HTTP ${response.statusCode}');
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Invalid health summary response.');
    }
    return HealthSummaryData.fromJson(decoded);
  }

  /// Emergency SOS: POST /api/v1/sos
  static Future<bool> triggerSos({
    required String patientId,
    double? latitude,
    double? longitude,
    double? accuracyMeters,
  }) async {
    final baseUrl = await SessionService.getBaseUrl();

    try {
      final uri = Uri.parse('$baseUrl/api/v1/sos');

      // Location only when a real fix exists; responders must never be sent
      // to a placeholder address.
      final body = <String, dynamic>{
        'patient_id': patientId,
        'source': 'relative_portal',
        'device_lat': ?latitude,
        'device_lon': ?longitude,
        'device_accuracy_m': ?accuracyMeters,
      };

      final response = await _withAuth(
        (token) => http
            .post(
              uri,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $token',
              },
              body: jsonEncode(body),
            )
            .timeout(const Duration(seconds: 8)),
      );

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

      if (response.statusCode != 200 && response.statusCode != 201) {
        return false;
      }
      // An unassigned watch gets 201 with accepted: false; nobody is alerted.
      final decoded = jsonDecode(response.body);
      return decoded is! Map || decoded['accepted'] != false;
    } catch (_) {
      return false;
    }
  }

  static RelativePatientView generateFallbackView(String id, String name) {
    return _generateOfflineNoDataView(id, name);
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
      // Unknown, not zero: nothing here may read as a measurement.
      vitals: VitalsData(),
      problems: [
        ClinicalProblem(
          key: 'conn_lost',
          title: 'Aloqa uzilgan',
          detail:
              "Serverdan yangi ma'lumot olinmadi. Internetni tekshirib, yangilang.",
          severity: 'warning',
        ),
      ],
      sparkline: const [],
    );
  }
}

/// The server stored the batch but refused some records (for example no
/// device assignment or revoked consent). Resending cannot change that answer.
class HealthIngestRejected implements Exception {
  final int count;

  const HealthIngestRejected(this.count);

  @override
  String toString() => 'Server rejected $count health data records.';
}

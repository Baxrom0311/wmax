import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';

class SessionService {
  static const String _keyBaseUrl = 'wmax_base_url';
  static const String _keyAccessToken = 'wmax_access_token';
  static const String _keyRefreshToken = 'wmax_refresh_token';
  static const String _keyRelativeName = 'wmax_relative_name';
  static const String _keyPhone = 'wmax_phone';
  static const String _keyPatientsJson = 'wmax_patients_json';
  static const String _keySelectedPatientId = 'wmax_selected_patient_id';
  static const String _keyIsUzbek = 'wmax_is_uzbek';

  static const String _defaultLiveUrl = 'https://wmax.boos.uz';

  static String getDefaultBaseUrl() {
    return _defaultLiveUrl;
  }

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_keyBaseUrl);
    if (saved == null || saved.isEmpty || saved.contains('10.0.2.2') || saved.contains('127.0.0.1')) {
      return _defaultLiveUrl;
    }
    return saved;
  }

  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyBaseUrl, url.trim());
  }

  static Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyAccessToken);
  }

  static Future<String?> getRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyRefreshToken);
  }

  static Future<String> getRelativeName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyRelativeName) ?? 'Qarovchi';
  }

  static Future<String?> getPhone() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyPhone);
  }

  static Future<bool> isUzbek() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyIsUzbek) ?? true;
  }

  static Future<void> setIsUzbek(bool isUzbek) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyIsUzbek, isUzbek);
  }

  static Future<void> saveSession({
    required String accessToken,
    required String refreshToken,
    required String fullName,
    required String phone,
    required List<PatientSummary> patients,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccessToken, accessToken);
    await prefs.setString(_keyRefreshToken, refreshToken);
    await prefs.setString(_keyRelativeName, fullName);
    await prefs.setString(_keyPhone, phone);

    final rawList = patients.map((p) => p.toJson()).toList();
    await prefs.setString(_keyPatientsJson, jsonEncode(rawList));

    if (patients.isNotEmpty) {
      await prefs.setString(_keySelectedPatientId, patients.first.id);
    }
  }

  static Future<List<PatientSummary>> getSavedPatients() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_keyPatientsJson);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List;
      return list.map((p) => PatientSummary.fromJson(p as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  static Future<String?> getSelectedPatientId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keySelectedPatientId);
  }

  static Future<void> setSelectedPatientId(String id) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keySelectedPatientId, id);
  }

  static Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }

  static Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyAccessToken);
    await prefs.remove(_keyRefreshToken);
    await prefs.remove(_keyRelativeName);
    await prefs.remove(_keyPhone);
    await prefs.remove(_keyPatientsJson);
    await prefs.remove(_keySelectedPatientId);
  }
}

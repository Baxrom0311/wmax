import 'package:shared_preferences/shared_preferences.dart';

import 'native_health_bridge.dart';

/// Keeps Health Connect data (Samsung Health, Fitbit, Wear OS watches) flowing
/// to the server while the app is open, without asking for permissions again.
class HealthAutoSync {
  static const _lastSyncKey = 'wmax_health_connect_last_sync';
  static const interval = Duration(minutes: 15);
  static bool _running = false;

  /// Hours of history to read: since the last successful upload plus an
  /// overlap hour, so records written late by the watch app are not missed.
  /// Server-side idempotency makes the overlap harmless.
  static int windowHours(DateTime? lastSync, DateTime now) {
    if (lastSync == null) return 24;
    final hours = now.difference(lastSync).inMinutes / 60;
    return (hours.ceil() + 1).clamp(2, 72);
  }

  static bool isDue(DateTime? lastSync, DateTime now) =>
      lastSync == null || now.difference(lastSync) >= interval;

  /// Returns true when an upload ran and succeeded.
  static Future<bool> syncIfDue({required String deviceToken}) async {
    if (_running) return false;
    _running = true;
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_lastSyncKey);
      final lastSync = raw == null ? null : DateTime.tryParse(raw);
      final now = DateTime.now();
      if (!isDue(lastSync, now)) return false;

      final platform = await NativeHealthBridge.getHealthPlatformStatus();
      if (platform['wear_os_device'] == true ||
          platform['health_connect_available'] != true) {
        return false;
      }
      final granted = await NativeHealthBridge.grantedHealthDataPermissions();
      if (granted.isEmpty) return false;

      await NativeHealthBridge.syncRecentHealthData(
        deviceToken: deviceToken,
        hours: windowHours(lastSync, now),
      );
      await prefs.setString(_lastSyncKey, now.toUtc().toIso8601String());
      return true;
    } catch (_) {
      // Leave the timestamp unchanged so the next refresh retries the window.
      return false;
    } finally {
      _running = false;
    }
  }
}

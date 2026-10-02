import 'package:flutter/services.dart';

class DeviceCredentialStore {
  static const _channel = MethodChannel('wmax/native_health');

  static Future<String?> read() =>
      _channel.invokeMethod<String>('readDeviceCredential');

  static Future<void> save(String token) async {
    await _channel.invokeMethod<void>('saveDeviceCredential', {'token': token});
  }

  static Future<void> clear() =>
      _channel.invokeMethod<void>('clearDeviceCredential');
}

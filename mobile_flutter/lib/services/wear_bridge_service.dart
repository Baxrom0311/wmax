import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import '../api/api_service.dart';

class WearNode {
  final String id;
  final String name;
  final bool nearby;

  const WearNode({required this.id, required this.name, required this.nearby});

  factory WearNode.fromMap(Map<dynamic, dynamic> map) => WearNode(
    id: '${map['id'] ?? ''}',
    name: '${map['name'] ?? 'Wear OS'}',
    nearby: map['nearby'] == true,
  );
}

class WearBridgeService {
  static const _method = MethodChannel('com.wmax.mobile_flutter/wear');
  static const _events = EventChannel('com.wmax.mobile_flutter/wear_telemetry');
  StreamSubscription<dynamic>? _subscription;

  Future<List<WearNode>> connectedNodes() async {
    final raw = await _method.invokeMethod<List<dynamic>>('connectedNodes');
    return (raw ?? const [])
        .whereType<Map<dynamic, dynamic>>()
        .map(WearNode.fromMap)
        .toList();
  }

  void start({
    required String patientId,
    required String deviceId,
    void Function(String)? onError,
  }) {
    _subscription?.cancel();
    _subscription = _events.receiveBroadcastStream().listen((event) async {
      if (event is! Map) return;
      final path = '${event['path'] ?? ''}';
      final payload = '${event['payload'] ?? ''}';
      try {
        final data = jsonDecode(payload) as Map<String, dynamic>;
        if (path == '/wmax/reading_batch') {
          await ApiService.ingestWatchReading(
            patientId: patientId,
            deviceId: deviceId,
            reading: data,
          );
        } else if (path == '/wmax/sos') {
          await ApiService.triggerSos(
            patientId: patientId,
            reason: 'Wear OS SOS',
          );
        }
      } catch (error) {
        onError?.call('$error');
      }
    }, onError: (Object error) => onError?.call('$error'));
  }

  Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
  }
}

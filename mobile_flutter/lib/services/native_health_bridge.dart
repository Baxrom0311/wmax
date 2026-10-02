import 'dart:convert';

import 'package:flutter/services.dart';

import '../api/api_service.dart';
import '../models/models.dart';

class NativeHealthBridge {
  static const MethodChannel _channel = MethodChannel('wmax/native_health');

  static Future<Map<String, dynamic>> getHealthPlatformStatus() async {
    final raw = await _channel.invokeMapMethod<String, dynamic>(
      'getHealthPlatformStatus',
    );
    return raw ?? <String, dynamic>{};
  }

  static Future<Map<String, dynamic>> startWearHealthMonitoring() async {
    final raw = await _channel.invokeMapMethod<String, dynamic>(
      'startWearHealthMonitoring',
    );
    return raw ?? <String, dynamic>{};
  }

  static Future<void> openHealthConnectSettings() async {
    await _channel.invokeMethod<bool>('openHealthConnectSettings');
  }

  static Future<Map<String, dynamic>> requestHealthDataPermissions() async {
    final raw = await _channel.invokeMapMethod<String, dynamic>(
      'requestHealthDataPermissions',
    );
    return raw ?? <String, dynamic>{};
  }

  static Future<HealthDataBatch> readRecentHealthData({
    int hours = 24,
  }) async {
    final raw = await _channel.invokeMapMethod<String, dynamic>(
      'readRecentHealthData',
      {'hours': hours},
    );
    if (raw == null) {
      throw PlatformException(
        code: 'empty_health_connect_payload',
        message: 'Health Connect returned no data payload.',
      );
    }
    return _batchFromJson(raw);
  }

  static Future<void> syncRecentHealthData({
    required String deviceToken,
    int hours = 24,
  }) async {
    final batch = await readRecentHealthData(hours: hours);
    await ApiService.ingestHealthData(deviceToken: deviceToken, batch: batch);
  }

  static Future<List<HealthDataBatch>> drainWearDataLayerQueue() async {
    final payloads = await _channel.invokeListMethod<String>(
      'getWearDataLayerQueue',
    );
    if (payloads == null || payloads.isEmpty) {
      return const [];
    }
    final batches = <HealthDataBatch>[];
    for (final payload in payloads) {
      final decoded = jsonDecode(payload);
      if (decoded is Map<String, dynamic>) {
        batches.add(_batchFromJson(decoded));
      }
    }
    return batches;
  }

  static Future<int> syncQueuedWearData({required String deviceToken}) async {
    final payloads = await _channel.invokeListMethod<String>(
      'getWearDataLayerQueue',
    );
    if (payloads == null || payloads.isEmpty) return 0;

    final acknowledged = <String>[];
    var uploaded = 0;
    try {
      for (final payload in payloads) {
        final decoded = jsonDecode(payload);
        if (decoded is! Map<String, dynamic>) continue;
        final batch = _batchFromJson(decoded);
        await ApiService.ingestHealthData(
          deviceToken: deviceToken,
          batch: batch,
        );
        acknowledged.add(payload);
        uploaded++;
      }
    } finally {
      if (acknowledged.isNotEmpty) {
        await _channel.invokeMethod<bool>('ackWearDataLayerQueue', {
          'payloads': acknowledged,
        });
      }
    }
    return uploaded;
  }

  static HealthDataBatch _batchFromJson(Map<String, dynamic> json) {
    return HealthDataBatch(
      batchId: '${json['batch_id']}',
      sequence: json['sequence'] is int
          ? json['sequence'] as int
          : int.tryParse('${json['sequence']}'),
      source: _sourceFromJson('${json['source']}'),
      samples: (json['samples'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(_sampleFromJson)
          .toList(),
      sleepSessions: (json['sleep_sessions'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(_sleepFromJson)
          .toList(),
      exerciseSessions: (json['exercise_sessions'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(_exerciseFromJson)
          .toList(),
      metadata: (json['metadata'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  static HealthDataSource _sourceFromJson(String raw) {
    switch (raw) {
      case 'health_connect':
        return HealthDataSource.healthConnect;
      case 'healthkit':
        return HealthDataSource.healthKit;
      case 'wear_data_layer':
        return HealthDataSource.wearDataLayer;
      case 'manual':
        return HealthDataSource.manual;
      case 'wear_health_services':
      default:
        return HealthDataSource.wearHealthServices;
    }
  }

  static HealthSample _sampleFromJson(Map<String, dynamic> json) {
    return HealthSample(
      metric: '${json['metric']}',
      recordedAt: DateTime.parse('${json['recorded_at']}'),
      valueNum: json['value_num'] is num
          ? (json['value_num'] as num).toDouble()
          : double.tryParse('${json['value_num']}'),
      valueText: json['value_text']?.toString(),
      unit: json['unit']?.toString(),
      startedAt: json['started_at'] == null
          ? null
          : DateTime.parse('${json['started_at']}'),
      endedAt: json['ended_at'] == null
          ? null
          : DateTime.parse('${json['ended_at']}'),
      sourceRecordId: json['source_record_id']?.toString(),
      quality: json['quality'] is num
          ? (json['quality'] as num).toDouble()
          : double.tryParse('${json['quality']}'),
      metadata: (json['metadata'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  static SleepSessionUpload _sleepFromJson(Map<String, dynamic> json) {
    return SleepSessionUpload(
      startTime: DateTime.parse('${json['start_time']}'),
      endTime: DateTime.parse('${json['end_time']}'),
      sourceRecordId: json['source_record_id']?.toString(),
      stages: (json['stages'] as List? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(
            (stage) => SleepStage(
              stage: '${stage['stage']}',
              startTime: DateTime.parse('${stage['start_time']}'),
              endTime: DateTime.parse('${stage['end_time']}'),
            ),
          )
          .toList(),
      metrics: (json['metrics'] as Map?)?.cast<String, dynamic>() ?? const {},
      metadata: (json['metadata'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }

  static ExerciseSessionUpload _exerciseFromJson(Map<String, dynamic> json) {
    return ExerciseSessionUpload(
      exerciseType: '${json['exercise_type']}',
      startTime: DateTime.parse('${json['start_time']}'),
      endTime: DateTime.parse('${json['end_time']}'),
      sourceRecordId: json['source_record_id']?.toString(),
      metrics: (json['metrics'] as Map?)?.cast<String, dynamic>() ?? const {},
      route: (json['route'] as List?)
          ?.whereType<Map<String, dynamic>>()
          .map((point) => point.cast<String, dynamic>())
          .toList(),
      metadata: (json['metadata'] as Map?)?.cast<String, dynamic>() ?? const {},
    );
  }
}

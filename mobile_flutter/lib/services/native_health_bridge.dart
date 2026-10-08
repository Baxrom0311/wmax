import 'dart:convert';
import 'dart:math';

import 'package:flutter/services.dart';

import '../api/api_service.dart';
import '../models/models.dart';
import 'edge_sensor_filter.dart';

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

  static Future<Map<String, dynamic>> getWearHealthCapabilities() async {
    final raw = await _channel.invokeMapMethod<String, dynamic>(
      'getWearHealthCapabilities',
    );
    return raw ?? <String, dynamic>{};
  }

  static Future<void> startWearExercise({
    String exerciseType = 'WALKING',
  }) async {
    await _channel.invokeMethod<bool>('startWearExercise', {
      'exerciseType': exerciseType,
    });
  }

  static Future<void> requestWearExercisePermissions() async {
    await _channel.invokeMethod<bool>('requestWearExercisePermissions');
  }

  static Future<void> stopWearExercise() async {
    await _channel.invokeMethod<bool>('stopWearExercise');
  }

  static Future<Map<String, dynamic>> getWearExerciseStatus() async {
    final raw = await _channel.invokeMapMethod<String, dynamic>(
      'getWearExerciseStatus',
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

  static Future<HealthDataBatch> readRecentHealthData({int hours = 24}) async {
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
    final chunkCount = [
      (batch.samples.length / 500).ceil(),
      (batch.sleepSessions.length / 20).ceil(),
      (batch.exerciseSessions.length / 20).ceil(),
      1,
    ].reduce((left, right) => left > right ? left : right);
    for (var index = 0; index < chunkCount; index++) {
      await ApiService.ingestHealthData(
        deviceToken: deviceToken,
        batch: HealthDataBatch(
          batchId: _newBatchId(),
          sequence: (batch.sequence ?? 0) + index,
          source: batch.source,
          samples: _slice(batch.samples, index, 500),
          sleepSessions: _slice(batch.sleepSessions, index, 20),
          exerciseSessions: _slice(batch.exerciseSessions, index, 20),
          metadata: {...batch.metadata, 'parent_batch_id': batch.batchId},
        ),
      );
    }
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
    Object? firstError;
    try {
      for (final payload in payloads) {
        try {
          final decoded = jsonDecode(payload);
          if (decoded is! Map<String, dynamic>) continue;
          final batch = _batchFromJson(decoded);
          await ApiService.ingestHealthData(
            deviceToken: deviceToken,
            batch: batch,
          );
          acknowledged.add(payload);
          uploaded++;
        } catch (error) {
          firstError ??= error;
        }
      }
    } finally {
      if (acknowledged.isNotEmpty) {
        await _channel.invokeMethod<bool>('ackWearDataLayerQueue', {
          'payloads': acknowledged,
        });
      }
    }
    if (firstError != null) throw firstError;
    return uploaded;
  }

  static Future<bool> enqueueWearDataBatch(HealthDataBatch batch) async {
    final payload = jsonEncode(batch.toJson());
    final success = await _channel.invokeMethod<bool>('enqueueWearPayload', {
      'payload': payload,
    });
    return success ?? false;
  }

  static List<HealthSample> filterSamples(List<HealthSample> samples) {
    return samples.where((sample) {
      if (sample.valueNum == null) return true;
      if (sample.metric == 'heart_rate_bpm') {
        return EdgeSensorFilter.isValidHeartRate(sample.valueNum);
      }
      if (sample.metric == 'oxygen_saturation_pct') {
        return EdgeSensorFilter.isValidSpo2(sample.valueNum);
      }
      if (sample.metric.startsWith('skin_temperature') ||
          sample.metric == 'body_temperature_c') {
        return EdgeSensorFilter.isValidSkinTemp(sample.valueNum);
      }
      return true;
    }).toList();
  }

  static List<T> _slice<T>(List<T> values, int chunkIndex, int chunkSize) {
    final start = chunkIndex * chunkSize;
    if (start >= values.length) return const [];
    return values.sublist(start, min(start + chunkSize, values.length));
  }

  static String newBatchId() {
    final bytes = List<int>.generate(16, (_) => Random.secure().nextInt(256));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    final hex = bytes
        .map((byte) => byte.toRadixString(16).padLeft(2, '0'))
        .join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-'
        '${hex.substring(12, 16)}-${hex.substring(16, 20)}-'
        '${hex.substring(20)}';
  }

  static String _newBatchId() => newBatchId();

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

import 'dart:async';

import 'package:flutter/material.dart';

import '../api/api_service.dart';
import '../models/models.dart';
import '../services/device_credential_store.dart';
import '../services/edge_sensor_filter.dart';
import '../services/native_health_bridge.dart';

class WatchRuntimeScreen extends StatefulWidget {
  final bool isUzbek;

  const WatchRuntimeScreen({super.key, required this.isUzbek});

  @override
  State<WatchRuntimeScreen> createState() => _WatchRuntimeScreenState();
}

enum _WatchSendState { idle, sending, sent, failed }

class _WatchRuntimeScreenState extends State<WatchRuntimeScreen> {
  static const _patientId = String.fromEnvironment('WMAX_PATIENT_ID');
  String? _deviceToken;

  Timer? _clockTimer;
  Timer? _healthStatusTimer;
  Timer? _sosTimer;

  DateTime _now = DateTime.now();
  int? _hr;
  int? _dailySteps;
  int? _spo2;
  double? _skinTemp;
  String? _sleepState;
  int _battery = -1;
  List<Map<String, dynamic>> _exerciseTypes = const [];
  List<String> _passiveDataTypes = const [];
  bool _exerciseActive = false;
  String? _activeExerciseType;
  String? _exerciseError;
  int? _exerciseHr;
  _WatchSendState _sendState = _WatchSendState.idle;
  int _sentCount = 0;
  int _sosCountdown = 0;

  @override
  void initState() {
    super.initState();
    _clockTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() => _now = DateTime.now());
    });
    _refreshHealthStatus();
    _refreshCapabilities();
    _loadDeviceCredential();
    _healthStatusTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      _refreshHealthStatus();
    });
  }

  Future<void> _loadDeviceCredential() async {
    try {
      final token = await DeviceCredentialStore.read();
      if (mounted) setState(() => _deviceToken = token);
    } catch (_) {
      if (mounted) setState(() => _deviceToken = null);
    }
  }

  @override
  void dispose() {
    _clockTimer?.cancel();
    _healthStatusTimer?.cancel();
    _sosTimer?.cancel();
    super.dispose();
  }

  Future<void> _refreshHealthStatus() async {
    try {
      final status = await NativeHealthBridge.getHealthPlatformStatus();
      final exercise = await NativeHealthBridge.getWearExerciseStatus();
      if (!mounted) return;
      final latestAt = DateTime.tryParse('${status['latest_heart_rate_at']}');
      final bpm = (status['latest_heart_rate_bpm'] as num?)?.round();
      final isFresh =
          latestAt != null &&
          DateTime.now().difference(latestAt).inMinutes <= 10;
      final validHr = (isFresh &&
              bpm != null &&
              EdgeSensorFilter.isValidHeartRate(bpm.toDouble()))
          ? bpm
          : null;

      final stepsAt = DateTime.tryParse('${status['latest_daily_steps_at']}');
      final stepsValue = (status['latest_daily_steps'] as num?)?.toInt();
      final stepsAreFresh =
          stepsAt != null &&
          DateTime.now().difference(stepsAt).inHours <= 30 &&
          stepsValue != null &&
          stepsValue >= 0;

      final spo2Val = (status['latest_spo2_pct'] as num?)?.round();
      final spo2At = DateTime.tryParse('${status['latest_spo2_at']}');
      final spo2IsFresh =
          spo2At != null && DateTime.now().difference(spo2At).inHours <= 24;
      final validSpo2 = (spo2IsFresh &&
              spo2Val != null &&
              EdgeSensorFilter.isValidSpo2(spo2Val.toDouble()))
          ? spo2Val
          : null;

      final tempVal = (status['latest_skin_temp_c'] as num?)?.toDouble();
      final tempAt = DateTime.tryParse('${status['latest_skin_temp_at']}');
      final tempIsFresh =
          tempAt != null && DateTime.now().difference(tempAt).inHours <= 24;
      final validTemp = (tempIsFresh &&
              tempVal != null &&
              EdgeSensorFilter.isValidSkinTemp(tempVal))
          ? tempVal
          : null;

      final activityState = status['latest_activity_state']?.toString();
      final sleepStage = status['latest_sleep_stage']?.toString();
      final sleepAt = DateTime.tryParse('${status['latest_sleep_at']}');
      final sleepIsFresh =
          sleepAt != null && DateTime.now().difference(sleepAt).inHours <= 24;
      final currentSleepState = (sleepIsFresh || activityState == 'asleep')
          ? (sleepStage ?? activityState)
          : null;

      setState(() {
        _hr = validHr;
        _dailySteps = stepsAreFresh ? stepsValue : null;
        _spo2 = validSpo2;
        _skinTemp = validTemp;
        _sleepState = currentSleepState;
        _battery = (status['battery_pct'] as num?)?.toInt() ?? -1;
        _exerciseActive = exercise['active'] == true;
        _activeExerciseType = exercise['exercise_type']?.toString();
        _exerciseError = exercise['error']?.toString();
        final exerciseHr = (exercise['heart_rate_bpm'] as num?)?.round();
        final exerciseHrAt = DateTime.tryParse('${exercise['heart_rate_at']}');
        final exerciseHrIsFresh =
            exerciseHrAt != null &&
            DateTime.now().difference(exerciseHrAt).inMinutes < 2;
        _exerciseHr = exerciseHrIsFresh && exerciseHr != null && exerciseHr > 0
            ? exerciseHr
            : null;
      });
    } catch (_) {
      // The screen can still be used to retry monitoring setup.
    }
  }

  Future<void> _startExercise(String type) async {
    setState(() {
      _sendState = _WatchSendState.sending;
      _exerciseError = null;
    });
    try {
      await NativeHealthBridge.requestWearExercisePermissions();
      await NativeHealthBridge.startWearExercise(exerciseType: type);
      for (var attempt = 0; attempt < 15; attempt++) {
        await Future<void>.delayed(const Duration(milliseconds: 300));
        await _refreshHealthStatus();
        if (_exerciseActive || _exerciseError != null) break;
      }
      if (!mounted) return;
      setState(() {
        _sendState = _exerciseActive
            ? _WatchSendState.sent
            : _WatchSendState.failed;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _sendState = _WatchSendState.failed);
    }
  }

  bool _supportsExercise(String type) => _exerciseTypes.any(
    (exercise) => '${exercise['type']}'.toUpperCase() == type,
  );

  Future<void> _stopExercise() async {
    setState(() => _sendState = _WatchSendState.sending);
    try {
      await NativeHealthBridge.stopWearExercise();
      await _refreshHealthStatus();
      if (!mounted) return;
      setState(() => _sendState = _WatchSendState.sent);
    } catch (_) {
      if (!mounted) return;
      setState(() => _sendState = _WatchSendState.failed);
    }
  }

  Future<void> _refreshCapabilities() async {
    try {
      final result = await NativeHealthBridge.getWearHealthCapabilities();
      final exerciseTypes = (result['exercise_types'] as List? ?? const [])
          .whereType<Map>()
          .map((item) => item.cast<String, dynamic>())
          .toList();
      final passiveDataTypes =
          (result['passive_data_types'] as List? ?? const [])
              .whereType<String>()
              .toList();
      if (!mounted) return;
      setState(() {
        _exerciseTypes = exerciseTypes;
        _passiveDataTypes = passiveDataTypes;
      });
    } catch (_) {
      // Capability discovery is informative; it must not block watch controls.
    }
  }

  Future<void> _showCapabilities() async {
    final uz = widget.isUzbek;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
          children: [
            Text(
              uz ? 'Soat imkoniyatlari' : 'Возможности часов',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            Text(uz ? 'Doimiy kuzatuv' : 'Фоновый мониторинг'),
            Text(
              _passiveDataTypes.isEmpty
                  ? (uz ? 'Ma’lumot topilmadi' : 'Данные не найдены')
                  : _passiveDataTypes.join(', '),
            ),
            const SizedBox(height: 16),
            Text(uz ? 'Mashq turlari' : 'Типы тренировок'),
            if (_exerciseTypes.isEmpty)
              Text(uz ? 'Qo‘llab-quvvatlanmaydi' : 'Не поддерживается'),
            for (final exercise in _exerciseTypes)
              ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                title: Text('${exercise['type']}'),
                subtitle: Text(
                  (exercise['data_types'] as List? ?? const []).join(', '),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _syncHealthStreams() async {
    setState(() => _sendState = _WatchSendState.sending);
    try {
      final platform = await NativeHealthBridge.getHealthPlatformStatus();
      if (platform['wear_os_device'] == true) {
        await NativeHealthBridge.startWearHealthMonitoring();
      } else {
        if (_deviceToken == null || _deviceToken!.isEmpty) {
          throw StateError('Device enrollment is required before health sync.');
        }
        final permissionResult =
            await NativeHealthBridge.requestHealthDataPermissions();
        final canReadHealthData =
            permissionResult['all_granted'] == true ||
            (platform['healthkit_available'] == true &&
                permissionResult['request_completed'] == true);
        if (canReadHealthData) {
          await NativeHealthBridge.syncRecentHealthData(
            deviceToken: _deviceToken!,
            hours: 24,
          );
        }
      }
      if (_battery >= 0 && _deviceToken != null && _deviceToken!.isNotEmpty) {
        try {
          await ApiService.ingestHealthData(
            deviceToken: _deviceToken!,
            batch: HealthDataBatch(
              batchId: NativeHealthBridge.newBatchId(),
              source: HealthDataSource.wearHealthServices,
              samples: [
                HealthSample(
                  metric: 'battery_pct',
                  recordedAt: DateTime.now(),
                  valueNum: _battery.toDouble(),
                  unit: '%',
                  quality: 1.0,
                ),
              ],
            ),
          );
        } catch (_) {}
      }
      final uploaded = _deviceToken == null || _deviceToken!.isEmpty
          ? 0
          : await NativeHealthBridge.syncQueuedWearData(
              deviceToken: _deviceToken!,
            );
      await _refreshHealthStatus();
      if (!mounted) return;
      setState(() {
        _sentCount += uploaded;
        _sendState = _WatchSendState.sent;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _sendState = _WatchSendState.failed;
      });
    }
  }

  Future<void> _pairDevice() async {
    final deviceIdController = TextEditingController();
    final codeController = TextEditingController();
    final pair = await showDialog<(String, String)>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          widget.isUzbek ? 'Qurilmani bog‘lash' : 'Привязать устройство',
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: deviceIdController,
              decoration: InputDecoration(
                labelText: widget.isUzbek ? 'Qurilma ID' : 'ID устройства',
              ),
              autocorrect: false,
            ),
            TextField(
              controller: codeController,
              decoration: InputDecoration(
                labelText: widget.isUzbek ? '6 xonali kod' : 'Код из 6 цифр',
              ),
              keyboardType: TextInputType.number,
              maxLength: 6,
              autocorrect: false,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(widget.isUzbek ? 'Bekor' : 'Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, (
              deviceIdController.text.trim(),
              codeController.text.trim(),
            )),
            child: Text(widget.isUzbek ? 'Bog‘lash' : 'Привязать'),
          ),
        ],
      ),
    );
    deviceIdController.dispose();
    codeController.dispose();
    if (pair == null || !mounted) return;

    setState(() => _sendState = _WatchSendState.sending);
    try {
      final token = await ApiService.claimDeviceEnrollment(
        deviceId: pair.$1,
        code: pair.$2,
      );
      await DeviceCredentialStore.save(token);
      if (!mounted) return;
      setState(() {
        _deviceToken = token;
        _sendState = _WatchSendState.sent;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _sendState = _WatchSendState.failed);
    }
  }

  void _startSosCountdown() {
    final configured =
        _patientId.isNotEmpty || (_deviceToken?.isNotEmpty ?? false);
    if (!configured || _sosCountdown > 0) return;
    setState(() => _sosCountdown = 5);
    _sosTimer?.cancel();
    _sosTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      if (!mounted) return;
      if (_sosCountdown <= 1) {
        timer.cancel();
        setState(() => _sosCountdown = 0);
        await _dispatchSos();
        return;
      }
      setState(() => _sosCountdown--);
    });
  }

  Future<void> _dispatchSos() async {
    bool dispatched = false;
    if (_deviceToken != null && _deviceToken!.isNotEmpty) {
      dispatched = await ApiService.triggerDeviceSos(
        deviceToken: _deviceToken!,
        source: 'watch_button',
      );
    }
    if (!dispatched && _patientId.isNotEmpty) {
      dispatched = await ApiService.triggerSos(
        patientId: _patientId,
        reason: 'Flutter Watch SOS',
      );
    }
    // If online delivery failed or offline, persist to local outbox
    if (!dispatched) {
      try {
        final emergencyBatch = HealthDataBatch(
          batchId: NativeHealthBridge.newBatchId(),
          source: HealthDataSource.wearHealthServices,
          samples: [
            HealthSample(
              metric: 'fall_detected',
              recordedAt: DateTime.now(),
              valueText: 'manual_sos_trigger',
              quality: 1.0,
              metadata: {'source': 'watch_sos_button', 'offline': true},
            ),
            if (_hr != null)
              HealthSample(
                metric: 'heart_rate_bpm',
                recordedAt: DateTime.now(),
                valueNum: _hr!.toDouble(),
                unit: 'bpm',
              ),
            if (_battery >= 0)
              HealthSample(
                metric: 'battery_pct',
                recordedAt: DateTime.now(),
                valueNum: _battery.toDouble(),
                unit: '%',
              ),
          ],
          metadata: {
            'emergency_sos': true,
            'dispatched_at': DateTime.now().toIso8601String(),
          },
        );
        await NativeHealthBridge.enqueueWearDataBatch(emergencyBatch);
      } catch (_) {}
    }
  }

  @override
  Widget build(BuildContext context) {
    final uz = widget.isUzbek;
    final configured =
        _patientId.isNotEmpty || (_deviceToken?.isNotEmpty ?? false);
    final statusText = switch (_sendState) {
      _WatchSendState.idle => uz ? 'Tayyor' : 'Готово',
      _WatchSendState.sending => uz ? 'Yuborilmoqda' : 'Отправка',
      _WatchSendState.sent => uz ? 'Monitoring yoqilgan' : 'Мониторинг включен',
      _WatchSendState.failed => uz ? 'Xatolik' : 'Ошибка',
    };

    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      body: SafeArea(
        child: Center(
          child: AspectRatio(
            aspectRatio: 1,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF0F172A),
                  border: Border.all(color: const Color(0xFF1E293B), width: 3),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '${_now.hour.toString().padLeft(2, '0')}:${_now.minute.toString().padLeft(2, '0')}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 34,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        configured
                            ? statusText
                            : (uz ? 'Enroll kerak' : 'Нужна привязка'),
                        style: TextStyle(
                          color: configured
                              ? const Color(0xFF38BDF8)
                              : const Color(0xFFF97316),
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 18),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.favorite_rounded,
                            color: Color(0xFFEF4444),
                            size: 28,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _hr?.toString() ?? '--',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 42,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Text(
                            'bpm',
                            style: TextStyle(color: Color(0xFF94A3B8)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        alignment: WrapAlignment.center,
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _Pill(
                            icon: Icons.battery_5_bar_rounded,
                            text: _battery >= 0 ? '$_battery%' : '--%',
                            iconColor: _battery >= 0 && _battery < 20
                                ? const Color(0xFFEF4444)
                                : null,
                          ),
                          _Pill(
                            icon: Icons.watch_rounded,
                            text: _hr == null ? 'NO DATA' : 'LIVE',
                          ),
                          if (_spo2 != null)
                            _Pill(
                              icon: Icons.air_rounded,
                              text: '$_spo2%',
                              textColor: _spo2! < 92
                                  ? const Color(0xFFEF4444)
                                  : const Color(0xFF38BDF8),
                              iconColor: _spo2! < 92
                                  ? const Color(0xFFEF4444)
                                  : const Color(0xFF38BDF8),
                            ),
                          if (_skinTemp != null)
                            _Pill(
                              icon: Icons.thermostat_rounded,
                              text: '${_skinTemp!.toStringAsFixed(1)}°C',
                              textColor: const Color(0xFFF59E0B),
                              iconColor: const Color(0xFFF59E0B),
                            ),
                          _Pill(
                            icon: Icons.directions_walk_rounded,
                            text: _dailySteps?.toString() ?? '--',
                          ),
                          if (_sleepState != null)
                            _Pill(
                              icon: Icons.bedtime_rounded,
                              text: _sleepState!.toUpperCase(),
                              textColor: const Color(0xFFA78BFA),
                              iconColor: const Color(0xFFA78BFA),
                            ),
                          _Pill(
                            icon: Icons.cloud_upload_rounded,
                            text: '$_sentCount',
                          ),
                          if (_exerciseTypes.isNotEmpty)
                            _Pill(
                              icon: Icons.fitness_center_rounded,
                              text: '${_exerciseTypes.length}',
                            ),
                        ],
                      ),
                      if (_exerciseTypes.isNotEmpty ||
                          _passiveDataTypes.isNotEmpty)
                        IconButton(
                          tooltip: uz
                              ? 'Soat imkoniyatlari'
                              : 'Возможности часов',
                          onPressed: _showCapabilities,
                          icon: const Icon(
                            Icons.sensors_rounded,
                            color: Color(0xFF38BDF8),
                          ),
                        ),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton(
                              onPressed: configured ? _syncHealthStreams : null,
                              style: FilledButton.styleFrom(
                                backgroundColor: const Color(0xFF0284C7),
                                foregroundColor: Colors.white,
                              ),
                              child: const Icon(Icons.sync_rounded, size: 20),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _exerciseActive
                                ? FilledButton(
                                    onPressed: _stopExercise,
                                    style: FilledButton.styleFrom(
                                      backgroundColor: const Color(0xFFB45309),
                                      foregroundColor: Colors.white,
                                    ),
                                    child: const Icon(
                                      Icons.stop_rounded,
                                      size: 20,
                                    ),
                                  )
                                : PopupMenuButton<String>(
                                    tooltip: uz
                                        ? 'Mashqni boshlash'
                                        : 'Начать тренировку',
                                    onSelected: _startExercise,
                                    itemBuilder: (context) => [
                                      PopupMenuItem(
                                        value: 'WALKING',
                                        enabled: _supportsExercise('WALKING'),
                                        child: Text(uz ? 'Yurish' : 'Ходьба'),
                                      ),
                                      PopupMenuItem(
                                        value: 'RUNNING',
                                        enabled: _supportsExercise('RUNNING'),
                                        child: Text(uz ? 'Yugurish' : 'Бег'),
                                      ),
                                    ],
                                    child: Container(
                                      height: 44,
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF047857),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: const Icon(
                                        Icons.fitness_center_rounded,
                                        color: Colors.white,
                                        size: 20,
                                      ),
                                    ),
                                  ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: FilledButton(
                              onPressed: configured ? _startSosCountdown : null,
                              style: FilledButton.styleFrom(
                                backgroundColor: const Color(0xFFDC2626),
                                foregroundColor: Colors.white,
                              ),
                              child: Text(
                                _sosCountdown > 0 ? '$_sosCountdown' : 'SOS',
                              ),
                            ),
                          ),
                        ],
                      ),
                      if (_exerciseActive)
                        Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(
                            '${_activeExerciseType ?? 'WORKOUT'}${_exerciseHr == null ? '' : ' · $_exerciseHr bpm'}',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Color(0xFF6EE7B7),
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      if (_exerciseError != null && !_exerciseActive)
                        Text(
                          _exerciseError!,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Color(0xFFFCA5A5),
                            fontSize: 9,
                          ),
                        ),
                      if (_deviceToken == null || _deviceToken!.isEmpty)
                        TextButton(
                          onPressed: _pairDevice,
                          child: Text(
                            uz ? 'Qurilmani bog‘lash' : 'Привязать устройство',
                          ),
                        ),
                      const SizedBox(height: 8),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final IconData icon;
  final String text;
  final Color? textColor;
  final Color? iconColor;

  const _Pill({
    required this.icon,
    required this.text,
    this.textColor,
    this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: iconColor ?? const Color(0xFF94A3B8), size: 13),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: textColor ?? Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

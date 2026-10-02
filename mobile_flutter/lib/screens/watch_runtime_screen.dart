import 'dart:async';

import 'package:flutter/material.dart';

import '../api/api_service.dart';
import '../services/device_credential_store.dart';
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
  int _battery = -1;
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
      if (!mounted) return;
      final latestAt = DateTime.tryParse('${status['latest_heart_rate_at']}');
      final bpm = (status['latest_heart_rate_bpm'] as num?)?.round();
      final isFresh =
          latestAt != null &&
          DateTime.now().difference(latestAt).inMinutes <= 10;
      final stepsAt = DateTime.tryParse('${status['latest_daily_steps_at']}');
      final stepsValue = (status['latest_daily_steps'] as num?)?.toInt();
      final stepsAreFresh =
          stepsAt != null &&
          DateTime.now().difference(stepsAt).inHours <= 30 &&
          stepsValue != null &&
          stepsValue >= 0;
      setState(() {
        _hr = isFresh ? bpm : null;
        _dailySteps = stepsAreFresh ? stepsValue : null;
        _battery = (status['battery_pct'] as num?)?.toInt() ?? -1;
      });
    } catch (_) {
      // The screen can still be used to retry monitoring setup.
    }
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
    if (_patientId.isEmpty || _sosCountdown > 0) return;
    setState(() => _sosCountdown = 5);
    _sosTimer?.cancel();
    _sosTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      if (!mounted) return;
      if (_sosCountdown <= 1) {
        timer.cancel();
        setState(() => _sosCountdown = 0);
        await ApiService.triggerSos(
          patientId: _patientId,
          reason: 'Flutter Watch SOS',
        );
        return;
      }
      setState(() => _sosCountdown--);
    });
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
                          ),
                          _Pill(
                            icon: Icons.watch_rounded,
                            text: _hr == null ? 'NO DATA' : 'LIVE',
                          ),
                          _Pill(
                            icon: Icons.directions_walk_rounded,
                            text: _dailySteps?.toString() ?? '--',
                          ),
                          _Pill(
                            icon: Icons.cloud_upload_rounded,
                            text: '$_sentCount',
                          ),
                        ],
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

  const _Pill({required this.icon, required this.text});

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
          Icon(icon, color: const Color(0xFF94A3B8), size: 13),
          const SizedBox(width: 4),
          Text(
            text,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

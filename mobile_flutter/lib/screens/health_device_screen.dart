import 'package:flutter/material.dart';

import '../api/api_service.dart';
import '../services/device_credential_store.dart';
import '../services/native_health_bridge.dart';

class HealthDeviceScreen extends StatefulWidget {
  final bool isUzbek;

  const HealthDeviceScreen({super.key, required this.isUzbek});

  @override
  State<HealthDeviceScreen> createState() => _HealthDeviceScreenState();
}

class _HealthDeviceScreenState extends State<HealthDeviceScreen> {
  final _deviceIdController = TextEditingController();
  final _codeController = TextEditingController();

  Map<String, dynamic> _platform = const {};
  String? _deviceToken;
  bool _loading = false;
  bool _pairing = false;
  bool _showPairForm = true;
  String? _message;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _loadCredential();
    _refreshPlatform();
  }

  @override
  void dispose() {
    _deviceIdController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  Future<void> _loadCredential() async {
    try {
      final token = await DeviceCredentialStore.read();
      if (mounted) {
        setState(() {
          _deviceToken = token;
          _showPairForm = token == null || token.isEmpty;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _deviceToken = null;
          _showPairForm = true;
          _failed = true;
          _message = widget.isUzbek
              ? 'Saqlangan qurilma kalitini ochib bo‘lmadi. Qayta bog‘lang.'
              : 'Не удалось открыть сохранённый ключ. Привяжите устройство заново.';
        });
      }
    }
  }

  Future<void> _refreshPlatform() async {
    try {
      final platform = await NativeHealthBridge.getHealthPlatformStatus();
      if (mounted) setState(() => _platform = platform);
    } catch (_) {
      if (mounted) setState(() => _platform = const {});
    }
  }

  Future<void> _sync() async {
    final token = _deviceToken;
    if (token == null || token.isEmpty || _loading) return;
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final platform = await NativeHealthBridge.getHealthPlatformStatus();
      if (mounted) setState(() => _platform = platform);
      final permission =
          await NativeHealthBridge.requestHealthDataPermissions();
      // Sync whatever the person allowed; declined record types are skipped
      // by the native reader instead of blocking every other type.
      final granted =
          permission['all_granted'] == true ||
          (permission['granted'] is List &&
              (permission['granted'] as List).isNotEmpty) ||
          (platform['healthkit_available'] == true &&
              permission['request_completed'] == true);
      if (!granted) {
        throw StateError('Health data access was not granted.');
      }
      await NativeHealthBridge.syncRecentHealthData(
        deviceToken: token,
        hours: 24,
      );
      final queued = await NativeHealthBridge.syncQueuedWearData(
        deviceToken: token,
      );
      if (mounted) {
        setState(() {
          _message = widget.isUzbek
              ? 'Sog‘liq ma’lumotlari sinxronlandi. Navbatdan: $queued ta.'
              : 'Данные здоровья синхронизированы. Из очереди: $queued.';
          _failed = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _message = widget.isUzbek
              ? 'Sinxronlash bajarilmadi. Ruxsat va internetni tekshiring.'
              : 'Не удалось синхронизировать. Проверьте доступ и интернет.';
          _failed = true;
        });
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _pairDevice() async {
    if (_pairing) return;
    setState(() {
      _pairing = true;
      _message = null;
    });
    try {
      final token = await ApiService.claimDeviceEnrollment(
        deviceId: _deviceIdController.text.trim(),
        code: _codeController.text.trim(),
      );
      await DeviceCredentialStore.save(token);
      if (mounted) {
        setState(() {
          _deviceToken = token;
          _showPairForm = false;
          _codeController.clear();
          _failed = false;
          _message = widget.isUzbek
              ? 'Qurilma muvaffaqiyatli bog‘landi.'
              : 'Устройство успешно привязано.';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _failed = true;
          _message = widget.isUzbek
              ? 'Bog‘lash bajarilmadi. Qurilma ID va bir martalik kodni tekshiring.'
              : 'Не удалось привязать. Проверьте ID устройства и одноразовый код.';
        });
      }
    } finally {
      if (mounted) setState(() => _pairing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final uz = widget.isUzbek;
    final isAvailable =
        _platform['healthkit_available'] == true ||
        _platform['health_connect_available'] == true;
    final provider = _platform['health_platform'] == 'healthkit'
        ? 'Apple Health'
        : 'Health Connect';

    return Scaffold(
      appBar: AppBar(title: const Text('WMAX')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: ListView(
            padding: const EdgeInsets.all(24),
            shrinkWrap: true,
            children: [
              Icon(
                isAvailable
                    ? Icons.health_and_safety
                    : Icons.health_and_safety_outlined,
                size: 42,
                color: isAvailable ? const Color(0xFF0284C7) : Colors.grey,
              ),
              const SizedBox(height: 16),
              Text(
                isAvailable
                    ? provider
                    : (uz
                          ? 'Sog‘liq platformasi mavjud emas'
                          : 'Платформа здоровья недоступна'),
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                uz
                    ? 'Oxirgi 24 soatdagi ruxsat berilgan ko‘rsatkichlar bemor qurilmasi hisobiga uzatiladi.'
                    : 'Разрешённые показатели за последние 24 часа будут переданы в учётную запись устройства пациента.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 24),
              if (_showPairForm || _deviceToken == null) ...[
                TextField(
                  controller: _deviceIdController,
                  autocorrect: false,
                  decoration: InputDecoration(
                    labelText: uz ? 'Qurilma ID' : 'ID устройства',
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _codeController,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  autocorrect: false,
                  decoration: InputDecoration(
                    labelText: uz ? 'Bir martalik kod' : 'Одноразовый код',
                    border: const OutlineInputBorder(),
                  ),
                ),
                FilledButton.icon(
                  onPressed: !_pairing ? _pairDevice : null,
                  icon: _pairing
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.link),
                  label: Text(
                    uz ? 'Qurilmani bog‘lash' : 'Привязать устройство',
                  ),
                ),
              ] else ...[
                Text(
                  uz ? 'Qurilma bog‘langan' : 'Устройство привязано',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Color(0xFF166534)),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: isAvailable && !_loading ? _sync : null,
                  icon: _loading
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.sync),
                  label: Text(uz ? 'Sinxronlash' : 'Синхронизировать'),
                ),
                TextButton(
                  onPressed: () => setState(() => _showPairForm = true),
                  child: Text(
                    uz
                        ? 'Qurilmani qayta bog‘lash'
                        : 'Перепривязать устройство',
                  ),
                ),
              ],
              if ((_deviceToken == null || _showPairForm) && !isAvailable) ...[
                const SizedBox(height: 12),
                Text(
                  uz
                      ? 'Sog‘liq platformasi aniqlanmadi.'
                      : 'Платформа здоровья не обнаружена.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
              if (_message case final message?) ...[
                const SizedBox(height: 16),
                Text(
                  message,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: _failed
                        ? Theme.of(context).colorScheme.error
                        : const Color(0xFF166534),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

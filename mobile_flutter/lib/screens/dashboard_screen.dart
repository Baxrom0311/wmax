import 'dart:async';
import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/session_service.dart';
import '../api/api_service.dart';
import '../widgets/vitals_card.dart';
import '../widgets/watch_sheet.dart';
import '../widgets/language_selector.dart';
import '../services/wear_bridge_service.dart';

class CaregiverMainDashboard extends StatefulWidget {
  final bool isUzbek;
  final List<PatientSummary> initialPatients;
  final VoidCallback onToggleLang;
  final ValueChanged<bool>? onSelectLang;
  final VoidCallback onLogout;

  const CaregiverMainDashboard({
    super.key,
    required this.isUzbek,
    required this.initialPatients,
    required this.onToggleLang,
    this.onSelectLang,
    required this.onLogout,
  });

  @override
  State<CaregiverMainDashboard> createState() => _CaregiverMainDashboardState();
}

class _CaregiverMainDashboardState extends State<CaregiverMainDashboard> {
  int _currentTabIndex = 0;
  late List<PatientSummary> _patients;
  int _selectedPatientIndex = 0;

  RelativePatientView? _currentPatientView;
  bool _isLoadingView = false;

  // Local alert notifications
  final List<Map<String, dynamic>> _alerts = [];

  Timer? _autoRefreshTimer;
  final WearBridgeService _wearBridge = WearBridgeService();
  bool _wearConnected = false;

  @override
  void initState() {
    super.initState();
    _patients = widget.initialPatients.isNotEmpty
        ? widget.initialPatients
        : [
            PatientSummary(
              id: "00000000-0000-0000-0000-000000000001",
              fullName: "Otabek Ro'zmetov",
              relationship: "Otangiz",
              accessToken: "tok_otabek",
              level: AlertLevel.amber,
              diagnosis: "YIK, Stenokardiya FK III, SYuYe IIB",
              age: 68,
            ),
            PatientSummary(
              id: "00000000-0000-0000-0000-000000000002",
              fullName: "Gulnora Matyoqubova",
              relationship: "Onangiz",
              accessToken: "tok_gulnora",
              level: AlertLevel.green,
              diagnosis: "Arterial gipertoniya II bosqich",
              age: 65,
            ),
          ];

    _fetchCurrentPatientData();
    _startWearBridge();

    // Auto-refresh telemetry every 15 seconds
    _autoRefreshTimer = Timer.periodic(const Duration(seconds: 15), (timer) {
      if (mounted) {
        _fetchCurrentPatientData(silent: true);
      }
    });
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    _wearBridge.dispose();
    super.dispose();
  }

  Future<void> _startWearBridge() async {
    try {
      final nodes = await _wearBridge.connectedNodes();
      if (!mounted) return;
      setState(() {
        _wearConnected = nodes.isNotEmpty;
      });
      _wearBridge.start(
        patientId: currentPatient.id,
        deviceId: _currentPatientView?.deviceModel ?? 'WMAX-WATCH-20260919',
        onError: (_) {},
      );
    } catch (_) {
      if (mounted) {
        setState(() {
          _wearConnected = false;
        });
      }
    }
  }

  PatientSummary get currentPatient =>
      _patients.isNotEmpty ? _patients[_selectedPatientIndex] : _patients.first;

  Future<void> _fetchCurrentPatientData({bool silent = false}) async {
    if (_patients.isEmpty) return;

    if (!silent) {
      setState(() => _isLoadingView = true);
    }

    final p = currentPatient;
    try {
      final view = await ApiService.fetchPatientView(
        patientAccessToken: p.accessToken,
        patientId: p.id,
        patientName: p.fullName,
      );

      if (mounted) {
        setState(() {
          _currentPatientView = view;
          _isLoadingView = false;
          // Synchronize alerts from live backend
          for (final a in view.alerts) {
            final exists = _alerts.any((item) => item['id'] == a.id);
            if (!exists) {
              _alerts.insert(0, {
                'id': a.id,
                'titleUz': a.level == AlertLevel.red
                    ? '🚨 Kritik Signal (Z-Score: ${a.compositeScore.toStringAsFixed(1)})'
                    : '⚠️ Klinik Ogohlantirish',
                'titleRu': a.level == AlertLevel.red
                    ? '🚨 Критический сигнал (Z-Score: ${a.compositeScore.toStringAsFixed(1)})'
                    : '⚠️ Предупреждение',
                'descUz': '${p.fullName} bo\'yicha signal: ${a.reason}',
                'descRu': 'Сигнал по ${p.fullName}: ${a.reason}',
                'time':
                    '${a.ts.hour.toString().padLeft(2, '0')}:${a.ts.minute.toString().padLeft(2, '0')}',
                'isCritical': a.level == AlertLevel.red,
              });
            }
          }
        });
      }
    } catch (_) {
      if (mounted && !silent) {
        setState(() {
          _currentPatientView = ApiService.generateFallbackView(
            p.id,
            p.fullName,
          );
          _isLoadingView = false;
        });
      }
    }
  }

  void _onSelectPatient(int index) {
    if (_selectedPatientIndex == index) return;
    setState(() {
      _selectedPatientIndex = index;
    });
    _fetchCurrentPatientData();
    _startWearBridge();
  }

  // Bluetooth Pairing Modal
  void _openBluetoothModal() {
    _startWearBridge().then((_) {
      if (!mounted) return;
      final message = _wearConnected
          ? (widget.isUzbek
                ? 'Wear OS soat ulandi, telemetriya tinglanmoqda.'
                : 'Wear OS подключён, телеметрия активна.')
          : (widget.isUzbek
                ? 'Soat topilmadi. Wear OS ilovasida pairingni tekshiring.'
                : 'Часы не найдены. Проверьте pairing в Wear OS.');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: _wearConnected
              ? const Color(0xFF0D9488)
              : const Color(0xFFDC2626),
        ),
      );
    });
  }

  void _openWatchSimulatorModal() {
    final p = currentPatient;
    final view = _currentPatientView;
    final hr = (view?.vitals.hr ?? 76).toInt();
    final spo2 = (view?.vitals.spo2 ?? 97).toInt();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => WearOsWatchSheet(
        isUzbek: widget.isUzbek,
        patientName: p.fullName,
        currentHr: hr,
        currentSpo2: spo2,
        onTriggerSos: (source) => _triggerSos("Soatdan bosilgan SOS"),
      ),
    );
  }

  void _triggerSos([String? reason]) async {
    final p = currentPatient;
    await ApiService.triggerSos(
      patientId: p.id,
      lat: _currentPatientView?.lat ?? 41.556,
      lon: _currentPatientView?.lon ?? 60.631,
      reason: reason ?? "Qarovchi mobil ilovasidan SOS signali berildi",
    );

    setState(() {
      _alerts.insert(0, {
        "titleUz": "🚨 Shoshilinch SOS chaqiruvi!",
        "titleRu": "🚨 Экстренный SOS вызов!",
        "descUz":
            "${p.fullName} uchun 103 dispetcher va navbatchi shifokorga signal uzatildi.",
        "descRu":
            "Сигнал для ${p.fullName} передан в диспетчерскую 103 и дежурному врачу.",
        "time": "Hozirgina",
        "isCritical": true,
      });
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            widget.isUzbek
                ? "🚨 SOS qabul qilindi! Shifokor va 103 ga yetkazildi."
                : "🚨 SOS принят! Сигнал передан врачу и 103.",
          ),
          backgroundColor: const Color(0xFFDC2626),
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool uz = widget.isUzbek;

    final pages = [
      _buildMonitoringView(uz),
      _buildDevicesView(uz),
      _buildAlertsView(uz),
      _buildProfileView(uz),
    ];

    return Scaffold(
      extendBody: true,
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        titleSpacing: 16,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF0284C7).withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.favorite_rounded,
                color: Color(0xFF0284C7),
                size: 18,
              ),
            ),
            const SizedBox(width: 8),
            const Text(
              'WMAX',
              style: TextStyle(
                color: Color(0xFF0F172A),
                fontWeight: FontWeight.w900,
                fontSize: 18,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(
              Icons.refresh_rounded,
              color: Color(0xFF64748B),
              size: 22,
            ),
            onPressed: () => _fetchCurrentPatientData(),
          ),
          InkWell(
            onTap: _openWatchSimulatorModal,
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              margin: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF0284C7).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: const Color(0xFF0284C7).withValues(alpha: 0.25),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.watch_rounded,
                    color: Color(0xFF0284C7),
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    uz ? "SOAT" : "ЧАСЫ",
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      color: Color(0xFF0284C7),
                      fontSize: 11,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          LanguageSelectorBadge(
            isUzbek: uz,
            onSelectLang: (selectedUz) {
              if (widget.onSelectLang != null) {
                widget.onSelectLang!(selectedUz);
              } else if (selectedUz != uz) {
                widget.onToggleLang();
              }
            },
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: SafeArea(
        top: false,
        bottom: false,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 580),
            child: Column(
              children: [
                _buildPatientSwitcher(uz),
                Expanded(
                  child: IndexedStack(index: _currentTabIndex, children: pages),
                ),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        bottom: true,
        child: _buildCurvedNavBar(uz),
      ),
    );
  }

  Widget _buildPatientSwitcher(bool uz) {
    if (_patients.isEmpty) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 6),
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        children: List.generate(_patients.length, (index) {
          final p = _patients[index];
          final bool isSelected = index == _selectedPatientIndex;
          return Expanded(
            child: GestureDetector(
              onTap: () => _onSelectPatient(index),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
                decoration: BoxDecoration(
                  color: isSelected
                      ? const Color(0xFF0284C7)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      index == 0
                          ? Icons.person_rounded
                          : Icons.person_outline_rounded,
                      color: isSelected
                          ? Colors.white
                          : const Color(0xFF64748B),
                      size: 16,
                    ),
                    const SizedBox(width: 6),
                    Flexible(
                      child: Text(
                        "${p.fullName.split(' ').first} (${p.relationship})",
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 12.5,
                          fontWeight: isSelected
                              ? FontWeight.bold
                              : FontWeight.w500,
                          color: isSelected
                              ? Colors.white
                              : const Color(0xFF475569),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildMonitoringView(bool uz) {
    if (_isLoadingView && _currentPatientView == null) {
      return const Center(
        child: CircularProgressIndicator(
          strokeWidth: 2.5,
          color: Color(0xFF0284C7),
        ),
      );
    }

    final p = currentPatient;
    final view =
        _currentPatientView ??
        ApiService.generateFallbackView(p.id, p.fullName);
    final vitals = view.vitals;
    final alertLevel = view.level;

    Color badgeBg;
    Color badgeBorder;
    Color badgeText;
    String badgeTitle;

    switch (alertLevel) {
      case AlertLevel.red:
        badgeBg = const Color(0xFFFEF2F2);
        badgeBorder = const Color(0xFFFECACA);
        badgeText = const Color(0xFFB91C1C);
        badgeTitle = uz
            ? "I Daraja (Shoshilinch dekompensatsiya)"
            : "I Уровень (Острая декомпенсация)";
        break;
      case AlertLevel.amber:
        badgeBg = const Color(0xFFFFFBEB);
        badgeBorder = const Color(0xFFFDE68A);
        badgeText = const Color(0xFFB45309);
        badgeTitle = uz
            ? "II Daraja (Klinik kuzatuv)"
            : "II Уровень (Наблюдение)";
        break;
      case AlertLevel.green:
        badgeBg = const Color(0xFFF0FDF4);
        badgeBorder = const Color(0xFFBBF7D0);
        badgeText = const Color(0xFF166534);
        badgeTitle = uz
            ? "III Daraja (Barqaror remissiya)"
            : "III Уровень (Стабильно)";
        break;
      case AlertLevel.noData:
        badgeBg = const Color(0xFFF8FAFC);
        badgeBorder = const Color(0xFFE2E8F0);
        badgeText = const Color(0xFF64748B);
        badgeTitle = uz ? "Telemetriya uzilgan" : "Нет связи с датчиком";
        break;
    }

    return RefreshIndicator(
      onRefresh: () => _fetchCurrentPatientData(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 90),
        children: [
          // Clinical status banner
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: badgeBg,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: badgeBorder),
            ),
            child: Row(
              children: [
                Icon(
                  alertLevel == AlertLevel.red
                      ? Icons.error_rounded
                      : alertLevel == AlertLevel.amber
                      ? Icons.warning_rounded
                      : alertLevel == AlertLevel.green
                      ? Icons.check_circle_rounded
                      : Icons.cloud_off_rounded,
                  color: badgeText,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    badgeTitle,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: badgeText,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Patient Summary Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      p.fullName,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 17,
                        color: Color(0xFF0F172A),
                      ),
                    ),
                    Text(
                      "${p.age} ${uz ? 'yosh' : 'лет'}",
                      style: const TextStyle(
                        color: Color(0xFF64748B),
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  p.diagnosis,
                  style: const TextStyle(
                    color: Color(0xFF475569),
                    fontSize: 12.5,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(
                      Icons.location_on_outlined,
                      size: 14,
                      color: Color(0xFF94A3B8),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        view.address,
                        style: const TextStyle(
                          color: Color(0xFF94A3B8),
                          fontSize: 11,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // 4 Live Vitals Cards (Grid)
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            childAspectRatio: 1.45,
            children: [
              MetricCard(
                title: uz ? 'Puls (Yurak)' : 'Пульс',
                value: vitals.hr != null ? '${vitals.hr!.toInt()}' : '--',
                unit: 'bpm',
                icon: Icons.favorite_rounded,
                color: const Color(0xFFEF4444),
                status: (vitals.hr != null && vitals.hr! > 100)
                    ? (uz ? 'Taxikardiya' : 'Тахикардия')
                    : (uz ? 'Normada (60-90)' : 'В норме'),
                isAlert:
                    vitals.hr != null && (vitals.hr! > 100 || vitals.hr! < 55),
              ),
              MetricCard(
                title: uz ? 'Saturatsiya SpO2' : 'Кислород SpO2',
                value: vitals.spo2 != null ? '${vitals.spo2!.toInt()}' : '--',
                unit: '%',
                icon: Icons.air_rounded,
                color: const Color(0xFF0284C7),
                status: (vitals.spo2 != null && vitals.spo2! < 92)
                    ? (uz ? 'Past (Gipoksemiya)' : 'Низкий!')
                    : (uz ? 'Normada (>95%)' : 'В норме'),
                isAlert: vitals.spo2 != null && vitals.spo2! < 92,
              ),
              MetricCard(
                title: uz ? 'Tana harorati' : 'Температура',
                value: vitals.temp != null
                    ? vitals.temp!.toStringAsFixed(1)
                    : '--',
                unit: '°C',
                icon: Icons.thermostat_rounded,
                color: const Color(0xFFF59E0B),
                status: vitals.temp != null
                    ? '${vitals.temp!.toStringAsFixed(1)} °C'
                    : '--',
                isAlert: vitals.temp != null && vitals.temp! > 37.5,
              ),
              MetricCard(
                title: uz ? 'Nafas soni' : 'Частота дыхания',
                value: vitals.rr != null ? '${vitals.rr!.toInt()}' : '--',
                unit: uz ? 'm/daq' : 'в/мин',
                icon: Icons.waves_rounded,
                color: const Color(0xFF10B981),
                status: (vitals.rr != null && vitals.rr! > 22)
                    ? (uz ? 'Tezlashgan' : 'Учащенное')
                    : (uz ? 'Normada (14-18)' : 'В норме'),
                isAlert: vitals.rr != null && vitals.rr! > 22,
              ),
            ],
          ),
          const SizedBox(height: 14),

          // AI Clinical Prognosis & Recommendation
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(
                          Icons.psychology_rounded,
                          color: Color(0xFF0284C7),
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          uz
                              ? "AI Klinik Xulosa & Xavf"
                              : "AI Прогноз & Оценка",
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                            color: Color(0xFF0F172A),
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        color: view.prognosis.riskScore > 50
                            ? const Color(0xFFFEE2E2)
                            : const Color(0xFFF0FDF4),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        "${uz ? 'Xavf' : 'Риск'}: ${view.prognosis.riskScore}%",
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: view.prognosis.riskScore > 50
                              ? const Color(0xFFDC2626)
                              : const Color(0xFF16A34A),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  uz
                      ? view.prognosis.recommendationUz
                      : view.prognosis.recommendationRu,
                  style: const TextStyle(
                    fontSize: 12.5,
                    color: Color(0xFF475569),
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // 7-Day Stability Trend (Sparkline)
          if (view.sparkline.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(
                            Icons.show_chart_rounded,
                            color: Color(0xFF0284C7),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            uz
                                ? "7 Kunlik Barqarorlik Dinamikasi"
                                : "7-Дневная Динамика Состояния",
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 13.5,
                              color: Color(0xFF0F172A),
                            ),
                          ),
                        ],
                      ),
                      Text(
                        uz ? "Oxirgi 7 kun" : "За 7 дней",
                        style: const TextStyle(
                          fontSize: 11,
                          color: Color(0xFF94A3B8),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    height: 62,
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: List.generate(view.sparkline.length, (idx) {
                        final val = view.sparkline[idx].clamp(0.05, 1.0);
                        final isLast = idx == view.sparkline.length - 1;
                        final Color barColor = val > 0.7
                            ? const Color(0xFFEF4444)
                            : val > 0.4
                            ? const Color(0xFFF59E0B)
                            : const Color(0xFF10B981);
                        return Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                Container(
                                  height: 38 * val,
                                  decoration: BoxDecoration(
                                    color: barColor,
                                    borderRadius: BorderRadius.circular(4),
                                    border: isLast
                                        ? Border.all(
                                            color: const Color(0xFF0284C7),
                                            width: 1.5,
                                          )
                                        : null,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  idx == view.sparkline.length - 1
                                      ? (uz ? "Bugun" : "Сегодня")
                                      : "D-${view.sparkline.length - 1 - idx}",
                                  style: TextStyle(
                                    fontSize: 8.5,
                                    fontWeight: isLast
                                        ? FontWeight.bold
                                        : FontWeight.w500,
                                    color: isLast
                                        ? const Color(0xFF0284C7)
                                        : const Color(0xFF94A3B8),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      }),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
          ],

          // Active Clinical Problems
          if (view.problems.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        uz
                            ? "Klinik Chetlanishlar va Anomaliyalar"
                            : "Клинические Отклонения",
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 13.5,
                          color: Color(0xFF1E293B),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF3C7),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          "${view.problems.length} ta",
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFFB45309),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ...view.problems.map((prob) {
                    final bool isCrit =
                        prob.severity == "critical" || prob.severity == "high";
                    return Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isCrit
                            ? const Color(0xFFFEF2F2)
                            : const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: isCrit
                              ? const Color(0xFFFECACA)
                              : const Color(0xFFE2E8F0),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Expanded(
                                child: Text(
                                  prob.title,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 12.5,
                                    color: Color(0xFF0F172A),
                                  ),
                                ),
                              ),
                              if (prob.deviation != null)
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: isCrit
                                        ? const Color(0xFFFEE2E2)
                                        : const Color(0xFFFEF3C7),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    prob.deviation!,
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: isCrit
                                          ? const Color(0xFFDC2626)
                                          : const Color(0xFFD97706),
                                    ),
                                  ),
                                ),
                            ],
                          ),
                          if (prob.baselineRange != null) ...[
                            const SizedBox(height: 3),
                            Text(
                              "${uz ? 'Shaxsiy me\'yor' : 'Норма'}: ${prob.baselineRange} ${prob.currentValue != null ? '• Joriy: ${prob.currentValue}' : ''}",
                              style: const TextStyle(
                                fontSize: 11,
                                color: Color(0xFF64748B),
                              ),
                            ),
                          ],
                          if (prob.detail.isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text(
                              prob.detail,
                              style: const TextStyle(
                                fontSize: 11.5,
                                color: Color(0xFF475569),
                                height: 1.3,
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
            const SizedBox(height: 14),
          ],

          // Emergency SOS & Doctor Action Row
          Row(
            children: [
              Expanded(
                flex: 3,
                child: ElevatedButton.icon(
                  onPressed: () =>
                      _triggerSos("Qarovchi tugmasi orqali tezkor SOS"),
                  icon: const Icon(
                    Icons.sos_rounded,
                    color: Colors.white,
                    size: 22,
                  ),
                  label: Text(
                    uz ? "TEZKOR SOS (103)" : "ЭКСТРЕННЫЙ SOS",
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFDC2626),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                flex: 2,
                child: OutlinedButton.icon(
                  onPressed: () {
                    final doc = view.doctor;
                    showDialog(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: Text(
                          uz ? "Shifokor bilan bog'lanish" : "Связь с врачом",
                        ),
                        content: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              doc?.name ?? "Dr. Alimov Bahrom",
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              doc?.phone ?? "+998 90 123 45 67",
                              style: const TextStyle(
                                fontSize: 13,
                                color: Color(0xFF0284C7),
                              ),
                            ),
                          ],
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(ctx),
                            child: Text(uz ? "Yopish" : "Закрыть"),
                          ),
                          ElevatedButton(
                            onPressed: () {
                              Navigator.pop(ctx);
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    "${doc?.phone ?? '+998 90 123 45 67'} ga qo'ng'iroq qilinmoqda...",
                                  ),
                                ),
                              );
                            },
                            child: Text(uz ? "Qo'ng'iroq" : "Позвонить"),
                          ),
                        ],
                      ),
                    );
                  },
                  icon: const Icon(
                    Icons.phone_rounded,
                    color: Color(0xFF0284C7),
                    size: 18,
                  ),
                  label: Text(
                    uz ? "Shifokor" : "Врач",
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF0284C7),
                    side: const BorderSide(color: Color(0xFFBAE6FD)),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDevicesView(bool uz) {
    final p = currentPatient;
    final view =
        _currentPatientView ??
        ApiService.generateFallbackView(p.id, p.fullName);
    final deviceModel = view.deviceModel;
    final battery = view.deviceBattery;
    final isOnline = _wearConnected;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 90),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE0F2FE),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.watch_rounded,
                      color: Color(0xFF0284C7),
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          deviceModel,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                            color: Color(0xFF0F172A),
                          ),
                        ),
                        Text(
                          isOnline
                              ? (uz
                                    ? "Faol • Wear OS telemetriya ulangan"
                                    : "Активен • Wear OS телеметрия подключена")
                              : (uz
                                    ? "Telemetriya uzilgan"
                                    : "Телеметрия отключена"),
                          style: TextStyle(
                            fontSize: 12,
                            color: isOnline
                                ? const Color(0xFF10B981)
                                : const Color(0xFF94A3B8),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.battery_charging_full_rounded,
                          color: Color(0xFF10B981),
                          size: 16,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          "$battery%",
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const Divider(height: 24, color: Color(0xFFF1F5F9)),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    uz ? "Biriktirilgan bemor:" : "Прикрепленный пациент:",
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF64748B),
                    ),
                  ),
                  Text(
                    p.fullName,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    uz ? "Oxirgi sinxronizatsiya:" : "Синхронизация:",
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF64748B),
                    ),
                  ),
                  const Text(
                    "Bugun, bir necha soniya oldin",
                    style: TextStyle(fontSize: 12, color: Color(0xFF0284C7)),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _openBluetoothModal,
                icon: const Icon(Icons.bluetooth_searching_rounded, size: 18),
                label: Text(uz ? "Soatni qayta ulash" : "Переподключить"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0284C7),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _openWatchSimulatorModal,
                icon: const Icon(Icons.watch_outlined, size: 18),
                label: Text(uz ? "Soat Simulyatori" : "Симулятор"),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF0284C7),
                  side: const BorderSide(color: Color(0xFFBAE6FD)),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildAlertsView(bool uz) {
    if (_alerts.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.notifications_off_outlined,
              size: 48,
              color: Color(0xFF94A3B8),
            ),
            const SizedBox(height: 12),
            Text(
              uz ? "Hech qanday ogohlantirish yo'q" : "Предупреждений нет",
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Color(0xFF475569),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              uz
                  ? "Barcha bemorlar barqaror nazoratda"
                  : "Все пациенты под контролем",
              style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
            ),
          ],
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 90),
      children: [
        ..._alerts.map((alt) {
          final bool crit = alt["isCritical"] == true;
          return Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: crit ? const Color(0xFFFEF2F2) : Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: crit ? const Color(0xFFFECACA) : const Color(0xFFE2E8F0),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  crit
                      ? Icons.warning_amber_rounded
                      : Icons.info_outline_rounded,
                  color: crit
                      ? const Color(0xFFDC2626)
                      : const Color(0xFF0284C7),
                  size: 20,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            uz ? alt["titleUz"] : alt["titleRu"],
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                              color: crit
                                  ? const Color(0xFF991B1B)
                                  : const Color(0xFF0F172A),
                            ),
                          ),
                          Text(
                            alt["time"],
                            style: const TextStyle(
                              fontSize: 11,
                              color: Color(0xFF94A3B8),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        uz ? alt["descUz"] : alt["descRu"],
                        style: TextStyle(
                          fontSize: 12,
                          color: crit
                              ? const Color(0xFF7F1D1D)
                              : const Color(0xFF475569),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  Widget _buildProfileView(bool uz) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 90),
      children: [
        FutureBuilder<String>(
          future: SessionService.getRelativeName(),
          builder: (ctx, snap) {
            final name = snap.data ?? "Qarovchi";
            return Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: Row(
                children: [
                  const CircleAvatar(
                    radius: 24,
                    backgroundColor: Color(0xFFE0F2FE),
                    child: Icon(
                      Icons.person_rounded,
                      color: Color(0xFF0284C7),
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          name,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                            color: Color(0xFF0F172A),
                          ),
                        ),
                        Text(
                          uz
                              ? "Qarovchi (${_patients.length} ta bemor biriktirilgan)"
                              : "Опекун (Прикреплено ${_patients.length} пациентов)",
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF64748B),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          },
        ),
        const SizedBox(height: 14),

        // Shifokor bilan tezkor aloqa
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Row(
            children: [
              const Icon(
                Icons.medical_services_rounded,
                color: Color(0xFF0284C7),
                size: 20,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _currentPatientView?.doctor?.name ?? "Dr. Alimov Bahrom",
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13.5,
                      ),
                    ),
                    Text(
                      uz
                          ? "Kardiolog • ${_currentPatientView?.doctor?.phone ?? '+998 90 123 45 67'}"
                          : "Кардиолог • ${_currentPatientView?.doctor?.phone ?? '+998 90 123 45 67'}",
                      style: const TextStyle(
                        fontSize: 11.5,
                        color: Color(0xFF64748B),
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                onPressed: () {
                  final ph =
                      _currentPatientView?.doctor?.phone ?? "+998 90 123 45 67";
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("$ph ga ulanmoqda...")),
                  );
                },
                icon: const Icon(
                  Icons.phone_rounded,
                  color: Color(0xFF0284C7),
                  size: 20,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        ListTile(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          tileColor: Colors.white,
          leading: const Icon(Icons.language_rounded, color: Color(0xFF0284C7)),
          title: Text(
            uz ? "Dastur tili" : "Язык приложения",
            style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600),
          ),
          trailing: LanguageSelectorBadge(
            isUzbek: uz,
            onSelectLang: (selectedUz) {
              if (widget.onSelectLang != null) {
                widget.onSelectLang!(selectedUz);
              } else if (selectedUz != uz) {
                widget.onToggleLang();
              }
            },
          ),
        ),

        const SizedBox(height: 8),

        ListTile(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          tileColor: Colors.white,
          leading: const Icon(Icons.logout_rounded, color: Color(0xFFDC2626)),
          title: Text(
            uz ? "Tizimdan chiqish" : "Выйти из системы",
            style: const TextStyle(
              fontSize: 13.5,
              fontWeight: FontWeight.w600,
              color: Color(0xFFDC2626),
            ),
          ),
          onTap: widget.onLogout,
        ),
      ],
    );
  }

  Widget _buildCurvedNavBar(bool uz) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      height: 60,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 20,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNavItem(
            0,
            Icons.monitor_heart_rounded,
            uz ? "Monitoring" : "Мониторинг",
          ),
          _buildNavItem(1, Icons.watch_rounded, uz ? "Qurilmalar" : "Приборы"),
          _buildNavItem(
            2,
            Icons.notifications_rounded,
            uz ? "Xabarlar" : "Сигналы",
          ),
          _buildNavItem(3, Icons.person_rounded, uz ? "Profil" : "Профиль"),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    final bool isSelected = _currentTabIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentTabIndex = index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFE0F2FE) : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: isSelected
                  ? const Color(0xFF0284C7)
                  : const Color(0xFF94A3B8),
              size: 22,
            ),
            if (isSelected) ...[
              const SizedBox(width: 6),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF0284C7),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

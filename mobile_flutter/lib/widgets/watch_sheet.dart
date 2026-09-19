import 'dart:async';
import 'package:flutter/material.dart';

/// Wear OS 3.5 / 4.0 Interactive Smartwatch Simulation Modal
/// Styled with Dark AMOLED, Tashkent Digital Clock, Pulsing Heart Rate,
/// Off-Body Wear Detection, 3-Stage Emergency SOS, and Live Telemetry Sync.
class WearOsWatchSheet extends StatefulWidget {
  final bool isUzbek;
  final String patientName;
  final int? currentHr;
  final int? currentSpo2;
  final int initialHr;
  final int initialSpo2;
  final double initialTemp;
  final int battery;
  final bool isWorn;
  final void Function(int hr, int spo2, bool isWorn, int battery)? onVitalsChanged;
  final ValueChanged<String>? onTriggerSos;

  const WearOsWatchSheet({
    super.key,
    required this.isUzbek,
    required this.patientName,
    this.currentHr,
    this.currentSpo2,
    this.initialHr = 74,
    this.initialSpo2 = 98,
    this.initialTemp = 36.6,
    this.battery = 88,
    this.isWorn = true,
    this.onVitalsChanged,
    this.onTriggerSos,
  });

  @override
  State<WearOsWatchSheet> createState() => _WearOsWatchSheetState();
}

enum SosStage { idle, countdown, dispatched }

class _WearOsWatchSheetState extends State<WearOsWatchSheet>
    with SingleTickerProviderStateMixin {
  late int _hr;
  late int _spo2;
  late double _temp;
  late int _battery;
  late bool _isWorn;

  // Clock
  Timer? _clockTimer;
  DateTime _currentTime = DateTime.now();

  // Pulse animation
  late AnimationController _pulseController;
  late Animation<double> _pulseScale;

  // SOS state
  SosStage _sosStage = SosStage.idle;
  int _sosCountdown = 5;
  int _sosCancelWindow = 30;
  Timer? _sosTimer;
  double _holdProgress = 0.0;
  Timer? _holdTimer;

  @override
  void initState() {
    super.initState();
    _hr = widget.currentHr ?? widget.initialHr;
    _spo2 = widget.currentSpo2 ?? widget.initialSpo2;
    _temp = widget.initialTemp;
    _battery = widget.battery;
    _isWorn = widget.isWorn;

    // Pulse animation based on current heart rate
    _pulseController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: (60000 / _hr.clamp(40, 180)).round()),
    )..repeat(reverse: true);

    _pulseScale = Tween<double>(begin: 0.92, end: 1.14).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Tashkent Clock ticker (every second)
    _clockTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() {
          _currentTime = DateTime.now();
        });
      }
    });
  }

  @override
  void dispose() {
    _clockTimer?.cancel();
    _sosTimer?.cancel();
    _holdTimer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  void _updatePulseRate() {
    final ms = (60000 / _hr.clamp(40, 180)).round();
    _pulseController.duration = Duration(milliseconds: ms);
    if (!_pulseController.isAnimating) {
      _pulseController.repeat(reverse: true);
    }
  }

  void _notifyParent() {
    widget.onVitalsChanged?.call(_hr, _spo2, _isWorn, _battery);
  }

  // ── SOS LOGIC (Hold 3s -> Countdown 5s -> Dispatched 30s) ──
  void _startHoldProgress() {
    _holdProgress = 0.0;
    _holdTimer?.cancel();
    _holdTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      if (mounted) {
        setState(() {
          _holdProgress += 0.05 / 2.0; // 2 seconds to fill
          if (_holdProgress >= 1.0) {
            _holdProgress = 0.0;
            timer.cancel();
            _triggerSosCountdown();
          }
        });
      }
    });
  }

  void _cancelHoldProgress() {
    _holdTimer?.cancel();
    if (mounted && _sosStage == SosStage.idle) {
      setState(() {
        _holdProgress = 0.0;
      });
    }
  }

  void _triggerSosCountdown() {
    _sosTimer?.cancel();
    setState(() {
      _sosStage = SosStage.countdown;
      _sosCountdown = 5;
    });

    _sosTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_sosCountdown > 1) {
          _sosCountdown--;
        } else {
          timer.cancel();
          _dispatchSosAlert();
        }
      });
    });
  }

  void _dispatchSosAlert() {
    _sosTimer?.cancel();
    setState(() {
      _sosStage = SosStage.dispatched;
      _sosCancelWindow = 30;
    });

    widget.onTriggerSos?.call(
      widget.isUzbek
          ? "Galaxy Watch 5 favqulodda SOS tugmasi"
          : "Экстренная кнопка Galaxy Watch 5",
    );

    _sosTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_sosCancelWindow > 1) {
          _sosCancelWindow--;
        } else {
          timer.cancel();
          _sosStage = SosStage.idle;
        }
      });
    });
  }

  void _cancelSos() {
    _sosTimer?.cancel();
    setState(() {
      _sosStage = SosStage.idle;
      _sosCountdown = 5;
      _holdProgress = 0.0;
    });
  }

  String _formatTime() {
    final h = _currentTime.hour.toString().padLeft(2, '0');
    final m = _currentTime.minute.toString().padLeft(2, '0');
    final s = _currentTime.second.toString().padLeft(2, '0');
    return "$h:$m:$s";
  }

  @override
  Widget build(BuildContext context) {
    final bool uz = widget.isUzbek;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.92,
      ),
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
      decoration: const BoxDecoration(
        color: Color(0xFF0F172A), // Dark slate companion container
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Drag handle
            Center(
              child: Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFF334155),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Modal Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0284C7).withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(
                        Icons.watch_rounded,
                        color: Color(0xFF38BDF8),
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          uz ? "Wear OS 3.5 — Jonli Soat" : "Wear OS 3.5 — Смарт-часы",
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 15,
                          ),
                        ),
                        Text(
                          "${widget.patientName} • Samsung Galaxy Watch 5",
                          style: const TextStyle(
                            color: Color(0xFF94A3B8),
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded, color: Color(0xFF94A3B8)),
                  tooltip: uz ? "Yopish" : "Закрыть",
                ),
              ],
            ),
            const SizedBox(height: 16),

            // ─────────────────────────────────────────────────────────────────
            // CIRCULAR AMOLED WATCH CHASSIS & DIAL
            // ─────────────────────────────────────────────────────────────────
            Center(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Titanium Bezel with Digital Crown Accent
                  Container(
                    width: 292,
                    height: 292,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const RadialGradient(
                        colors: [
                          Color(0xFF334155),
                          Color(0xFF1E293B),
                          Color(0xFF0F172A),
                        ],
                        stops: [0.75, 0.92, 1.0],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF0284C7).withValues(alpha: 0.25),
                          blurRadius: 28,
                          spreadRadius: 4,
                        ),
                      ],
                      border: Border.all(color: const Color(0xFF475569), width: 2),
                    ),
                  ),

                  // Digital Crown Button Right Mockup
                  Positioned(
                    right: 4,
                    child: Container(
                      width: 8,
                      height: 38,
                      decoration: BoxDecoration(
                        color: const Color(0xFF64748B),
                        borderRadius: BorderRadius.circular(4),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.5),
                            blurRadius: 4,
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Inner Circular AMOLED Screen (270 x 270)
                  Container(
                    width: 270,
                    height: 270,
                    clipBehavior: Clip.antiAlias,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Color(0xFF000000), // AMOLED Pitch Black
                    ),
                    child: _buildWatchScreenContent(uz),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // ─────────────────────────────────────────────────────────────────
            // SIMULATION & TELEMETRY CONTROLS (Sinov paneli)
            // ─────────────────────────────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF334155)),
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
                            Icons.tune_rounded,
                            color: Color(0xFF38BDF8),
                            size: 17,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            uz ? "Jonli Telemetriya Sinovi" : "Управление Телеметрией",
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                      // Off-body sensor toggle
                      FilterChip(
                        selected: _isWorn,
                        showCheckmark: false,
                        avatar: Icon(
                          _isWorn ? Icons.check_circle_rounded : Icons.warning_rounded,
                          size: 14,
                          color: _isWorn ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                        ),
                        label: Text(
                          _isWorn
                              ? (uz ? "Taqilgan" : "На руке")
                              : (uz ? "Yechilgan" : "Снят"),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: _isWorn ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                          ),
                        ),
                        backgroundColor: const Color(0xFF0F172A),
                        selectedColor: const Color(0xFF10B981).withValues(alpha: 0.15),
                        side: BorderSide(
                          color: _isWorn
                              ? const Color(0xFF10B981).withValues(alpha: 0.4)
                              : const Color(0xFFF59E0B).withValues(alpha: 0.4),
                        ),
                        onSelected: (val) {
                          setState(() {
                            _isWorn = val;
                          });
                          _notifyParent();
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Heart Rate Slider
                  Row(
                    children: [
                      const Icon(Icons.favorite_rounded, color: Color(0xFFEF4444), size: 16),
                      const SizedBox(width: 8),
                      Text(
                        uz ? "Yurak urishi (HR):" : "Пульс (ЧСС):",
                        style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 12),
                      ),
                      const Spacer(),
                      Text(
                        "$_hr bpm",
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12.5,
                        ),
                      ),
                    ],
                  ),
                  SliderTheme(
                    data: SliderTheme.of(context).copyWith(
                      trackHeight: 3,
                      activeTrackColor: const Color(0xFFEF4444),
                      inactiveTrackColor: const Color(0xFF334155),
                      thumbColor: const Color(0xFFEF4444),
                      overlayColor: const Color(0xFFEF4444).withValues(alpha: 0.2),
                      thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                    ),
                    child: Slider(
                      value: _hr.toDouble(),
                      min: 45,
                      max: 140,
                      onChanged: (val) {
                        setState(() {
                          _hr = val.round();
                        });
                        _updatePulseRate();
                        _notifyParent();
                      },
                    ),
                  ),

                  // SpO2 Slider
                  Row(
                    children: [
                      const Icon(Icons.air_rounded, color: Color(0xFF38BDF8), size: 16),
                      const SizedBox(width: 8),
                      Text(
                        uz ? "Kislorod (SpO2):" : "Кислород (SpO2):",
                        style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 12),
                      ),
                      const Spacer(),
                      Text(
                        "$_spo2%",
                        style: TextStyle(
                          color: _spo2 < 92 ? const Color(0xFFEF4444) : Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12.5,
                        ),
                      ),
                    ],
                  ),
                  SliderTheme(
                    data: SliderTheme.of(context).copyWith(
                      trackHeight: 3,
                      activeTrackColor: const Color(0xFF38BDF8),
                      inactiveTrackColor: const Color(0xFF334155),
                      thumbColor: const Color(0xFF38BDF8),
                      overlayColor: const Color(0xFF38BDF8).withValues(alpha: 0.2),
                      thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
                    ),
                    child: Slider(
                      value: _spo2.toDouble(),
                      min: 82,
                      max: 100,
                      onChanged: (val) {
                        setState(() {
                          _spo2 = val.round();
                        });
                        _notifyParent();
                      },
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // WATCH SCREEN CONTENT (AMOLED DISPATCHER: Normal vs Countdown vs Dispatched)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildWatchScreenContent(bool uz) {
    if (_sosStage == SosStage.countdown) {
      return _buildSosCountdownScreen(uz);
    }
    if (_sosStage == SosStage.dispatched) {
      return _buildSosDispatchedScreen(uz);
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // 1. TOP CURVED STATUS BAR (Tashkent Clock, Battery %, Bluetooth)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // BLE Connection Dot
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _isWorn ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Icon(Icons.bluetooth_rounded, color: Color(0xFF38BDF8), size: 12),
                  ],
                ),

                // Live Tashkent Clock
                Text(
                  _formatTime(),
                  style: const TextStyle(
                    color: Color(0xFFE2E8F0),
                    fontSize: 12.5,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                  ),
                ),

                // Battery Status
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      "$_battery%",
                      style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 10.5),
                    ),
                    const SizedBox(width: 2),
                    const Icon(Icons.battery_5_bar_rounded, color: Color(0xFF10B981), size: 12),
                  ],
                ),
              ],
            ),
          ),

          // 2. CENTER HEART RATE SECTION WITH ANIMATED PULSE
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                uz ? "YURAK URISHI" : "ПУЛЬС",
                style: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 9.5,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: 2),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  ScaleTransition(
                    scale: _pulseScale,
                    child: const Icon(
                      Icons.favorite_rounded,
                      color: Color(0xFFFF5252),
                      size: 26,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    "$_hr",
                    style: TextStyle(
                      color: _hr > 100 || _hr < 55
                          ? const Color(0xFFFF5252)
                          : Colors.white,
                      fontSize: 38,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -1,
                    ),
                  ),
                  const SizedBox(width: 4),
                  const Text(
                    "bpm",
                    style: TextStyle(
                      color: Color(0xFFFF8A80),
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),

          // 3. SECONDARY VITALS ROW (SpO2 & Skin Temperature)
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // SpO2
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF1E293B)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.air_rounded, color: Color(0xFF38BDF8), size: 12),
                    const SizedBox(width: 4),
                    Text(
                      "$_spo2%",
                      style: TextStyle(
                        color: _spo2 < 92 ? const Color(0xFFFF5252) : const Color(0xFFF1F5F9),
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),

              // Skin Temperature
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF1E293B)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.thermostat_rounded, color: Color(0xFFF59E0B), size: 12),
                    const SizedBox(width: 4),
                    Text(
                      "$_temp°C",
                      style: const TextStyle(
                        color: Color(0xFFF1F5F9),
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // 4. WEAR STATUS PILL & 3-SECOND SOS HOLD BUTTON
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Wear detection status pill
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _isWorn
                        ? const Color(0xFF10B981).withValues(alpha: 0.12)
                        : const Color(0xFFF59E0B).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _isWorn
                          ? const Color(0xFF10B981).withValues(alpha: 0.3)
                          : const Color(0xFFF59E0B).withValues(alpha: 0.3),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 5,
                        height: 5,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _isWorn ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        _isWorn
                            ? (uz ? "Taqilgan" : "На руке")
                            : (uz ? "Yechilgan" : "Снят"),
                        style: TextStyle(
                          color: _isWorn ? const Color(0xFF6EE7B7) : const Color(0xFFFCD34D),
                          fontSize: 9.5,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),

                // 3-SECOND SOS EMERGENCY HOLD BUTTON
                GestureDetector(
                  onTapDown: (_) => _startHoldProgress(),
                  onTapUp: (_) => _cancelHoldProgress(),
                  onTapCancel: _cancelHoldProgress,
                  onTap: _triggerSosCountdown,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      if (_holdProgress > 0)
                        SizedBox(
                          width: 44,
                          height: 44,
                          child: CircularProgressIndicator(
                            value: _holdProgress,
                            strokeWidth: 3,
                            color: const Color(0xFFEF4444),
                            backgroundColor: Colors.transparent,
                          ),
                        ),
                      Container(
                        width: 38,
                        height: 38,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: const LinearGradient(
                            colors: [Color(0xFFDC2626), Color(0xFF991B1B)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFFDC2626).withValues(alpha: 0.5),
                              blurRadius: 8,
                            ),
                          ],
                        ),
                        child: const Center(
                          child: Text(
                            "SOS",
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w900,
                              fontSize: 10.5,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // STAGE 2: COUNTDOWN SCREEN (Emergency 5s timer with cancel option)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildSosCountdownScreen(bool uz) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: const Color(0xFF450A0A),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            uz ? "SOS YUBORILMOQDA" : "ОТПРАВКА SOS",
            style: const TextStyle(
              color: Color(0xFFFCA5A5),
              fontWeight: FontWeight.bold,
              fontSize: 11,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            "$_sosCountdown",
            style: const TextStyle(
              color: Colors.white,
              fontSize: 54,
              fontWeight: FontWeight.w900,
            ),
          ),
          Text(
            uz ? "103 va shifokorga xabar beriladi" : "Врач и 103 будут вызваны",
            style: const TextStyle(color: Color(0xFFE2E8F0), fontSize: 10),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 32,
            child: ElevatedButton(
              onPressed: _cancelSos,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF334155),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: Text(
                uz ? "Bekor qilish" : "Отмена",
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // STAGE 3: DISPATCHED SCREEN (With 30s cancellation window)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildSosDispatchedScreen(bool uz) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: const Color(0xFF064E3B),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle_rounded, color: Color(0xFF34D399), size: 36),
          const SizedBox(height: 6),
          Text(
            uz ? "SOS YUBORILDI!" : "SOS ОТПРАВЛЕН!",
            style: const TextStyle(
              color: Color(0xFF6EE7B7),
              fontWeight: FontWeight.w900,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            uz ? "103 va Shifokor xabardor qilindi" : "103 и Врач уведомлены",
            style: const TextStyle(color: Color(0xFFE2E8F0), fontSize: 10),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 30,
            child: OutlinedButton(
              onPressed: _cancelSos,
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: Color(0xFFF87171)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                padding: const EdgeInsets.symmetric(horizontal: 12),
              ),
              child: Text(
                "${uz ? 'Bekor qilish' : 'Отмена'} ($_sosCancelWindow)",
                style: const TextStyle(
                  color: Color(0xFFF87171),
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

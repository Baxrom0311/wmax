import 'dart:async';
import 'package:flutter/material.dart';

void main() {
  runApp(const WmaxApp());
}

class WmaxApp extends StatefulWidget {
  const WmaxApp({super.key});

  @override
  State<WmaxApp> createState() => _WmaxAppState();
}

class _WmaxAppState extends State<WmaxApp> {
  bool isUzbek = true;

  void toggleLanguage() {
    setState(() {
      isUzbek = !isUzbek;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WMAX Caregiver — Bemor Parvarishi',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0284C7),
          primary: const Color(0xFF0284C7),
          surface: Colors.white,
        ),
        fontFamily: 'Roboto',
      ),
      home: WmaxRootFlow(
        isUzbek: isUzbek,
        onToggleLang: toggleLanguage,
      ),
    );
  }
}

/// Root State Flow
class WmaxRootFlow extends StatefulWidget {
  final bool isUzbek;
  final VoidCallback onToggleLang;

  const WmaxRootFlow({
    super.key,
    required this.isUzbek,
    required this.onToggleLang,
  });

  @override
  State<WmaxRootFlow> createState() => _WmaxRootFlowState();
}

enum AppFlowState { splash, login, mainApp }

class _WmaxRootFlowState extends State<WmaxRootFlow> {
  AppFlowState _flowState = AppFlowState.splash;

  @override
  void initState() {
    super.initState();
    Timer(const Duration(milliseconds: 1800), () {
      if (mounted) {
        setState(() {
          _flowState = AppFlowState.login;
        });
      }
    });
  }

  void _onLoginSuccess() {
    setState(() {
      _flowState = AppFlowState.mainApp;
    });
  }

  void _onLogout() {
    setState(() {
      _flowState = AppFlowState.login;
    });
  }

  @override
  Widget build(BuildContext context) {
    switch (_flowState) {
      case AppFlowState.splash:
        return SplashScreen(isUzbek: widget.isUzbek);
      case AppFlowState.login:
        return CaregiverLoginScreen(
          isUzbek: widget.isUzbek,
          onToggleLang: widget.onToggleLang,
          onLogin: _onLoginSuccess,
        );
      case AppFlowState.mainApp:
        return CaregiverMainDashboard(
          isUzbek: widget.isUzbek,
          onToggleLang: widget.onToggleLang,
          onLogout: _onLogout,
        );
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. SPLASH SCREEN (Soddalashtirilgan, sokin va estetik)
// ─────────────────────────────────────────────────────────────────────────────
class SplashScreen extends StatelessWidget {
  final bool isUzbek;

  const SplashScreen({super.key, required this.isUzbek});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF0284C7).withOpacity(0.15),
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF0284C7).withOpacity(0.4)),
              ),
              child: const Icon(
                Icons.favorite_rounded,
                color: Color(0xFF38BDF8),
                size: 52,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'WMAX',
              style: TextStyle(
                fontSize: 34,
                fontWeight: FontWeight.w900,
                color: Colors.white,
                letterSpacing: 3,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              isUzbek ? 'Bemor Parvarishi va Monitoring' : 'Уход и Мониторинг Пациентов',
              style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8), letterSpacing: 0.5),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. CAREGIVER LOGIN (Toza, shovqinsiz login)
// ─────────────────────────────────────────────────────────────────────────────
class CaregiverLoginScreen extends StatefulWidget {
  final bool isUzbek;
  final VoidCallback onToggleLang;
  final VoidCallback onLogin;

  const CaregiverLoginScreen({
    super.key,
    required this.isUzbek,
    required this.onToggleLang,
    required this.onLogin,
  });

  @override
  State<CaregiverLoginScreen> createState() => _CaregiverLoginScreenState();
}

class _CaregiverLoginScreenState extends State<CaregiverLoginScreen> {
  final TextEditingController _phoneController =
      TextEditingController(text: "+998 90 111 22 33");
  final TextEditingController _pinController =
      TextEditingController(text: "112233");
  bool _isLoading = false;

  void _submitLogin() {
    setState(() => _isLoading = true);
    Timer(const Duration(milliseconds: 600), () {
      if (mounted) {
        setState(() => _isLoading = false);
        widget.onLogin();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final bool uz = widget.isUzbek;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          TextButton(
            onPressed: widget.onToggleLang,
            child: Text(
              uz ? 'RU' : 'UZ',
              style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0284C7)),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(16),
                    decoration: const BoxDecoration(
                      color: Color(0xFFE0F2FE),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.supervised_user_circle_rounded,
                      color: Color(0xFF0284C7),
                      size: 40,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Center(
                  child: Text(
                    uz ? 'Qarovchi Kirishi' : 'Вход Опекуна',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                ),
                const SizedBox(height: 6),
                Center(
                  child: Text(
                    uz ? 'Oila a\'zolaringiz salomatligi nazorati' : 'Контроль здоровья ваших близких',
                    style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                  ),
                ),
                const SizedBox(height: 28),

                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.03),
                        blurRadius: 16,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        uz ? 'Telefon raqam' : 'Телефон',
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: Color(0xFF475569)),
                      ),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: const Color(0xFFF8FAFC),
                          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        uz ? 'Maxfiy PIN kod' : 'Секретный PIN-код',
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: Color(0xFF475569)),
                      ),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _pinController,
                        obscureText: true,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          filled: true,
                          fillColor: const Color(0xFFF8FAFC),
                          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
                          ),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _submitLogin,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF0284C7),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            elevation: 0,
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : Text(
                                  uz ? 'Kirish' : 'Войти',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Center(
                  child: Text(
                    uz ? "PIN: 112233 (Demo hisob)" : "PIN: 112233 (Демо вход)",
                    style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PATIENT DATA MODEL (2 ta bemor uchun)
// ─────────────────────────────────────────────────────────────────────────────
class PatientInfo {
  final String id;
  final String name;
  final String relationUz;
  final String relationRu;
  final int age;
  final String diagnosisUz;
  final String diagnosisRu;
  final String deviceName;
  final String addressUz;
  final String addressRu;
  bool isConnected;
  int battery;
  int hr;
  int spo2;
  double temp;
  int rr;

  PatientInfo({
    required this.id,
    required this.name,
    required this.relationUz,
    required this.relationRu,
    required this.age,
    required this.diagnosisUz,
    required this.diagnosisRu,
    required this.deviceName,
    required this.addressUz,
    required this.addressRu,
    this.isConnected = false,
    this.battery = 88,
    this.hr = 74,
    this.spo2 = 97,
    this.temp = 36.6,
    this.rr = 16,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. MAIN DASHBOARD (Curved Navbar, Switcher, Bluetooth Pairing)
// ─────────────────────────────────────────────────────────────────────────────
class CaregiverMainDashboard extends StatefulWidget {
  final bool isUzbek;
  final VoidCallback onToggleLang;
  final VoidCallback onLogout;

  const CaregiverMainDashboard({
    super.key,
    required this.isUzbek,
    required this.onToggleLang,
    required this.onLogout,
  });

  @override
  State<CaregiverMainDashboard> createState() => _CaregiverMainDashboardState();
}

class _CaregiverMainDashboardState extends State<CaregiverMainDashboard> {
  int _currentTabIndex = 0;

  // Ikkita bemor: Ota va Ona
  final List<PatientInfo> _patients = [
    PatientInfo(
      id: "p1",
      name: "Otabek Rahimov",
      relationUz: "Otangiz",
      relationRu: "Отец",
      age: 68,
      diagnosisUz: "Yurak ishemik kasalligi (YIK), SYuYe IIB",
      diagnosisRu: "ИБС, стенокардия, СН IIB ст.",
      deviceName: "Samsung Galaxy Watch 5",
      addressUz: "Urganch sh., Al-Xorazmiy 45-uy",
      addressRu: "г. Ургенч, ул. Аль-Хорезми 45",
      isConnected: false, // Dastlab ulanmagan
      battery: 88,
      hr: 74,
      spo2: 97,
      temp: 36.6,
      rr: 16,
    ),
    PatientInfo(
      id: "p2",
      name: "Sayyora Rahimova",
      relationUz: "Onangiz",
      relationRu: "Мать",
      age: 65,
      diagnosisUz: "Arterial gipertoniya II-bosqich, Qandli diabet 2-tip",
      diagnosisRu: "Артериальная гипертензия II ст., Сахарный диабет 2 типа",
      deviceName: "Xiaomi Watch 2 Pro",
      addressUz: "Urganch sh., Al-Xorazmiy 45-uy",
      addressRu: "г. Ургенч, ул. Аль-Хорезми 45",
      isConnected: false, // Dastlab ulanmagan
      battery: 76,
      hr: 78,
      spo2: 96,
      temp: 36.5,
      rr: 18,
    ),
  ];

  int _selectedPatientIndex = 0;
  Timer? _jitterTimer;

  // Alerts list
  final List<Map<String, dynamic>> _alerts = [
    {
      "titleUz": "⚠️ SpO2 ogohlantirishi",
      "titleRu": "⚠️ Предупреждение SpO2",
      "descUz": "Otabek Rahimovda SpO2 91% ga tushdi. Shifokorga yetkazildi.",
      "descRu": "У Отабека Рахимова SpO2 снизился до 91%. Врач уведомлен.",
      "time": "10:30",
      "isCritical": false,
    },
    {
      "titleUz": "💊 Dori vaqti keldi",
      "titleRu": "💊 Напоминание о лекарстве",
      "descUz": "Sayyora Rahimova: Metformin 500mg qabul qilindi.",
      "descRu": "Сайёра Рахимова: Метформин 500мг принят.",
      "time": "08:15",
      "isCritical": false,
    },
  ];

  @override
  void initState() {
    super.initState();
    _jitterTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      if (mounted) {
        setState(() {
          final p = _patients[_selectedPatientIndex];
          if (p.isConnected) {
            p.hr = 72 + (DateTime.now().second % 5);
            p.spo2 = 96 + (DateTime.now().second % 3);
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _jitterTimer?.cancel();
    super.dispose();
  }

  PatientInfo get currentPatient => _patients[_selectedPatientIndex];

  // Bluetooth Pairing Modal
  void _openBluetoothModal() {
    final p = currentPatient;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => BluetoothPairingSheet(
        isUzbek: widget.isUzbek,
        patientName: p.name,
        targetDeviceName: p.deviceName,
        onConnected: () {
          setState(() {
            p.isConnected = true;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                widget.isUzbek
                    ? "${p.deviceName} muvaffaqiyatli ulandi! Jonli o'lchovlar faollashtirildi."
                    : "${p.deviceName} успешно подключен! Онлайн-показатели активны.",
              ),
              backgroundColor: const Color(0xFF0D9488),
            ),
          );
        },
      ),
    );
  }

  void _triggerSos() {
    setState(() {
      _alerts.insert(0, {
        "titleUz": "🚨 Yangi SOS chaqiruvi!",
        "titleRu": "🚨 Новый экстренный SOS!",
        "descUz": "${currentPatient.name} bo'yicha tezkor signal 103 ga yetkazildi.",
        "descRu": "Экстренный вызов по ${currentPatient.name} направлен в 103.",
        "time": "Hozirgina",
        "isCritical": true,
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final bool uz = widget.isUzbek;

    final pages = [
      // 0. Bosh sahifa (Monitoring)
      _buildMonitoringView(uz),
      // 1. Qurilma & Bluetooth boshqaruvi
      _buildDevicesView(uz),
      // 2. SOS va Xabarnomalar
      _buildAlertsView(uz),
      // 3. Qarovchi Profili
      _buildProfileView(uz),
    ];

    return Scaffold(
      extendBody: true, // Curved floating navbar uchun kerak
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF0284C7).withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.favorite_rounded, color: Color(0xFF0284C7), size: 20),
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
          // Til almashtirish
          TextButton(
            onPressed: widget.onToggleLang,
            child: Text(
              uz ? 'RU' : 'UZ',
              style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0284C7), fontSize: 13),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 580),
          child: Column(
            children: [
              // BEMORLARNI ALMASHTIRGICH (PATIENT SWITCHER: 2 bemor)
              _buildPatientSwitcher(uz),
              Expanded(
                child: IndexedStack(
                  index: _currentTabIndex,
                  children: pages,
                ),
              ),
            ],
          ),
        ),
      ),
      // FLOATING CURVED MODERN NAVBAR
      bottomNavigationBar: _buildCurvedNavBar(uz),
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // TOP PATIENT SWITCHER (Bir emas 2 ta bemorni tanlash)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildPatientSwitcher(bool uz) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 8),
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
              onTap: () {
                setState(() {
                  _selectedPatientIndex = index;
                });
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                decoration: BoxDecoration(
                  color: isSelected ? const Color(0xFF0284C7) : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      index == 0 ? Icons.person_rounded : Icons.person_outline_rounded,
                      color: isSelected ? Colors.white : const Color(0xFF64748B),
                      size: 16,
                    ),
                    const SizedBox(width: 6),
                    Flexible(
                      child: Text(
                        "${p.name} (${uz ? p.relationUz : p.relationRu})",
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: isSelected ? Colors.white : const Color(0xFF475569),
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                          fontSize: 12.5,
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

  // ───────────────────────────────────────────────────────────────────────────
  // FLOATING CURVED NAVBAR
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildCurvedNavBar(bool uz) {
    return Container(
      margin: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      height: 66,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: const Color(0xFFE2E8F0).withOpacity(0.8)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0F172A).withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNavItem(0, Icons.monitor_heart_outlined, Icons.monitor_heart_rounded, uz ? 'Holat' : 'Обзор'),
          _buildNavItem(1, Icons.watch_outlined, Icons.watch_rounded, uz ? 'Qurilma' : 'Девайс'),
          _buildNavItem(2, Icons.notifications_none_rounded, Icons.notifications_rounded, uz ? 'SOS' : 'SOS', hasBadge: _alerts.isNotEmpty),
          _buildNavItem(3, Icons.person_outline_rounded, Icons.person_rounded, uz ? 'Profil' : 'Профиль'),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, IconData activeIcon, String label, {bool hasBadge = false}) {
    final bool isSelected = _currentTabIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentTabIndex = index),
      behavior: HitTestBehavior.opaque,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(
                  isSelected ? activeIcon : icon,
                  color: isSelected ? const Color(0xFF0284C7) : const Color(0xFF94A3B8),
                  size: 24,
                ),
                if (hasBadge)
                  Positioned(
                    top: -2,
                    right: -2,
                    child: Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: Color(0xFFDC2626),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                color: isSelected ? const Color(0xFF0284C7) : const Color(0xFF94A3B8),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // VIEW 0: MONITORING (Bemor ko'rsatkichlari)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildMonitoringView(bool uz) {
    final p = currentPatient;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 85),
      children: [
        // 1. Patient Profile Info
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: const Color(0xFFE0F2FE),
                child: Text(
                  p.name.substring(0, 1),
                  style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0284C7)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      p.name,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A)),
                    ),
                    Text(
                      "${p.age} yosh • ${uz ? p.diagnosisUz : p.diagnosisRu}",
                      style: const TextStyle(fontSize: 11.5, color: Color(0xFF64748B)),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: p.isConnected ? const Color(0xFFDCFCE7) : const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  p.isConnected ? (uz ? "Faol" : "Онлайн") : (uz ? "Kutilmoqda" : "Офлайн"),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: p.isConnected ? const Color(0xFF166534) : const Color(0xFF64748B),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // 2. Device not connected banner (agar ulanmagan bo'lsa)
        if (!p.isConnected)
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFEFF6FF),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFBFDBFE)),
            ),
            child: Row(
              children: [
                const Icon(Icons.bluetooth_searching_rounded, color: Color(0xFF0284C7), size: 26),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        uz ? "Aqlli soat ulanmagan" : "Часы не подключены",
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF1E3A8A)),
                      ),
                      Text(
                        uz ? "${p.deviceName} ni Bluetooth orqali ulang" : "Подключите ${p.deviceName} по Bluetooth",
                        style: const TextStyle(fontSize: 11.5, color: Color(0xFF3B82F6)),
                      ),
                    ],
                  ),
                ),
                ElevatedButton(
                  onPressed: _openBluetoothModal,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0284C7),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  child: Text(uz ? "Ulash" : "Связать", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          )
        else
          // Ulangandagi sokin indikator
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFE2E8F0)),
            ),
            child: Row(
              children: [
                const Icon(Icons.bluetooth_connected_rounded, color: Color(0xFF10B981), size: 18),
                const SizedBox(width: 8),
                Text(
                  "${p.deviceName} • ${uz ? 'Batareya' : 'Заряд'}: ${p.battery}%",
                  style: const TextStyle(fontSize: 12, color: Color(0xFF334155), fontWeight: FontWeight.w600),
                ),
                const Spacer(),
                Text(
                  uz ? "Barqaror" : "Стабильно",
                  style: const TextStyle(fontSize: 11, color: Color(0xFF10B981), fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
        const SizedBox(height: 14),

        // 3. Vitals 2x2 Grid
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: 1.45,
          children: [
            _buildCleanMetricCard(
              title: uz ? 'Puls / Yurak' : 'Пульс',
              value: p.isConnected ? '${p.hr}' : '--',
              unit: 'bpm',
              icon: Icons.favorite_rounded,
              color: const Color(0xFFEF4444),
              status: p.isConnected ? (uz ? 'Normada (70-80)' : 'Норма') : (uz ? 'Ulanmagan' : 'Нет данных'),
            ),
            _buildCleanMetricCard(
              title: uz ? 'SpO2 Kislorod' : 'SpO2 Кислород',
              value: p.isConnected ? '${p.spo2}' : '--',
              unit: '%',
              icon: Icons.water_drop_rounded,
              color: const Color(0xFF0284C7),
              status: p.isConnected ? (uz ? 'A\'lo (>95%)' : 'Норма') : (uz ? 'Ulanmagan' : 'Нет данных'),
            ),
            _buildCleanMetricCard(
              title: uz ? 'Tana Harorati' : 'Температура',
              value: p.isConnected ? '${p.temp}' : '--',
              unit: '°C',
              icon: Icons.thermostat_rounded,
              color: const Color(0xFFF59E0B),
              status: p.isConnected ? '36.6 °C' : '--',
            ),
            _buildCleanMetricCard(
              title: uz ? 'Nafas Soni' : 'Дыхание',
              value: p.isConnected ? '${p.rr}' : '--',
              unit: '/min',
              icon: Icons.air_rounded,
              color: const Color(0xFF10B981),
              status: p.isConnected ? '16 /min' : '--',
            ),
          ],
        ),
        const SizedBox(height: 16),

        // 4. Favqulodda SOS tugmasi (Minimalistik, ortiqcha shovqinsiz)
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFFECACA)),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.emergency_share_rounded, color: Color(0xFFDC2626), size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      uz ? "Favqulodda SOS" : "Экстренный SOS",
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5, color: Color(0xFF991B1B)),
                    ),
                    Text(
                      uz ? "Shifokor va 103 ga tezkor chaqiruv" : "Мгновенный вызов врача и 103",
                      style: const TextStyle(fontSize: 11.5, color: Color(0xFF7F1D1D)),
                    ),
                  ],
                ),
              ),
              ElevatedButton(
                onPressed: () {
                  _triggerSos();
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        uz ? "SOS signali shifokorga yetkazildi!" : "Сигнал SOS отправлен врачу!",
                      ),
                      backgroundColor: const Color(0xFFDC2626),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFDC2626),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: Text(uz ? "SOS Yuborish" : "Отправить", style: const TextStyle(fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCleanMetricCard({
    required String title,
    required String value,
    required String unit,
    required IconData icon,
    required Color color,
    required String status,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 11.5, color: Color(0xFF64748B), fontWeight: FontWeight.w600)),
              Icon(icon, color: color, size: 16),
            ],
          ),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Color(0xFF0F172A))),
              const SizedBox(width: 4),
              Text(unit, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
            ],
          ),
          Text(status, style: const TextStyle(fontSize: 10.5, color: Color(0xFF10B981), fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // VIEW 1: DEVICES & BLUETOOTH (Qurilmalar va ulanish)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildDevicesView(bool uz) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 85),
      children: [
        Text(
          uz ? "Qurilmalar Boshqaruvi" : "Управление Устройствами",
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
        ),
        const SizedBox(height: 4),
        Text(
          uz ? "Bemorlarga biriktirilgan aqlli soatlarni Bluetooth orqali ulash" : "Подключение часов пациентов через Bluetooth",
          style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
        ),
        const SizedBox(height: 16),

        ..._patients.map((p) {
          return Container(
            margin: const EdgeInsets.only(bottom: 12),
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
                        color: p.isConnected ? const Color(0xFFDCFCE7) : const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.watch_rounded,
                        color: p.isConnected ? const Color(0xFF16A34A) : const Color(0xFF64748B),
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            p.deviceName,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF0F172A)),
                          ),
                          Text(
                            "${p.name} (${uz ? p.relationUz : p.relationRu})",
                            style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: p.isConnected ? const Color(0xFFDCFCE7) : const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        p.isConnected ? (uz ? "Ulangan" : "Подключен") : (uz ? "Uzilgan" : "Отключен"),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: p.isConnected ? const Color(0xFF16A34A) : const Color(0xFF64748B),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Text(
                      p.isConnected
                          ? "${uz ? 'Batareya' : 'Заряд'}: ${p.battery}% • Bluetooth faol"
                          : (uz ? "Bluetooth o'chiq" : "Bluetooth выключен"),
                      style: const TextStyle(fontSize: 11.5, color: Color(0xFF64748B)),
                    ),
                    const Spacer(),
                    OutlinedButton.icon(
                      onPressed: () {
                        if (p.isConnected) {
                          setState(() => p.isConnected = false);
                        } else {
                          _openBluetoothModal();
                        }
                      },
                      icon: Icon(
                        p.isConnected ? Icons.link_off_rounded : Icons.bluetooth_searching_rounded,
                        size: 16,
                        color: p.isConnected ? const Color(0xFFDC2626) : const Color(0xFF0284C7),
                      ),
                      label: Text(
                        p.isConnected ? (uz ? "Uzish" : "Отключить") : (uz ? "Bluetooth ulash" : "Подключить"),
                        style: TextStyle(
                          fontSize: 11.5,
                          color: p.isConnected ? const Color(0xFFDC2626) : const Color(0xFF0284C7),
                        ),
                      ),
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(
                          color: p.isConnected ? const Color(0xFFFECACA) : const Color(0xFFBAE6FD),
                        ),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        }),
      ],
    );
  }

  // ───────────────────────────────────────────────────────────────────────────
  // VIEW 2: ALERTS & SOS (Xabarlar)
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildAlertsView(bool uz) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 85),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              uz ? "Bildirishnomalar & SOS" : "Оповещения и SOS",
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            Text(
              "${_alerts.length} ta",
              style: const TextStyle(fontSize: 12, color: Color(0xFF0284C7), fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 12),
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
                  crit ? Icons.warning_amber_rounded : Icons.info_outline_rounded,
                  color: crit ? const Color(0xFFDC2626) : const Color(0xFF0284C7),
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
                              color: crit ? const Color(0xFF991B1B) : const Color(0xFF0F172A),
                            ),
                          ),
                          Text(alt["time"], style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        uz ? alt["descUz"] : alt["descRu"],
                        style: TextStyle(
                          fontSize: 12,
                          color: crit ? const Color(0xFF7F1D1D) : const Color(0xFF475569),
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

  // ───────────────────────────────────────────────────────────────────────────
  // VIEW 3: CAREGIVER PROFILE
  // ───────────────────────────────────────────────────────────────────────────
  Widget _buildProfileView(bool uz) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 85),
      children: [
        Container(
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
                child: Icon(Icons.person_rounded, color: Color(0xFF0284C7), size: 28),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Jasur Rahimov",
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF0F172A)),
                    ),
                    Text(
                      uz ? "Qarovchi (2 ta bemor biriktirilgan)" : "Опекун (Прикреплено 2 пациента)",
                      style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                    ),
                  ],
                ),
              ),
            ],
          ),
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
              const Icon(Icons.medical_services_rounded, color: Color(0xFF0284C7), size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Dr. Islom Yusupov", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5)),
                    Text(uz ? "Kardiolog • +998 90 123 45 67" : "Кардиолог • +998 90 123 45 67", style: const TextStyle(fontSize: 11.5, color: Color(0xFF64748B))),
                  ],
                ),
              ),
              IconButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text("+998 90 123 45 67 ga ulanmoqda...")),
                  );
                },
                icon: const Icon(Icons.phone_rounded, color: Color(0xFF0284C7), size: 20),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        ListTile(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          tileColor: Colors.white,
          leading: const Icon(Icons.language_rounded, color: Color(0xFF0284C7)),
          title: Text(uz ? "Tilni o'zgartirish" : "Сменить язык", style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
          trailing: Text(uz ? "O'zbekcha" : "Русский", style: const TextStyle(fontSize: 12, color: Color(0xFF64748B))),
          onTap: widget.onToggleLang,
        ),
        const SizedBox(height: 8),
        ListTile(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          tileColor: Colors.white,
          leading: const Icon(Icons.logout_rounded, color: Color(0xFFDC2626)),
          title: Text(uz ? "Tizimdan chiqish" : "Выйти", style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: Color(0xFFDC2626))),
          onTap: widget.onLogout,
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// BLUETOOTH PAIRING SHEET (Qidirish va ulash dialogi)
// ─────────────────────────────────────────────────────────────────────────────
class BluetoothPairingSheet extends StatefulWidget {
  final bool isUzbek;
  final String patientName;
  final String targetDeviceName;
  final VoidCallback onConnected;

  const BluetoothPairingSheet({
    super.key,
    required this.isUzbek,
    required this.patientName,
    required this.targetDeviceName,
    required this.onConnected,
  });

  @override
  State<BluetoothPairingSheet> createState() => _BluetoothPairingSheetState();
}

class _BluetoothPairingSheetState extends State<BluetoothPairingSheet> {
  bool _isSearching = true;
  String? _pairingDevice;

  @override
  void initState() {
    super.initState();
    // 1.5s search simulation
    Timer(const Duration(milliseconds: 1400), () {
      if (mounted) {
        setState(() => _isSearching = false);
      }
    });
  }

  void _pair(String deviceName) {
    setState(() {
      _pairingDevice = deviceName;
    });
    Timer(const Duration(milliseconds: 1000), () {
      if (mounted) {
        Navigator.of(context).pop();
        widget.onConnected();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final bool uz = widget.isUzbek;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: const Color(0xFFCBD5E1),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Icon(Icons.bluetooth_searching_rounded, color: Color(0xFF0284C7), size: 24),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  uz ? "Bluetooth Qurilma Ulash" : "Подключение по Bluetooth",
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            uz
                ? "${widget.patientName} uchun aqlli soatni qidirish"
                : "Поиск смарт-часов для ${widget.patientName}",
            style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
          ),
          const SizedBox(height: 20),

          if (_isSearching)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Column(
                  children: [
                    const SizedBox(
                      width: 32,
                      height: 32,
                      child: CircularProgressIndicator(strokeWidth: 2.5, color: Color(0xFF0284C7)),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      uz ? "Yaqin-atrofdagi soatlar qidirilmoqda..." : "Поиск доступных часов рядом...",
                      style: const TextStyle(fontSize: 12.5, color: Color(0xFF64748B)),
                    ),
                  ],
                ),
              ),
            )
          else ...[
            Text(
              uz ? "Topilgan qurilmalar:" : "Найденные устройства:",
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF475569)),
            ),
            const SizedBox(height: 10),
            _buildDeviceRow(widget.targetDeviceName, "-54 dBm", isTarget: true),
            const SizedBox(height: 8),
            _buildDeviceRow("Smart Band 8 (BLE)", "-72 dBm"),
            const SizedBox(height: 16),
          ],
        ],
      ),
    );
  }

  Widget _buildDeviceRow(String name, String rssi, {bool isTarget = false}) {
    final bool isConnecting = _pairingDevice == name;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isTarget ? const Color(0xFFF0F9FF) : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isTarget ? const Color(0xFFBAE6FD) : const Color(0xFFE2E8F0)),
      ),
      child: Row(
        children: [
          const Icon(Icons.watch_rounded, color: Color(0xFF0284C7), size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                Text("Signal: $rssi", style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
              ],
            ),
          ),
          ElevatedButton(
            onPressed: isConnecting ? null : () => _pair(name),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF0284C7),
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              elevation: 0,
            ),
            child: isConnecting
                ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Text(widget.isUzbek ? "Ulash" : "Связать", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}

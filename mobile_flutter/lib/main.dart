import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'models/models.dart';
import 'services/session_service.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Disable bottom phone navigation bar, keep clean status bar at top
  await SystemChrome.setEnabledSystemUIMode(
    SystemUiMode.manual,
    overlays: [SystemUiOverlay.top],
  );

  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
    systemNavigationBarColor: Colors.transparent,
    systemNavigationBarDividerColor: Colors.transparent,
    systemNavigationBarIconBrightness: Brightness.dark,
  ));

  final isUzbek = await SessionService.isUzbek();
  final loggedIn = await SessionService.isLoggedIn();
  runApp(WmaxApp(initialIsUzbek: isUzbek, initialLoggedIn: loggedIn));
}

class WmaxApp extends StatefulWidget {
  final bool initialIsUzbek;
  final bool initialLoggedIn;

  const WmaxApp({
    super.key,
    this.initialIsUzbek = true,
    this.initialLoggedIn = false,
  });

  @override
  State<WmaxApp> createState() => _WmaxAppState();
}

class _WmaxAppState extends State<WmaxApp> {
  late bool isUzbek;

  @override
  void initState() {
    super.initState();
    isUzbek = widget.initialIsUzbek;
  }

  void toggleLanguage() async {
    final next = !isUzbek;
    setState(() => isUzbek = next);
    await SessionService.setIsUzbek(next);
  }

  void setLanguage(bool uz) async {
    if (isUzbek == uz) return;
    setState(() => isUzbek = uz);
    await SessionService.setIsUzbek(uz);
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
        onSelectLang: setLanguage,
        initialLoggedIn: widget.initialLoggedIn,
      ),
    );
  }
}

/// Root State Flow
class WmaxRootFlow extends StatefulWidget {
  final bool isUzbek;
  final VoidCallback onToggleLang;
  final ValueChanged<bool> onSelectLang;
  final bool initialLoggedIn;

  const WmaxRootFlow({
    super.key,
    required this.isUzbek,
    required this.onToggleLang,
    required this.onSelectLang,
    required this.initialLoggedIn,
  });

  @override
  State<WmaxRootFlow> createState() => _WmaxRootFlowState();
}

enum AppFlowState { splash, login, mainApp }

class _WmaxRootFlowState extends State<WmaxRootFlow> {
  AppFlowState _flowState = AppFlowState.splash;
  List<PatientSummary> _loadedPatients = [];

  @override
  void initState() {
    super.initState();
    _checkInitialAuth();
  }

  void _checkInitialAuth() async {
    await Future.delayed(const Duration(milliseconds: 1200));
    if (!mounted) return;

    if (widget.initialLoggedIn) {
      final patients = await SessionService.getSavedPatients();
      if (mounted) {
        setState(() {
          _loadedPatients = patients;
          _flowState = AppFlowState.mainApp;
        });
      }
    } else {
      setState(() {
        _flowState = AppFlowState.login;
      });
    }
  }

  void _onLoginSuccess(List<PatientSummary> patients) {
    setState(() {
      _loadedPatients = patients;
      _flowState = AppFlowState.mainApp;
    });
  }

  void _onLogout() async {
    await SessionService.clearSession();
    if (mounted) {
      setState(() {
        _loadedPatients = [];
        _flowState = AppFlowState.login;
      });
    }
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
          onSelectLang: widget.onSelectLang,
          onLoginSuccess: _onLoginSuccess,
        );
      case AppFlowState.mainApp:
        return CaregiverMainDashboard(
          isUzbek: widget.isUzbek,
          initialPatients: _loadedPatients,
          onToggleLang: widget.onToggleLang,
          onSelectLang: widget.onSelectLang,
          onLogout: _onLogout,
        );
    }
  }
}

/// Splash Screen
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
                color: const Color(0xFF0284C7).withValues(alpha: 0.15),
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF0284C7).withValues(alpha: 0.4)),
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
            const SizedBox(height: 32),
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF38BDF8)),
            ),
          ],
        ),
      ),
    );
  }
}

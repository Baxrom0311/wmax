import 'package:flutter/material.dart';
import '../models/models.dart';
import '../api/api_service.dart';
import '../widgets/language_selector.dart';

class CaregiverLoginScreen extends StatefulWidget {
  final bool isUzbek;
  final VoidCallback onToggleLang;
  final ValueChanged<bool>? onSelectLang;
  final ValueChanged<List<PatientSummary>> onLoginSuccess;

  const CaregiverLoginScreen({
    super.key,
    required this.isUzbek,
    required this.onToggleLang,
    this.onSelectLang,
    required this.onLoginSuccess,
  });

  @override
  State<CaregiverLoginScreen> createState() => _CaregiverLoginScreenState();
}

class _CaregiverLoginScreenState extends State<CaregiverLoginScreen> {
  final TextEditingController _phoneController =
      TextEditingController(text: "+998 90 111 00 11");
  final TextEditingController _pinController =
      TextEditingController(text: "112233");
  final TextEditingController _passwordController = TextEditingController();
  String _role = 'relative';
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
  }

  void _submitLogin() async {
    final phone = _phoneController.text.trim();
    final pin = _pinController.text.trim();

    if (phone.isEmpty || (_role == 'doctor' ? _passwordController.text.trim().isEmpty : pin.isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(widget.isUzbek
              ? "Iltimos, telefon va PIN kodni kiriting"
              : "Пожалуйста, введите номер телефона и PIN"),
          backgroundColor: const Color(0xFFEF4444),
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final res = _role == 'doctor'
          ? await ApiService.loginClinician(phone: phone, password: _passwordController.text.trim())
          : _role == 'patient'
              ? await ApiService.loginPatient(phone: phone, pin: pin)
              : await ApiService.loginRelative(phone: phone, pin: pin);
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              widget.isUzbek
                  ? "Xush kelibsiz, ${res.fullName}!"
                  : "Добро пожаловать, ${res.fullName}!",
            ),
            backgroundColor: const Color(0xFF0D9488),
          ),
        );
        widget.onLoginSuccess(res.patients);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString().replaceAll('Exception: ', '')),
            backgroundColor: const Color(0xFFDC2626),
            duration: const Duration(seconds: 4),
          ),
        );
      }
    }
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
          const SizedBox(width: 16),
        ],
      ),
      body: SafeArea(
        child: Center(
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
                  const SizedBox(height: 24),

                  SegmentedButton<String>(
                    segments: [
                      ButtonSegment(value: 'relative', label: Text(uz ? 'Qarindosh' : 'Опекун')),
                      ButtonSegment(value: 'patient', label: Text(uz ? 'Bemor' : 'Пациент')),
                      ButtonSegment(value: 'doctor', label: Text(uz ? 'Shifokor' : 'Врач')),
                    ],
                    selected: {_role},
                    onSelectionChanged: (value) => setState(() => _role = value.first),
                  ),
                  const SizedBox(height: 16),

                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.03),
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
                        _role == 'doctor'
                            ? (uz ? 'Parol' : 'Пароль')
                            : (uz ? 'PIN kod (6 xonali)' : 'ПИН-код (6 цифр)'),
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: Color(0xFF475569)),
                      ),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _role == 'doctor' ? _passwordController : _pinController,
                        keyboardType: TextInputType.number,
                        obscureText: true,
                        maxLength: _role == 'doctor' ? 64 : 6,
                        decoration: InputDecoration(
                          counterText: "",
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
                      const SizedBox(height: 20),

                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _submitLogin,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF0284C7),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
                                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),

                // Quick Demo Buttons
                Text(
                  uz ? "Tezkor sinov hisoblari:" : "Быстрый демо-вход:",
                  style: const TextStyle(fontSize: 12, color: Color(0xFF64748B), fontWeight: FontWeight.w600),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          _phoneController.text = "+998 90 111 00 11";
                          _pinController.text = "112233";
                        },
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: Text(
                          uz ? "👵 Dilnoza (Otabek)" : "👵 Дильноза",
                          style: const TextStyle(fontSize: 11),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                          _phoneController.text = "+998 90 111 00 22";
                          _pinController.text = "112233";
                        },
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: Text(
                          uz ? "👴 Sardor (Gulnora)" : "👴 Сардор",
                          style: const TextStyle(fontSize: 11),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
}

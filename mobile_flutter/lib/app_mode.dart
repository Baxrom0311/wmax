/// Which UI the app starts in: `watch`, `health` or `phone`.
///
/// An explicit `--dart-define=WMAX_APP_MODE=...` wins. Without it, the Wear OS
/// flavor (`--flavor wear`) still starts the watch runtime, so a watch build
/// never opens the caregiver login and never leaves passive monitoring off.
String resolveAppMode({required String defined, String? flavor}) {
  final explicit = defined.trim();
  if (explicit.isNotEmpty) return explicit;
  if (flavor == 'wear') return 'watch';
  return 'phone';
}

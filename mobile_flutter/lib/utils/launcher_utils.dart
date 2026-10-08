import 'package:url_launcher/url_launcher.dart';

Future<bool> makePhoneCall(String phoneNumber) async {
  final cleanNumber = phoneNumber.replaceAll(RegExp(r'[^\d+]'), '');
  final Uri launchUri = Uri(
    scheme: 'tel',
    path: cleanNumber,
  );
  try {
    if (await canLaunchUrl(launchUri)) {
      return await launchUrl(launchUri, mode: LaunchMode.externalApplication);
    }
  } catch (_) {
    // Return false on failure
  }
  return false;
}

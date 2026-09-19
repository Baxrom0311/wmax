import 'dart:async';
import 'package:flutter/material.dart';

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
            _buildDeviceRow("Medical PPG Band (BLE)", "-72 dBm"),
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

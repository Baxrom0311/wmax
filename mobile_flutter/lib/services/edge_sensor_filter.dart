/// On-Device (Edge) Filtering Service for WMAX Wearable / Mobile.
/// Filters impossible biometric anomalies and physical motion noise before buffering.
class EdgeSensorFilter {
  static const double minValidHr = 30.0;
  static const double maxValidHr = 240.0;
  static const double minValidSpo2 = 60.0;
  static const double maxValidSpo2 = 100.0;
  static const double minValidTemp = 25.0;
  static const double maxValidTemp = 44.0;

  /// Returns true if the reading is physically plausible and not pure motion artifact.
  static bool isValidBiometricSample({
    required double? heartRate,
    required double? spo2,
    required double? skinTemp,
    required int? stepsDelta,
    required bool isWorn,
  }) {
    if (!isWorn) return false;

    // Validate Heart Rate
    if (heartRate != null) {
      if (heartRate < minValidHr || heartRate > maxValidHr) {
        return false;
      }
    }

    // Validate SpO2
    if (spo2 != null) {
      if (spo2 < minValidSpo2 || spo2 > maxValidSpo2) {
        return false;
      }
      // If patient is running heavily, optical PPG SpO2 reading has high artifact rate
      if (stepsDelta != null && stepsDelta > 80 && spo2 < 85.0) {
        return false; // suppress motion artifact false dip
      }
    }

    // Validate Skin Temperature
    if (skinTemp != null) {
      if (skinTemp < minValidTemp || skinTemp > maxValidTemp) {
        return false;
      }
    }

    return true;
  }

  static bool isValidHeartRate(double? hr) {
    if (hr == null) return false;
    return hr >= minValidHr && hr <= maxValidHr;
  }

  static bool isValidSpo2(double? spo2) {
    if (spo2 == null) return false;
    return spo2 >= minValidSpo2 && spo2 <= maxValidSpo2;
  }

  static bool isValidSkinTemp(double? temp) {
    if (temp == null) return false;
    return temp >= minValidTemp && temp <= maxValidTemp;
  }
}

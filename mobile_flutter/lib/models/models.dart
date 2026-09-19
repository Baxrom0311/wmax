/// Alert levels defined in WMAX protocol
enum AlertLevel { green, amber, red, noData }

AlertLevel parseAlertLevel(String? val) {
  switch (val?.toLowerCase()) {
    case 'green':
      return AlertLevel.green;
    case 'amber':
      return AlertLevel.amber;
    case 'red':
      return AlertLevel.red;
    case 'no_data':
    default:
      return AlertLevel.noData;
  }
}

String alertLevelToString(AlertLevel level) {
  switch (level) {
    case AlertLevel.green:
      return 'green';
    case AlertLevel.amber:
      return 'amber';
    case AlertLevel.red:
      return 'red';
    case AlertLevel.noData:
      return 'no_data';
  }
}

/// Relative authentication response from /api/v1/auth/relative/login
class RelativeAuthResponse {
  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final String role;
  final String fullName;
  final List<PatientSummary> patients;

  RelativeAuthResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    required this.role,
    required this.fullName,
    required this.patients,
  });

  factory RelativeAuthResponse.fromJson(Map<String, dynamic> json) {
    var rawPatients = json['patients'];
    List<PatientSummary> patientList = [];
    if (rawPatients is List) {
      patientList = rawPatients
          .map((p) => PatientSummary.fromJson(p as Map<String, dynamic>))
          .toList();
    }

    return RelativeAuthResponse(
      accessToken: json['access_token'] ?? '',
      refreshToken: json['refresh_token'] ?? '',
      expiresIn: json['expires_in'] ?? 3600,
      role: json['role'] ?? 'relative',
      fullName: json['full_name'] ?? 'Qarovchi',
      patients: patientList,
    );
  }

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'expires_in': expiresIn,
        'role': role,
        'full_name': fullName,
        'patients': patients.map((p) => p.toJson()).toList(),
      };
}

/// Patient summary item in relative login response
class PatientSummary {
  final String id;
  final String fullName;
  final String relationship;
  final String accessToken;
  final AlertLevel level;
  final String diagnosis;
  final int age;
  final DateTime? lastReadingAt;

  PatientSummary({
    required this.id,
    required this.fullName,
    required this.relationship,
    required this.accessToken,
    required this.level,
    required this.diagnosis,
    required this.age,
    this.lastReadingAt,
  });

  factory PatientSummary.fromJson(Map<String, dynamic> json) {
    DateTime? lastReading;
    if (json['last_reading_at'] != null) {
      try {
        lastReading = DateTime.parse(json['last_reading_at']);
      } catch (_) {}
    }

    return PatientSummary(
      id: json['id']?.toString() ?? '',
      fullName: json['full_name'] ?? 'Bemor',
      relationship: json['relationship'] ?? 'Oila a\'zosi',
      accessToken: json['access_token'] ?? '',
      level: parseAlertLevel(json['level']),
      diagnosis: json['diagnosis'] ?? 'Tashxis ko\'rsatilmagan',
      age: json['age'] is int ? json['age'] : (int.tryParse('${json['age']}') ?? 65),
      lastReadingAt: lastReading,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'full_name': fullName,
        'relationship': relationship,
        'access_token': accessToken,
        'level': alertLevelToString(level),
        'diagnosis': diagnosis,
        'age': age,
        'last_reading_at': lastReadingAt?.toIso8601String(),
      };
}

/// Vital signs model
class VitalsData {
  final double? hr;
  final double? spo2;
  final double? temp;
  final double? rr;
  final int? steps;
  final double? sleepHours;
  final int? battery;

  VitalsData({
    this.hr,
    this.spo2,
    this.temp,
    this.rr,
    this.steps,
    this.sleepHours,
    this.battery,
  });

  factory VitalsData.fromJson(Map<String, dynamic> json) {
    return VitalsData(
      hr: json['hr'] != null ? (json['hr'] as num).toDouble() : null,
      spo2: json['spo2'] != null ? (json['spo2'] as num).toDouble() : null,
      temp: json['skin_temp'] != null
          ? (json['skin_temp'] as num).toDouble()
          : (json['temp'] != null ? (json['temp'] as num).toDouble() : null),
      rr: json['rr'] != null ? (json['rr'] as num).toDouble() : null,
      steps: json['steps'] is int ? json['steps'] : int.tryParse('${json['steps']}'),
      sleepHours: json['sleep_hours'] != null ? (json['sleep_hours'] as num).toDouble() : null,
      battery: json['battery'] is int ? json['battery'] : int.tryParse('${json['battery']}'),
    );
  }

  Map<String, dynamic> toJson() => {
        'hr': hr,
        'spo2': spo2,
        'skin_temp': temp,
        'rr': rr,
        'steps': steps,
        'sleep_hours': sleepHours,
        'battery': battery,
      };
}

/// Doctor contact information
class DoctorContact {
  final String name;
  final String phone;

  DoctorContact({required this.name, required this.phone});

  factory DoctorContact.fromJson(Map<String, dynamic> json) {
    return DoctorContact(
      name: json['name'] ?? 'Dr. Islom Yusupov',
      phone: json['phone'] ?? '+998901234567',
    );
  }

  Map<String, dynamic> toJson() => {'name': name, 'phone': phone};
}

/// AI Prognosis information
class PrognosisData {
  final String riskLevel;
  final int riskProbabilityPct;
  final String summary;
  final String? recommendation;
  final int earlyWarningHours;
  final String? primaryConcern;

  PrognosisData({
    required this.riskLevel,
    required this.riskProbabilityPct,
    required this.summary,
    this.recommendation,
    this.earlyWarningHours = 72,
    this.primaryConcern,
  });

  factory PrognosisData.fromJson(Map<String, dynamic> json) {
    return PrognosisData(
      riskLevel: json['risk_level'] ?? 'low',
      riskProbabilityPct: json['risk_probability_pct'] is int
          ? json['risk_probability_pct']
          : (int.tryParse('${json['risk_probability_pct']}') ?? 12),
      summary: json['summary'] ?? 'Barcha ko\'rsatkichlar me\'yorida.',
      recommendation: json['recommendation'],
      earlyWarningHours: json['early_warning_hours'] is int ? json['early_warning_hours'] : 72,
      primaryConcern: json['primary_concern'],
    );
  }

  int get riskScore => riskProbabilityPct;
  String get recommendationUz => (recommendation != null && recommendation!.isNotEmpty) ? recommendation! : summary;
  String get recommendationRu => (recommendation != null && recommendation!.isNotEmpty) ? recommendation! : summary;

  Map<String, dynamic> toJson() => {
        'risk_level': riskLevel,
        'risk_probability_pct': riskProbabilityPct,
        'summary': summary,
        'recommendation': recommendation,
        'early_warning_hours': earlyWarningHours,
        'primary_concern': primaryConcern,
      };
}

/// Clinical problem item from WMAX analysis
class ClinicalProblem {
  final String key;
  final String title;
  final String detail;
  final String severity;
  final String? deviation;
  final String? baselineRange;
  final double? currentValue;

  ClinicalProblem({
    required this.key,
    required this.title,
    required this.detail,
    required this.severity,
    this.deviation,
    this.baselineRange,
    this.currentValue,
  });

  String get titleUz => title;
  String get titleRu => detail.isNotEmpty ? detail : title;

  factory ClinicalProblem.fromJson(Map<String, dynamic> json) {
    return ClinicalProblem(
      key: json['param'] ?? json['key'] ?? '',
      title: json['label'] ?? json['title'] ?? '',
      detail: json['explanation'] ?? json['detail'] ?? '',
      severity: json['severity'] ?? 'mild',
      deviation: json['deviation'],
      baselineRange: json['baseline_range'],
      currentValue: (json['current_value'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'key': key,
        'title': title,
        'detail': detail,
        'severity': severity,
        'deviation': deviation,
        'baseline_range': baselineRange,
        'current_value': currentValue,
      };
}

/// Clinical alert item from backend
class PatientAlertItem {
  final int id;
  final DateTime ts;
  final AlertLevel level;
  final double compositeScore;
  final String reason;
  final Map<String, dynamic>? triggeredParams;

  PatientAlertItem({
    required this.id,
    required this.ts,
    required this.level,
    required this.compositeScore,
    required this.reason,
    this.triggeredParams,
  });

  factory PatientAlertItem.fromJson(Map<String, dynamic> json) {
    DateTime parsedTs = DateTime.now();
    if (json['ts'] != null) {
      try {
        parsedTs = DateTime.parse(json['ts']);
      } catch (_) {}
    }
    return PatientAlertItem(
      id: json['id'] is int ? json['id'] : (int.tryParse('${json['id']}') ?? 0),
      ts: parsedTs,
      level: parseAlertLevel(json['level']),
      compositeScore: (json['composite_score'] as num?)?.toDouble() ?? 0.0,
      reason: json['reason'] ?? '',
      triggeredParams: json['triggered_params'] is Map<String, dynamic> ? json['triggered_params'] : null,
    );
  }
}

/// Detailed patient view from GET /api/v1/relatives/{token}/view
class RelativePatientView {
  final String patientId;
  final String patientName;
  final String relationship;
  final AlertLevel level;
  final String levelWordKey;
  final double compositeScore;
  final DateTime? lastReadingAt;
  final PrognosisData prognosis;
  final VitalsData vitals;
  final DoctorContact? doctorContact;
  final List<ClinicalProblem> problems;
  final List<double> sparkline;
  final List<PatientAlertItem> alerts;

  RelativePatientView({
    required this.patientId,
    required this.patientName,
    required this.relationship,
    required this.level,
    required this.levelWordKey,
    required this.compositeScore,
    this.lastReadingAt,
    required this.prognosis,
    required this.vitals,
    this.doctorContact,
    required this.problems,
    required this.sparkline,
    this.alerts = const [],
  });

  DoctorContact? get doctor => doctorContact;
  String get deviceModel => "Samsung Galaxy Watch 5";
  int get deviceBattery => vitals.battery ?? 90;
  bool get isDeviceOnline => level != AlertLevel.noData;
  String get address => "Urganch sh., Al-Xorazmiy ko'chasi";
  double get lat => 41.5562;
  double get lon => 60.6311;

  factory RelativePatientView.fromJson(Map<String, dynamic> json) {
    DateTime? lastReading;
    if (json['last_reading_at'] != null) {
      try {
        lastReading = DateTime.parse(json['last_reading_at']);
      } catch (_) {}
    }

    var rawProblems = json['problems'];
    List<ClinicalProblem> problemsList = [];
    if (rawProblems is List) {
      problemsList = rawProblems
          .map((p) => ClinicalProblem.fromJson(p as Map<String, dynamic>))
          .toList();
    }

    var rawSpark = json['sparkline'];
    List<double> sparkList = [];
    if (rawSpark is List) {
      sparkList = rawSpark
          .map((v) => (v is num) ? v.toDouble() : 0.0)
          .toList();
    }
    var rawAlerts = json['alerts'];
    List<PatientAlertItem> alertsList = [];
    if (rawAlerts is List) {
      alertsList = rawAlerts
          .map((a) => PatientAlertItem.fromJson(a as Map<String, dynamic>))
          .toList();
    }

    return RelativePatientView(
      patientId: json['patient_id']?.toString() ?? '',
      patientName: json['patient_name'] ?? 'Bemor',
      relationship: json['relationship'] ?? 'Oila a\'zosi',
      level: parseAlertLevel(json['level']),
      levelWordKey: json['level_word_key'] ?? 'state.good',
      compositeScore: (json['composite_score'] as num?)?.toDouble() ?? 0.0,
      lastReadingAt: lastReading,
      prognosis: json['prognosis'] is Map<String, dynamic>
          ? PrognosisData.fromJson(json['prognosis'])
          : PrognosisData(riskLevel: 'low', riskProbabilityPct: 15, summary: 'Holat barqaror.'),
      vitals: json['vitals'] is Map<String, dynamic>
          ? VitalsData.fromJson(json['vitals'])
          : VitalsData(),
      doctorContact: json['doctor_contact'] is Map<String, dynamic>
          ? DoctorContact.fromJson(json['doctor_contact'])
          : null,
      problems: problemsList,
      sparkline: sparkList,
      alerts: alertsList,
    );
  }
}

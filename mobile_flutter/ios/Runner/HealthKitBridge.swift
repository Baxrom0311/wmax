import Flutter
import HealthKit
import Foundation
import Security

final class HealthKitBridge: NSObject, FlutterPlugin {
  private let store = HKHealthStore()

  static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(name: "wmax/native_health", binaryMessenger: registrar.messenger())
    registrar.addMethodCallDelegate(HealthKitBridge(), channel: channel)
  }

  func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    switch call.method {
    case "getHealthPlatformStatus":
      result(status())
    case "readDeviceCredential":
      readDeviceCredential(result: result)
    case "saveDeviceCredential":
      let arguments = call.arguments as? [String: Any]
      saveDeviceCredential(arguments?["token"] as? String, result: result)
    case "clearDeviceCredential":
      clearDeviceCredential(result: result)
    case "getWearExerciseStatus":
      result(["supported": false, "active": false, "status": "unsupported_platform"])
    case "getWearHealthCapabilities":
      result(["supported": false, "exercise_types": [], "passive_data_types": []])
    case "getWearDataLayerQueue", "drainWearDataLayerQueue":
      result([String]())
    case "ackWearDataLayerQueue":
      result(true)
    case "startWearHealthMonitoring", "requestWearExercisePermissions", "startWearExercise", "stopWearExercise":
      result(FlutterError(code: "WEAR_OS_UNAVAILABLE", message: "Wear OS workout controls are not available on iOS.", details: nil))
    case "requestHealthConnectPermissions", "requestHealthDataPermissions":
      requestReadAuthorization(result: result)
    case "readRecentHealthConnect", "readRecentHealthData":
      let arguments = call.arguments as? [String: Any]
      let hours = (arguments?["hours"] as? NSNumber)?.intValue ?? 24
      readRecent(hours: hours, result: result)
    default:
      result(FlutterMethodNotImplemented)
    }
  }

  private let credentialService = "uz.boos.wmax.device-credential"

  private func credentialQuery() -> [String: Any] {
    [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: credentialService,
      kSecAttrAccount as String: "device-token",
    ]
  }

  private func readDeviceCredential(result: @escaping FlutterResult) {
    var query = credentialQuery()
    query[kSecReturnData as String] = true
    query[kSecMatchLimit as String] = kSecMatchLimitOne
    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecItemNotFound {
      result(nil)
    } else if status != errSecSuccess {
      result(FlutterError(code: "KEYCHAIN_READ_FAILED", message: "Device credential could not be read.", details: status))
    } else if let data = item as? Data, let token = String(data: data, encoding: .utf8) {
      result(token)
    } else {
      result(FlutterError(code: "KEYCHAIN_DATA_INVALID", message: "Stored device credential is invalid.", details: nil))
    }
  }

  private func saveDeviceCredential(_ token: String?, result: @escaping FlutterResult) {
    guard let token, !token.isEmpty, let data = token.data(using: .utf8) else {
      result(FlutterError(code: "DEVICE_TOKEN_INVALID", message: "A non-empty device token is required.", details: nil))
      return
    }
    let query = credentialQuery()
    let attributes: [String: Any] = [kSecValueData as String: data]
    let updateStatus = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
    if updateStatus == errSecSuccess {
      result(true)
      return
    }
    guard updateStatus == errSecItemNotFound else {
      result(FlutterError(code: "KEYCHAIN_WRITE_FAILED", message: "Device credential could not be updated.", details: updateStatus))
      return
    }
    var insert = query
    attributes.forEach { insert[$0.key] = $0.value }
    insert[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
    let insertStatus = SecItemAdd(insert as CFDictionary, nil)
    if insertStatus == errSecSuccess {
      result(true)
    } else {
      result(FlutterError(code: "KEYCHAIN_WRITE_FAILED", message: "Device credential could not be saved.", details: insertStatus))
    }
  }

  private func clearDeviceCredential(result: @escaping FlutterResult) {
    let status = SecItemDelete(credentialQuery() as CFDictionary)
    if status == errSecSuccess || status == errSecItemNotFound {
      result(true)
    } else {
      result(FlutterError(code: "KEYCHAIN_DELETE_FAILED", message: "Device credential could not be removed.", details: status))
    }
  }

  private let quantityDefinitions: [(HKQuantityTypeIdentifier, String, HKUnit, String)] = [
    (.heartRate, "heart_rate_bpm", HKUnit.count().unitDivided(by: HKUnit.minute()), "bpm"),
    (.restingHeartRate, "resting_heart_rate_bpm", HKUnit.count().unitDivided(by: HKUnit.minute()), "bpm"),
    (.heartRateVariabilitySDNN, "heart_rate_variability_sdnn_ms", HKUnit.secondUnit(with: .milli), "ms"),
    (.bloodPressureSystolic, "blood_pressure_systolic_mmhg", HKUnit.millimeterOfMercury(), "mmHg"),
    (.bloodPressureDiastolic, "blood_pressure_diastolic_mmhg", HKUnit.millimeterOfMercury(), "mmHg"),
    (.bloodGlucose, "blood_glucose_mmol_l", HKUnit.moleUnit(with: .milli, molarMass: HKUnitMolarMassBloodGlucose).unitDivided(by: .liter()), "mmol/L"),
    (.bodyMass, "weight_kg", .gramUnit(with: .kilo), "kg"),
    (.bodyFatPercentage, "body_fat_pct", .percent(), "%"),
    (.vo2Max, "vo2_max_ml_kg_min", HKUnit.literUnit(with: .milli).unitDivided(by: HKUnit.gramUnit(with: .kilo).unitMultiplied(by: HKUnit.minute())), "mL/kg/min"),
    (.stepCount, "steps", .count(), "steps"),
    (.oxygenSaturation, "oxygen_saturation_pct", .percent(), "%"),
    (.respiratoryRate, "respiratory_rate_bpm", HKUnit.count().unitDivided(by: HKUnit.minute()), "breaths/min"),
    (.bodyTemperature, "body_temperature_c", .degreeCelsius(), "celsius"),
    (.distanceWalkingRunning, "distance_m", .meter(), "m"),
    (.activeEnergyBurned, "active_calories_kcal", .kilocalorie(), "kcal"),
    (.flightsClimbed, "floors", .count(), "floors"),
  ]

  func status() -> [String: Any] {
    [
      "health_connect_available": false,
      "healthkit_available": HKHealthStore.isHealthDataAvailable(),
      "health_connect_package_installed": false,
      "wear_os_device": false,
      "health_platform": "healthkit",
    ]
  }

  func requestReadAuthorization(result: @escaping FlutterResult) {
    guard HKHealthStore.isHealthDataAvailable() else {
      result(FlutterError(code: "HEALTH_DATA_UNAVAILABLE", message: "HealthKit is unavailable on this device.", details: nil))
      return
    }
    let readTypes = requestedReadTypes()
    store.requestAuthorization(toShare: [], read: readTypes) { success, error in
      DispatchQueue.main.async {
        if let error {
          result(FlutterError(code: "HEALTHKIT_AUTHORIZATION_FAILED", message: error.localizedDescription, details: nil))
        } else {
          result(["request_completed": success, "health_platform": "healthkit"])
        }
      }
    }
  }

  func readRecent(hours: Int, result: @escaping FlutterResult) {
    guard HKHealthStore.isHealthDataAvailable() else {
      result(FlutterError(code: "HEALTH_DATA_UNAVAILABLE", message: "HealthKit is unavailable on this device.", details: nil))
      return
    }

    let end = Date()
    let start = end.addingTimeInterval(-Double(min(max(hours, 1), 24 * 30)) * 3600)
    let predicate = HKQuery.predicateForSamples(withStart: start, end: end, options: [])
    let group = DispatchGroup()
    let lock = NSLock()
    var samples = [[String: Any]]()
    var sleepRecords = [HKCategorySample]()
    var workouts = [HKWorkout]()

    for (identifier, metric, unit, unitName) in quantityDefinitions {
      guard let type = HKObjectType.quantityType(forIdentifier: identifier) else { continue }
      group.enter()
      let query = HKSampleQuery(sampleType: type, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, resultSamples, _ in
        let mapped = (resultSamples as? [HKQuantitySample] ?? []).map { sample in
          self.sample(
            metric: metric,
            value: self.percentMetrics.contains(metric)
              ? sample.quantity.doubleValue(for: unit) * 100
              : sample.quantity.doubleValue(for: unit),
            unit: unitName,
            start: sample.startDate,
            end: sample.endDate,
            source: sample.sourceRevision.source.bundleIdentifier,
            recordId: sample.uuid.uuidString
          )
        }
        lock.lock()
        samples.append(contentsOf: mapped)
        lock.unlock()
        group.leave()
      }
      store.execute(query)
    }

    if let type = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) {
      group.enter()
      let query = HKSampleQuery(sampleType: type, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)]) { _, results, _ in
        lock.lock()
        sleepRecords = results as? [HKCategorySample] ?? []
        lock.unlock()
        group.leave()
      }
      store.execute(query)
    }

    group.enter()
    let workoutQuery = HKSampleQuery(sampleType: .workoutType(), predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, results, _ in
      lock.lock()
      workouts = results as? [HKWorkout] ?? []
      lock.unlock()
      group.leave()
    }
    store.execute(workoutQuery)

    group.notify(queue: .main) {
      lock.lock()
      let collectedSamples = samples
      let collectedSleep = sleepRecords
      let collectedWorkouts = workouts
      lock.unlock()
      result([
        "batch_id": UUID().uuidString,
        "source": "healthkit",
        "samples": collectedSamples,
        "sleep_sessions": self.sleepSessions(collectedSleep),
        "exercise_sessions": collectedWorkouts.map(self.exerciseSession),
        "metadata": [
          "reader": "healthkit",
          "window_hours": hours,
          "start_time": ISO8601DateFormatter().string(from: start),
          "end_time": ISO8601DateFormatter().string(from: end),
        ],
      ])
    }
  }

  private let percentMetrics: Set<String> = ["body_fat_pct", "oxygen_saturation_pct"]

  private func requestedReadTypes() -> Set<HKObjectType> {
    var types = Set<HKObjectType>()
    for (identifier, _, _, _) in quantityDefinitions {
      if let type = HKObjectType.quantityType(forIdentifier: identifier) { types.insert(type) }
    }
    if let sleep = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) { types.insert(sleep) }
    types.insert(HKObjectType.workoutType())
    return types
  }

  private func sample(metric: String, value: Double, unit: String, start: Date, end: Date, source: String, recordId: String) -> [String: Any] {
    [
      "metric": metric,
      "recorded_at": ISO8601DateFormatter().string(from: end),
      "started_at": ISO8601DateFormatter().string(from: start),
      "ended_at": ISO8601DateFormatter().string(from: end),
      "value_num": value,
      "unit": unit,
      "source_record_id": recordId,
      "metadata": ["data_origin_bundle": source],
    ]
  }

  private func sleepSessions(_ records: [HKCategorySample]) -> [[String: Any]] {
    let staged = records.compactMap { record -> (HKCategorySample, String)? in
      let name: String
      switch record.value {
      case 1: name = "asleep_unspecified"
      case 2: name = "awake"
      case 3: name = "light"
      case 4: name = "deep"
      case 5: name = "rem"
      default: return nil
      }
      return (record, name)
    }

    var groups = [[(HKCategorySample, String)]]()
    for item in staged {
      if let last = groups.last?.last, item.0.startDate.timeIntervalSince(last.0.endDate) <= 2 * 3600 {
        groups[groups.count - 1].append(item)
      } else {
        groups.append([item])
      }
    }
    return groups.map { group in
      let first = group.map { $0.0.startDate }.min() ?? Date()
      let last = group.map { $0.0.endDate }.max() ?? first
      return [
        "start_time": ISO8601DateFormatter().string(from: first),
        "end_time": ISO8601DateFormatter().string(from: last),
        "source_record_id": group.map { $0.0.uuid.uuidString }.joined(separator: ","),
        "stages": group.map { record, name in
          [
            "stage": name,
            "start_time": ISO8601DateFormatter().string(from: record.startDate),
            "end_time": ISO8601DateFormatter().string(from: record.endDate),
          ]
        },
        "metrics": [String: Any](),
        "metadata": ["data_origin_bundle": group.first?.0.sourceRevision.source.bundleIdentifier ?? ""],
      ]
    }
  }

  private func exerciseSession(_ workout: HKWorkout) -> [String: Any] {
    [
      "exercise_type": String(workout.workoutActivityType.rawValue),
      "start_time": ISO8601DateFormatter().string(from: workout.startDate),
      "end_time": ISO8601DateFormatter().string(from: workout.endDate),
      "source_record_id": workout.uuid.uuidString,
      "metrics": ["duration_seconds": workout.duration],
      "metadata": ["data_origin_bundle": workout.sourceRevision.source.bundleIdentifier],
    ]
  }
}

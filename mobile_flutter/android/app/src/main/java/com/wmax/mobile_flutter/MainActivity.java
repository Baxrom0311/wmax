package com.wmax.mobile_flutter;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorManager;
import android.os.BatteryManager;
import android.os.Build;
import android.provider.Settings;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import androidx.annotation.NonNull;
import androidx.activity.result.contract.ActivityResultContract;
import androidx.health.connect.client.PermissionController;
import androidx.health.connect.client.permission.HealthPermission;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

import io.flutter.embedding.android.FlutterActivity;
import io.flutter.embedding.engine.FlutterEngine;
import io.flutter.plugin.common.MethodChannel;

public class MainActivity extends FlutterActivity {
    private static final String CHANNEL = "wmax/native_health";
    private static final String ACTION_HEALTH_CONNECT_SETTINGS = "android.settings.HEALTH_CONNECT_SETTINGS";
    private static final int HEALTH_CONNECT_PERMISSION_REQUEST_CODE = 7301;
    private static final int BODY_SENSOR_PERMISSION_REQUEST_CODE = 7302;
    private static final int BACKGROUND_SENSOR_PERMISSION_REQUEST_CODE = 7303;
    private static final int ACTIVITY_RECOGNITION_PERMISSION_REQUEST_CODE = 7304;
    private static final String DEVICE_CREDENTIAL_PREFS = "wmax_device_credentials";
    private static final String DEVICE_CREDENTIAL_KEY = "device_token";
    private static final String DEVICE_CREDENTIAL_KEY_ALIAS = "wmax_device_token_v1";
    private final ActivityResultContract<Set<String>, Set<String>> healthPermissionContract =
            PermissionController.createRequestPermissionResultContract();
    private MethodChannel.Result pendingHealthPermissionResult;
    private MethodChannel.Result pendingWearHealthResult;
    private boolean pendingWearPermissionOnly;
    private boolean activityRecognitionRequestAttempted;

    @Override
    public void configureFlutterEngine(@NonNull FlutterEngine flutterEngine) {
        super.configureFlutterEngine(flutterEngine);
        new MethodChannel(flutterEngine.getDartExecutor().getBinaryMessenger(), CHANNEL)
                .setMethodCallHandler((call, result) -> {
                    switch (call.method) {
                        case "getHealthPlatformStatus":
                            result.success(getHealthPlatformStatus());
                            break;
                        case "readDeviceCredential":
                            readDeviceCredential(result);
                            break;
                        case "saveDeviceCredential":
                            saveDeviceCredential(call.argument("token"), result);
                            break;
                        case "clearDeviceCredential":
                            clearDeviceCredential(result);
                            break;
                        case "startWearHealthMonitoring":
                            startWearHealthMonitoring(result);
                            break;
                        case "requestWearExercisePermissions":
                            requestWearExercisePermissions(result);
                            break;
                        case "getWearHealthCapabilities":
                            getWearHealthCapabilities(result);
                            break;
                        case "startWearExercise":
                            startWearExercise(call.argument("exerciseType"), result);
                            break;
                        case "stopWearExercise":
                            stopWearExercise(result);
                            break;
                        case "getWearExerciseStatus":
                            result.success(getWearExerciseStatus());
                            break;
                        case "drainWearDataLayerQueue":
                        case "getWearDataLayerQueue":
                            result.success(getWearQueue());
                            break;
                        case "ackWearDataLayerQueue":
                            acknowledgeWearQueue(call.argument("payloads"));
                            result.success(true);
                            break;
                        case "enqueueWearPayload":
                            String queuePayload = call.argument("payload");
                            if (queuePayload != null && !queuePayload.trim().isEmpty()) {
                                result.success(WmaxWearDataListenerService.enqueuePayload(this, queuePayload));
                            } else {
                                result.error("INVALID_PAYLOAD", "Payload cannot be empty", null);
                            }
                            break;
                        case "openHealthConnectSettings":
                            openHealthConnectSettings();
                            result.success(true);
                            break;
                        case "requestHealthConnectPermissions":
                        case "requestHealthDataPermissions":
                            requestHealthConnectPermissions(result);
                            break;
                        case "readRecentHealthConnect":
                        case "readRecentHealthData":
                            Number hoursArg = call.argument("hours");
                            long hours = hoursArg == null ? 24L : hoursArg.longValue();
                            HealthConnectReader.readRecent(this, hours, new HealthConnectResultCallback() {
                                @Override
                                public void onSuccess(Map<String, ?> payload) {
                                    runOnUiThread(() -> result.success(payload));
                                }

                                @Override
                                public void onError(String code, String message) {
                                    runOnUiThread(() -> result.error(code, message, null));
                                }
                            });
                            break;
                        default:
                            result.notImplemented();
                    }
                });
    }

    private SecretKey getDeviceCredentialKey() throws Exception {
        KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
        keyStore.load(null);
        if (keyStore.containsAlias(DEVICE_CREDENTIAL_KEY_ALIAS)) {
            return (SecretKey) keyStore.getKey(DEVICE_CREDENTIAL_KEY_ALIAS, null);
        }

        KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(
                DEVICE_CREDENTIAL_KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build());
        return generator.generateKey();
    }

    private void readDeviceCredential(MethodChannel.Result result) {
        try {
            String encoded = getSharedPreferences(DEVICE_CREDENTIAL_PREFS, MODE_PRIVATE)
                    .getString(DEVICE_CREDENTIAL_KEY, null);
            if (encoded == null) {
                result.success(null);
                return;
            }
            byte[] stored = Base64.decode(encoded, Base64.NO_WRAP);
            ByteBuffer buffer = ByteBuffer.wrap(stored);
            int ivLength = buffer.get() & 0xff;
            byte[] iv = new byte[ivLength];
            buffer.get(iv);
            byte[] ciphertext = new byte[buffer.remaining()];
            buffer.get(ciphertext);

            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, getDeviceCredentialKey(), new GCMParameterSpec(128, iv));
            byte[] plaintext = cipher.doFinal(ciphertext);
            result.success(new String(plaintext, StandardCharsets.UTF_8));
        } catch (Exception exception) {
            result.error("DEVICE_CREDENTIAL_READ_FAILED", "Stored device credential could not be decrypted.", null);
        }
    }

    private void saveDeviceCredential(String token, MethodChannel.Result result) {
        if (token == null || token.trim().isEmpty()) {
            result.error("DEVICE_TOKEN_INVALID", "A non-empty device token is required.", null);
            return;
        }
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, getDeviceCredentialKey());
            byte[] iv = cipher.getIV();
            byte[] ciphertext = cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
            ByteBuffer payload = ByteBuffer.allocate(1 + iv.length + ciphertext.length);
            payload.put((byte) iv.length).put(iv).put(ciphertext);
            String encoded = Base64.encodeToString(payload.array(), Base64.NO_WRAP);
            boolean saved = getSharedPreferences(DEVICE_CREDENTIAL_PREFS, MODE_PRIVATE)
                    .edit()
                    .putString(DEVICE_CREDENTIAL_KEY, encoded)
                    .commit();
            if (!saved) {
                result.error("DEVICE_CREDENTIAL_WRITE_FAILED", "Device credential could not be saved.", null);
                return;
            }
            result.success(true);
        } catch (Exception exception) {
            result.error("DEVICE_CREDENTIAL_WRITE_FAILED", "Device credential could not be encrypted.", null);
        }
    }

    private void clearDeviceCredential(MethodChannel.Result result) {
        try {
            boolean removed = getSharedPreferences(DEVICE_CREDENTIAL_PREFS, MODE_PRIVATE)
                    .edit()
                    .remove(DEVICE_CREDENTIAL_KEY)
                    .commit();
            KeyStore keyStore = KeyStore.getInstance("AndroidKeyStore");
            keyStore.load(null);
            if (keyStore.containsAlias(DEVICE_CREDENTIAL_KEY_ALIAS)) {
                keyStore.deleteEntry(DEVICE_CREDENTIAL_KEY_ALIAS);
            }
            if (!removed) {
                result.error("DEVICE_CREDENTIAL_DELETE_FAILED", "Device credential could not be removed.", null);
                return;
            }
            result.success(true);
        } catch (Exception exception) {
            result.error("DEVICE_CREDENTIAL_DELETE_FAILED", "Device credential could not be removed.", null);
        }
    }

    private Map<String, Object> getHealthPlatformStatus() {
        Map<String, Object> status = new HashMap<>();
        PackageManager pm = getPackageManager();
        SensorManager sensors = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        BatteryManager battery = (BatteryManager) getSystemService(Context.BATTERY_SERVICE);

        boolean healthConnectPackage = isPackageInstalled("com.google.android.apps.healthdata");
        boolean healthConnectSystem = Build.VERSION.SDK_INT >= 34;
        boolean watch = pm.hasSystemFeature(PackageManager.FEATURE_WATCH);
        boolean heartRateSensor = sensors != null && sensors.getDefaultSensor(Sensor.TYPE_HEART_RATE) != null;
        boolean stepCounterSensor = sensors != null && sensors.getDefaultSensor(Sensor.TYPE_STEP_COUNTER) != null;

        status.put("sdk_int", Build.VERSION.SDK_INT);
        status.put("health_connect_available", healthConnectPackage || healthConnectSystem);
        status.put("health_connect_package_installed", healthConnectPackage);
        status.put("wear_os_device", watch);
        status.put("heart_rate_sensor_available", heartRateSensor);
        status.put("step_counter_available", stepCounterSensor);
        status.put("battery_pct", battery != null ? battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY) : -1);
        android.content.SharedPreferences healthState = getSharedPreferences("wmax_health_state", Context.MODE_PRIVATE);
        status.put("latest_heart_rate_bpm", healthState.getFloat("heart_rate_bpm", -1f));
        status.put("latest_heart_rate_at", healthState.getString("heart_rate_at", null));
        status.put("latest_daily_steps", healthState.getLong("daily_steps", -1L));
        status.put("latest_daily_steps_at", healthState.getString("daily_steps_at", null));
        status.put("latest_spo2_pct", healthState.getFloat("spo2_pct", -1f));
        status.put("latest_spo2_at", healthState.getString("spo2_at", null));
        status.put("latest_skin_temp_c", healthState.getFloat("skin_temp_c", -1f));
        status.put("latest_skin_temp_at", healthState.getString("skin_temp_at", null));
        status.put("latest_activity_state", healthState.getString("activity_state", null));
        status.put("latest_activity_state_at", healthState.getString("activity_state_at", null));
        status.put("latest_sleep_stage", healthState.getString("sleep_stage", null));
        status.put("latest_sleep_at", healthState.getString("sleep_at", null));
        status.put("latest_vo2_max", healthState.getFloat("vo2_max", -1f));
        status.put("latest_vo2_max_at", healthState.getString("vo2_max_at", null));
        status.put("queued_wear_batches", getWearQueue().size());
        status.put("health_connect_permissions", new ArrayList<>(requiredHealthConnectPermissions()));
        return status;
    }

    private void requestHealthConnectPermissions(MethodChannel.Result result) {
        if (pendingHealthPermissionResult != null) {
            result.error("HEALTH_CONNECT_PERMISSION_IN_PROGRESS", "Health Connect permission request is already in progress.", null);
            return;
        }

        pendingHealthPermissionResult = result;
        Intent intent = healthPermissionContract.createIntent(this, requiredHealthConnectPermissions());
        startActivityForResult(intent, HEALTH_CONNECT_PERMISSION_REQUEST_CODE);
    }

    private void startWearHealthMonitoring(MethodChannel.Result result) {
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_WATCH)) {
            result.error("NOT_WEAR_OS", "Health Services monitoring is available on Wear OS watches.", null);
            return;
        }
        if (pendingWearHealthResult != null) {
            result.error("SENSOR_PERMISSION_IN_PROGRESS", "Sensor permission request is already in progress.", null);
            return;
        }
        pendingWearHealthResult = result;
        pendingWearPermissionOnly = false;
        activityRecognitionRequestAttempted = false;
        String heartRatePermission = Build.VERSION.SDK_INT >= 36
                ? "android.permission.health.READ_HEART_RATE"
                : android.Manifest.permission.BODY_SENSORS;
        if (checkSelfPermission(heartRatePermission) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                    new String[]{heartRatePermission},
                    BODY_SENSOR_PERMISSION_REQUEST_CODE);
            return;
        }
        requestBackgroundPermissionOrRegister();
    }

    private void requestWearExercisePermissions(MethodChannel.Result result) {
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_WATCH)) {
            result.error("NOT_WEAR_OS", "Exercise tracking is available on Wear OS watches.", null);
            return;
        }
        if (pendingWearHealthResult != null) {
            result.error("SENSOR_PERMISSION_IN_PROGRESS", "A sensor permission request is already in progress.", null);
            return;
        }
        pendingWearHealthResult = result;
        pendingWearPermissionOnly = true;
        activityRecognitionRequestAttempted = false;
        String heartRatePermission = Build.VERSION.SDK_INT >= 36
                ? "android.permission.health.READ_HEART_RATE"
                : android.Manifest.permission.BODY_SENSORS;
        if (checkSelfPermission(heartRatePermission) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{heartRatePermission}, BODY_SENSOR_PERMISSION_REQUEST_CODE);
            return;
        }
        requestBackgroundPermissionOrRegister();
    }

    private void getWearHealthCapabilities(MethodChannel.Result result) {
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_WATCH)) {
            result.success(WearHealthServices.capabilitySnapshot(this));
            return;
        }
        new Thread(() -> {
            try {
                Map<String, Object> capabilities = WearHealthServices.capabilitySnapshot(this);
                runOnUiThread(() -> result.success(capabilities));
            } catch (Exception error) {
                runOnUiThread(() -> result.error(
                        "HEALTH_CAPABILITY_QUERY_FAILED",
                        error.getMessage() == null ? "Could not query watch capabilities." : error.getMessage(),
                        null));
            }
        }, "wmax-health-capabilities").start();
    }

    private void startWearExercise(String exerciseType, MethodChannel.Result result) {
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_WATCH)) {
            result.error("NOT_WEAR_OS", "Exercise tracking is available on Wear OS watches.", null);
            return;
        }
        Intent intent = new Intent()
                .setClassName(getPackageName(), "com.wmax.mobile_flutter.WearExerciseService")
                .setAction("com.wmax.mobile_flutter.action.START_EXERCISE")
                .putExtra("exercise_type",
                        exerciseType == null ? "WALKING" : exerciseType);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(intent);
            else startService(intent);
            result.success(true);
        } catch (Exception error) {
            result.error("EXERCISE_START_FAILED", error.getMessage(), null);
        }
    }

    private void stopWearExercise(MethodChannel.Result result) {
        Intent intent = new Intent()
                .setClassName(getPackageName(), "com.wmax.mobile_flutter.WearExerciseService")
                .setAction("com.wmax.mobile_flutter.action.STOP_EXERCISE");
        try {
            startService(intent);
            result.success(true);
        } catch (Exception error) {
            result.error("EXERCISE_STOP_FAILED", error.getMessage(), null);
        }
    }

    private Map<String, Object> getWearExerciseStatus() {
        android.content.SharedPreferences prefs = getSharedPreferences(
                "wmax_exercise_state", Context.MODE_PRIVATE);
        Map<String, Object> status = new HashMap<>();
        status.put("active", prefs.getBoolean("active", false));
        status.put("state", prefs.getString("status", "idle"));
        status.put("exercise_type", prefs.getString("type", null));
        status.put("start_time", prefs.getString("start_time", null));
        status.put("heart_rate_bpm", prefs.getFloat("latest_hr_value", -1f));
        status.put("heart_rate_at", prefs.getString("latest_hr_at", null));
        status.put("error", prefs.getString("error", null));
        return status;
    }

    private void requestBackgroundPermissionOrRegister() {
        if (!activityRecognitionRequestAttempted
                && checkSelfPermission(android.Manifest.permission.ACTIVITY_RECOGNITION) != PackageManager.PERMISSION_GRANTED) {
            activityRecognitionRequestAttempted = true;
            requestPermissions(
                    new String[]{android.Manifest.permission.ACTIVITY_RECOGNITION},
                    ACTIVITY_RECOGNITION_PERMISSION_REQUEST_CODE);
            return;
        }
        String backgroundSensorPermission = Build.VERSION.SDK_INT >= 36
                ? "android.permission.health.READ_HEALTH_DATA_IN_BACKGROUND"
                : "android.permission.BODY_SENSORS_BACKGROUND";
        if (!pendingWearPermissionOnly && Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(backgroundSensorPermission) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                    new String[]{backgroundSensorPermission},
                    BACKGROUND_SENSOR_PERMISSION_REQUEST_CODE);
            return;
        }
        if (pendingWearPermissionOnly) {
            MethodChannel.Result pending = pendingWearHealthResult;
            pendingWearHealthResult = null;
            pendingWearPermissionOnly = false;
            if (pending != null) pending.success(true);
        } else {
            registerWearHealthMonitoring();
        }
    }

    private void registerWearHealthMonitoring() {
        WearHealthServices.register(this, new WearHealthRegistrationCallback() {
            @Override
            public void onComplete(boolean registered, String message) {
                runOnUiThread(() -> {
                    MethodChannel.Result pending = pendingWearHealthResult;
                    pendingWearHealthResult = null;
                    pendingWearPermissionOnly = false;
                    if (pending == null) return;
                    if (registered) {
                        Map<String, Object> status = new HashMap<>();
                        status.put("registered", true);
                        status.put("metric", "heart_rate_bpm");
                        pending.success(status);
                    } else {
                        pending.error("HEALTH_SERVICES_REGISTRATION_FAILED", message, null);
                    }
                });
            }
        });
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == BODY_SENSOR_PERMISSION_REQUEST_CODE) {
            if (grantResults.length == 0 || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                finishWearHealthRequest("HEART_RATE_PERMISSION_DENIED");
            } else {
                requestBackgroundPermissionOrRegister();
            }
        } else if (requestCode == BACKGROUND_SENSOR_PERMISSION_REQUEST_CODE) {
            if (grantResults.length == 0 || grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                finishWearHealthRequest("BACKGROUND_SENSOR_PERMISSION_DENIED");
            } else {
                requestBackgroundPermissionOrRegister();
            }
        } else if (requestCode == ACTIVITY_RECOGNITION_PERMISSION_REQUEST_CODE) {
            requestBackgroundPermissionOrRegister();
        }
    }

    private void finishWearHealthRequest(String error) {
        MethodChannel.Result pending = pendingWearHealthResult;
        pendingWearHealthResult = null;
        pendingWearPermissionOnly = false;
        if (pending != null) pending.error(error, "Sensor access is required for passive heart-rate monitoring.", null);
    }

    private void acknowledgeWearQueue(ArrayList<String> acknowledged) {
        WmaxWearDataListenerService.acknowledgePayloads(this, acknowledged);
    }

    private ArrayList<String> getWearQueue() {
        return WmaxWearDataListenerService.getQueuedPayloads(this);
    }

    private boolean isPackageInstalled(String packageName) {
        try {
            getPackageManager().getPackageInfo(packageName, 0);
            return true;
        } catch (PackageManager.NameNotFoundException ignored) {
            return false;
        }
    }

    private void openHealthConnectSettings() {
        Intent intent;
        if (Build.VERSION.SDK_INT >= 34) {
            intent = new Intent(ACTION_HEALTH_CONNECT_SETTINGS);
        } else {
            intent = getPackageManager().getLaunchIntentForPackage("com.google.android.apps.healthdata");
            if (intent == null) {
                intent = new Intent(Settings.ACTION_APPLICATION_SETTINGS);
            }
        }
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != HEALTH_CONNECT_PERMISSION_REQUEST_CODE) {
            return;
        }

        MethodChannel.Result pending = pendingHealthPermissionResult;
        pendingHealthPermissionResult = null;
        if (pending == null) {
            return;
        }

        Set<String> granted = healthPermissionContract.parseResult(resultCode, data);
        Set<String> requested = requiredHealthConnectPermissions();
        Set<String> missing = new HashSet<>(requested);
        missing.removeAll(granted);

        Map<String, Object> payload = new HashMap<>();
        payload.put("granted", new ArrayList<>(granted));
        payload.put("missing", new ArrayList<>(missing));
        payload.put("all_granted", missing.isEmpty());
        pending.success(payload);
    }

    private Set<String> requiredHealthConnectPermissions() {
        Set<String> permissions = new HashSet<>();
        permissions.add(HealthPermission.READ_HEART_RATE);
        permissions.add(HealthPermission.READ_RESTING_HEART_RATE);
        permissions.add(HealthPermission.READ_HEART_RATE_VARIABILITY);
        permissions.add(HealthPermission.READ_OXYGEN_SATURATION);
        permissions.add(HealthPermission.READ_RESPIRATORY_RATE);
        permissions.add(HealthPermission.READ_SKIN_TEMPERATURE);
        permissions.add(HealthPermission.READ_BODY_TEMPERATURE);
        permissions.add(HealthPermission.READ_BLOOD_PRESSURE);
        permissions.add(HealthPermission.READ_BLOOD_GLUCOSE);
        permissions.add(HealthPermission.READ_WEIGHT);
        permissions.add(HealthPermission.READ_BODY_FAT);
        permissions.add(HealthPermission.READ_VO2_MAX);
        permissions.add(HealthPermission.READ_STEPS);
        permissions.add(HealthPermission.READ_DISTANCE);
        permissions.add(HealthPermission.READ_ACTIVE_CALORIES_BURNED);
        permissions.add(HealthPermission.READ_TOTAL_CALORIES_BURNED);
        permissions.add(HealthPermission.READ_SPEED);
        permissions.add(HealthPermission.READ_SLEEP);
        permissions.add(HealthPermission.READ_EXERCISE);
        return permissions;
    }
}

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val releaseStoreFile = providers.gradleProperty("WMAX_UPLOAD_STORE_FILE").orNull
    ?: System.getenv("WMAX_UPLOAD_STORE_FILE")
val releaseStorePassword = providers.gradleProperty("WMAX_UPLOAD_STORE_PASSWORD").orNull
    ?: System.getenv("WMAX_UPLOAD_STORE_PASSWORD")
val releaseKeyAlias = providers.gradleProperty("WMAX_UPLOAD_KEY_ALIAS").orNull
    ?: System.getenv("WMAX_UPLOAD_KEY_ALIAS")
val releaseKeyPassword = providers.gradleProperty("WMAX_UPLOAD_KEY_PASSWORD").orNull
    ?: System.getenv("WMAX_UPLOAD_KEY_PASSWORD")
val hasReleaseSigning = listOf(
    releaseStoreFile,
    releaseStorePassword,
    releaseKeyAlias,
    releaseKeyPassword,
).all { !it.isNullOrBlank() }

android {
    namespace = "com.wmax.mobile_flutter"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = "27.1.12297006"

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.wmax.mobile_flutter"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = 26
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    flavorDimensions += "device"
    productFlavors {
        create("phone") {
            dimension = "device"
            minSdk = 26
        }
        create("wear") {
            dimension = "device"
            minSdk = 30
        }
    }

    buildTypes {
        if (hasReleaseSigning) {
            signingConfigs.create("release") {
                storeFile = file(releaseStoreFile!!)
                storePassword = releaseStorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
            }
        }
        release {
            if (hasReleaseSigning) signingConfig = signingConfigs.getByName("release")
        }
    }
}

flutter {
    source = "../.."
}

dependencies {
    implementation("com.google.android.gms:play-services-wearable:20.0.1")
    implementation("androidx.health.connect:connect-client:1.1.0")
    add("wearImplementation", "androidx.health:health-services-client:1.1.0-rc02")
    add("wearImplementation", "com.google.guava:guava:32.0.1-android")
    add("wearImplementation", "androidx.work:work-runtime-ktx:2.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
}

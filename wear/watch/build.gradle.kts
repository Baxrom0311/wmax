plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "uz.wmax.watch"
    compileSdk = 34

    defaultConfig {
        applicationId = "uz.wmax.watch"
        minSdk = 30
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        // Supplied at build time; never commit live patient credentials.
        buildConfigField("String", "WMAX_PATIENT_ID", "\"${project.findProperty("WMAX_PATIENT_ID") ?: ""}\"")
        buildConfigField("String", "WMAX_INGEST_KEY", "\"${project.findProperty("WMAX_INGEST_KEY") ?: ""}\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)

    // Wear Compose
    implementation(libs.wear.compose.material)
    implementation(libs.wear.compose.foundation)
    implementation(libs.wear.compose.navigation)

    // Health Services & Play Services Wearable
    implementation(libs.health.services)
    implementation(libs.play.services.wearable)

    // Coroutines & Guava for ListenableFuture interop
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.kotlinx.coroutines.guava)
    implementation(libs.kotlinx.coroutines.play.services)
    implementation(libs.guava)

    // Networking for direct Wi-Fi/LTE ingestion to https://wmax.boos.uz/
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)

    // JSON serialization
    implementation(libs.gson)
}

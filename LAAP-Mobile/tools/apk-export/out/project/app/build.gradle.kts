plugins {
    id("com.android.application")
}

android {
    namespace = "org.laap.webapp.testapp"
    compileSdk = 35
    defaultConfig {
        applicationId = "org.laap.webapp.testapp"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
    signingConfigs {
        create("release") {
            storeFile = file(System.getProperty("user.home") + "/.android/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
            enableV1Signing = true
            enableV2Signing = true
            enableV3Signing = true
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity:1.9.3")
}

// AndroidX pulls kotlin-stdlib via different versions (1.8.22 from core-ktx,
// 1.6.21 jdk7/jdk8 from activity). kotlin-stdlib 1.8.22 already contains the
// jdk7/jdk8 classes, so drop the legacy split jars to avoid duplicate classes.
configurations.configureEach {
    exclude(group = "org.jetbrains.kotlin", module = "kotlin-stdlib-jdk7")
    exclude(group = "org.jetbrains.kotlin", module = "kotlin-stdlib-jdk8")
}

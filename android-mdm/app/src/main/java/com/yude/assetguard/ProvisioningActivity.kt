package com.yude.assetguard

import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.PersistableBundle
import android.provider.Settings

class ProvisioningActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        when (intent.action) {
            DevicePolicyManager.ACTION_GET_PROVISIONING_MODE -> handleProvisioningMode()
            DevicePolicyManager.ACTION_ADMIN_POLICY_COMPLIANCE -> handlePolicyCompliance()
            else -> {
                setResult(RESULT_CANCELED)
                finish()
            }
        }
    }

    private fun handleProvisioningMode() {
        val allowed = intent.getIntegerArrayListExtra(
            DevicePolicyManager.EXTRA_PROVISIONING_ALLOWED_PROVISIONING_MODES
        )

        val fullyManaged = DevicePolicyManager.PROVISIONING_MODE_FULLY_MANAGED_DEVICE
        if (allowed != null && !allowed.contains(fullyManaged)) {
            setResult(RESULT_CANCELED)
            finish()
            return
        }

        val result = Intent().apply {
            putExtra(DevicePolicyManager.EXTRA_PROVISIONING_MODE, fullyManaged)
            provisioningExtras()?.let {
                putExtra(DevicePolicyManager.EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE, it)
            }
        }
        setResult(RESULT_OK, result)
        finish()
    }

    private fun handlePolicyCompliance() {
        val extras = provisioningExtras()
        val serverUrl = extras?.getString("server_url")?.trim()?.trimEnd('/')
        val enrollmentToken = extras?.getString("enrollment_token")?.trim()

        if (SecureStore.getDeviceToken(this) != null) {
            setResult(RESULT_OK)
            finish()
            return
        }

        if (serverUrl.isNullOrBlank() || enrollmentToken.isNullOrBlank()) {
            // Provisioning can still complete; enrollment can be finished manually in the app.
            setResult(RESULT_OK)
            finish()
            return
        }

        if (!serverUrl.startsWith("https://", ignoreCase = true)) {
            setResult(RESULT_CANCELED)
            finish()
            return
        }

        val androidId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
        Thread {
            try {
                val result = AssetApi.enroll(serverUrl, enrollmentToken, androidId)
                getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
                    .edit()
                    .putString("server_url", serverUrl)
                    .putString("device_id", result.deviceId)
                    .apply()
                SecureStore.putDeviceToken(this, result.deviceToken)
                HeartbeatScheduler.schedule(this)
                runOnUiThread {
                    setResult(RESULT_OK)
                    finish()
                }
            } catch (_: Exception) {
                runOnUiThread {
                    setResult(RESULT_CANCELED)
                    finish()
                }
            }
        }.start()
    }

    @Suppress("DEPRECATION")
    private fun provisioningExtras(): PersistableBundle? {
        return intent.getParcelableExtra(
            DevicePolicyManager.EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE
        ) as? PersistableBundle
    }
}

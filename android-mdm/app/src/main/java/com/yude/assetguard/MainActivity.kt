package com.yude.assetguard

import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.os.Bundle
import android.provider.Settings
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var serverUrl: EditText
    private lateinit var enrollmentToken: EditText

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val prefs = getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
        val dpm = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val admin = ComponentName(this, YudeDeviceAdminReceiver::class.java)
        val isDeviceOwner = dpm.isDeviceOwnerApp(packageName)
        val isAdmin = dpm.isAdminActive(admin)
        val androidId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 48, 40, 40)
        }

        val title = TextView(this).apply {
            text = "YUDE Asset Guard"
            textSize = 26f
        }

        status = TextView(this).apply {
            textSize = 16f
            setPadding(0, 18, 0, 18)
            text = buildString {
                appendLine("Estado MDM")
                appendLine("Device Owner: " + if (isDeviceOwner) "ACTIVO" else "NO")
                appendLine("Device Admin: " + if (isAdmin) "ACTIVO" else "NO")
                appendLine("Android ID: " + androidId)
                appendLine("Modelo: " + android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL)
                appendLine("Android: " + android.os.Build.VERSION.RELEASE)
                appendLine("Enrolado: " + if (prefs.getString("device_token", null) != null) "SÍ" else "NO")
            }
        }

        serverUrl = EditText(this).apply {
            hint = "https://assets.empresa.com"
            setText(prefs.getString("server_url", ""))
        }
        enrollmentToken = EditText(this).apply {
            hint = "Token de enrolamiento"
        }

        val enrollButton = Button(this).apply {
            text = "Enrolar tablet"
            setOnClickListener { enroll(androidId) }
        }
        val heartbeatButton = Button(this).apply {
            text = "Enviar heartbeat"
            setOnClickListener { sendHeartbeat() }
        }

        root.addView(title)
        root.addView(status)
        root.addView(serverUrl, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        root.addView(enrollmentToken, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        root.addView(enrollButton)
        root.addView(heartbeatButton)
        setContentView(root)

        if (prefs.getString("device_token", null) != null) scheduleHeartbeat()
    }

    private fun enroll(androidId: String) {
        val url = serverUrl.text.toString().trim().trimEnd('/')
        val token = enrollmentToken.text.toString().trim()
        if (!url.startsWith("https://") || token.isBlank()) {
            status.append("\nSe requiere URL HTTPS y token.")
            return
        }

        status.append("\nEnrolando...")
        Thread {
            try {
                val result = AssetApi.enroll(url, token, androidId)
                getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
                    .edit()
                    .putString("server_url", url)
                    .putString("device_id", result.deviceId)
                    .putString("device_token", result.deviceToken)
                    .apply()
                runOnUiThread {
                    enrollmentToken.setText("")
                    status.append("\nEnrolamiento correcto: " + result.deviceId)
                    scheduleHeartbeat()
                }
            } catch (e: Exception) {
                runOnUiThread { status.append("\nError: " + e.message) }
            }
        }.start()
    }

    private fun sendHeartbeat() {
        status.append("\nEnviando heartbeat...")
        Thread {
            try {
                val result = AssetApi.heartbeat(this)
                runOnUiThread { status.append("\nHeartbeat OK. Lost mode: " + result.lostMode) }
            } catch (e: Exception) {
                runOnUiThread { status.append("\nError: " + e.message) }
            }
        }.start()
    }

    private fun scheduleHeartbeat() {
        val work = PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES).build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "assetguard-heartbeat",
            ExistingPeriodicWorkPolicy.UPDATE,
            work
        )
    }
}

package com.yude.assetguard

import android.app.Activity
import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import android.os.Bundle
import android.provider.Settings
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val dpm = getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val admin = ComponentName(this, YudeDeviceAdminReceiver::class.java)
        val isDeviceOwner = dpm.isDeviceOwnerApp(packageName)
        val isAdmin = dpm.isAdminActive(admin)
        val androidId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)

        val title = TextView(this).apply {
            text = "YUDE Asset Guard"
            textSize = 26f
        }
        val state = TextView(this).apply {
            text = buildString {
                appendLine("Estado MDM")
                appendLine("Device Owner: ${if (isDeviceOwner) "ACTIVO" else "NO"}")
                appendLine("Device Admin: ${if (isAdmin) "ACTIVO" else "NO"}")
                appendLine("Android ID: $androidId")
                appendLine("Modelo: ${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}")
                appendLine("Android: ${android.os.Build.VERSION.RELEASE}")
            }
            textSize = 17f
            setPadding(0, 24, 0, 0)
        }

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(40, 56, 40, 40)
            addView(title)
            addView(state)
        }
        setContentView(root)
    }
}

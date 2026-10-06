package com.yude.assetguard

import android.content.Context
import android.os.BatteryManager
import android.provider.Settings
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

data class EnrollResult(val deviceId: String, val deviceToken: String)
data class HeartbeatResult(val lostMode: Boolean, val rotated: Boolean)

object AssetApi {
    fun enroll(serverUrl: String, enrollmentToken: String, androidId: String): EnrollResult {
        val payload = JSONObject()
            .put("enrollment_token", enrollmentToken)
            .put("hostname", android.os.Build.MODEL)
            .put("serial", androidId)
            .put("platform", "android")
            .put("os_version", "Android " + android.os.Build.VERSION.RELEASE)
            .put("architecture", android.os.Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown")
            .put("agent_version", "0.2.0")
            .put("manufacturer", android.os.Build.MANUFACTURER)
            .put("model", android.os.Build.MODEL)
            .put("hardware_uuid", androidId)

        val response = post(serverUrl + "/api/v1/enroll", null, payload)
        return EnrollResult(
            response.getString("device_id"),
            response.getString("device_token")
        )
    }

    fun heartbeat(context: Context): HeartbeatResult {
        val prefs = context.getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
        val serverUrl = prefs.getString("server_url", null) ?: error("Servidor no configurado")
        val deviceToken = prefs.getString("device_token", null) ?: error("Tablet no enrolada")
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        val battery = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val percent = battery.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)

        val payload = JSONObject()
            .put("hostname", android.os.Build.MODEL)
            .put("serial", androidId)
            .put("os_version", "Android " + android.os.Build.VERSION.RELEASE)
            .put("architecture", android.os.Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown")
            .put("agent_version", "0.2.0")
            .put("manufacturer", android.os.Build.MANUFACTURER)
            .put("model", android.os.Build.MODEL)
            .put("hardware_uuid", androidId)
            .put("battery_percent", percent)

        val response = post(serverUrl + "/api/v1/heartbeat", deviceToken, payload)
        val rotatedToken = response.optString("device_token", "")
        var rotated = false
        if (rotatedToken.isNotBlank() && rotatedToken != deviceToken) {
            prefs.edit().putString("device_token", rotatedToken).apply()
            rotated = true
        }
        return HeartbeatResult(
            response.optBoolean("lost_mode", false),
            rotated
        )
    }

    private fun post(url: String, bearer: String?, payload: JSONObject): JSONObject {
        val connection = URL(url).openConnection() as HttpURLConnection
        connection.requestMethod = "POST"
        connection.connectTimeout = 15000
        connection.readTimeout = 15000
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json")
        if (!bearer.isNullOrBlank()) {
            connection.setRequestProperty("Authorization", "Bearer " + bearer)
        }

        connection.outputStream.use {
            it.write(payload.toString().toByteArray(Charsets.UTF_8))
        }

        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
        if (code !in 200..299) {
            error("HTTP " + code + ": " + body.take(300))
        }
        return JSONObject(body)
    }
}

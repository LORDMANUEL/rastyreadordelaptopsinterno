package com.yude.assetguard

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

object SecureStore {
    private const val keyAlias = "yude_asset_guard_device_identity"
    private const val prefsName = "asset_guard_secure"
    private const val tokenCiphertextKey = "device_token_ciphertext"
    private const val tokenIvKey = "device_token_iv"

    private fun keyStore(): KeyStore =
        KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    private fun getOrCreateKey(): SecretKey {
        val store = keyStore()
        val existing = store.getKey(keyAlias, null) as? SecretKey
        if (existing != null) return existing

        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(
            KeyGenParameterSpec.Builder(
                keyAlias,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }

    fun putDeviceToken(context: Context, value: String) {
        require(value.isNotBlank()) { "device token cannot be blank" }

        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())

        val ciphertext = cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        val prefs = context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
        prefs.edit()
            .putString(tokenCiphertextKey, Base64.encodeToString(ciphertext, Base64.NO_WRAP))
            .putString(tokenIvKey, Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .apply()

        // Remove legacy plaintext token after successful secure persistence.
        context.getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
            .edit()
            .remove("device_token")
            .apply()
    }

    fun getDeviceToken(context: Context): String? {
        val securePrefs = context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
        val ciphertextValue = securePrefs.getString(tokenCiphertextKey, null)
        val ivValue = securePrefs.getString(tokenIvKey, null)

        if (!ciphertextValue.isNullOrBlank() && !ivValue.isNullOrBlank()) {
            return try {
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(
                    Cipher.DECRYPT_MODE,
                    getOrCreateKey(),
                    GCMParameterSpec(128, Base64.decode(ivValue, Base64.NO_WRAP))
                )
                val plain = cipher.doFinal(Base64.decode(ciphertextValue, Base64.NO_WRAP))
                plain.toString(Charsets.UTF_8)
            } catch (_: Exception) {
                null
            }
        }

        // One-time migration from the pre-Keystore implementation.
        val legacyPrefs = context.getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
        val legacy = legacyPrefs.getString("device_token", null)
        if (!legacy.isNullOrBlank()) {
            putDeviceToken(context, legacy)
            return legacy
        }
        return null
    }

    fun clearDeviceToken(context: Context) {
        context.getSharedPreferences(prefsName, Context.MODE_PRIVATE)
            .edit()
            .remove(tokenCiphertextKey)
            .remove(tokenIvKey)
            .apply()
        context.getSharedPreferences("asset_guard", Context.MODE_PRIVATE)
            .edit()
            .remove("device_token")
            .apply()
    }
}

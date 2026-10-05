package com.yude.assetguard

import android.content.Context
import androidx.work.Worker
import androidx.work.WorkerParameters

class HeartbeatWorker(
    context: Context,
    params: WorkerParameters
) : Worker(context, params) {
    override fun doWork(): Result {
        return try {
            AssetApi.heartbeat(applicationContext)
            Result.success()
        } catch (_: Exception) {
            Result.retry()
        }
    }
}

package com.yude.assetguard

import android.content.Context
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

object HeartbeatScheduler {
    fun schedule(context: Context) {
        val work = PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES).build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "assetguard-heartbeat",
            ExistingPeriodicWorkPolicy.UPDATE,
            work
        )
    }
}

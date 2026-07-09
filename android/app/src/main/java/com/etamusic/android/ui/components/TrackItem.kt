package com.etamusic.android.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.etamusic.android.data.model.Track

@Composable
fun TrackItem(
    track: Track,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = { Text(track.title) },
        supportingContent = {
            Text(track.artist ?: "未知艺术家")
        },
        trailingContent = {
            track.duration?.let { dur ->
                val min = (dur / 60).toInt()
                val sec = (dur % 60).toInt()
                Text(String.format("%d:%02d", min, sec))
            }
        },
        modifier = Modifier.clickable(onClick = onClick)
    )
}

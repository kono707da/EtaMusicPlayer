package com.etamusic.android.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.etamusic.android.data.model.Playlist

@Composable
fun PlaylistItem(
    playlist: Playlist,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = { Text(playlist.name) },
        supportingContent = {
            Text("${playlist.trackCount} 首歌曲")
        },
        modifier = Modifier.clickable(onClick = onClick)
    )
}

package com.etamusic.android.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun PlayerScreen() {
    Column(
        modifier = Modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Surface(
            modifier = Modifier.size(200.dp),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surfaceVariant
        ) {}
        Spacer(modifier = Modifier.height(24.dp))
        Text("正在播放", style = MaterialTheme.typography.titleLarge)
        Text("选择一首歌曲开始播放", style = MaterialTheme.typography.bodyMedium)
        Spacer(modifier = Modifier.height(24.dp))
        Row(
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            FilledTonalButton(onClick = {}) { Text("上一首") }
            Button(onClick = {}) { Text("播放") }
            FilledTonalButton(onClick = {}) { Text("下一首") }
        }
    }
}

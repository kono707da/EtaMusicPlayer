package com.etamusic.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import com.etamusic.android.ui.theme.EtaMusicTheme
import com.etamusic.android.ui.navigation.EtaMusicNavGraph
import com.etamusic.android.ui.components.MiniPlayer
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            EtaMusicTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    bottomBar = { MiniPlayer() }
                ) { innerPadding ->
                    EtaMusicNavGraph(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

package com.etamusic.android.playback

import androidx.media3.session.MediaSessionService

class PlaybackService : MediaSessionService() {
    override fun onDestroy() {
        super.onDestroy()
    }
}

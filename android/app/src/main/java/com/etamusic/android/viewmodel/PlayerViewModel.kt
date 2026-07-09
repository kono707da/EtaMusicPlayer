package com.etamusic.android.viewmodel

import androidx.lifecycle.ViewModel
import com.etamusic.android.data.model.Track
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject

@HiltViewModel
class PlayerViewModel @Inject constructor() : ViewModel() {
    private val _currentTrack = MutableStateFlow<Track?>(null)
    val currentTrack: StateFlow<Track?> = _currentTrack

    private val _isPlaying = MutableStateFlow(false)
    val isPlaying: StateFlow<Boolean> = _isPlaying

    fun play(track: Track) {
        _currentTrack.value = track
        _isPlaying.value = true
    }

    fun togglePlayback() {
        _isPlaying.value = !_isPlaying.value
    }
}

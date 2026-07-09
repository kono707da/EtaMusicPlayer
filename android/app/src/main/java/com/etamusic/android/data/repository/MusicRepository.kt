package com.etamusic.android.data.repository

import com.etamusic.android.data.api.EtaMusicApi
import com.etamusic.android.data.model.Playlist
import com.etamusic.android.data.model.Track
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MusicRepository @Inject constructor(
    private val api: EtaMusicApi
) {
    suspend fun login(username: String, password: String): Result<String> = runCatching {
        val response = api.login(username, password)
        response.accessToken
    }

    suspend fun getTracks(page: Int = 1, search: String? = null): Result<Pair<List<Track>, Int>> = runCatching {
        val response = api.getTracks(page = page, search = search)
        response.items to response.total
    }

    suspend fun getPlaylists(): Result<List<Playlist>> = runCatching {
        api.getPlaylists()
    }

    suspend fun getPlaylistTracks(playlistId: Int): Result<List<Track>> = runCatching {
        val response = api.getPlaylistTracks(playlistId)
        response.items
    }
}

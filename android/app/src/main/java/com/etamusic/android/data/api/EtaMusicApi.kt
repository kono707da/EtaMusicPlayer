package com.etamusic.android.data.api

import com.etamusic.android.data.model.AuthResponse
import com.etamusic.android.data.model.Playlist
import com.etamusic.android.data.model.Track
import retrofit2.http.*

interface EtaMusicApi {

    @POST("local_node/api/auth/login")
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String
    ): AuthResponse

    @GET("local_node/api/tracks")
    suspend fun getTracks(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 50,
        @Query("search") search: String? = null
    ): TrackListResponse

    @GET("local_node/api/tracks/{id}/stream")
    suspend fun getStreamUrl(@Path("id") trackId: Int): String

    @GET("local_node/api/playlists")
    suspend fun getPlaylists(): List<Playlist>

    @GET("local_node/api/playlists/{id}/tracks")
    suspend fun getPlaylistTracks(@Path("id") playlistId: Int): TrackListResponse

    @GET("api/plugins")
    suspend fun getPlugins(): PluginListResponse

    data class TrackListResponse(val items: List<Track>, val total: Int, val page: Int, val pages: Int)
    data class PluginListResponse(val items: List<PluginInfo>)
    data class PluginInfo(val name: String, val description: String, val version: String, val enabled: Boolean)
}

package com.etamusic.android.data.model

data class Playlist(
    val id: Int,
    val name: String,
    val description: String? = null,
    @com.google.gson.annotations.SerializedName("is_system")
    val isSystem: Boolean = false,
    @com.google.gson.annotations.SerializedName("track_count")
    val trackCount: Int = 0,
    @com.google.gson.annotations.SerializedName("owner_id")
    val ownerId: Int? = null
)

package com.etamusic.android.data.model

import com.google.gson.annotations.SerializedName

data class Track(
    val id: Int,
    val title: String,
    val artist: String? = null,
    val album: String? = null,
    val duration: Float? = null,
    @SerializedName("file_path")
    val filePath: String? = null,
    @SerializedName("file_size")
    val fileSize: Long? = null,
    @SerializedName("cover_path")
    val coverPath: String? = null,
    val format: String? = null,
    val bitrate: Int? = null
)

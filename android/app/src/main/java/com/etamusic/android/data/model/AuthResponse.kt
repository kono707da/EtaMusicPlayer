package com.etamusic.android.data.model

data class AuthResponse(
    @com.google.gson.annotations.SerializedName("access_token")
    val accessToken: String,
    @com.google.gson.annotations.SerializedName("token_type")
    val tokenType: String = "bearer"
)

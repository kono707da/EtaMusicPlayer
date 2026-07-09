package com.etamusic.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.etamusic.android.ui.screens.LibraryScreen
import com.etamusic.android.ui.screens.LoginScreen
import com.etamusic.android.ui.screens.PlaylistsScreen

object Routes {
    const val LOGIN = "login"
    const val LIBRARY = "library"
    const val PLAYLISTS = "playlists"
}

@Composable
fun EtaMusicNavGraph(
    modifier: Modifier = Modifier,
    navController: NavHostController = rememberNavController()
) {
    NavHost(
        navController = navController,
        startDestination = Routes.LOGIN,
        modifier = modifier
    ) {
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Routes.LIBRARY) {
                        popUpTo(Routes.LOGIN) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.LIBRARY) {
            LibraryScreen(
                onNavigateToPlaylists = { navController.navigate(Routes.PLAYLISTS) }
            )
        }
        composable(Routes.PLAYLISTS) {
            PlaylistsScreen()
        }
    }
}

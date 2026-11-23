import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/register_screen.dart';
import '../../features/auth/presentation/screens/splash_screen.dart';
import '../../features/auth/presentation/screens/forgot_password_screen.dart';
import '../../features/auth/presentation/screens/verify_otp_screen.dart';
import '../../features/auth/presentation/screens/set_new_password_screen.dart';
import '../../features/auth/presentation/screens/password_changed_screen.dart';
import '../../features/auth/providers/auth_provider.dart';

import '../../features/dashboard/presentation/screens/main_shell_screen.dart';

import '../../features/ask_fm/ask_fm_screen.dart';

import '../../features/farm/presentation/screens/add_farm_screen.dart';

import '../../features/farmer/presentation/screens/edit_profile_screen.dart';

import '../../features/onboarding/screens/post_login_onboarding_screen.dart';

GoRouter createRouter(AuthProvider authProvider) {
  return GoRouter(
    initialLocation: '/',
    refreshListenable: authProvider,

    // ==========================================================
    // REDIRECT
    // ==========================================================
    redirect: (context, state) {
      final status = authProvider.status;
      final location = state.matchedLocation;

      // ========================================================
      // ROUTE FLAGS
      // ========================================================

      final isSplash = location == '/';
      final isLogin = location == '/login';
      final isRegister = location == '/register';

      // Password recovery is reached while logged out, so the recovery
      // routes are part of the unauthenticated whitelist.
      final isForgotPassword = location == '/forgot-password' ||
          location == '/verify-otp' ||
          location == '/set-new-password' ||
          location == '/password-changed';

      final isOnboarding = location == '/onboarding';

      final isDashboard = location == '/dashboard';
      final isEditProfile = location == '/edit-profile';
      final isAddFarm = location == '/add-farm';
      final isAskFm = location == '/ask-fm';

      final isAuthScreen = isLogin || isRegister || isForgotPassword;

      // ========================================================
      // SPLASH
      // ========================================================

      if (isSplash) {
        return null;
      }

      // ========================================================
      // WAIT FOR AUTH INITIALIZATION / LOGIN
      // ========================================================

      if (status == AuthStatus.initial || status == AuthStatus.loading) {
        return null;
      }

      // ========================================================
      // AUTHENTICATION STATUS
      // ========================================================

      final isAuthenticated = status == AuthStatus.authenticated;

      // ========================================================
      // NOT AUTHENTICATED
      // ========================================================

      if (!isAuthenticated) {
        if (isAuthScreen) {
          return null;
        }

        return '/login';
      }

      // ========================================================
      // AUTHENTICATED
      //
      // No farmer profile:
      //     → Post-login AI onboarding
      //
      // Farmer profile exists:
      //     → Dashboard
      // ========================================================

      if (!authProvider.hasFarmerProfile) {
        if (isOnboarding) {
          return null;
        }

        return '/onboarding';
      }

      // ========================================================
      // FARMER PROFILE EXISTS
      // ========================================================

      if (isDashboard) {
        return null;
      }

      if (isEditProfile) {
        return null;
      }

      if (isAddFarm) {
        return null;
      }

      if (isAskFm) {
        return null;
      }

      // ========================================================
      // DEFAULT
      // ========================================================

      return '/dashboard';
    },

    // ==========================================================
    // ROUTES
    // ==========================================================
    routes: [
      // ========================================================
      // SPLASH
      // ========================================================
      GoRoute(
        path: '/',
        builder: (context, state) {
          return const SplashScreen();
        },
      ),

      // ========================================================
      // LOGIN
      // ========================================================
      GoRoute(
        path: '/login',
        builder: (context, state) {
          return const LoginScreen();
        },
      ),

      // ========================================================
      // REGISTER
      // ========================================================
      GoRoute(
        path: '/register',
        builder: (context, state) {
          return const RegisterScreen();
        },
      ),

      // ========================================================
      // POST-LOGIN AI ONBOARDING
      //
      // Flow:
      //
      // Login
      //   ↓
      // Location
      //   ↓
      // Language
      //   ↓
      // Experience
      //   ↓
      // Profile Created
      //   ↓
      // Add Farm?   ← we will design this next
      // ========================================================
      GoRoute(
        path: '/onboarding',
        builder: (context, state) {
          return const PostLoginOnboardingScreen();
        },
      ),

      // ========================================================
      // DASHBOARD
      // ========================================================
      GoRoute(
        path: '/dashboard',
        builder: (context, state) {
          return const MainShellScreen();
        },
      ),

      // ========================================================
      // EDIT PROFILE
      // ========================================================
      GoRoute(
        path: '/edit-profile',
        builder: (context, state) {
          return const EditProfileScreen();
        },
      ),

      // ========================================================
      // ADD FARM
      // ========================================================
      GoRoute(
        path: '/add-farm',
        builder: (context, state) {
          return const AddFarmScreen();
        },
      ),

      // ========================================================
      // ASK FM
      // ========================================================
      GoRoute(
        path: '/ask-fm',
        builder: (context, state) {
          return const AskFMScreen();
        },
      ),

      // ========================================================
      // FORGOT PASSWORD
      // ========================================================
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          return ForgotPasswordScreen(
            initialEmail: args?['email']?.toString() ?? '',
          );
        },
      ),

      // ========================================================
      // VERIFY OTP
      // ========================================================
      GoRoute(
        path: '/verify-otp',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          return VerifyOtpsScreen(
            initialEmail: args?['email']?.toString() ?? '',
          );
        },
      ),

      // ========================================================
      // SET NEW PASSWORD
      // ========================================================
      GoRoute(
        path: '/set-new-password',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          return SetNewPasswordScreen(
            resetToken: args?['reset_token']?.toString() ?? '',
            expiresAt: args?['expires_at']?.toString() ?? '',
            email: args?['email']?.toString() ?? '',
          );
        },
      ),

      // ========================================================
      // PASSWORD CHANGED
      // ========================================================
      GoRoute(
        path: '/password-changed',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          return PasswordChangedScreen(
            email: args?['email']?.toString() ?? '',
          );
        },
      ),
    ],
  );
}

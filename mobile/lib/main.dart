import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import 'firebase_options.dart';

import 'app/router/app_router.dart';
import 'app/theme/app_theme.dart';

import 'core/network/api_client.dart';

import 'features/notifications/data/device_token_repository.dart';
import 'features/notifications/services/notification_navigation.dart';
import 'features/notifications/services/push_message.dart';
import 'features/notifications/services/push_messaging_client.dart';
import 'features/notifications/services/push_notification_service.dart';

// ============================================================
// AUTH
// ============================================================

import 'features/auth/data/auth_repository.dart';
import 'features/auth/providers/auth_provider.dart';

// ============================================================
// ONBOARDING
// ============================================================

import 'features/onboarding/data/onboarding_repository.dart';
import 'features/onboarding/providers/onboarding_provider.dart';

// ============================================================
// WEATHER
// ============================================================

import 'features/weather/providers/weather_provider.dart';
import 'features/weather/data/models/weather_repository.dart';

// ============================================================
// DASHBOARD
// ============================================================

import 'features/dashboard/providers/dashboard_provider.dart';
import 'features/dashboard/data/repositories/dashboard_repository.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (error) {
    debugPrint('Firebase initialization skipped/failed: $error');
  }

  // ============================================================
  // SHARED API CLIENT
  // ============================================================

  final apiClient = ApiClient();

  // ============================================================
  // PUSH NOTIFICATIONS
  // ============================================================

  final pushNotificationService = PushNotificationService(
    deviceRepository: DeviceTokenRepository(apiClient: apiClient),
  );

  final firebaseReady = await pushNotificationService.initialize();

  if (firebaseReady) {
    try {
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
    } catch (_) {
      // Background message handling is optional and must not block startup.
    }
  }

  // ============================================================
  // ONBOARDING REPOSITORY
  // ============================================================

  final onboardingRepository = OnboardingRepository(apiClient: apiClient);

  // ============================================================
  // ONBOARDING PROVIDER
  // ============================================================

  final onboardingProvider = OnboardingProvider(
    repository: onboardingRepository,
  );

  // ============================================================
  // AUTH REPOSITORY
  // ============================================================

  final authRepository = AuthRepository(apiClient: apiClient);

  // ============================================================
  // AUTH PROVIDER
  // ============================================================

  final authProvider = AuthProvider(
    authRepository: authRepository,
    onboardingProvider: onboardingProvider,
    onBeforeLogout: pushNotificationService.unregisterCurrentDevice,
  );

  // ============================================================
  // WEATHER REPOSITORY
  // ============================================================

  final weatherRepository = WeatherRepository(apiClient: apiClient);

  // ============================================================
  // WEATHER PROVIDER
  // ============================================================

  final weatherProvider = WeatherProvider(weatherRepository: weatherRepository);

  // ============================================================
  // DASHBOARD REPOSITORY
  // ============================================================

  final dashboardRepository = DashboardRepository(apiClient: apiClient);

  // ============================================================
  // DASHBOARD PROVIDER
  // ============================================================

  final dashboardProvider = DashboardProvider(repository: dashboardRepository);

  // ============================================================
  // CHECK AUTHENTICATION
  // ============================================================

  await authProvider.checkAuthStatus();

  pushNotificationService.bind(
    authListenable: authProvider,
    isAuthenticated: () => authProvider.isAuthenticated,
  );

  // ============================================================
  // START APPLICATION
  // ============================================================

  final router = createRouter(authProvider);
  final messengerKey = GlobalKey<ScaffoldMessengerState>();

  void openNotification(PushMessage message) {
    final route = NotificationNavigation.resolveRoute(
      message,
      isAuthenticated: authProvider.isAuthenticated,
    );

    if (route != null) {
      router.go(route);
    }
  }

  pushNotificationService.foregroundMessages.listen((message) {
    final messenger = messengerKey.currentState;

    if (messenger == null) {
      return;
    }

    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            message.body.isEmpty ? message.title : message.body,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          action: SnackBarAction(
            label: 'Open',
            onPressed: () => openNotification(message),
          ),
        ),
      );
  });

  pushNotificationService.openedMessages.listen(openNotification);

  runApp(
    FarmMateApp(
      authProvider: authProvider,
      onboardingProvider: onboardingProvider,
      weatherProvider: weatherProvider,
      dashboardProvider: dashboardProvider,
      router: router,
      scaffoldMessengerKey: messengerKey,
    ),
  );

  WidgetsBinding.instance.addPostFrameCallback((_) {
    unawaited(pushNotificationService.syncAuthState());
    unawaited(pushNotificationService.handleInitialMessage());
  });
}

// ============================================================
// FARM MATE APP
// ============================================================

class FarmMateApp extends StatelessWidget {
  const FarmMateApp({
    super.key,
    required this.authProvider,
    required this.onboardingProvider,
    required this.weatherProvider,
    required this.dashboardProvider,
    required this.router,
    required this.scaffoldMessengerKey,
  });

  final AuthProvider authProvider;
  final OnboardingProvider onboardingProvider;
  final WeatherProvider weatherProvider;
  final DashboardProvider dashboardProvider;
  final GoRouter router;
  final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // ========================================================
        // AUTH
        // ========================================================
        ChangeNotifierProvider<AuthProvider>.value(value: authProvider),

        // ========================================================
        // ONBOARDING
        // ========================================================
        ChangeNotifierProvider<OnboardingProvider>.value(
          value: onboardingProvider,
        ),

        // ========================================================
        // WEATHER
        // ========================================================
        ChangeNotifierProvider<WeatherProvider>.value(value: weatherProvider),

        // ========================================================
        // DASHBOARD
        // ========================================================
        ChangeNotifierProvider<DashboardProvider>.value(
          value: dashboardProvider,
        ),
      ],

      // ==========================================================
      // APP
      // ==========================================================
      child: MaterialApp.router(
        debugShowCheckedModeBanner: false,
        title: 'FarmMate AI',
        theme: AppTheme.lightTheme,
        scaffoldMessengerKey: scaffoldMessengerKey,
        routerConfig: router,
      ),
    );
  }
}

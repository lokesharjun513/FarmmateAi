import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/dashboard/data/models/dashboard_model.dart';
import 'package:mobile/features/dashboard/data/repositories/dashboard_repository.dart';
import 'package:mobile/features/dashboard/presentation/screens/home_tab.dart';
import 'package:mobile/features/dashboard/providers/dashboard_provider.dart';
import 'package:provider/provider.dart';

class FakeDashboardRepository extends DashboardRepository {
  FakeDashboardRepository({this.dashboard, this.error, this.completer});

  DashboardModel? dashboard;
  Object? error;
  Completer<DashboardModel>? completer;
  int calls = 0;

  @override
  Future<DashboardModel> getDashboard() async {
    calls++;

    if (completer != null) {
      return completer!.future;
    }

    if (error != null) {
      throw error!;
    }

    return dashboard!;
  }
}

DashboardModel testDashboard({
  bool withFarm = true,
  bool withCrop = true,
  bool weatherAvailable = true,
  bool advisorAvailable = true,
  bool activeSession = false,
  String farmerName = 'Test Farmer',
  String farmName = 'North Field',
  String village = 'Ramapuram',
  String mandal = 'Kavali',
  String district = 'Nellore',
  String cropName = 'Paddy',
  String variety = 'BPT 5204',
  String stage = 'Tillering',
  String season = 'Kharif 2026',
  String advisorSummary = 'Irrigate before noon.',
  int progress = 38,
  int todayTasks = 2,
  int pendingTasks = 4,
  int completedTasks = 7,
  List<Map<String, dynamic>>? activities,
}) {
  final dashboardActivities =
      activities ??
      [
        {
          'id': 'activity-1',
          'title': 'Check field moisture',
          'activity_type': 'IRRIGATION',
          'priority': 'HIGH',
          'status': 'PENDING',
          'scheduled_date': '2026-10-22',
        },
        {
          'id': 'activity-2',
          'title': 'Inspect leaf health',
          'activity_type': 'MONITORING',
          'priority': 'LOW',
          'status': 'COMPLETED',
          'scheduled_date': '2026-10-22',
        },
      ];

  return DashboardModel.fromJson({
    'greeting': 'Hello',
    'farmer': {
      'id': 'farmer-1',
      'full_name': farmerName,
      'preferred_language': 'English',
    },
    'farm': withFarm
        ? {
            'id': 'farm-1',
            'farm_name': farmName,
            'village': village,
            'mandal': mandal,
            'district': district,
            'state': 'Andhra Pradesh',
            'land_area': 2.5,
            'land_unit': 'Acres',
            'soil_type': 'Clay',
            'water_source': 'Borewell',
            'is_primary': true,
          }
        : null,
    'active_crop': withCrop
        ? {
            'id': 'crop-1',
            'crop_name': cropName,
            'crop_variety': variety,
            'season': season,
            'crop_age_days': 45,
            'estimated_duration_days': 120,
            'progress_percentage': progress,
            'current_stage': {'name': stage},
          }
        : null,
    'weather': {
      'temperature': weatherAvailable ? 31 : 0,
      'humidity': weatherAvailable ? 64 : 0,
      'condition': weatherAvailable ? 'Sunny' : 'Unavailable',
      'rain_probability': weatherAvailable ? 20 : null,
      'is_available': weatherAvailable,
    },
    'advisor': {
      'summary': advisorSummary,
      'priority': 'HIGH',
      'available': advisorAvailable,
    },
    'stats': {
      'total_tasks': pendingTasks + completedTasks,
      'pending_tasks': pendingTasks,
      'completed_tasks': completedTasks,
      'today_tasks': todayTasks,
    },
    'activities': dashboardActivities,
    'ask_fm': {'active_session': activeSession},
  });
}

Widget buildHomeApp({
  required DashboardProvider provider,
  VoidCallback? onOpenProfile,
  VoidCallback? onOpenFarms,
  double textScale = 1,
}) {
  final router = GoRouter(
    routes: [
      GoRoute(
        path: '/',
        builder: (_, _) =>
            HomeTab(onOpenProfile: onOpenProfile, onOpenFarms: onOpenFarms),
      ),
      GoRoute(
        path: '/add-farm',
        builder: (_, _) => const Scaffold(body: Text('Add Farm route')),
      ),
      GoRoute(
        path: '/ask-fm',
        builder: (_, _) => const Scaffold(body: Text('Ask FarmMate route')),
      ),
      GoRoute(
        path: '/edit-profile',
        builder: (_, _) => const Scaffold(body: Text('Edit Profile route')),
      ),
    ],
  );

  addTearDown(router.dispose);

  return ChangeNotifierProvider<DashboardProvider>.value(
    value: provider,
    child: MaterialApp.router(
      theme: AppTheme.lightTheme,
      routerConfig: router,
      builder: (context, child) {
        final mediaQuery = MediaQuery.of(context);

        return MediaQuery(
          data: mediaQuery.copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        );
      },
    ),
  );
}

void setPhoneSize(WidgetTester tester, {Size size = const Size(390, 844)}) {
  tester.view
    ..physicalSize = size
    ..devicePixelRatio = 1;

  addTearDown(() {
    tester.view
      ..resetPhysicalSize()
      ..resetDevicePixelRatio();
  });
}

Future<void> scrollTo(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    250,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pumpAndSettle();
}

DashboardProvider providerFor(DashboardModel dashboard) {
  final provider = DashboardProvider(
    repository: FakeDashboardRepository(dashboard: dashboard),
  );

  addTearDown(provider.dispose);

  return provider;
}

void main() {
  testWidgets('renders the redesigned dashboard and primary sections', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = providerFor(testDashboard());
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    expect(find.textContaining('Hello, Test'), findsOneWidget);
    expect(find.text('North Field'), findsOneWidget);
    expect(find.text('Ramapuram, Kavali, Nellore'), findsOneWidget);
    expect(find.text('2.5 Acres'), findsOneWidget);
    expect(find.text('Sunny'), findsOneWidget);
    expect(find.text('64%'), findsOneWidget);
    expect(find.text('Irrigate before noon.'), findsOneWidget);
    expect(find.text('High'), findsOneWidget);

    await scrollTo(tester, find.text('Paddy'));

    expect(find.text('Paddy'), findsOneWidget);
    expect(find.text('BPT 5204'), findsOneWidget);
    expect(find.text('Tillering'), findsOneWidget);
    expect(find.text('Kharif 2026'), findsOneWidget);
    expect(find.text('38%'), findsOneWidget);

    await scrollTo(tester, find.text('Farm tasks'));

    expect(find.text('Today'), findsOneWidget);
    expect(find.text('Crop pending'), findsOneWidget);
    expect(find.text('Crop completed'), findsOneWidget);
    expect(find.text('Check field moisture'), findsOneWidget);
    expect(find.text('Inspect leaf health'), findsOneWidget);

    await scrollTo(tester, find.byKey(const Key('home_ask_farmmate_button')));

    expect(find.text('Ask FarmMate'), findsOneWidget);
    expect(
      find.text('Ask about pests, weather, or crop health.'),
      findsOneWidget,
    );

    await scrollTo(tester, find.byKey(const Key('home_quick_edit_profile')));

    expect(find.text('Quick actions'), findsOneWidget);
    expect(find.text('Edit profile'), findsOneWidget);
    expect(find.text('Refresh'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('loading, empty and error states render and recover', (
    tester,
  ) async {
    setPhoneSize(tester);

    final completer = Completer<DashboardModel>();
    final repository = FakeDashboardRepository(completer: completer);
    final provider = DashboardProvider(repository: repository);
    addTearDown(provider.dispose);

    unawaited(provider.loadDashboard());

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pump();

    expect(find.text('Preparing your dashboard'), findsOneWidget);

    completer.complete(testDashboard());
    await tester.pumpAndSettle();

    expect(find.text('Preparing your dashboard'), findsNothing);
    expect(find.text('North Field'), findsOneWidget);

    final emptyProvider = DashboardProvider(
      repository: FakeDashboardRepository(dashboard: testDashboard()),
    );
    addTearDown(emptyProvider.dispose);

    await tester.pumpWidget(buildHomeApp(provider: emptyProvider));
    await tester.pumpAndSettle();

    expect(find.text('Welcome to FarmMate AI'), findsOneWidget);

    await tester.tap(find.byKey(const Key('home_dashboard_load_button')));
    await tester.pumpAndSettle();

    expect(find.text('North Field'), findsOneWidget);

    final errorProvider = DashboardProvider(
      repository: FakeDashboardRepository(
        error: Exception('Unable to load dashboard.'),
      ),
    );
    addTearDown(errorProvider.dispose);

    await errorProvider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: errorProvider));
    await tester.pumpAndSettle();

    expect(find.text('Dashboard unavailable'), findsOneWidget);
    expect(find.text('Unable to load dashboard.'), findsOneWidget);
    expect(
      find.byKey(const Key('home_dashboard_retry_button')),
      findsOneWidget,
    );
  });

  testWidgets('no-farm state opens Add Farm', (tester) async {
    setPhoneSize(tester);

    final provider = providerFor(
      testDashboard(withFarm: false, withCrop: false, advisorAvailable: false),
    );
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    expect(find.text('Your farm is not set up yet'), findsOneWidget);
    expect(find.text('No crop advice yet'), findsOneWidget);

    await tester.tap(find.byKey(const Key('home_add_farm_button')));
    await tester.pumpAndSettle();

    expect(find.text('Add Farm route'), findsOneWidget);
  });

  testWidgets('Ask FarmMate opens the chat route', (tester) async {
    setPhoneSize(tester);

    final provider = providerFor(testDashboard());
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    await scrollTo(tester, find.byKey(const Key('home_ask_farmmate_button')));
    await tester.tap(find.byKey(const Key('home_ask_farmmate_button')));
    await tester.pumpAndSettle();

    expect(find.text('Ask FarmMate route'), findsOneWidget);
  });

  testWidgets('farm card opens the farms tab action', (tester) async {
    setPhoneSize(tester);

    var farmsOpened = false;
    final provider = providerFor(testDashboard());
    await provider.refreshDashboard();

    await tester.pumpWidget(
      buildHomeApp(
        provider: provider,
        onOpenFarms: () {
          farmsOpened = true;
        },
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('home_view_farms_button')));
    await tester.pump();

    expect(farmsOpened, isTrue);
  });

  testWidgets('profile avatar invokes the profile action', (tester) async {
    setPhoneSize(tester);

    var profileTapped = false;
    final provider = providerFor(testDashboard());
    await provider.refreshDashboard();

    await tester.pumpWidget(
      buildHomeApp(
        provider: provider,
        onOpenProfile: () {
          profileTapped = true;
        },
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('home_profile_button')));
    await tester.pump();

    expect(profileTapped, isTrue);
  });

  testWidgets('weather unavailable state is honest and refreshable', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeDashboardRepository(
      dashboard: testDashboard(weatherAvailable: false),
    );
    final provider = DashboardProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    await scrollTo(tester, find.text('Weather unavailable'));

    expect(find.text('Weather unavailable'), findsOneWidget);
    expect(find.text('31°'), findsNothing);

    await tester.tap(find.byKey(const Key('home_weather_refresh_button')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
  });

  testWidgets('advisor unavailable state is honest and retryable', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeDashboardRepository(
      dashboard: testDashboard(advisorAvailable: false),
    );
    final provider = DashboardProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    await scrollTo(tester, find.text('Advice unavailable'));

    expect(find.text('Advice unavailable'), findsOneWidget);
    expect(find.text('High'), findsNothing);

    await tester.tap(find.byKey(const Key('home_advisor_retry_button')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
  });

  testWidgets('stale dashboard remains visible and retry recovers', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeDashboardRepository(dashboard: testDashboard());
    final provider = DashboardProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.refreshDashboard();

    repository.error = Exception('Refresh failed.');

    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    expect(find.text('North Field'), findsOneWidget);
    expect(
      find.text('Couldn’t refresh. Showing your last loaded dashboard.'),
      findsOneWidget,
    );

    repository.error = null;

    await tester.tap(find.byKey(const Key('home_stale_retry_button')));
    await tester.pumpAndSettle();

    expect(
      find.text('Couldn’t refresh. Showing your last loaded dashboard.'),
      findsNothing,
    );
    expect(find.text('North Field'), findsOneWidget);
  });

  testWidgets('active crop and task activity render from backend data', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = providerFor(testDashboard());
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider));
    await tester.pumpAndSettle();

    await scrollTo(tester, find.text('Farm tasks'));

    expect(find.text('Today'), findsOneWidget);
    expect(find.text('Crop pending'), findsOneWidget);
    expect(find.text('Crop completed'), findsOneWidget);
    expect(find.text('Check field moisture'), findsOneWidget);
    expect(find.text('Pending'), findsOneWidget);
    expect(find.text('Completed'), findsOneWidget);
  });

  testWidgets('narrow screens and larger text do not overflow', (tester) async {
    setPhoneSize(tester, size: const Size(320, 568));

    final provider = providerFor(
      testDashboard(
        farmerName: 'Venkata Ramana Reddy',
        farmName: 'North Field Agricultural Research Farm',
        village: 'Ramapuram Agraharam',
        mandal: 'Kavali Revenue Mandal',
        district: 'Nellore District',
        cropName: 'Long Duration Paddy Variety',
        variety: 'BPT 5204 Improved Selection',
        stage: 'Late Tillering Stage',
        season: 'Kharif Season 2026',
        advisorSummary:
            'Irrigate the field before noon and inspect the lower leaves for early signs of pest damage.',
      ),
    );
    await provider.refreshDashboard();

    await tester.pumpWidget(buildHomeApp(provider: provider, textScale: 1.25));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);

    await scrollTo(tester, find.byKey(const Key('home_ask_farmmate_button')));
    expect(tester.takeException(), isNull);

    await scrollTo(tester, find.byKey(const Key('home_quick_refresh')));
    expect(tester.takeException(), isNull);
  });
}

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/auth/data/models/user_model.dart';
import 'package:mobile/features/auth/providers/auth_provider.dart';
import 'package:mobile/features/dashboard/data/models/dashboard_model.dart';
import 'package:mobile/features/dashboard/data/repositories/dashboard_repository.dart';
import 'package:mobile/features/dashboard/providers/dashboard_provider.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:mobile/features/farm/presentation/screens/add_farm_screen.dart';
import 'package:mobile/features/farm/presentation/widgets/add_farm_form.dart';
import 'package:mobile/features/farmer/data/farmer_repository.dart';
import 'package:mobile/features/farmer/data/models/farmer_profile_model.dart';
import 'package:mobile/features/onboarding/screens/post_login_onboarding_screen.dart';
import 'package:mobile/features/weather/location_service.dart';
import 'package:provider/provider.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository({this.error, this.completer, FarmModel? farm})
    : farm = farm ?? testFarm();

  Object? error;
  Completer<FarmModel>? completer;
  FarmModel farm;

  int createCalls = 0;
  FarmCreateInput? lastInput;

  @override
  Future<FarmModel> createFarm(FarmCreateInput input) async {
    createCalls++;
    lastInput = input;

    if (completer != null) {
      return completer!.future;
    }

    if (error != null) {
      throw error!;
    }

    return farm;
  }
}

class FakeDashboardRepository extends DashboardRepository {
  FakeDashboardRepository(this.dashboard);

  final DashboardModel dashboard;
  int calls = 0;

  @override
  Future<DashboardModel> getDashboard() async {
    calls++;
    return dashboard;
  }
}

class FakeOnboardingAuthProvider extends ChangeNotifier
    implements AuthProvider {
  bool profileCreated = false;

  @override
  AuthStatus get status => AuthStatus.authenticated;

  @override
  Future<void> Function()? get onBeforeLogout => null;

  @override
  UserModel? get user => null;

  @override
  String? get errorMessage => null;

  @override
  bool get isAuthenticated => true;

  @override
  bool get isUnauthenticated => false;

  @override
  bool get isLoading => false;

  @override
  bool get isInitial => false;

  @override
  bool get hasUser => false;

  @override
  bool get hasFarmerProfile => profileCreated;

  @override
  bool get needsFarmerOnboarding => !profileCreated;

  @override
  Future<void> checkAuthStatus() async {}

  @override
  Future<bool> login({
    required String identifier,
    required String password,
  }) async {
    return false;
  }

  @override
  Future<bool> register({
    required String fullName,
    required String mobile,
    required String email,
    required String password,
  }) async {
    return false;
  }

  @override
  Future<bool> refreshFarmerProfile() async => profileCreated;

  @override
  void markFarmerProfileCreated() {
    profileCreated = true;
    notifyListeners();
  }

  @override
  Future<void> logout() async {}

  @override
  void clearError() {}
}

class FakeFarmerRepository extends FarmerRepository {
  int createCalls = 0;
  int updateCalls = 0;

  @override
  Future<FarmerProfileModel?> getProfile() async => null;

  @override
  Future<FarmerProfileModel> createProfile({
    required String preferredLanguage,
    required int experienceYears,
  }) async {
    createCalls++;
    return FarmerProfileModel(
      id: 'farmer-1',
      userId: 'user-1',
      preferredLanguage: preferredLanguage,
      experienceYears: experienceYears,
      profileCompletion: 60,
      onboardingCompleted: false,
    );
  }

  @override
  Future<FarmerProfileModel> updateProfile({
    required String preferredLanguage,
    required int experienceYears,
  }) async {
    updateCalls++;
    return createProfile(
      preferredLanguage: preferredLanguage,
      experienceYears: experienceYears,
    );
  }
}

class FakeLocationService extends LocationService {
  const FakeLocationService();

  @override
  Future<LocationData?> getCurrentLocation() async {
    return const LocationData(
      latitude: 14.9167,
      longitude: 79.9944,
      locationName: 'Ramapuram, Nellore',
      state: 'Andhra Pradesh',
      district: 'Nellore',
      mandal: 'Kavali',
      village: 'Ramapuram',
    );
  }
}

class AddFarmHost extends StatefulWidget {
  const AddFarmHost({
    super.key,
    required this.repository,
    required this.onResult,
  });

  final FarmRepository repository;
  final ValueChanged<bool?> onResult;

  @override
  State<AddFarmHost> createState() => _AddFarmHostState();
}

class _AddFarmHostState extends State<AddFarmHost> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          key: const Key('open_add_farm_button'),
          onPressed: () async {
            final result = await Navigator.of(context).push<bool>(
              MaterialPageRoute(
                builder: (_) => AddFarmScreen(repository: widget.repository),
              ),
            );

            if (!mounted) {
              return;
            }

            widget.onResult(result);
          },
          child: const Text('Open Add Farm'),
        ),
      ),
    );
  }
}

FarmModel testFarm() {
  return const FarmModel(
    id: 'farm-1',
    farmerId: 'farmer-1',
    farmName: 'North Field',
    state: 'Andhra Pradesh',
    district: 'Nellore',
    mandal: 'Kavali',
    village: 'Ramapuram',
    latitude: 14.9167,
    longitude: 79.9944,
    landArea: 2.5,
    landUnit: 'Acres',
    soilType: 'Clay',
    waterSource: 'Borewell',
    waterAvailability: 'HIGH',
    irrigationMethod: 'Drip',
    isPrimary: true,
  );
}

DashboardModel dashboardWithFarm() {
  return DashboardModel.fromJson({
    'greeting': 'Hello',
    'farmer': {
      'id': 'farmer-1',
      'full_name': 'Test Farmer',
      'preferred_language': 'English',
    },
    'farm': {
      'id': 'farm-1',
      'farm_name': 'North Field',
      'village': 'Ramapuram',
      'mandal': 'Kavali',
      'district': 'Nellore',
      'state': 'Andhra Pradesh',
      'land_area': 2.5,
      'land_unit': 'Acres',
      'is_primary': true,
    },
    'weather': {
      'temperature': 30,
      'humidity': 60,
      'condition': 'Clear',
      'is_available': true,
    },
    'advisor': {
      'summary': 'Check soil moisture.',
      'priority': 'LOW',
      'available': true,
    },
    'stats': {
      'total_tasks': 0,
      'pending_tasks': 0,
      'in_progress_tasks': 0,
      'completed_tasks': 0,
      'skipped_tasks': 0,
      'today_tasks': 0,
      'today_completed_tasks': 0,
      'today_pending_tasks': 0,
      'today_in_progress_tasks': 0,
    },
    'activities': [],
    'ask_fm': {'active_session': false},
  });
}

Widget buildForm({
  required FakeFarmRepository repository,
  ValueChanged<FarmModel>? onContinue,
}) {
  return MaterialApp(
    theme: AppTheme.lightTheme,
    home: Scaffold(
      body: AddFarmForm(
        repository: repository,
        onContinue: onContinue ?? (_) {},
      ),
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

Future<void> fillRequiredFields(WidgetTester tester) async {
  await tester.enterText(
    find.byKey(const Key('farm_name_field')),
    'North Field',
  );
  await tester.enterText(
    find.byKey(const Key('farm_state_field')),
    'Andhra Pradesh',
  );
  await tester.enterText(
    find.byKey(const Key('farm_district_field')),
    'Nellore',
  );
  await tester.enterText(find.byKey(const Key('farm_mandal_field')), 'Kavali');
  await tester.enterText(
    find.byKey(const Key('farm_village_field')),
    'Ramapuram',
  );
  await tester.enterText(find.byKey(const Key('farm_land_area_field')), '2.5');
}

Future<void> tapSubmit(WidgetTester tester) async {
  final button = find.byKey(const Key('add_farm_submit_button'));

  await tester.ensureVisible(button);
  await tester.tap(button);
  await tester.pump();
}

void main() {
  testWidgets('valid farm creation shows success and returns created farm', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository();
    FarmModel? continuedFarm;

    await tester.pumpWidget(
      buildForm(
        repository: repository,
        onContinue: (farm) {
          continuedFarm = farm;
        },
      ),
    );

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(find.text('Farm added'), findsOneWidget);
    expect(find.text('North Field'), findsOneWidget);
    expect(repository.createCalls, 1);
    expect(repository.lastInput!.isPrimary, isTrue);
    expect(repository.lastInput!.landArea, 2.5);
    expect(repository.lastInput!.waterSource, isNull);

    await tester.ensureVisible(
      find.byKey(const Key('add_farm_continue_button')),
    );
    await tester.tap(find.byKey(const Key('add_farm_continue_button')));
    await tester.pumpAndSettle();

    expect(continuedFarm?.id, 'farm-1');
  });

  testWidgets('required fields show validation errors', (tester) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository();

    await tester.pumpWidget(buildForm(repository: repository));

    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(find.text('Farm name is required'), findsOneWidget);
    expect(find.text('State is required'), findsOneWidget);
    expect(find.text('District is required'), findsOneWidget);
    expect(find.text('Mandal is required'), findsOneWidget);
    expect(find.text('Village is required'), findsOneWidget);
    expect(find.text('Land area is required'), findsOneWidget);
    expect(repository.createCalls, 0);
  });

  testWidgets('API failure shows message and retry succeeds', (tester) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository(
      error: Exception('Unable to save farm right now.'),
    );

    await tester.pumpWidget(buildForm(repository: repository));

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(find.text('Unable to save farm right now.'), findsOneWidget);
    expect(repository.createCalls, 1);

    repository.error = null;

    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(repository.createCalls, 2);
    expect(find.text('Farm added'), findsOneWidget);
  });

  testWidgets('duplicate submissions are prevented while request is pending', (
    tester,
  ) async {
    setPhoneSize(tester);

    final completer = Completer<FarmModel>();
    final repository = FakeFarmRepository(completer: completer);

    await tester.pumpWidget(buildForm(repository: repository));

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tapSubmit(tester);

    expect(repository.createCalls, 1);

    completer.complete(testFarm());
    await tester.pumpAndSettle();

    expect(find.text('Farm added'), findsOneWidget);
  });

  testWidgets('add farm screen returns result and dashboard refreshes', (
    tester,
  ) async {
    setPhoneSize(tester);

    final farmRepository = FakeFarmRepository();
    bool? result;

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.lightTheme,
        home: AddFarmHost(
          repository: farmRepository,
          onResult: (value) {
            result = value;
          },
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('open_add_farm_button')));
    await tester.pumpAndSettle();

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    await tester.ensureVisible(
      find.byKey(const Key('add_farm_continue_button')),
    );
    await tester.tap(find.byKey(const Key('add_farm_continue_button')));
    await tester.pumpAndSettle();

    expect(result, isTrue);

    final dashboardRepository = FakeDashboardRepository(dashboardWithFarm());
    final dashboardProvider = DashboardProvider(
      repository: dashboardRepository,
    );

    await dashboardProvider.refreshDashboard();

    expect(dashboardProvider.dashboard?.farm?.farmName, 'North Field');
  });

  testWidgets('onboarding creates farm and lands on refreshed dashboard', (
    tester,
  ) async {
    setPhoneSize(tester);

    final farmRepository = FakeFarmRepository();
    final farmerRepository = FakeFarmerRepository();
    final authProvider = FakeOnboardingAuthProvider();
    final dashboardRepository = FakeDashboardRepository(dashboardWithFarm());

    final router = GoRouter(
      initialLocation: '/onboarding',
      routes: [
        GoRoute(
          path: '/onboarding',
          builder: (_, _) => PostLoginOnboardingScreen(
            locationService: const FakeLocationService(),
            farmerRepository: farmerRepository,
            farmRepository: farmRepository,
          ),
        ),
        GoRoute(
          path: '/dashboard',
          builder: (_, _) => ChangeNotifierProvider<DashboardProvider>(
            create: (_) =>
                DashboardProvider(repository: dashboardRepository)
                  ..refreshDashboard(),
            child: Consumer<DashboardProvider>(
              builder: (_, provider, _) => Scaffold(
                body: Center(
                  child: Text(
                    provider.dashboard?.farm?.farmName ?? 'Dashboard loading',
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );

    addTearDown(router.dispose);

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: authProvider,
        child: MaterialApp.router(
          theme: AppTheme.lightTheme,
          routerConfig: router,
        ),
      ),
    );

    await tester.pumpAndSettle();

    await tester.tap(find.text('English'));
    await tester.pump();
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('1–3 years'));
    await tester.pump();
    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Continue'));
    await tester.pumpAndSettle();

    expect(find.text('Skip adding your farm?'), findsOneWidget);

    await tester.tap(find.text('Add My Farm'));
    await tester.pumpAndSettle();

    expect(farmerRepository.createCalls, 1);
    expect(find.byKey(const Key('farm_name_field')), findsOneWidget);

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    await tester.ensureVisible(
      find.byKey(const Key('add_farm_continue_button')),
    );
    await tester.tap(find.byKey(const Key('add_farm_continue_button')));
    await tester.pumpAndSettle();

    expect(authProvider.profileCreated, isTrue);
    expect(farmRepository.createCalls, 1);
    expect(dashboardRepository.calls, 1);
    expect(find.text('North Field'), findsOneWidget);
  });

  test('farm create input sends required fields and primary flag', () {
    const input = FarmCreateInput(
      farmName: ' North Field ',
      state: ' Andhra Pradesh ',
      district: ' Nellore ',
      mandal: ' Kavali ',
      village: ' Ramapuram ',
      latitude: 14.9167,
      longitude: 79.9944,
      landArea: 2.5,
      soilType: 'Clay',
      isPrimary: true,
    );

    final payload = input.toJson();

    expect(payload['farm_name'], 'North Field');
    expect(payload['state'], 'Andhra Pradesh');
    expect(payload['district'], 'Nellore');
    expect(payload['mandal'], 'Kavali');
    expect(payload['village'], 'Ramapuram');
    expect(payload['land_area'], 2.5);
    expect(payload['land_unit'], 'Acres');
    expect(payload['soil_type'], 'Clay');
    expect(payload['latitude'], 14.9167);
    expect(payload['longitude'], 79.9944);
    expect(payload['is_primary'], isTrue);
    expect(payload.containsKey('water_source'), isFalse);
  });
}

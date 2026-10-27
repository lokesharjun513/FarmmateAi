import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:mobile/features/farm/presentation/screens/farm_tab.dart';
import 'package:mobile/features/farm/providers/farm_provider.dart';
import 'package:provider/provider.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository({
    List<FarmModel>? farms,
    FarmModel? createdFarm,
    this.listError,
    this.createError,
    this.setPrimaryError,
  }) : farms = farms ?? const [],
       createdFarm =
           createdFarm ??
           testFarm(id: 'farm-new', name: 'New Field', isPrimary: true);

  List<FarmModel> farms;
  FarmModel createdFarm;
  Object? listError;
  Object? createError;
  Object? setPrimaryError;
  Completer<List<FarmModel>>? listCompleter;
  Completer<FarmModel>? createCompleter;
  Completer<FarmModel>? setPrimaryCompleter;
  int listCalls = 0;
  int createCalls = 0;
  int setPrimaryCalls = 0;
  FarmCreateInput? lastInput;
  String? lastPrimaryFarmId;

  @override
  Future<List<FarmModel>> getFarms() async {
    listCalls++;

    if (listCompleter != null) {
      return listCompleter!.future;
    }

    if (listError != null) {
      throw listError!;
    }

    return List<FarmModel>.of(farms);
  }

  @override
  Future<FarmModel> createFarm(FarmCreateInput input) async {
    createCalls++;
    lastInput = input;

    if (createCompleter != null) {
      return createCompleter!.future;
    }

    if (createError != null) {
      throw createError!;
    }

    return createdFarm;
  }

  @override
  Future<FarmModel> setPrimary(String farmId) async {
    setPrimaryCalls++;
    lastPrimaryFarmId = farmId;

    if (setPrimaryCompleter != null) {
      return setPrimaryCompleter!.future;
    }

    if (setPrimaryError != null) {
      throw setPrimaryError!;
    }

    final selected = farms.firstWhere((farm) => farm.id == farmId);

    return selected.copyWith(isPrimary: true);
  }
}

FarmModel testFarm({
  String id = 'farm-1',
  String name = 'North Field',
  bool isPrimary = true,
  String village = 'Ramapuram',
  String mandal = 'Kavali',
  String district = 'Nellore',
  String state = 'Andhra Pradesh',
  double landArea = 2.5,
  String landUnit = 'Acres',
  String? soilType = 'Clay',
  String? waterSource = 'Borewell',
  String? waterAvailability = 'HIGH',
  String? irrigationMethod = 'Drip',
}) {
  return FarmModel(
    id: id,
    farmerId: 'farmer-1',
    farmName: name,
    state: state,
    district: district,
    mandal: mandal,
    village: village,
    latitude: null,
    longitude: null,
    landArea: landArea,
    landUnit: landUnit,
    soilType: soilType,
    waterSource: waterSource,
    waterAvailability: waterAvailability,
    irrigationMethod: irrigationMethod,
    isPrimary: isPrimary,
  );
}

Widget buildFarmApp(
  FarmProvider provider, {
  ValueChanged<FarmModel>? onFarmCreated,
  ValueChanged<FarmModel>? onPrimaryChanged,
  double textScale = 1,
}) {
  return ChangeNotifierProvider<FarmProvider>.value(
    value: provider,
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      builder: (context, child) {
        final mediaQuery = MediaQuery.of(context);

        return MediaQuery(
          data: mediaQuery.copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        );
      },
      home: Scaffold(
        body: FarmTab(
          onFarmCreated: onFarmCreated,
          onPrimaryChanged: onPrimaryChanged,
        ),
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
  await tester.enterText(find.byKey(const Key('farm_name_field')), 'New Field');
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
  await tester.enterText(find.byKey(const Key('farm_land_area_field')), '1.5');
}

Future<void> tapSubmit(WidgetTester tester) async {
  final button = find.byKey(const Key('add_farm_submit_button'));

  await tester.ensureVisible(button);
  await tester.tap(button);
  await tester.pump();
}

void main() {
  testWidgets('shows a skeleton while farms are loading', (tester) async {
    setPhoneSize(tester);

    final completer = Completer<List<FarmModel>>();
    final repository = FakeFarmRepository()..listCompleter = completer;
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    unawaited(provider.loadFarms());

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pump();

    expect(find.byKey(const Key('farm_tab_loading')), findsOneWidget);
    expect(find.byKey(const Key('farm_tab_empty')), findsNothing);
    expect(find.byKey(const Key('farm_tab_error')), findsNothing);

    completer.complete(const []);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('farm_tab_empty')), findsOneWidget);
  });

  testWidgets('empty state adds the first farm as primary', (tester) async {
    setPhoneSize(tester);

    final provider = FarmProvider(
      repository: FakeFarmRepository(farms: const []),
    );
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('farm_tab_empty')), findsOneWidget);
    expect(find.text('No farms yet'), findsOneWidget);

    await tester.tap(find.byKey(const Key('farm_tab_empty_add_button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('add_farm_sheet')), findsOneWidget);
    expect(
      find.text(
        'This will be your primary farm and will appear on your Home dashboard.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('initial error retries into the loaded portfolio', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository(
      listError: Exception('Unable to load farms.'),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('farm_tab_error')), findsOneWidget);
    expect(find.text('Couldn’t load your farms'), findsOneWidget);
    expect(find.text('Unable to load farms.'), findsOneWidget);
    expect(find.byKey(const Key('farm_tab_add_button')), findsNothing);

    repository
      ..listError = null
      ..farms = [testFarm()];

    await tester.tap(find.byKey(const Key('farm_tab_retry_button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('farm_tab_error')), findsNothing);
    expect(find.byKey(const Key('farm_portfolio_summary')), findsOneWidget);
    expect(find.text('North Field'), findsOneWidget);
  });

  testWidgets(
    'portfolio shows primary farm and expands details independently',
    (tester) async {
      setPhoneSize(tester);

      final provider = FarmProvider(
        repository: FakeFarmRepository(
          farms: [
            testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
            testFarm(id: 'farm-1', name: 'North Field'),
          ],
        ),
      );
      addTearDown(provider.dispose);
      await provider.loadFarms();

      await tester.pumpWidget(buildFarmApp(provider));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('farm_portfolio_summary')), findsOneWidget);
      expect(find.text('Primary · North Field'), findsOneWidget);
      expect(find.text('Primary'), findsOneWidget);
      expect(find.text('2'), findsOneWidget);
      expect(find.text('5'), findsOneWidget);
      expect(find.text('Acres'), findsOneWidget);

      await tester.tap(find.byKey(const Key('farm_card_toggle_farm-1')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('farm_card_details_farm-1')), findsOneWidget);
      expect(find.text('Land area'), findsOneWidget);
      expect(find.text('Soil type'), findsOneWidget);
      expect(find.text('Water source'), findsOneWidget);
      expect(find.text('Water availability'), findsOneWidget);
      expect(find.text('High'), findsOneWidget);
      expect(find.text('Irrigation method'), findsOneWidget);
      expect(find.text('Farm details are view-only.'), findsOneWidget);

      final secondToggle = find.byKey(const Key('farm_card_toggle_farm-2'));
      await tester.scrollUntilVisible(secondToggle, 250);
      await tester.tap(secondToggle);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('farm_card_details_farm-1')), findsOneWidget);
      expect(find.byKey(const Key('farm_card_details_farm-2')), findsOneWidget);
    },
  );

  testWidgets('refresh failure keeps farms and offers retry', (tester) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository(farms: [testFarm()]);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    repository.listError = Exception('Refresh failed.');
    await provider.refreshFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    expect(find.text('North Field'), findsOneWidget);
    expect(
      find.text('Couldn’t refresh. Showing your last loaded farms.'),
      findsOneWidget,
    );

    repository.listError = null;

    await tester.tap(find.byKey(const Key('farm_tab_stale_retry_button')));
    await tester.pumpAndSettle();

    expect(
      find.text('Couldn’t refresh. Showing your last loaded farms.'),
      findsNothing,
    );
    expect(find.text('North Field'), findsOneWidget);
  });

  testWidgets('new farm creation updates the portfolio and expands it', (
    tester,
  ) async {
    setPhoneSize(tester);

    FarmModel? createdCallbackFarm;
    final repository = FakeFarmRepository(farms: const []);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(
      buildFarmApp(
        provider,
        onFarmCreated: (farm) {
          createdCallbackFarm = farm;
        },
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('farm_tab_empty_add_button')));
    await tester.pumpAndSettle();

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(find.text('Farm added'), findsOneWidget);
    expect(repository.createCalls, 1);
    expect(repository.lastInput!.isPrimary, isTrue);
    expect(provider.farms, hasLength(1));
    expect(provider.farms.single.id, 'farm-new');
    expect(createdCallbackFarm?.id, 'farm-new');

    await tester.ensureVisible(
      find.byKey(const Key('add_farm_continue_button')),
    );
    await tester.tap(find.byKey(const Key('add_farm_continue_button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('add_farm_sheet')), findsNothing);
    expect(find.byKey(const Key('farm_card_farm-new')), findsOneWidget);
    expect(find.byKey(const Key('farm_card_details_farm-new')), findsOneWidget);
    expect(find.text('New Field'), findsOneWidget);
  });

  testWidgets('additional farms default to non-primary', (tester) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository(
      farms: [testFarm()],
      createdFarm: testFarm(
        id: 'farm-new',
        name: 'New Field',
        isPrimary: false,
      ),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('farm_tab_add_button')));
    await tester.pumpAndSettle();

    expect(
      find.text(
        'This farm will be added to your farm profile. Your current primary farm will stay on Home.',
      ),
      findsOneWidget,
    );

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(repository.lastInput!.isPrimary, isFalse);
    expect(provider.farms, hasLength(2));
    expect(provider.farms.first.farmName, 'North Field');
    expect(provider.farms.last.farmName, 'New Field');
  });

  testWidgets('non-primary farm can be set as primary', (tester) async {
    setPhoneSize(tester);

    FarmModel? changedFarm;
    final repository = FakeFarmRepository(
      farms: [
        testFarm(id: 'farm-1', name: 'North Field'),
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
      ],
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(
      buildFarmApp(
        provider,
        onPrimaryChanged: (farm) {
          changedFarm = farm;
        },
      ),
    );
    await tester.pumpAndSettle();

    final secondToggle = find.byKey(const Key('farm_card_toggle_farm-2'));
    await tester.scrollUntilVisible(secondToggle, 250);
    await tester.tap(secondToggle);
    await tester.pumpAndSettle();

    final setPrimaryButton = find.byKey(const Key('farm_set_primary_farm-2'));
    await tester.drag(
      find.byKey(const Key('farm_tab_scroll')),
      const Offset(0, -220),
    );
    await tester.pumpAndSettle();
    await tester.tap(setPrimaryButton);
    await tester.pumpAndSettle();

    expect(repository.setPrimaryCalls, 1);
    expect(repository.lastPrimaryFarmId, 'farm-2');
    expect(provider.farms.map((farm) => farm.id), ['farm-2', 'farm-1']);
    expect(provider.farms.first.isPrimary, isTrue);
    expect(provider.farms.last.isPrimary, isFalse);
    expect(changedFarm?.id, 'farm-2');
    expect(find.text('South Field is now your primary farm.'), findsOneWidget);
    expect(find.text('Primary · South Field'), findsOneWidget);
    expect(find.byKey(const Key('farm_set_primary_farm-2')), findsNothing);
  });

  testWidgets('primary farm card has no set-primary action', (tester) async {
    setPhoneSize(tester);

    final provider = FarmProvider(
      repository: FakeFarmRepository(
        farms: [
          testFarm(id: 'farm-1', name: 'North Field'),
          testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        ],
      ),
    );
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('farm_card_toggle_farm-1')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('farm_set_primary_farm-1')), findsNothing);
  });

  testWidgets('failed primary switch keeps the previous primary', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository(
      farms: [
        testFarm(id: 'farm-1', name: 'North Field'),
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
      ],
      setPrimaryError: Exception('Unable to switch primary farm.'),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    final secondToggle = find.byKey(const Key('farm_card_toggle_farm-2'));
    await tester.scrollUntilVisible(secondToggle, 250);
    await tester.tap(secondToggle);
    await tester.pumpAndSettle();

    final setPrimaryButton = find.byKey(const Key('farm_set_primary_farm-2'));
    await tester.drag(
      find.byKey(const Key('farm_tab_scroll')),
      const Offset(0, -220),
    );
    await tester.pumpAndSettle();
    await tester.tap(setPrimaryButton);
    await tester.pumpAndSettle();

    expect(find.text('Unable to switch primary farm.'), findsOneWidget);
    expect(provider.farms.first.id, 'farm-1');
    expect(provider.farms.first.isPrimary, isTrue);
    expect(provider.farms.last.isPrimary, isFalse);
    expect(find.byKey(const Key('farm_set_primary_farm-2')), findsOneWidget);
  });

  testWidgets('primary switch shows a pending state', (tester) async {
    setPhoneSize(tester);

    final completer = Completer<FarmModel>();
    final repository = FakeFarmRepository(
      farms: [
        testFarm(id: 'farm-1', name: 'North Field'),
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
      ],
    )..setPrimaryCompleter = completer;
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    final secondToggle = find.byKey(const Key('farm_card_toggle_farm-2'));
    await tester.scrollUntilVisible(secondToggle, 250);
    await tester.tap(secondToggle);
    await tester.pumpAndSettle();

    final setPrimaryButton = find.byKey(const Key('farm_set_primary_farm-2'));
    await tester.drag(
      find.byKey(const Key('farm_tab_scroll')),
      const Offset(0, -220),
    );
    await tester.pumpAndSettle();
    await tester.tap(setPrimaryButton);
    await tester.pump();

    expect(find.text('Setting as primary…'), findsOneWidget);
    expect(tester.widget<OutlinedButton>(setPrimaryButton).onPressed, isNull);

    completer.complete(
      testFarm(id: 'farm-2', name: 'South Field', isPrimary: true),
    );
    await tester.pumpAndSettle();

    expect(provider.farms.first.id, 'farm-2');
    expect(find.text('South Field is now your primary farm.'), findsOneWidget);
  });

  testWidgets('modal failure keeps input and retry succeeds', (tester) async {
    setPhoneSize(tester);

    final repository = FakeFarmRepository(
      farms: const [],
      createError: Exception('Unable to save farm right now.'),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('farm_tab_empty_add_button')));
    await tester.pumpAndSettle();

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(find.text('Unable to save farm right now.'), findsOneWidget);
    expect(find.byKey(const Key('add_farm_sheet')), findsOneWidget);
    expect(
      tester
          .widget<TextFormField>(find.byKey(const Key('farm_name_field')))
          .controller
          ?.text,
      'New Field',
    );

    repository.createError = null;

    await tapSubmit(tester);
    await tester.pumpAndSettle();

    expect(find.text('Farm added'), findsOneWidget);
    expect(provider.farms, hasLength(1));
    expect(repository.createCalls, 2);
  });

  testWidgets('modal remains usable when the keyboard is open', (tester) async {
    setPhoneSize(tester);

    final provider = FarmProvider(
      repository: FakeFarmRepository(farms: const []),
    );
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('farm_tab_empty_add_button')));
    await tester.pumpAndSettle();

    tester.view.viewInsets = const FakeViewPadding(bottom: 320);
    addTearDown(tester.view.resetViewInsets);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('add_farm_sheet')), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.enterText(
      find.byKey(const Key('farm_name_field')),
      'New Field',
    );
    await tester.pump();

    expect(tester.takeException(), isNull);
  });

  testWidgets('modal cannot be dismissed while creation is pending', (
    tester,
  ) async {
    setPhoneSize(tester);

    final completer = Completer<FarmModel>();
    final repository = FakeFarmRepository(farms: const [])
      ..createCompleter = completer;
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('farm_tab_empty_add_button')));
    await tester.pumpAndSettle();

    await fillRequiredFields(tester);
    await tapSubmit(tester);
    await tester.pump();

    final closeButton = find.byKey(const Key('add_farm_sheet_close_button'));
    expect(tester.widget<IconButton>(closeButton).onPressed, isNull);

    await tester.binding.handlePopRoute();
    await tester.pump();

    expect(find.byKey(const Key('add_farm_sheet')), findsOneWidget);

    completer.complete(testFarm(id: 'farm-new', name: 'New Field'));
    await tester.pumpAndSettle();

    expect(find.text('Farm added'), findsOneWidget);
    expect(provider.farms, hasLength(1));
  });

  testWidgets('narrow screens and larger text do not overflow', (tester) async {
    setPhoneSize(tester, size: const Size(320, 568));

    final provider = FarmProvider(
      repository: FakeFarmRepository(
        farms: [
          testFarm(
            id: 'farm-1',
            name: 'North Field Agricultural Research Farm',
            village: 'Ramapuram Agraharam',
            mandal: 'Kavali Revenue Mandal',
            district: 'Nellore District',
            landArea: 12.75,
            soilType: 'Deep Clay Loam Soil',
            waterSource: 'Community Borewell',
            irrigationMethod: 'Sprinkler Irrigation',
          ),
          testFarm(
            id: 'farm-2',
            name: 'South Field',
            isPrimary: false,
            landArea: 1.25,
            landUnit: 'Hectares',
            soilType: null,
            waterSource: null,
            waterAvailability: null,
            irrigationMethod: null,
          ),
        ],
      ),
    );
    addTearDown(provider.dispose);
    await provider.loadFarms();

    await tester.pumpWidget(buildFarmApp(provider, textScale: 1.25));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);

    final firstToggle = find.byKey(const Key('farm_card_toggle_farm-1'));
    await tester.scrollUntilVisible(firstToggle, 250);
    await tester.tap(firstToggle);
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);

    final secondCard = find.byKey(const Key('farm_card_farm-2'));
    await tester.scrollUntilVisible(secondCard, 250);
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });
}

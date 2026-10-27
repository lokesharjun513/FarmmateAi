import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_recommendation_model.dart';
import 'package:mobile/features/crops/data/models/crop_season_model.dart';
import 'package:mobile/features/crops/presentation/screens/add_crop_screen.dart';
import 'package:mobile/features/crops/providers/crop_provider.dart';
import 'package:mobile/features/crops/providers/crop_recommendation_provider.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:provider/provider.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository({this.farms = const []});

  List<FarmModel> farms;

  @override
  Future<List<FarmModel>> getFarms() async => List<FarmModel>.of(farms);
}

class FakeCropRepository extends CropRepository {
  FakeCropRepository({
    Map<String, CropRecommendationModel>? recommendations,
    this.recommendationError,
    Map<String, Completer<void>>? recommendationGates,
  }) : recommendations = recommendations ?? {},
       recommendationGates = recommendationGates ?? {};

  Map<String, CropRecommendationModel> recommendations;
  Object? recommendationError;
  Map<String, Completer<void>> recommendationGates;
  final List<String> recommendationFarmIds = [];

  @override
  Future<List<CropSeasonModel>> getCropSeasons(String farmId) async => const [];

  @override
  Future<CropRecommendationModel> getCropRecommendations(String farmId) async {
    recommendationFarmIds.add(farmId);

    final gate = recommendationGates[farmId];

    if (gate != null) {
      await gate.future;
    }

    if (recommendationError != null) {
      throw recommendationError!;
    }

    final result = recommendations[farmId];

    if (result == null) {
      throw Exception('No recommendation fixture for $farmId.');
    }

    return result;
  }
}

FarmModel testFarm({
  String id = 'farm-1',
  String name = 'North Field',
  bool isPrimary = true,
}) {
  return FarmModel(
    id: id,
    farmerId: 'farmer-1',
    farmName: name,
    state: 'Andhra Pradesh',
    district: 'Nellore',
    mandal: 'Kavali',
    village: 'Ramapuram',
    latitude: null,
    longitude: null,
    landArea: 2.5,
    landUnit: 'Acres',
    soilType: 'Clay',
    waterSource: 'Borewell',
    waterAvailability: 'HIGH',
    irrigationMethod: 'Drip',
    isPrimary: isPrimary,
  );
}

CropRecommendationModel recommendationFor(
  String farmId, {
  required String firstCrop,
  String? secondCrop,
  String date = '2026-08-20',
}) {
  return CropRecommendationModel(
    farmId: farmId,
    recommendedSowingDate: DateTime.tryParse(date),
    recommendedCrops: [
      RecommendedCropModel(
        cropName: firstCrop,
        confidence: 95,
        reason: 'Suitable for the current season and water conditions.',
      ),
      if (secondCrop != null)
        RecommendedCropModel(
          cropName: secondCrop,
          confidence: 80,
          reason: 'Good alternative for the available conditions.',
        ),
    ],
  );
}

Widget buildApp({
  required CropProvider cropProvider,
  required CropRecommendationProvider recommendationProvider,
}) {
  return MultiProvider(
    providers: [
      ChangeNotifierProvider<CropProvider>.value(value: cropProvider),
      ChangeNotifierProvider<CropRecommendationProvider>.value(
        value: recommendationProvider,
      ),
    ],
    child: MaterialApp(theme: AppTheme.lightTheme, home: const AddCropScreen()),
  );
}

void setPhoneSize(WidgetTester tester, {Size size = const Size(390, 1100)}) {
  tester.view
    ..physicalSize = size
    ..devicePixelRatio = 1;

  addTearDown(() {
    tester.view
      ..resetPhysicalSize()
      ..resetDevicePixelRatio();
  });
}

Future<void> selectFarm(WidgetTester tester, String farmName) async {
  await tester.tap(find.byKey(const Key('add_crop_farm_field')));
  await tester.pumpAndSettle();
  await tester.tap(find.text(farmName).last);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 250));
}

ElevatedButton continueButton(WidgetTester tester) {
  return tester.widget<ElevatedButton>(
    find.byKey(const Key('crop_recommendation_continue_button')),
  );
}

void main() {
  testWidgets('shows an initial state until a farm is selected', (
    tester,
  ) async {
    setPhoneSize(tester);

    final farmRepository = FakeFarmRepository(farms: [testFarm()]);
    final repository = FakeCropRepository(
      recommendations: {
        'farm-1': recommendationFor('farm-1', firstCrop: 'Rice'),
      },
    );
    final cropProvider = CropProvider(
      repository: repository,
      farmRepository: farmRepository,
    );
    final recommendationProvider = CropRecommendationProvider(
      repository: repository,
    );

    addTearDown(cropProvider.dispose);
    addTearDown(recommendationProvider.dispose);

    await cropProvider.loadCrops();
    await tester.pumpWidget(
      buildApp(
        cropProvider: cropProvider,
        recommendationProvider: recommendationProvider,
      ),
    );

    expect(
      find.byKey(const Key('crop_recommendation_initial')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('crop_manual_section')), findsNothing);
    expect(continueButton(tester).onPressed, isNull);
    expect(repository.recommendationFarmIds, isEmpty);
  });

  testWidgets('loads recommendations, selects one, and prefills crop details', (
    tester,
  ) async {
    setPhoneSize(tester);

    final gate = Completer<void>();
    final repository = FakeCropRepository(
      recommendations: {
        'farm-1': recommendationFor(
          'farm-1',
          firstCrop: 'Rice',
          secondCrop: 'Maize',
        ),
      },
      recommendationGates: {'farm-1': gate},
    );
    final cropProvider = CropProvider(
      repository: repository,
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
    );
    final recommendationProvider = CropRecommendationProvider(
      repository: repository,
    );

    addTearDown(cropProvider.dispose);
    addTearDown(recommendationProvider.dispose);

    await cropProvider.loadCrops();
    await tester.pumpWidget(
      buildApp(
        cropProvider: cropProvider,
        recommendationProvider: recommendationProvider,
      ),
    );

    await selectFarm(tester, 'North Field');

    expect(
      find.byKey(const Key('crop_recommendation_loading')),
      findsOneWidget,
    );
    expect(find.textContaining('Primary farm'), findsOneWidget);
    expect(continueButton(tester).onPressed, isNull);

    gate.complete();
    await tester.pumpAndSettle();

    expect(find.text('Recommended for North Field'), findsOneWidget);
    expect(find.text('Rice'), findsOneWidget);
    expect(find.text('Maize'), findsOneWidget);
    expect(find.text('95/100'), findsOneWidget);
    expect(find.text('80/100'), findsOneWidget);
    expect(
      find.text('Suitable for the current season and water conditions.'),
      findsOneWidget,
    );
    expect(find.text('Recommended sowing: 20 Aug 2026'), findsNWidgets(2));
    expect(continueButton(tester).onPressed, isNull);

    await tester.ensureVisible(
      find.byKey(const Key('crop_recommendation_card_0')),
    );
    await tester.tap(find.byKey(const Key('crop_recommendation_card_0')));
    await tester.pump();

    expect(find.text('Selected: Rice'), findsOneWidget);
    expect(find.byKey(const Key('add_crop_selected_summary')), findsOneWidget);
    expect(find.text('AI recommendation • 95/100 suitability'), findsOneWidget);
    expect(
      find.text('Prefilled from the recommendation. You can change it.'),
      findsOneWidget,
    );
    expect(continueButton(tester).onPressed, isNotNull);

    await tester.ensureVisible(
      find.byKey(const Key('crop_recommendation_continue_button')),
    );
    await tester.tap(
      find.byKey(const Key('crop_recommendation_continue_button')),
    );
    await tester.pumpAndSettle();

    expect(find.text('Plan your next crop'), findsOneWidget);
    expect(find.byKey(const Key('crop_selected_farm')), findsOneWidget);
    expect(find.text('North Field'), findsOneWidget);
    expect(find.text('20 Aug 2026'), findsOneWidget);

    final cropNameField = tester.widget<TextFormField>(
      find.byKey(const Key('crop_name_field')),
    );

    expect(cropNameField.controller?.text, 'Rice');
  });

  testWidgets('manual crop entry remains available when recommendations fail', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(
      recommendationError: Exception('Recommendations are unavailable.'),
    );
    final cropProvider = CropProvider(
      repository: repository,
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
    );
    final recommendationProvider = CropRecommendationProvider(
      repository: repository,
    );

    addTearDown(cropProvider.dispose);
    addTearDown(recommendationProvider.dispose);

    await cropProvider.loadCrops();
    await tester.pumpWidget(
      buildApp(
        cropProvider: cropProvider,
        recommendationProvider: recommendationProvider,
      ),
    );

    await selectFarm(tester, 'North Field');
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_recommendation_error')), findsOneWidget);
    expect(find.text('Recommendations are unavailable.'), findsOneWidget);
    expect(find.text('Suitability confidence'), findsNothing);
    expect(
      find.byKey(const Key('crop_recommendation_manual_button')),
      findsOneWidget,
    );
    expect(continueButton(tester).onPressed, isNull);

    await tester.enterText(
      find.byKey(const Key('crop_manual_name_field')),
      'Tomato',
    );
    await tester.pump();

    expect(find.text('Selected: Tomato'), findsNothing);
    expect(find.text('Manual entry (unverified)'), findsOneWidget);
    expect(
      find.byKey(const Key('add_crop_change_crop_button')),
      findsOneWidget,
    );
    expect(continueButton(tester).onPressed, isNotNull);

    await tester.ensureVisible(
      find.byKey(const Key('crop_recommendation_continue_button')),
    );
    await tester.tap(
      find.byKey(const Key('crop_recommendation_continue_button')),
    );
    await tester.pumpAndSettle();

    final cropNameField = tester.widget<TextFormField>(
      find.byKey(const Key('crop_name_field')),
    );

    expect(cropNameField.controller?.text, 'Tomato');
  });

  testWidgets('changing farms clears old recommendations and loads new ones', (
    tester,
  ) async {
    setPhoneSize(tester);

    final firstGate = Completer<void>();
    final secondGate = Completer<void>();
    final repository = FakeCropRepository(
      recommendations: {
        'farm-1': recommendationFor('farm-1', firstCrop: 'Rice'),
        'farm-2': recommendationFor('farm-2', firstCrop: 'Maize'),
      },
      recommendationGates: {'farm-1': firstGate, 'farm-2': secondGate},
    );
    final cropProvider = CropProvider(
      repository: repository,
      farmRepository: FakeFarmRepository(
        farms: [
          testFarm(),
          testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        ],
      ),
    );
    final recommendationProvider = CropRecommendationProvider(
      repository: repository,
    );

    addTearDown(cropProvider.dispose);
    addTearDown(recommendationProvider.dispose);

    await cropProvider.loadCrops();
    await tester.pumpWidget(
      buildApp(
        cropProvider: cropProvider,
        recommendationProvider: recommendationProvider,
      ),
    );

    await selectFarm(tester, 'North Field');
    firstGate.complete();
    await tester.pumpAndSettle();

    expect(find.text('Rice'), findsOneWidget);

    await selectFarm(tester, 'South Field');

    expect(
      find.byKey(const Key('crop_recommendation_loading')),
      findsOneWidget,
    );
    expect(find.text('Rice'), findsNothing);

    secondGate.complete();
    await tester.pumpAndSettle();

    expect(find.text('Maize'), findsOneWidget);
    expect(find.text('Rice'), findsNothing);
    expect(repository.recommendationFarmIds, ['farm-1', 'farm-2']);
  });

  testWidgets('retry requests recommendations again after failure', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(
      recommendations: {
        'farm-1': recommendationFor('farm-1', firstCrop: 'Rice'),
      },
      recommendationError: Exception('Recommendations are unavailable.'),
    );
    final cropProvider = CropProvider(
      repository: repository,
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
    );
    final recommendationProvider = CropRecommendationProvider(
      repository: repository,
    );

    addTearDown(cropProvider.dispose);
    addTearDown(recommendationProvider.dispose);

    await cropProvider.loadCrops();
    await tester.pumpWidget(
      buildApp(
        cropProvider: cropProvider,
        recommendationProvider: recommendationProvider,
      ),
    );

    await selectFarm(tester, 'North Field');
    await tester.pumpAndSettle();

    expect(
      find.byKey(const Key('crop_recommendation_retry_button')),
      findsOneWidget,
    );

    repository.recommendationError = null;

    await tester.tap(find.byKey(const Key('crop_recommendation_retry_button')));
    await tester.pumpAndSettle();

    expect(find.text('Rice'), findsOneWidget);
    expect(find.byKey(const Key('crop_recommendation_error')), findsNothing);
    expect(repository.recommendationFarmIds, ['farm-1', 'farm-1']);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_plan_models.dart';
import 'package:mobile/features/crops/data/models/crop_season_create_input.dart';
import 'package:mobile/features/crops/data/models/crop_season_model.dart';
import 'package:mobile/features/crops/presentation/crop_creation_outcome.dart';
import 'package:mobile/features/crops/presentation/screens/crop_create_screen.dart';
import 'package:mobile/features/crops/providers/crop_provider.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:provider/provider.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository(this.farms);

  final List<FarmModel> farms;

  @override
  Future<List<FarmModel>> getFarms() async => List<FarmModel>.of(farms);
}

class FakeCropRepository extends CropRepository {
  Object? createError;
  Object? planError;
  Object? stagesError;
  Object? activitiesError;

  int createCalls = 0;
  int planCalls = 0;
  int stageCalls = 0;
  int activityCalls = 0;

  String? lastFarmId;
  CropSeasonCreateInput? lastInput;
  CropSeasonModel? createdCrop;

  @override
  Future<List<CropSeasonModel>> getCropSeasons(String farmId) async => const [];

  @override
  Future<CropSeasonModel> createCropSeason({
    required String farmId,
    required CropSeasonCreateInput input,
  }) async {
    createCalls += 1;
    lastFarmId = farmId;
    lastInput = input;

    if (createError != null) {
      throw createError!;
    }

    final crop = CropSeasonModel(
      id: 'crop-1',
      farmId: farmId,
      cropName: input.cropName.trim(),
      cropVariety: input.cropVariety,
      season: input.season,
      year: input.year,
      sowingDate: input.sowingDate,
      expectedHarvestDate: input.expectedHarvestDate,
      harvestedDate: null,
      landArea: input.landArea,
      landUnit: input.landUnit,
      status: CropSeasonStatus.planned,
      isActive: false,
      notes: input.notes,
      cancellationReason: null,
    );

    createdCrop = crop;

    return crop;
  }

  @override
  Future<CropPlanSummary> generateCropPlan({
    required String cropSeasonId,
    required String state,
    required String district,
    required String village,
    String? soilType,
  }) async {
    planCalls += 1;

    if (planError != null) {
      throw planError!;
    }

    final cropName = createdCrop?.cropName ?? 'Rice';

    return CropPlanSummary(
      cropSeasonId: cropSeasonId,
      cropName: cropName,
      cropVariety: null,
      season: FarmingSeason.kharif,
      estimatedDurationDays: 100,
      stagesCreated: 1,
      activitiesCreated: 0,
    );
  }

  @override
  Future<List<CropStageModel>> getCropStages(String cropSeasonId) async {
    stageCalls += 1;

    if (stagesError != null) {
      throw stagesError!;
    }

    return [
      CropStageModel(
        id: 'stage-1',
        cropSeasonId: cropSeasonId,
        name: 'Land preparation',
        description: 'Prepare the field before sowing.',
        stageOrder: 1,
        startDay: 1,
        endDay: 10,
        status: CropStageStatus.pending,
        startedAt: null,
        completedAt: null,
      ),
    ];
  }

  @override
  Future<List<CropActivityModel>> getCropActivities(String cropSeasonId) async {
    activityCalls += 1;

    if (activitiesError != null) {
      throw activitiesError!;
    }

    return const [];
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
    latitude: null,
    longitude: null,
    landArea: 2.5,
    landUnit: 'Acres',
    soilType: 'Clay',
    waterSource: 'Borewell',
    waterAvailability: 'HIGH',
    irrigationMethod: 'Drip',
    isPrimary: true,
  );
}

CropProvider buildProvider(FakeCropRepository repository) {
  final provider = CropProvider(
    repository: repository,
    farmRepository: FakeFarmRepository([testFarm()]),
  );

  addTearDown(provider.dispose);

  return provider;
}

Widget buildScreen(
  CropProvider provider, {
  String initialCropName = 'Rice',
  DateTime? initialSowingDate,
}) {
  return ChangeNotifierProvider<CropProvider>.value(
    value: provider,
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      home: CropCreateScreen(
        farm: testFarm(),
        initialCropName: initialCropName,
        initialSowingDate: initialSowingDate,
      ),
    ),
  );
}

Widget buildNavigableScreen(
  CropProvider provider, {
  required String initialCropName,
  required void Function(CropCreationOutcome?) onResult,
}) {
  return ChangeNotifierProvider<CropProvider>.value(
    value: provider,
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      home: Builder(
        builder: (context) {
          return Scaffold(
            body: Center(
              child: ElevatedButton(
                key: const Key('open_crop_create'),
                onPressed: () async {
                  final result = await Navigator.of(context)
                      .push<CropCreationOutcome>(
                        MaterialPageRoute(
                          builder: (_) => CropCreateScreen(
                            farm: testFarm(),
                            initialCropName: initialCropName,
                          ),
                        ),
                      );

                  onResult(result);
                },
                child: const Text('Open'),
              ),
            ),
          );
        },
      ),
    ),
  );
}

Future<void> systemBack(WidgetTester tester) async {
  await tester.binding.handlePopRoute();
  await tester.pumpAndSettle();
}

void setPhoneSize(WidgetTester tester, {Size size = const Size(390, 1000)}) {
  tester.view
    ..physicalSize = size
    ..devicePixelRatio = 1;

  addTearDown(() {
    tester.view
      ..resetPhysicalSize()
      ..resetDevicePixelRatio();
  });
}

Future<void> tapCreate(WidgetTester tester) async {
  final button = find.byKey(const Key('crop_create_submit_button'));

  await tester.ensureVisible(button);
  await tester.tap(button);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('create failure does not generate a plan and allows retry', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository()
      ..createError = Exception('Unable to save crop right now.');
    final provider = buildProvider(repository);
    final sowingDate = DateTime(2026, 8, 20);

    await tester.pumpWidget(
      buildScreen(
        provider,
        initialCropName: 'Rice',
        initialSowingDate: sowingDate,
      ),
    );

    final cropNameField = tester.widget<TextFormField>(
      find.byKey(const Key('crop_name_field')),
    );

    expect(cropNameField.controller?.text, 'Rice');
    expect(find.text('20 Aug 2026'), findsOneWidget);

    await tapCreate(tester);

    expect(find.text('Unable to save crop right now.'), findsOneWidget);
    expect(repository.createCalls, 1);
    expect(repository.planCalls, 0);
    expect(find.byKey(const Key('crop_name_field')), findsOneWidget);

    repository.createError = null;

    await tapCreate(tester);

    expect(repository.createCalls, 2);
    expect(repository.planCalls, 1);
    expect(repository.lastFarmId, 'farm-1');
    expect(repository.lastInput?.cropName, 'Rice');
    expect(repository.lastInput?.sowingDate, sowingDate);
    expect(find.byKey(const Key('crop_plan_review')), findsOneWidget);
    expect(
      find.byKey(const Key('crop_plan_view_details_button')),
      findsOneWidget,
    );
    expect(find.text('View Crop Details'), findsOneWidget);
    expect(find.text('Go to Crops'), findsOneWidget);
  });

  testWidgets(
    'plan failure keeps the created crop and retry does not duplicate it',
    (tester) async {
      setPhoneSize(tester);

      final repository = FakeCropRepository()
        ..planError = Exception('Plan generation failed.');
      final provider = buildProvider(repository);

      await tester.pumpWidget(
        buildScreen(provider, initialCropName: 'Groundnut'),
      );

      await tapCreate(tester);

      expect(find.byKey(const Key('crop_plan_error')), findsOneWidget);
      expect(find.text('Plan generation failed.'), findsOneWidget);
      expect(
        find.text('Groundnut is saved as a planned crop.'),
        findsOneWidget,
      );
      expect(repository.createCalls, 1);
      expect(repository.planCalls, 1);
      expect(repository.lastInput?.cropName, 'Groundnut');

      repository.planError = null;

      await tester.tap(find.byKey(const Key('crop_plan_retry_button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('crop_plan_review')), findsOneWidget);
      expect(repository.createCalls, 1);
      expect(repository.planCalls, 2);
    },
  );

  testWidgets(
    'review loading failure retries only the plan data after generation',
    (tester) async {
      setPhoneSize(tester);

      final repository = FakeCropRepository()
        ..stagesError = Exception('Unable to load the crop plan.');
      final provider = buildProvider(repository);

      await tester.pumpWidget(buildScreen(provider));
      await tapCreate(tester);

      expect(find.byKey(const Key('crop_plan_error')), findsOneWidget);
      expect(find.text('Plan created, review unavailable'), findsOneWidget);
      expect(find.text('Retry loading review'), findsOneWidget);
      expect(repository.createCalls, 1);
      expect(repository.planCalls, 1);
      expect(repository.stageCalls, 1);

      repository.stagesError = null;

      await tester.tap(find.byKey(const Key('crop_plan_retry_button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('crop_plan_review')), findsOneWidget);
      expect(repository.createCalls, 1);
      expect(repository.planCalls, 1);
      expect(repository.stageCalls, 2);
    },
  );

  testWidgets('system back before creation returns none', (tester) async {
    setPhoneSize(tester);

    final provider = buildProvider(FakeCropRepository());
    CropCreationOutcome? outcome;

    await tester.pumpWidget(
      buildNavigableScreen(
        provider,
        initialCropName: 'Rice',
        onResult: (result) {
          outcome = result;
        },
      ),
    );

    await tester.tap(find.byKey(const Key('open_crop_create')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_name_field')), findsOneWidget);

    await systemBack(tester);

    expect(outcome, CropCreationOutcome.none);
    expect(find.byKey(const Key('crop_name_field')), findsNothing);
  });

  testWidgets('system back after plan review returns planReady', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository();
    final provider = buildProvider(repository);
    CropCreationOutcome? outcome;

    await tester.pumpWidget(
      buildNavigableScreen(
        provider,
        initialCropName: 'Rice',
        onResult: (result) {
          outcome = result;
        },
      ),
    );

    await tester.tap(find.byKey(const Key('open_crop_create')));
    await tester.pumpAndSettle();
    await tapCreate(tester);

    expect(find.byKey(const Key('crop_plan_review')), findsOneWidget);

    await systemBack(tester);

    expect(outcome, CropCreationOutcome.planReady);
    expect(repository.createCalls, 1);
  });

  testWidgets('system back after plan failure returns planFailed', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository()
      ..planError = Exception('Plan generation failed.');
    final provider = buildProvider(repository);
    CropCreationOutcome? outcome;

    await tester.pumpWidget(
      buildNavigableScreen(
        provider,
        initialCropName: 'Groundnut',
        onResult: (result) {
          outcome = result;
        },
      ),
    );

    await tester.tap(find.byKey(const Key('open_crop_create')));
    await tester.pumpAndSettle();
    await tapCreate(tester);

    expect(find.byKey(const Key('crop_plan_error')), findsOneWidget);

    await systemBack(tester);

    expect(outcome, CropCreationOutcome.planFailed);
    expect(repository.createCalls, 1);
  });
}

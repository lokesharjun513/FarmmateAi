import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_plan_models.dart';
import 'package:mobile/features/crops/data/models/crop_season_model.dart';
import 'package:mobile/features/crops/presentation/screens/crop_detail_screen.dart';
import 'package:mobile/features/crops/providers/crop_provider.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:provider/provider.dart';

class FakeFarmRepository extends FarmRepository {
  @override
  Future<List<FarmModel>> getFarms() async => const [];
}

class FakeCropRepository extends CropRepository {
  FakeCropRepository({
    List<CropStageModel>? stages,
    List<CropActivityModel>? activities,
    this.error,
    this.gate,
    this.generateGate,
  }) : stages = stages ?? [],
       activities = activities ?? [];

  List<CropStageModel> stages;
  List<CropActivityModel> activities;
  Object? error;
  Object? generateError;
  Completer<void>? gate;
  Completer<void>? generateGate;
  int stageCalls = 0;
  int generateCalls = 0;
  int activateCalls = 0;
  int harvestCalls = 0;
  int cancelCalls = 0;
  int deleteCalls = 0;
  int completeStageCalls = 0;
  int startActivityCalls = 0;
  String? cancelReason;
  DateTime? harvestedDate;

  @override
  Future<CropSeasonModel> activateCropSeason(String cropSeasonId) async {
    activateCalls += 1;

    return testCrop(status: CropSeasonStatus.active);
  }

  @override
  Future<CropSeasonModel> harvestCropSeason(
    String cropSeasonId, {
    DateTime? harvestedDate,
    String? notes,
  }) async {
    harvestCalls += 1;
    this.harvestedDate = harvestedDate;

    return testCrop(status: CropSeasonStatus.harvested);
  }

  @override
  Future<CropSeasonModel> cancelCropSeason(
    String cropSeasonId, {
    String? reason,
  }) async {
    cancelCalls += 1;
    cancelReason = reason;

    return testCrop(
      status: CropSeasonStatus.cancelled,
      cancellationReason: reason,
    );
  }

  @override
  Future<void> deleteCropSeason(String cropSeasonId) async {
    deleteCalls += 1;
  }

  @override
  Future<CropStageModel> completeCropStage(String stageId) async {
    completeStageCalls += 1;

    return testStage();
  }

  @override
  Future<CropActivityModel> startActivity(String activityId) async {
    startActivityCalls += 1;

    return testActivity();
  }

  @override
  Future<CropPlanSummary> generateCropPlan({
    required String cropSeasonId,
    required String state,
    required String district,
    required String village,
    String? soilType,
  }) async {
    generateCalls += 1;

    if (generateGate != null) {
      await generateGate!.future;
    }

    if (generateError != null) {
      throw generateError!;
    }

    stages = [testStage()];

    return CropPlanSummary(
      cropSeasonId: cropSeasonId,
      cropName: 'Rice',
      cropVariety: 'BPT 5204',
      season: FarmingSeason.kharif,
      estimatedDurationDays: 120,
      stagesCreated: 1,
      activitiesCreated: 0,
    );
  }

  @override
  Future<List<CropStageModel>> getCropStages(String cropSeasonId) async {
    stageCalls++;

    if (gate != null) {
      await gate!.future;
    }

    if (error != null) {
      throw error!;
    }

    return List<CropStageModel>.of(stages);
  }

  @override
  Future<List<CropActivityModel>> getCropActivities(String cropSeasonId) async {
    if (gate != null) {
      await gate!.future;
    }

    if (error != null) {
      throw error!;
    }

    return List<CropActivityModel>.of(activities);
  }
}

FarmModel testFarm() {
  return FarmModel(
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

CropSeasonModel testCrop({
  CropSeasonStatus status = CropSeasonStatus.active,
  String? cancellationReason,
}) {
  return CropSeasonModel(
    id: 'crop-1',
    farmId: 'farm-1',
    cropName: 'Rice',
    cropVariety: 'BPT 5204',
    season: FarmingSeason.kharif,
    year: 2026,
    sowingDate: DateTime(2026, 6, 12),
    expectedHarvestDate: DateTime(2026, 10, 20),
    harvestedDate: status == CropSeasonStatus.harvested
        ? DateTime(2026, 10, 20)
        : null,
    landArea: 2.5,
    landUnit: 'Acres',
    status: status,
    isActive: status == CropSeasonStatus.active,
    notes: null,
    cancellationReason: cancellationReason,
  );
}

CropStageModel testStage() {
  return const CropStageModel(
    id: 'stage-1',
    cropSeasonId: 'crop-1',
    name: 'Land preparation',
    description: 'Prepare the field before sowing.',
    stageOrder: 1,
    startDay: 1,
    endDay: 10,
    status: CropStageStatus.active,
    startedAt: null,
    completedAt: null,
  );
}

CropActivityModel testActivity() {
  return CropActivityModel(
    id: 'activity-1',
    cropSeasonId: 'crop-1',
    stageId: 'stage-1',
    activityType: 'LAND_PREPARATION',
    title: 'Plough the field',
    description: null,
    scheduledDate: DateTime(2026, 6, 12),
    originalScheduledDate: null,
    completedDate: null,
    status: CropActivityStatus.pending,
    notes: null,
    priority: CropActivityPriority.medium,
    estimatedDurationMinutes: null,
    source: 'AI',
  );
}

Widget buildApp(CropProvider provider, {CropSeasonModel? crop}) {
  return ChangeNotifierProvider<CropProvider>.value(
    value: provider,
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      home: CropDetailScreen(farm: testFarm(), crop: crop ?? testCrop()),
    ),
  );
}

CropProvider buildProvider(FakeCropRepository repository) {
  final provider = CropProvider(
    repository: repository,
    farmRepository: FakeFarmRepository(),
  );

  addTearDown(provider.dispose);

  return provider;
}

void setPhoneSize(WidgetTester tester) {
  tester.view
    ..physicalSize = const Size(390, 1200)
    ..devicePixelRatio = 1;

  addTearDown(() {
    tester.view
      ..resetPhysicalSize()
      ..resetDevicePixelRatio();
  });
}

void main() {
  testWidgets('shows loading then the crop plan timeline', (tester) async {
    setPhoneSize(tester);

    final gate = Completer<void>();
    final provider = buildProvider(
      FakeCropRepository(
        stages: [testStage()],
        activities: [testActivity()],
        gate: gate,
      ),
    );

    await tester.pumpWidget(buildApp(provider));
    await tester.pump();

    expect(find.byKey(const Key('crop_detail_loading')), findsOneWidget);
    expect(find.text('Rice'), findsOneWidget);
    expect(find.text('BPT 5204'), findsOneWidget);
    expect(find.text('North Field'), findsOneWidget);

    gate.complete();
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_loading')), findsNothing);
    expect(find.byKey(const Key('crop_detail_plan')), findsOneWidget);
    expect(find.text('Land preparation'), findsOneWidget);
    expect(find.text('Plough the field'), findsOneWidget);
  });

  testWidgets('shows an error with retry when the plan cannot load', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(
      error: Exception('Plan service unavailable.'),
    );
    final provider = buildProvider(repository);

    await tester.pumpWidget(buildApp(provider));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_error')), findsOneWidget);
    expect(find.text('Plan service unavailable.'), findsOneWidget);

    repository
      ..error = null
      ..stages = [testStage()];

    await tester.tap(find.byKey(const Key('crop_detail_retry_button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_error')), findsNothing);
    expect(find.byKey(const Key('crop_detail_plan')), findsOneWidget);
    expect(repository.stageCalls, 2);
  });

  testWidgets('shows an honest empty state when no plan exists', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = buildProvider(FakeCropRepository());

    await tester.pumpWidget(buildApp(provider));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_empty')), findsOneWidget);
    expect(find.text('No plan available yet'), findsOneWidget);
    expect(find.byKey(const Key('crop_detail_error')), findsNothing);
    expect(
      find.byKey(const Key('crop_detail_generate_button')),
      findsOneWidget,
    );
  });

  testWidgets('generates a plan for an existing planned crop', (tester) async {
    setPhoneSize(tester);

    final gate = Completer<void>();
    final repository = FakeCropRepository(generateGate: gate);
    final provider = buildProvider(repository);

    await tester.pumpWidget(
      buildApp(provider, crop: testCrop(status: CropSeasonStatus.planned)),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_empty')), findsOneWidget);

    await tester.tap(find.byKey(const Key('crop_detail_generate_button')));
    await tester.pump();

    expect(find.byKey(const Key('crop_detail_loading')), findsOneWidget);
    expect(repository.generateCalls, 1);

    gate.complete();
    await tester.pumpAndSettle();

    expect(repository.generateCalls, 1);
    expect(find.byKey(const Key('crop_detail_plan')), findsOneWidget);
    expect(find.text('Land preparation'), findsOneWidget);
  });

  testWidgets('plan generation failure retries generation, not just loading', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository()
      ..generateError = Exception('Plan generation failed.');
    final provider = buildProvider(repository);

    await tester.pumpWidget(
      buildApp(provider, crop: testCrop(status: CropSeasonStatus.planned)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_detail_generate_button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_error')), findsOneWidget);
    expect(find.text('Plan generation failed.'), findsOneWidget);
    expect(repository.generateCalls, 1);

    repository.generateError = null;

    await tester.tap(find.byKey(const Key('crop_detail_retry_button')));
    await tester.pumpAndSettle();

    expect(repository.generateCalls, 2);
    expect(find.byKey(const Key('crop_detail_plan')), findsOneWidget);
  });

  testWidgets('starts a planned crop once its plan exists', (tester) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(stages: [testStage()]);
    final provider = buildProvider(repository);

    await tester.pumpWidget(
      buildApp(provider, crop: testCrop(status: CropSeasonStatus.planned)),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_start_button')), findsOneWidget);

    await tester.tap(find.byKey(const Key('crop_detail_start_button')));
    await tester.pumpAndSettle();

    expect(repository.activateCalls, 1);
    expect(repository.harvestCalls, 0);
    expect(find.text('Crop started.'), findsOneWidget);
    expect(find.byKey(const Key('crop_detail_harvest_button')), findsOneWidget);
  });

  testWidgets('harvests an active crop after confirmation', (tester) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(stages: [testStage()]);
    final provider = buildProvider(repository);

    await tester.pumpWidget(buildApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_detail_harvest_button')));
    await tester.pumpAndSettle();

    expect(find.text('Mark crop as harvested?'), findsOneWidget);

    await tester.tap(
      find.byKey(const Key('crop_detail_harvest_confirm_button')),
    );
    await tester.pumpAndSettle();

    expect(repository.harvestCalls, 1);
    expect(repository.harvestedDate, isNotNull);
    expect(find.text('Crop marked as harvested.'), findsOneWidget);
  });

  testWidgets('cancels a crop with an optional reason', (tester) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(stages: [testStage()]);
    final provider = buildProvider(repository);

    await tester.pumpWidget(buildApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_detail_actions_button')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_detail_cancel_action')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('crop_detail_cancel_reason_field')),
      'Heavy rain damaged the nursery.',
    );
    await tester.tap(
      find.byKey(const Key('crop_detail_cancel_confirm_button')),
    );
    await tester.pumpAndSettle();

    expect(repository.cancelCalls, 1);
    expect(repository.cancelReason, 'Heavy rain damaged the nursery.');
    expect(find.text('Crop cancelled.'), findsOneWidget);
    expect(find.text('Heavy rain damaged the nursery.'), findsOneWidget);
  });

  testWidgets('deletes a cancelled crop after confirmation', (tester) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository();
    final provider = buildProvider(repository);

    await tester.pumpWidget(
      buildApp(provider, crop: testCrop(status: CropSeasonStatus.cancelled)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_detail_actions_button')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_detail_delete_action')));
    await tester.pumpAndSettle();

    await tester.tap(
      find.byKey(const Key('crop_detail_delete_confirm_button')),
    );
    await tester.pumpAndSettle();

    expect(repository.deleteCalls, 1);
  });

  testWidgets('shows activity timing and starts a pending activity', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(
      stages: [testStage()],
      activities: [testActivity()],
    );
    final provider = buildProvider(repository);

    await tester.pumpWidget(buildApp(provider));
    await tester.pumpAndSettle();

    expect(find.textContaining('Overdue'), findsOneWidget);

    await tester.tap(find.byKey(const Key('crop_activity_actions_activity-1')));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Start activity'));
    await tester.pumpAndSettle();

    expect(repository.startActivityCalls, 1);
    expect(find.text('Activity started.'), findsOneWidget);
  });

  testWidgets('completes the active crop stage', (tester) async {
    setPhoneSize(tester);

    final repository = FakeCropRepository(stages: [testStage()]);
    final provider = buildProvider(repository);

    await tester.pumpWidget(buildApp(provider));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('crop_stage_complete_stage-1')));
    await tester.pumpAndSettle();

    expect(repository.completeStageCalls, 1);
    expect(find.text('Stage completed.'), findsOneWidget);
  });
}

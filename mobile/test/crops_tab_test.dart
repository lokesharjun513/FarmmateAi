import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_plan_models.dart';
import 'package:mobile/features/crops/data/models/crop_season_model.dart';
import 'package:mobile/features/crops/presentation/screens/crops_tab.dart';
import 'package:mobile/features/crops/providers/crop_provider.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:provider/provider.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository({this.farms = const [], this.error});

  List<FarmModel> farms;
  Object? error;

  @override
  Future<List<FarmModel>> getFarms() async {
    if (error != null) {
      throw error!;
    }

    return List<FarmModel>.of(farms);
  }
}

class FakeCropRepository extends CropRepository {
  FakeCropRepository({
    Map<String, List<CropSeasonModel>>? cropsByFarm,
    this.error,
    this.gate,
    this.planError,
    List<CropStageModel>? planStages,
    List<CropActivityModel>? planActivities,
  }) : cropsByFarm = cropsByFarm ?? {},
       planStages = planStages ?? [],
       planActivities = planActivities ?? [];

  Map<String, List<CropSeasonModel>> cropsByFarm;
  Object? error;
  Completer<void>? gate;
  Object? planError;
  List<CropStageModel> planStages;
  List<CropActivityModel> planActivities;

  @override
  Future<List<CropSeasonModel>> getCropSeasons(String farmId) async {
    if (gate != null) {
      await gate!.future;
    }

    if (error != null) {
      throw error!;
    }

    return List<CropSeasonModel>.of(cropsByFarm[farmId] ?? const []);
  }

  @override
  Future<List<CropStageModel>> getCropStages(String cropSeasonId) async {
    if (planError != null) {
      throw planError!;
    }

    return List<CropStageModel>.of(planStages);
  }

  @override
  Future<List<CropActivityModel>> getCropActivities(String cropSeasonId) async {
    if (planError != null) {
      throw planError!;
    }

    return List<CropActivityModel>.of(planActivities);
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

CropSeasonModel testCrop({
  String id = 'crop-1',
  String farmId = 'farm-1',
  String cropName = 'Rice',
  String? cropVariety = 'BPT 5204',
  FarmingSeason season = FarmingSeason.kharif,
  int year = 2026,
  DateTime? sowingDate,
  DateTime? expectedHarvestDate,
  DateTime? harvestedDate,
  double landArea = 2.5,
  String landUnit = 'Acres',
  CropSeasonStatus status = CropSeasonStatus.active,
  bool isActive = true,
  String? cancellationReason,
}) {
  return CropSeasonModel(
    id: id,
    farmId: farmId,
    cropName: cropName,
    cropVariety: cropVariety,
    season: season,
    year: year,
    sowingDate: sowingDate ?? DateTime(2026, 6, 12),
    expectedHarvestDate: expectedHarvestDate ?? DateTime(2026, 10, 20),
    harvestedDate: harvestedDate,
    landArea: landArea,
    landUnit: landUnit,
    status: status,
    isActive: isActive,
    notes: null,
    cancellationReason: cancellationReason,
  );
}

CropStageModel testStage({
  String id = 'stage-1',
  String cropSeasonId = 'crop-1',
  String name = 'Land preparation',
  int stageOrder = 1,
  int startDay = 1,
  int endDay = 10,
  CropStageStatus status = CropStageStatus.active,
}) {
  return CropStageModel(
    id: id,
    cropSeasonId: cropSeasonId,
    name: name,
    description: 'Prepare the field before sowing.',
    stageOrder: stageOrder,
    startDay: startDay,
    endDay: endDay,
    status: status,
    startedAt: null,
    completedAt: null,
  );
}

CropActivityModel testActivity({
  String id = 'activity-1',
  String cropSeasonId = 'crop-1',
  String? stageId = 'stage-1',
  String title = 'Plough the field',
  DateTime? scheduledDate,
  CropActivityStatus status = CropActivityStatus.pending,
  CropActivityPriority priority = CropActivityPriority.medium,
}) {
  return CropActivityModel(
    id: id,
    cropSeasonId: cropSeasonId,
    stageId: stageId,
    activityType: 'LAND_PREPARATION',
    title: title,
    description: null,
    scheduledDate: scheduledDate ?? DateTime(2026, 6, 12),
    originalScheduledDate: null,
    completedDate: null,
    status: status,
    notes: null,
    priority: priority,
    estimatedDurationMinutes: null,
    source: 'AI',
  );
}

CropProvider buildProvider({
  required FakeFarmRepository farmRepository,
  required FakeCropRepository cropRepository,
}) {
  final provider = CropProvider(
    repository: cropRepository,
    farmRepository: farmRepository,
  );

  addTearDown(provider.dispose);

  return provider;
}

Widget buildCropsApp(CropProvider provider) {
  return ChangeNotifierProvider<CropProvider>.value(
    value: provider,
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      home: const Scaffold(body: CropsTab()),
    ),
  );
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

void main() {
  testWidgets('shows an honest loading state while crops load', (tester) async {
    setPhoneSize(tester);

    final gate = Completer<void>();
    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(
        gate: gate,
        cropsByFarm: {
          'farm-1': [testCrop()],
        },
      ),
    );

    final loading = provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.byKey(const Key('crops_loading')), findsOneWidget);
    expect(find.text('Loading your crops...'), findsOneWidget);

    gate.complete();
    await loading;
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crops_loading')), findsNothing);
    expect(find.text('Rice'), findsOneWidget);
  });

  testWidgets('shows a retryable error instead of a false empty state', (
    tester,
  ) async {
    setPhoneSize(tester);

    final cropRepository = FakeCropRepository(
      error: Exception('Unable to load crops.'),
    );
    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: cropRepository,
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.text('Crops unavailable'), findsOneWidget);
    expect(find.text('Unable to load crops.'), findsOneWidget);
    expect(find.byKey(const Key('crops_empty_view')), findsNothing);

    cropRepository
      ..error = null
      ..cropsByFarm = {
        'farm-1': [testCrop()],
      };

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();

    expect(find.text('Crops unavailable'), findsNothing);
    expect(find.text('Rice'), findsOneWidget);
  });

  testWidgets('shows the empty state only after a successful load', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.byKey(const Key('crops_empty_view')), findsOneWidget);
    expect(find.text('No crop seasons yet'), findsOneWidget);
    expect(find.text('North Field'), findsNothing);
  });

  testWidgets('renders status, season, area and accurate dates', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(
        cropsByFarm: {
          'farm-1': [
            testCrop(
              status: CropSeasonStatus.harvested,
              isActive: false,
              harvestedDate: DateTime(2026, 10, 18),
            ),
          ],
        },
      ),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.text('North Field'), findsOneWidget);
    expect(find.text('Rice'), findsOneWidget);
    expect(find.text('BPT 5204'), findsOneWidget);
    expect(find.text('Harvested'), findsWidgets);
    expect(find.text('Kharif 2026'), findsOneWidget);
    expect(find.text('2.5 Acres'), findsOneWidget);
    expect(find.text('12 Jun 2026'), findsOneWidget);
    expect(find.text('20 Oct 2026'), findsOneWidget);
    expect(find.text('18 Oct 2026'), findsOneWidget);
  });

  testWidgets('groups crops by farm and labels the primary farm', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(
        farms: [
          testFarm(),
          testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        ],
      ),
      cropRepository: FakeCropRepository(
        cropsByFarm: {
          'farm-1': [testCrop()],
          'farm-2': [
            testCrop(
              id: 'crop-2',
              farmId: 'farm-2',
              cropName: 'Cotton',
              cropVariety: null,
              season: FarmingSeason.rabi,
              status: CropSeasonStatus.planned,
              isActive: false,
            ),
          ],
        },
      ),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.text('Your crop seasons across 2 farms'), findsOneWidget);
    expect(find.text('North Field'), findsOneWidget);
    expect(find.text('South Field'), findsOneWidget);
    expect(find.text('Primary'), findsOneWidget);
    expect(find.text('Rice'), findsOneWidget);
    expect(find.text('Cotton'), findsOneWidget);
    expect(find.text('Rabi 2026'), findsOneWidget);
  });

  testWidgets('keeps loaded crops visible with a stale retry banner', (
    tester,
  ) async {
    setPhoneSize(tester);

    final cropRepository = FakeCropRepository(
      cropsByFarm: {
        'farm-1': [testCrop()],
      },
    );
    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: cropRepository,
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.text('Rice'), findsOneWidget);

    cropRepository.error = Exception('Refresh failed.');
    await provider.refreshCrops();
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crops_stale_banner')), findsOneWidget);
    expect(find.text('Refresh failed.'), findsOneWidget);
    expect(find.text('Rice'), findsOneWidget);
  });

  testWidgets('shows a per-farm empty message for farms without crops', (
    tester,
  ) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(
        farms: [
          testFarm(),
          testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        ],
      ),
      cropRepository: FakeCropRepository(
        cropsByFarm: {
          'farm-1': [testCrop()],
        },
      ),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(
      find.text('No crop seasons recorded for this farm.'),
      findsOneWidget,
    );
  });

  testWidgets('empty state provides an add crop action', (tester) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.byKey(const Key('crops_empty_add_button')), findsOneWidget);
  });

  testWidgets('summary includes the total crop count', (tester) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(
        cropsByFarm: {
          'farm-1': [testCrop(), testCrop(id: 'crop-2', cropName: 'Cotton')],
        },
      ),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    final totalMetric = find.byKey(const Key('summary_metric_total'));

    expect(totalMetric, findsOneWidget);
    expect(
      find.descendant(of: totalMetric, matching: find.text('2')),
      findsOneWidget,
    );
  });

  testWidgets('opens a crop detail screen from a crop card', (tester) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(
        cropsByFarm: {
          'farm-1': [testCrop()],
        },
        planStages: [testStage()],
        planActivities: [testActivity()],
      ),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    await tester.tap(find.byKey(const Key('crop_card_crop-1')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('crop_detail_screen')), findsOneWidget);
    expect(find.byKey(const Key('crop_detail_plan')), findsOneWidget);
    expect(find.text('Land preparation'), findsOneWidget);
    expect(find.text('Plough the field'), findsOneWidget);
  });

  testWidgets('shows cancellation reason for cancelled crops', (tester) async {
    setPhoneSize(tester);

    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: FakeCropRepository(
        cropsByFarm: {
          'farm-1': [
            testCrop(
              status: CropSeasonStatus.cancelled,
              isActive: false,
              cancellationReason: 'Heavy rain damaged the nursery.',
            ),
          ],
        },
      ),
    );

    await provider.loadCrops();
    await tester.pumpWidget(buildCropsApp(provider));

    expect(find.text('Cancelled'), findsOneWidget);
    expect(find.text('Heavy rain damaged the nursery.'), findsOneWidget);
  });
}

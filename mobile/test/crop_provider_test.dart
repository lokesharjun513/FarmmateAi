import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_plan_models.dart';
import 'package:mobile/features/crops/data/models/crop_season_model.dart';
import 'package:mobile/features/crops/providers/crop_provider.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository({this.farms = const [], this.error});

  List<FarmModel> farms;
  Object? error;
  int listCalls = 0;

  @override
  Future<List<FarmModel>> getFarms() async {
    listCalls++;

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
    List<CropStageModel>? planStages,
    List<CropActivityModel>? planActivities,
    this.planError,
  }) : cropsByFarm = cropsByFarm ?? {},
       planStages = planStages ?? [],
       planActivities = planActivities ?? [];

  Map<String, List<CropSeasonModel>> cropsByFarm;
  Object? error;
  Map<String, Object> farmErrors = {};
  Completer<void>? gate;
  List<CropStageModel> planStages;
  List<CropActivityModel> planActivities;
  Map<String, List<CropStageModel>> planStagesByCrop = {};
  Map<String, Completer<void>> planGates = {};
  Object? planError;
  final List<String> requestedFarmIds = [];

  @override
  Future<List<CropSeasonModel>> getCropSeasons(String farmId) async {
    requestedFarmIds.add(farmId);

    if (gate != null) {
      await gate!.future;
    }

    final farmError = farmErrors[farmId];

    if (farmError != null) {
      throw farmError;
    }

    if (error != null) {
      throw error!;
    }

    return List<CropSeasonModel>.of(cropsByFarm[farmId] ?? const []);
  }

  @override
  Future<List<CropStageModel>> getCropStages(String cropSeasonId) async {
    final planGate = planGates[cropSeasonId];

    if (planGate != null) {
      await planGate.future;
    }

    if (planError != null) {
      throw planError!;
    }

    return List<CropStageModel>.of(
      planStagesByCrop[cropSeasonId] ?? planStages,
    );
  }

  @override
  Future<List<CropActivityModel>> getCropActivities(String cropSeasonId) async {
    final planGate = planGates[cropSeasonId];

    if (planGate != null) {
      await planGate.future;
    }

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
}) {
  return CropStageModel(
    id: id,
    cropSeasonId: cropSeasonId,
    name: name,
    description: null,
    stageOrder: stageOrder,
    startDay: 1,
    endDay: 10,
    status: CropStageStatus.pending,
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

void main() {
  test('load exposes loading and groups farms with primary first', () async {
    final gate = Completer<void>();
    final farmRepository = FakeFarmRepository(
      farms: [
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        testFarm(id: 'farm-1', name: 'North Field'),
      ],
    );
    final cropRepository = FakeCropRepository(
      gate: gate,
      cropsByFarm: {
        'farm-1': [
          testCrop(id: 'planned', status: CropSeasonStatus.planned),
          testCrop(id: 'active', status: CropSeasonStatus.active),
          testCrop(id: 'harvested', status: CropSeasonStatus.harvested),
          testCrop(id: 'cancelled', status: CropSeasonStatus.cancelled),
        ],
      },
    );
    final provider = buildProvider(
      farmRepository: farmRepository,
      cropRepository: cropRepository,
    );

    final loading = provider.loadCrops();

    expect(provider.isInitialLoading, isTrue);
    expect(provider.hasLoaded, isFalse);

    gate.complete();
    await loading;

    expect(provider.isInitialLoading, isFalse);
    expect(provider.hasLoaded, isTrue);
    expect(provider.hasError, isFalse);
    expect(provider.hasMultipleFarms, isTrue);
    expect(provider.farmCount, 2);
    expect(provider.groups.map((group) => group.farm.id), ['farm-1', 'farm-2']);
    expect(provider.groups.first.farm.isPrimary, isTrue);
    expect(provider.groups.first.crops.map((crop) => crop.id), [
      'active',
      'planned',
      'harvested',
      'cancelled',
    ]);
    expect(provider.groups.last.hasCrops, isFalse);
    expect(provider.totalCrops, 4);
    expect(provider.activeCropCount, 1);
    expect(provider.plannedCropCount, 1);
    expect(provider.harvestedCropCount, 1);
    expect(provider.lastUpdated, isNotNull);
    expect(cropRepository.requestedFarmIds, ['farm-1', 'farm-2']);
  });

  test('empty farms and crops produce an honest empty state', () async {
    final farmRepository = FakeFarmRepository(farms: [testFarm()]);
    final cropRepository = FakeCropRepository();
    final provider = buildProvider(
      farmRepository: farmRepository,
      cropRepository: cropRepository,
    );

    await provider.loadCrops();

    expect(provider.hasLoaded, isTrue);
    expect(provider.isEmpty, isTrue);
    expect(provider.hasCrops, isFalse);
    expect(provider.isShowingStaleData, isFalse);
    expect(provider.groups, hasLength(1));
    expect(provider.groups.single.hasCrops, isFalse);
  });

  test('initial failure is honest and retry recovers', () async {
    final farmRepository = FakeFarmRepository(farms: [testFarm()]);
    final cropRepository = FakeCropRepository(
      error: Exception('Unable to load crops.'),
    );
    final provider = buildProvider(
      farmRepository: farmRepository,
      cropRepository: cropRepository,
    );

    await provider.loadCrops();

    expect(provider.hasLoaded, isFalse);
    expect(provider.hasError, isTrue);
    expect(provider.errorMessage, 'Unable to load crops.');
    expect(provider.isShowingStaleData, isFalse);
    expect(provider.groups, isEmpty);

    cropRepository
      ..error = null
      ..cropsByFarm = {
        'farm-1': [testCrop()],
      };

    await provider.retry();

    expect(provider.hasLoaded, isTrue);
    expect(provider.hasError, isFalse);
    expect(provider.crops, hasLength(1));
    expect(provider.groups.single.hasCrops, isTrue);
    expect(cropRepository.requestedFarmIds, ['farm-1', 'farm-1']);
  });

  test('refresh failure keeps the last loaded crops as stale data', () async {
    final farmRepository = FakeFarmRepository(farms: [testFarm()]);
    final cropRepository = FakeCropRepository(
      cropsByFarm: {
        'farm-1': [testCrop()],
      },
    );
    final provider = buildProvider(
      farmRepository: farmRepository,
      cropRepository: cropRepository,
    );

    await provider.loadCrops();
    cropRepository.error = Exception('Refresh failed.');

    await provider.refreshCrops();

    expect(provider.hasLoaded, isTrue);
    expect(provider.hasError, isTrue);
    expect(provider.isShowingStaleData, isTrue);
    expect(provider.errorMessage, 'Refresh failed.');
    expect(provider.crops, hasLength(1));
    expect(provider.groups.single.crops.single.cropName, 'Rice');

    cropRepository
      ..error = null
      ..cropsByFarm = {
        'farm-1': [testCrop(id: 'crop-2', cropName: 'Cotton')],
      };

    await provider.refreshCrops();

    expect(provider.hasError, isFalse);
    expect(provider.isShowingStaleData, isFalse);
    expect(provider.crops.single.cropName, 'Cotton');
  });

  test(
    'refresh failure during multi-farm load preserves every group',
    () async {
      final farmRepository = FakeFarmRepository(
        farms: [
          testFarm(),
          testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        ],
      );
      final cropRepository = FakeCropRepository(
        cropsByFarm: {
          'farm-1': [testCrop()],
          'farm-2': [
            testCrop(id: 'crop-2', farmId: 'farm-2', cropName: 'Cotton'),
          ],
        },
      );
      final provider = buildProvider(
        farmRepository: farmRepository,
        cropRepository: cropRepository,
      );

      await provider.loadCrops();
      cropRepository.error = Exception('One farm could not refresh.');

      await provider.refreshCrops();

      expect(provider.groups, hasLength(2));
      expect(provider.groups.first.crops.single.cropName, 'Rice');
      expect(provider.groups.last.crops.single.cropName, 'Cotton');
      expect(provider.isShowingStaleData, isTrue);
    },
  );

  test('load does not refetch after success without force refresh', () async {
    final farmRepository = FakeFarmRepository(farms: [testFarm()]);
    final cropRepository = FakeCropRepository(
      cropsByFarm: {
        'farm-1': [testCrop()],
      },
    );
    final provider = buildProvider(
      farmRepository: farmRepository,
      cropRepository: cropRepository,
    );

    await provider.loadCrops();
    await provider.loadCrops();

    expect(farmRepository.listCalls, 1);
    expect(cropRepository.requestedFarmIds, ['farm-1']);
  });

  test(
    'farm loading failures are reported without a false empty state',
    () async {
      final farmRepository = FakeFarmRepository(
        error: Exception('Unable to load farms.'),
      );
      final cropRepository = FakeCropRepository();
      final provider = buildProvider(
        farmRepository: farmRepository,
        cropRepository: cropRepository,
      );

      await provider.loadCrops();

      expect(provider.hasLoaded, isFalse);
      expect(provider.hasError, isTrue);
      expect(provider.errorMessage, 'Unable to load farms.');
      expect(provider.isEmpty, isFalse);
      expect(cropRepository.requestedFarmIds, isEmpty);
    },
  );

  test('loadCropPlan can represent a crop with no plan', () async {
    final cropRepository = FakeCropRepository();
    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: cropRepository,
    );

    await provider.loadCropPlan('crop-1', allowEmpty: true);

    expect(provider.planStages, isEmpty);
    expect(provider.planActivities, isEmpty);
    expect(provider.hasPlanError, isFalse);
  });

  test('loadCropPlan clears old stages before a failed refresh', () async {
    final cropRepository = FakeCropRepository(
      planStages: [testStage()],
      planActivities: [testActivity()],
    );
    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: cropRepository,
    );

    await provider.loadCropPlan('crop-1');

    expect(provider.planStages, hasLength(1));
    expect(provider.planActivities, hasLength(1));

    cropRepository.planError = Exception('Plan refresh failed.');

    await expectLater(provider.loadCropPlan('crop-1'), throwsException);

    expect(provider.planStages, isEmpty);
    expect(provider.planActivities, isEmpty);
    expect(provider.planErrorMessage, 'Plan refresh failed.');
  });

  test(
    'partial farm failure preserves successes and retries only failures',
    () async {
      final farmRepository = FakeFarmRepository(
        farms: [
          testFarm(),
          testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        ],
      );
      final cropRepository = FakeCropRepository(
        cropsByFarm: {
          'farm-1': [testCrop()],
          'farm-2': [
            testCrop(id: 'crop-2', farmId: 'farm-2', cropName: 'Cotton'),
          ],
        },
      );
      final provider = buildProvider(
        farmRepository: farmRepository,
        cropRepository: cropRepository,
      );

      await provider.loadCrops();
      cropRepository.farmErrors['farm-2'] = Exception('South Field failed.');

      await provider.refreshCrops();

      expect(provider.hasError, isTrue);
      expect(provider.hasPartialFailure, isTrue);
      expect(provider.farmErrors, {'farm-2': 'South Field failed.'});
      expect(provider.crops, hasLength(2));
      expect(provider.groups.first.crops.single.cropName, 'Rice');
      expect(provider.groups.last.crops.single.cropName, 'Cotton');

      cropRepository
        ..farmErrors.remove('farm-2')
        ..cropsByFarm['farm-2'] = [
          testCrop(id: 'crop-2', farmId: 'farm-2', cropName: 'Cotton v2'),
        ];
      cropRepository.requestedFarmIds.clear();

      await provider.retry();

      expect(cropRepository.requestedFarmIds, ['farm-2']);
      expect(provider.hasError, isFalse);
      expect(provider.farmErrors, isEmpty);
      expect(provider.crops, hasLength(2));
      expect(provider.groups.last.crops.single.cropName, 'Cotton v2');
    },
  );

  test('all farms failing on refresh preserves every stale group', () async {
    final farmRepository = FakeFarmRepository(
      farms: [
        testFarm(),
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
      ],
    );
    final cropRepository = FakeCropRepository(
      cropsByFarm: {
        'farm-1': [testCrop()],
        'farm-2': [
          testCrop(id: 'crop-2', farmId: 'farm-2', cropName: 'Cotton'),
        ],
      },
    );
    final provider = buildProvider(
      farmRepository: farmRepository,
      cropRepository: cropRepository,
    );

    await provider.loadCrops();
    cropRepository
      ..farmErrors['farm-1'] = Exception('North Field failed.')
      ..farmErrors['farm-2'] = Exception('South Field failed.');

    await provider.refreshCrops();

    expect(provider.hasError, isTrue);
    expect(provider.hasPartialFailure, isFalse);
    expect(provider.isShowingStaleData, isTrue);
    expect(provider.crops, hasLength(2));
    expect(provider.groups.first.crops.single.cropName, 'Rice');
    expect(provider.groups.last.crops.single.cropName, 'Cotton');
  });

  test('older plan response cannot overwrite a newer crop plan', () async {
    final firstGate = Completer<void>();
    final secondGate = Completer<void>();
    final cropRepository = FakeCropRepository()
      ..planGates = {'crop-a': firstGate, 'crop-b': secondGate}
      ..planStagesByCrop = {
        'crop-a': [
          testStage(id: 'stage-a', cropSeasonId: 'crop-a', name: 'Old plan'),
        ],
        'crop-b': [
          testStage(id: 'stage-b', cropSeasonId: 'crop-b', name: 'New plan'),
        ],
      };
    final provider = buildProvider(
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
      cropRepository: cropRepository,
    );

    final firstRequest = provider.loadCropPlan('crop-a');
    final secondRequest = provider.loadCropPlan('crop-b');

    secondGate.complete();
    await secondRequest;

    expect(provider.planStages, hasLength(1));
    expect(provider.planStages.single.cropSeasonId, 'crop-b');
    expect(provider.planStages.single.name, 'New plan');
    expect(provider.isLoadingPlan, isFalse);

    firstGate.complete();
    await firstRequest;

    expect(provider.planStages, hasLength(1));
    expect(provider.planStages.single.cropSeasonId, 'crop-b');
    expect(provider.planStages.single.name, 'New plan');
    expect(provider.isLoadingPlan, isFalse);
  });

  test('disposing during plan loading does not notify after dispose', () async {
    final gate = Completer<void>();
    final cropRepository = FakeCropRepository()..planGates = {'crop-1': gate};
    final provider = CropProvider(
      repository: cropRepository,
      farmRepository: FakeFarmRepository(farms: [testFarm()]),
    );

    final loading = provider.loadCropPlan('crop-1');
    provider.dispose();
    gate.complete();

    await loading;

    expect(provider.planStages, isEmpty);
  });
}

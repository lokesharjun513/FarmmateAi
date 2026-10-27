import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';
import 'package:mobile/features/farm/data/models/farm_model.dart';
import 'package:mobile/features/farm/providers/farm_provider.dart';

class FakeFarmRepository extends FarmRepository {
  FakeFarmRepository({
    List<FarmModel>? farms,
    FarmModel? createdFarm,
    this.listError,
    this.createError,
    this.setPrimaryError,
    this.listCompleter,
    this.createCompleter,
    this.setPrimaryCompleter,
  }) : farms = farms ?? const [],
       createdFarm = createdFarm ?? testFarm();

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
  double landArea = 2.5,
  String landUnit = 'Acres',
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
    landArea: landArea,
    landUnit: landUnit,
    soilType: 'Clay',
    waterSource: 'Borewell',
    waterAvailability: 'HIGH',
    irrigationMethod: 'Drip',
    isPrimary: isPrimary,
  );
}

FarmCreateInput createInput({bool isPrimary = false}) {
  return FarmCreateInput(
    farmName: 'South Field',
    state: 'Andhra Pradesh',
    district: 'Nellore',
    mandal: 'Kavali',
    village: 'Ramapuram',
    latitude: null,
    longitude: null,
    landArea: 1.5,
    isPrimary: isPrimary,
  );
}

void main() {
  test(
    'load exposes loading, sorts primary first, and records timestamp',
    () async {
      final completer = Completer<List<FarmModel>>();
      final repository = FakeFarmRepository(listCompleter: completer);
      final provider = FarmProvider(repository: repository);
      addTearDown(provider.dispose);

      final loading = provider.loadFarms();

      expect(provider.isInitialLoading, isTrue);
      expect(provider.canCreateFarm, isFalse);
      expect(provider.nextFarmIsPrimary, isNull);

      completer.complete([
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        testFarm(id: 'farm-1', name: 'North Field'),
      ]);

      await loading;

      expect(provider.isInitialLoading, isFalse);
      expect(provider.hasLoaded, isTrue);
      expect(provider.farms.map((farm) => farm.id), ['farm-1', 'farm-2']);
      expect(provider.canCreateFarm, isTrue);
      expect(provider.nextFarmIsPrimary, isFalse);
      expect(provider.lastUpdated, isNotNull);
    },
  );

  test('empty successful load makes the next farm primary', () async {
    final repository = FakeFarmRepository(farms: const []);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    expect(provider.hasLoaded, isTrue);
    expect(provider.isEmpty, isTrue);
    expect(provider.nextFarmIsPrimary, isTrue);
    expect(provider.canCreateFarm, isTrue);
  });

  test('initial failure is honest and retry recovers', () async {
    final repository = FakeFarmRepository(
      listError: Exception('Unable to load farms.'),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    expect(provider.hasLoaded, isFalse);
    expect(provider.hasError, isTrue);
    expect(provider.errorMessage, 'Unable to load farms.');
    expect(provider.canCreateFarm, isFalse);
    expect(provider.nextFarmIsPrimary, isNull);

    repository
      ..listError = null
      ..farms = [testFarm()];

    await provider.refreshFarms();

    expect(provider.hasLoaded, isTrue);
    expect(provider.hasError, isFalse);
    expect(provider.farms, hasLength(1));
    expect(repository.listCalls, 2);
  });

  test('refresh failure keeps the last loaded farms', () async {
    final repository = FakeFarmRepository(farms: [testFarm()]);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    repository.listError = Exception('Refresh failed.');

    await provider.refreshFarms();

    expect(provider.hasLoaded, isTrue);
    expect(provider.hasError, isTrue);
    expect(provider.farms, hasLength(1));
    expect(provider.farms.first.farmName, 'North Field');
  });

  test(
    'creating a non-primary farm appends it without changing primary',
    () async {
      final repository = FakeFarmRepository(
        farms: [testFarm()],
        createdFarm: testFarm(
          id: 'farm-2',
          name: 'South Field',
          isPrimary: false,
          landArea: 1.5,
        ),
      );
      final provider = FarmProvider(repository: repository);
      addTearDown(provider.dispose);

      await provider.loadFarms();

      final farm = await provider.createFarm(createInput());

      expect(farm.id, 'farm-2');
      expect(repository.createCalls, 1);
      expect(repository.lastInput!.isPrimary, isFalse);
      expect(provider.farms.map((item) => item.id), ['farm-1', 'farm-2']);
      expect(provider.farms.first.isPrimary, isTrue);
      expect(provider.farms.last.isPrimary, isFalse);
    },
  );

  test('creating a primary farm demotes the previous primary', () async {
    final repository = FakeFarmRepository(
      farms: [testFarm()],
      createdFarm: testFarm(id: 'farm-2', name: 'South Field', isPrimary: true),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    await provider.createFarm(createInput(isPrimary: true));

    expect(provider.farms.map((item) => item.id), ['farm-2', 'farm-1']);
    expect(provider.farms.where((farm) => farm.isPrimary), hasLength(1));
    expect(provider.farms.last.isPrimary, isFalse);
  });

  test('reconciliation does not duplicate an existing farm id', () async {
    final repository = FakeFarmRepository(
      farms: [testFarm(id: 'farm-1', name: 'Old Name')],
      createdFarm: testFarm(id: 'farm-1', name: 'North Field'),
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    await provider.createFarm(createInput(isPrimary: true));

    expect(provider.farms, hasLength(1));
    expect(provider.farms.single.farmName, 'North Field');
  });

  test('duplicate create submissions are guarded', () async {
    final completer = Completer<FarmModel>();
    final repository = FakeFarmRepository(
      farms: [testFarm()],
      createdFarm: testFarm(id: 'farm-2', name: 'South Field'),
    )..createCompleter = completer;
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    final first = provider.createFarm(createInput());
    expect(provider.isCreating, isTrue);

    await expectLater(
      provider.createFarm(createInput()),
      throwsA(
        isA<Exception>().having(
          (error) => error.toString(),
          'message',
          contains('already being added'),
        ),
      ),
    );

    completer.complete(testFarm(id: 'farm-2', name: 'South Field'));
    await first;

    expect(repository.createCalls, 1);
    expect(provider.isCreating, isFalse);
  });

  test('creation is disabled until the farm list is known', () async {
    final repository = FakeFarmRepository(farms: [testFarm()]);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await expectLater(
      provider.createFarm(createInput()),
      throwsA(
        isA<Exception>().having(
          (error) => error.toString(),
          'message',
          contains('Load your farms'),
        ),
      ),
    );

    expect(repository.createCalls, 0);
  });

  test('setting a primary farm demotes the previous primary', () async {
    final repository = FakeFarmRepository(
      farms: [
        testFarm(id: 'farm-1', name: 'North Field'),
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
      ],
    );
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    final primaryFarm = await provider.setPrimary('farm-2');

    expect(primaryFarm.id, 'farm-2');
    expect(repository.setPrimaryCalls, 1);
    expect(repository.lastPrimaryFarmId, 'farm-2');
    expect(provider.farms.map((farm) => farm.id), ['farm-2', 'farm-1']);
    expect(provider.farms.first.isPrimary, isTrue);
    expect(provider.farms.last.isPrimary, isFalse);
    expect(provider.isSettingPrimary, isFalse);
  });

  test('primary switch failure keeps the previous primary', () async {
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

    await expectLater(
      provider.setPrimary('farm-2'),
      throwsA(
        isA<Exception>().having(
          (error) => error.toString(),
          'message',
          contains('Unable to switch primary farm'),
        ),
      ),
    );

    expect(provider.farms.map((farm) => farm.id), ['farm-1', 'farm-2']);
    expect(provider.farms.first.isPrimary, isTrue);
    expect(provider.farms.last.isPrimary, isFalse);
    expect(provider.isSettingPrimary, isFalse);
  });

  test('selecting the current primary makes no request', () async {
    final repository = FakeFarmRepository(farms: [testFarm()]);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    final primaryFarm = await provider.setPrimary('farm-1');

    expect(primaryFarm.id, 'farm-1');
    expect(repository.setPrimaryCalls, 0);
    expect(provider.farms.single.isPrimary, isTrue);
  });

  test('duplicate primary switches are guarded', () async {
    final completer = Completer<FarmModel>();
    final repository = FakeFarmRepository(
      farms: [
        testFarm(id: 'farm-1'),
        testFarm(id: 'farm-2', name: 'South Field', isPrimary: false),
        testFarm(id: 'farm-3', name: 'East Field', isPrimary: false),
      ],
    )..setPrimaryCompleter = completer;
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    final first = provider.setPrimary('farm-2');

    expect(provider.isSettingPrimary, isTrue);
    expect(provider.isSettingPrimaryFor('farm-2'), isTrue);

    await expectLater(
      provider.setPrimary('farm-3'),
      throwsA(
        isA<Exception>().having(
          (error) => error.toString(),
          'message',
          contains('already being set as primary'),
        ),
      ),
    );

    completer.complete(
      testFarm(id: 'farm-2', name: 'South Field', isPrimary: true),
    );
    await first;

    expect(repository.setPrimaryCalls, 1);
    expect(provider.isSettingPrimary, isFalse);
  });

  test('primary switching requires a known farm', () async {
    final repository = FakeFarmRepository(farms: [testFarm()]);
    final provider = FarmProvider(repository: repository);
    addTearDown(provider.dispose);

    await provider.loadFarms();

    await expectLater(
      provider.setPrimary('missing-farm'),
      throwsA(
        isA<Exception>().having(
          (error) => error.toString(),
          'message',
          contains('could not be found'),
        ),
      ),
    );

    expect(repository.setPrimaryCalls, 0);
  });
}

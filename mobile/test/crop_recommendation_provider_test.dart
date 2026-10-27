import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_recommendation_model.dart';
import 'package:mobile/features/crops/providers/crop_recommendation_provider.dart';

class FakeRecommendationRepository extends CropRepository {
  FakeRecommendationRepository({
    Map<String, CropRecommendationModel>? results,
    this.error,
    Map<String, Completer<void>>? gates,
  }) : results = results ?? {},
       gates = gates ?? {};

  Map<String, CropRecommendationModel> results;
  Object? error;
  Map<String, Completer<void>> gates;
  final List<String> requestedFarmIds = [];

  @override
  Future<CropRecommendationModel> getCropRecommendations(String farmId) async {
    requestedFarmIds.add(farmId);

    final gate = gates[farmId];

    if (gate != null) {
      await gate.future;
    }

    if (error != null) {
      throw error!;
    }

    final result = results[farmId];

    if (result == null) {
      throw Exception('No recommendation fixture for $farmId.');
    }

    return result;
  }
}

CropRecommendationModel recommendationFor(
  String farmId, {
  String cropName = 'Rice',
  int confidence = 90,
  String date = '2026-08-20',
}) {
  return CropRecommendationModel(
    farmId: farmId,
    recommendedSowingDate: DateTime.tryParse(date),
    recommendedCrops: [
      RecommendedCropModel(
        cropName: cropName,
        confidence: confidence,
        reason: 'Suitable for this farm.',
      ),
    ],
  );
}

CropRecommendationProvider buildProvider(
  FakeRecommendationRepository repository,
) {
  final provider = CropRecommendationProvider(repository: repository);
  addTearDown(provider.dispose);
  return provider;
}

void main() {
  test(
    'loads recommendations and exposes loading then success state',
    () async {
      final gate = Completer<void>();
      final repository = FakeRecommendationRepository(
        results: {'farm-1': recommendationFor('farm-1')},
        gates: {'farm-1': gate},
      );
      final provider = buildProvider(repository);

      final loading = provider.loadRecommendations('farm-1');

      expect(provider.isLoading, isTrue);
      expect(provider.isInitialLoading, isTrue);
      expect(provider.hasLoaded, isFalse);
      expect(provider.recommendedCrops, isEmpty);

      gate.complete();
      await loading;

      expect(provider.isLoading, isFalse);
      expect(provider.hasLoaded, isTrue);
      expect(provider.hasError, isFalse);
      expect(provider.farmId, 'farm-1');
      expect(provider.recommendedCrops, hasLength(1));
      expect(provider.recommendedCrops.single.cropName, 'Rice');
      expect(provider.recommendedCrops.single.confidence, 90);
      expect(provider.recommendedSowingDate, DateTime(2026, 8, 20));
      expect(repository.requestedFarmIds, ['farm-1']);
    },
  );

  test('surfaces a failure and retry clears the error', () async {
    final repository = FakeRecommendationRepository(
      results: {'farm-1': recommendationFor('farm-1')},
      error: Exception('Recommendations are unavailable.'),
    );
    final provider = buildProvider(repository);

    await provider.loadRecommendations('farm-1');

    expect(provider.hasError, isTrue);
    expect(provider.errorMessage, 'Recommendations are unavailable.');
    expect(provider.hasLoaded, isFalse);
    expect(provider.isLoading, isFalse);

    repository.error = null;
    await provider.retry();

    expect(provider.hasError, isFalse);
    expect(provider.hasLoaded, isTrue);
    expect(provider.recommendedCrops.single.cropName, 'Rice');
    expect(repository.requestedFarmIds, ['farm-1', 'farm-1']);
  });

  test('ignores an older farm response after switching farms', () async {
    final firstGate = Completer<void>();
    final secondGate = Completer<void>();
    final repository = FakeRecommendationRepository(
      results: {
        'farm-1': recommendationFor('farm-1', cropName: 'Rice'),
        'farm-2': recommendationFor('farm-2', cropName: 'Maize'),
      },
      gates: {'farm-1': firstGate, 'farm-2': secondGate},
    );
    final provider = buildProvider(repository);

    final firstLoad = provider.loadRecommendations('farm-1');
    final secondLoad = provider.loadRecommendations('farm-2');

    secondGate.complete();
    await secondLoad;

    expect(provider.farmId, 'farm-2');
    expect(provider.recommendedCrops.single.cropName, 'Maize');
    expect(provider.isLoading, isFalse);

    firstGate.complete();
    await firstLoad;

    expect(provider.farmId, 'farm-2');
    expect(provider.recommendedCrops.single.cropName, 'Maize');
    expect(provider.isLoading, isFalse);
    expect(provider.hasError, isFalse);
  });

  test('does not reload the same farm after a successful load', () async {
    final repository = FakeRecommendationRepository(
      results: {'farm-1': recommendationFor('farm-1')},
    );
    final provider = buildProvider(repository);

    await provider.loadRecommendations('farm-1');
    await provider.loadRecommendations('farm-1');

    expect(repository.requestedFarmIds, ['farm-1']);
  });

  test('force refresh requests the same farm again', () async {
    final repository = FakeRecommendationRepository(
      results: {'farm-1': recommendationFor('farm-1')},
    );
    final provider = buildProvider(repository);

    await provider.loadRecommendations('farm-1');
    await provider.loadRecommendations('farm-1', forceRefresh: true);

    expect(repository.requestedFarmIds, ['farm-1', 'farm-1']);
  });

  test('requires a farm id and clears any previous recommendation', () async {
    final repository = FakeRecommendationRepository(
      results: {'farm-1': recommendationFor('farm-1')},
    );
    final provider = buildProvider(repository);

    await provider.loadRecommendations('farm-1');
    await provider.loadRecommendations('   ');

    expect(provider.farmId, isNull);
    expect(provider.recommendedCrops, isEmpty);
    expect(provider.hasError, isTrue);
    expect(provider.errorMessage, 'Select a farm to get crop recommendations.');
    expect(repository.requestedFarmIds, ['farm-1']);
  });

  test('clear cancels an in-flight request', () async {
    final gate = Completer<void>();
    final repository = FakeRecommendationRepository(
      results: {'farm-1': recommendationFor('farm-1')},
      gates: {'farm-1': gate},
    );
    final provider = buildProvider(repository);

    final loading = provider.loadRecommendations('farm-1');
    provider.clear();

    gate.complete();
    await loading;

    expect(provider.farmId, isNull);
    expect(provider.recommendedCrops, isEmpty);
    expect(provider.isLoading, isFalse);
    expect(provider.hasLoaded, isFalse);
  });
}

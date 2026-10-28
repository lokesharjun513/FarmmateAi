import 'package:flutter/foundation.dart';

import '../../farm/data/farm_repository.dart';
import '../../farm/data/models/farm_model.dart';
import '../data/crop_repository.dart';
import '../data/models/crop_plan_models.dart';
import '../data/models/crop_season_create_input.dart';
import '../data/models/crop_season_model.dart';

class CropFarmGroup {
  final FarmModel farm;
  final List<CropSeasonModel> crops;

  const CropFarmGroup({required this.farm, required this.crops});

  bool get hasCrops => crops.isNotEmpty;

  int get activeCropCount =>
      crops.where((crop) => crop.status == CropSeasonStatus.active).length;

  int get plannedCropCount =>
      crops.where((crop) => crop.status == CropSeasonStatus.planned).length;
}

class _FarmCropResult {
  const _FarmCropResult.success(this.farm, this.crops) : error = null;

  const _FarmCropResult.failure(this.farm, this.error) : crops = const [];

  final FarmModel farm;
  final List<CropSeasonModel> crops;
  final String? error;

  bool get isSuccess => error == null;
}

class CropProvider extends ChangeNotifier {
  CropProvider({CropRepository? repository, FarmRepository? farmRepository})
    : _repository = repository ?? CropRepository(),
      _farmRepository = farmRepository ?? FarmRepository();

  final CropRepository _repository;
  final FarmRepository _farmRepository;

  List<FarmModel> _farms = const [];
  List<CropFarmGroup> _groups = const [];
  List<CropSeasonModel> _crops = const [];
  bool _isLoading = false;
  bool _hasLoaded = false;
  bool _isCreatingCrop = false;
  bool _isGeneratingPlan = false;
  bool _isLoadingPlan = false;
  String? _errorMessage;
  String? _planErrorMessage;
  DateTime? _lastUpdated;
  CropSeasonModel? _createdCrop;
  CropPlanSummary? _planSummary;
  List<CropStageModel> _planStages = const [];
  List<CropActivityModel> _planActivities = const [];
  final Map<String, String> _farmErrors = {};
  int _planRequestId = 0;
  String? _planCropId;
  bool _isDisposed = false;

  List<FarmModel> get farms => List.unmodifiable(_farms);

  List<CropFarmGroup> get groups => List.unmodifiable(_groups);

  List<CropSeasonModel> get crops => List.unmodifiable(_crops);

  bool get isLoading => _isLoading;

  bool get hasLoaded => _hasLoaded;

  bool get hasError =>
      _errorMessage != null && _errorMessage!.trim().isNotEmpty;

  String? get errorMessage => _errorMessage;

  Map<String, String> get farmErrors => Map.unmodifiable(_farmErrors);

  bool get hasPartialFailure =>
      _farmErrors.isNotEmpty &&
      _farmErrors.length < _farms.length &&
      _farms.isNotEmpty;

  List<String> get failedFarmNames => [
    for (final farm in _farms)
      if (_farmErrors.containsKey(farm.id)) farm.farmName,
  ];

  DateTime? get lastUpdated => _lastUpdated;

  bool get isCreatingCrop => _isCreatingCrop;

  bool get isGeneratingPlan => _isGeneratingPlan;

  bool get isLoadingPlan => _isLoadingPlan;

  bool get isWorkingOnPlan => _isGeneratingPlan || _isLoadingPlan;

  bool get hasGeneratedPlan => _planSummary != null;

  bool get hasPlanError =>
      _planErrorMessage != null && _planErrorMessage!.trim().isNotEmpty;

  String? get planErrorMessage => _planErrorMessage;

  CropSeasonModel? get createdCrop => _createdCrop;

  CropPlanSummary? get planSummary => _planSummary;

  List<CropStageModel> get planStages => List.unmodifiable(_planStages);

  List<CropActivityModel> get planActivities =>
      List.unmodifiable(_planActivities);

  bool get isInitialLoading => _isLoading && !_hasLoaded;

  bool get isRefreshing => _isLoading && _hasLoaded;

  bool get isEmpty => _hasLoaded && _crops.isEmpty;

  bool get hasCrops => _crops.isNotEmpty;

  bool get isShowingStaleData => _hasLoaded && hasError;

  bool get hasMultipleFarms => _farms.length > 1;

  int get farmCount => _farms.length;

  int get totalCrops => _crops.length;

  int get activeCropCount =>
      _crops.where((crop) => crop.status == CropSeasonStatus.active).length;

  int get plannedCropCount =>
      _crops.where((crop) => crop.status == CropSeasonStatus.planned).length;

  int get harvestedCropCount =>
      _crops.where((crop) => crop.status == CropSeasonStatus.harvested).length;

  Future<void> loadCrops({bool forceRefresh = false}) async {
    if (_isLoading) {
      return;
    }

    if (_hasLoaded && !forceRefresh) {
      return;
    }

    _isLoading = true;
    _errorMessage = null;
    _farmErrors.clear();
    _notifyListeners();

    try {
      final farms = _sortFarms(await _farmRepository.getFarms());

      if (_isDisposed) {
        return;
      }

      final previousGroups = {
        for (final group in _groups) group.farm.id: group,
      };
      final results = await Future.wait(farms.map(_loadFarmCrops));

      if (_isDisposed) {
        return;
      }

      final groups = <CropFarmGroup>[];
      var successfulFarms = 0;

      for (final result in results) {
        if (result.isSuccess) {
          successfulFarms += 1;
          groups.add(
            CropFarmGroup(farm: result.farm, crops: _sortCrops(result.crops)),
          );
          continue;
        }

        _farmErrors[result.farm.id] = result.error!;
        final staleCrops = previousGroups[result.farm.id]?.crops ?? const [];
        groups.add(
          CropFarmGroup(farm: result.farm, crops: _sortCrops(staleCrops)),
        );
      }

      _farms = farms;

      if (farms.isEmpty || successfulFarms > 0 || _hasLoaded) {
        _groups = groups;
        _crops = groups.expand((group) => group.crops).toList(growable: false);
        _hasLoaded = true;

        if (successfulFarms > 0) {
          _lastUpdated = DateTime.now();
        }

        _errorMessage = _farmErrors.isEmpty
            ? null
            : _partialFailureMessage(farms.length);
      } else {
        _errorMessage = _partialFailureMessage(farms.length);
      }
    } catch (error) {
      _errorMessage = _cleanError(error);
    } finally {
      if (!_isDisposed) {
        _isLoading = false;
        _notifyListeners();
      }
    }
  }

  Future<void> refreshCrops() async {
    await loadCrops(forceRefresh: true);
  }

  Future<void> retry() async {
    if (_hasLoaded && _farmErrors.isNotEmpty) {
      await retryFailedFarms();
      return;
    }

    await refreshCrops();
  }

  Future<void> retryFailedFarms() async {
    if (_isLoading || _farmErrors.isEmpty) {
      return;
    }

    _isLoading = true;
    _errorMessage = null;
    _notifyListeners();

    final failedFarmIds = Set<String>.of(_farmErrors.keys);
    final farmsById = {for (final farm in _farms) farm.id: farm};

    try {
      final results = await Future.wait(
        failedFarmIds
            .where(farmsById.containsKey)
            .map((farmId) => _loadFarmCrops(farmsById[farmId]!)),
      );

      if (_isDisposed) {
        return;
      }

      final groupsById = {for (final group in _groups) group.farm.id: group};
      var successfulFarms = 0;

      for (final result in results) {
        if (result.isSuccess) {
          successfulFarms += 1;
          _farmErrors.remove(result.farm.id);
          groupsById[result.farm.id] = CropFarmGroup(
            farm: result.farm,
            crops: _sortCrops(result.crops),
          );
          continue;
        }

        _farmErrors[result.farm.id] = result.error!;
      }

      _groups = [
        for (final farm in _farms)
          groupsById[farm.id] ?? CropFarmGroup(farm: farm, crops: const []),
      ];
      _crops = _groups.expand((group) => group.crops).toList(growable: false);

      if (successfulFarms > 0) {
        _lastUpdated = DateTime.now();
      }

      _errorMessage = _farmErrors.isEmpty
          ? null
          : _partialFailureMessage(_farms.length);
    } catch (error) {
      _errorMessage = _cleanError(error);
    } finally {
      if (!_isDisposed) {
        _isLoading = false;
        _notifyListeners();
      }
    }
  }

  Future<CropSeasonModel> createCropSeason({
    required String farmId,
    required CropSeasonCreateInput input,
  }) async {
    if (_isDisposed) {
      throw StateError('The crop provider has been disposed.');
    }

    if (_isCreatingCrop) {
      throw Exception('A crop is already being created. Please wait.');
    }

    _isCreatingCrop = true;
    _createdCrop = null;
    _planSummary = null;
    _planStages = const [];
    _planActivities = const [];
    _planErrorMessage = null;
    _notifyListeners();

    try {
      final crop = await _repository.createCropSeason(
        farmId: farmId,
        input: input,
      );

      if (_isDisposed) {
        return crop;
      }

      _createdCrop = crop;

      return crop;
    } finally {
      _isCreatingCrop = false;

      if (!_isDisposed) {
        _notifyListeners();
      }
    }
  }

  Future<CropSeasonModel> updateCropSeason({
    required String cropSeasonId,
    String? cropName,
    String? cropVariety,
    FarmingSeason? season,
    int? year,
    DateTime? sowingDate,
    DateTime? expectedHarvestDate,
    double? landArea,
    String? landUnit,
    String? notes,
  }) async {
    final updated = await _repository.updateCropSeason(
      cropSeasonId: cropSeasonId,
      cropName: cropName,
      cropVariety: cropVariety,
      season: season,
      year: year,
      sowingDate: sowingDate,
      expectedHarvestDate: expectedHarvestDate,
      landArea: landArea,
      landUnit: landUnit,
      notes: notes,
    );

    _replaceCrop(updated);

    return updated;
  }

  Future<CropSeasonModel> activateCropSeason(String cropSeasonId) async {
    final updated = await _repository.activateCropSeason(cropSeasonId);

    _replaceCrop(updated);

    return updated;
  }

  Future<CropSeasonModel> harvestCropSeason(
    String cropSeasonId, {
    DateTime? harvestedDate,
    String? notes,
  }) async {
    final updated = await _repository.harvestCropSeason(
      cropSeasonId,
      harvestedDate: harvestedDate,
      notes: notes,
    );

    _replaceCrop(updated);

    return updated;
  }

  Future<CropSeasonModel> cancelCropSeason(
    String cropSeasonId, {
    String? reason,
  }) async {
    final updated = await _repository.cancelCropSeason(
      cropSeasonId,
      reason: reason,
    );

    _replaceCrop(updated);

    return updated;
  }

  Future<void> deleteCropSeason(String cropSeasonId) async {
    await _repository.deleteCropSeason(cropSeasonId);

    _groups = [
      for (final group in _groups)
        CropFarmGroup(
          farm: group.farm,
          crops: group.crops
              .where((crop) => crop.id != cropSeasonId)
              .toList(growable: false),
        ),
    ];
    _crops = _groups.expand((group) => group.crops).toList(growable: false);
    _notifyListeners();
  }

  Future<CropStageModel> completeCropStage(String stageId) {
    return _repository.completeCropStage(stageId);
  }

  Future<CropStageModel> skipCropStage(String stageId) {
    return _repository.skipCropStage(stageId);
  }

  Future<CropActivityModel> startActivity(String activityId) {
    return _repository.startActivity(activityId);
  }

  Future<CropActivityModel> completeActivity(String activityId) {
    return _repository.completeActivity(activityId);
  }

  Future<CropActivityModel> skipActivity(String activityId) {
    return _repository.skipActivity(activityId);
  }

  Future<CropActivityModel> rescheduleActivity(
    String activityId,
    DateTime scheduledDate,
  ) {
    return _repository.rescheduleActivity(activityId, scheduledDate);
  }

  Future<void> deleteActivity(String activityId) {
    return _repository.deleteActivity(activityId);
  }

  void _replaceCrop(CropSeasonModel updated) {
    _groups = [
      for (final group in _groups)
        CropFarmGroup(
          farm: group.farm,
          crops: [
            for (final crop in group.crops)
              if (crop.id == updated.id) updated else crop,
          ],
        ),
    ];
    _crops = _groups.expand((group) => group.crops).toList(growable: false);

    if (_createdCrop?.id == updated.id) {
      _createdCrop = updated;
    }

    _notifyListeners();
  }

  Future<CropPlanSummary> generateCropPlan({
    required CropSeasonModel crop,
    required FarmModel farm,
  }) async {
    if (_isDisposed) {
      throw StateError('The crop provider has been disposed.');
    }

    if (_isGeneratingPlan) {
      throw Exception('A crop plan is already being generated. Please wait.');
    }

    _planRequestId += 1;
    _planCropId = crop.id;
    _isGeneratingPlan = true;
    _isLoadingPlan = false;
    _planErrorMessage = null;
    _planSummary = null;
    _planStages = const [];
    _planActivities = const [];
    _notifyListeners();

    try {
      final summary = await _repository.generateCropPlan(
        cropSeasonId: crop.id,
        state: farm.state,
        district: farm.district,
        village: farm.village,
        soilType: farm.soilType,
      );

      if (_isDisposed) {
        return summary;
      }

      _planSummary = summary;

      return summary;
    } catch (error) {
      if (!_isDisposed) {
        _planErrorMessage = _cleanError(error);
      }

      rethrow;
    } finally {
      _isGeneratingPlan = false;

      if (!_isDisposed) {
        _notifyListeners();
      }
    }
  }

  Future<void> loadCropPlan(
    String cropSeasonId, {
    bool allowEmpty = false,
  }) async {
    if (_isDisposed) {
      throw StateError('The crop provider has been disposed.');
    }

    final normalizedCropId = cropSeasonId.trim();

    if (normalizedCropId.isEmpty) {
      throw Exception('A crop season is required to load its plan.');
    }

    final requestId = _planRequestId + 1;
    _planRequestId = requestId;
    _planCropId = normalizedCropId;
    _isLoadingPlan = true;
    _planErrorMessage = null;
    _planStages = const [];
    _planActivities = const [];
    _notifyListeners();

    try {
      final results = await Future.wait<Object>([
        _repository.getCropStages(normalizedCropId),
        _repository.getCropActivities(normalizedCropId),
      ]);

      if (!_isCurrentPlanRequest(requestId, normalizedCropId)) {
        return;
      }

      final stages = List<CropStageModel>.from(results[0] as List)
        ..sort((a, b) => a.stageOrder.compareTo(b.stageOrder));
      final activities = List<CropActivityModel>.from(results[1] as List)
        ..sort((a, b) {
          final dateOrder = a.scheduledDate.compareTo(b.scheduledDate);

          if (dateOrder != 0) {
            return dateOrder;
          }

          return a.title.toLowerCase().compareTo(b.title.toLowerCase());
        });

      if (stages.isEmpty && !allowEmpty) {
        throw Exception('No crop plan was found for this crop season.');
      }

      _planStages = stages;
      _planActivities = activities;
    } catch (error) {
      if (!_isCurrentPlanRequest(requestId, normalizedCropId)) {
        return;
      }

      _planErrorMessage = _cleanError(error);
      rethrow;
    } finally {
      if (_isCurrentPlanRequest(requestId, normalizedCropId)) {
        _isLoadingPlan = false;
        _notifyListeners();
      }
    }
  }

  bool _isCurrentPlanRequest(int requestId, String cropId) {
    return !_isDisposed && requestId == _planRequestId && _planCropId == cropId;
  }

  Future<_FarmCropResult> _loadFarmCrops(FarmModel farm) async {
    try {
      final crops = await _repository.getCropSeasons(farm.id);

      return _FarmCropResult.success(farm, crops);
    } catch (error) {
      return _FarmCropResult.failure(farm, _cleanError(error));
    }
  }

  String _partialFailureMessage(int farmCount) {
    final failedCount = _farmErrors.length;

    if (failedCount >= farmCount) {
      final errors = _farmErrors.values.toSet();

      if (errors.length == 1) {
        return errors.single;
      }

      if (_hasLoaded) {
        return 'Unable to refresh crops for any farm. Showing the latest available data.';
      }

      return 'Unable to load crops for any farm. Please try again.';
    }

    return 'Could not load crops for $failedCount of $farmCount farms. Showing the latest available data.';
  }

  List<FarmModel> _sortFarms(List<FarmModel> farms) {
    final sorted = List<FarmModel>.of(farms)
      ..sort((a, b) {
        if (a.isPrimary != b.isPrimary) {
          return a.isPrimary ? -1 : 1;
        }

        return a.farmName.toLowerCase().compareTo(b.farmName.toLowerCase());
      });

    return sorted;
  }

  List<CropSeasonModel> _sortCrops(List<CropSeasonModel> crops) {
    final sorted = List<CropSeasonModel>.of(crops)
      ..sort((a, b) {
        final statusOrder = _statusPriority(
          a.status,
        ).compareTo(_statusPriority(b.status));

        if (statusOrder != 0) {
          return statusOrder;
        }

        final dateOrder = b.sowingDate.compareTo(a.sowingDate);

        if (dateOrder != 0) {
          return dateOrder;
        }

        return a.cropName.toLowerCase().compareTo(b.cropName.toLowerCase());
      });

    return sorted;
  }

  int _statusPriority(CropSeasonStatus status) {
    return switch (status) {
      CropSeasonStatus.active => 0,
      CropSeasonStatus.planned => 1,
      CropSeasonStatus.harvested => 2,
      CropSeasonStatus.cancelled => 3,
    };
  }

  void _notifyListeners() {
    if (!_isDisposed) {
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _isDisposed = true;
    _planRequestId += 1;
    super.dispose();
  }

  String _cleanError(Object error) {
    var message = error.toString().trim();

    while (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length).trim();
    }

    return message.isEmpty
        ? 'Unable to load your crops. Please try again.'
        : message;
  }
}

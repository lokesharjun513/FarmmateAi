import 'package:flutter/foundation.dart';

import '../data/farm_repository.dart';
import '../data/models/farm_model.dart';

class FarmProvider extends ChangeNotifier {
  FarmProvider({FarmRepository? repository})
    : _repository = repository ?? FarmRepository();

  final FarmRepository _repository;

  List<FarmModel> _farms = const [];
  bool _isLoading = false;
  bool _hasLoaded = false;
  bool _isCreating = false;
  String? _settingPrimaryFarmId;
  String? _errorMessage;
  DateTime? _lastUpdated;

  List<FarmModel> get farms => List.unmodifiable(_farms);

  bool get isLoading => _isLoading;

  bool get hasLoaded => _hasLoaded;

  bool get isCreating => _isCreating;

  bool get isSettingPrimary => _settingPrimaryFarmId != null;

  String? get settingPrimaryFarmId => _settingPrimaryFarmId;

  bool isSettingPrimaryFor(String farmId) => _settingPrimaryFarmId == farmId;

  bool get hasError =>
      _errorMessage != null && _errorMessage!.trim().isNotEmpty;

  String? get errorMessage => _errorMessage;

  DateTime? get lastUpdated => _lastUpdated;

  bool get isInitialLoading => _isLoading && !_hasLoaded;

  bool get isRefreshing => _isLoading && _hasLoaded;

  bool get isEmpty => _hasLoaded && _farms.isEmpty;

  bool get hasFarms => _farms.isNotEmpty;

  bool get canCreateFarm => _hasLoaded && !_isLoading;

  bool? get nextFarmIsPrimary => _hasLoaded ? _farms.isEmpty : null;

  Future<void> loadFarms({bool forceRefresh = false}) async {
    if (_isLoading) {
      return;
    }

    if (_hasLoaded && !forceRefresh) {
      return;
    }

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final farms = await _repository.getFarms();

      _farms = _sortFarms(farms);
      _hasLoaded = true;
      _lastUpdated = DateTime.now();
      _errorMessage = null;
    } catch (error) {
      _errorMessage = _cleanError(error);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshFarms() async {
    await loadFarms(forceRefresh: true);
  }

  Future<FarmModel> createFarm(FarmCreateInput input) async {
    if (_isCreating) {
      throw Exception('A farm is already being added. Please wait.');
    }

    if (!_hasLoaded) {
      throw Exception('Load your farms before adding a new one.');
    }

    _isCreating = true;
    notifyListeners();

    try {
      final createdFarm = await _repository.createFarm(input);

      final nextFarms = _farms
          .where((farm) => farm.id != createdFarm.id)
          .map(
            (farm) =>
                createdFarm.isPrimary ? farm.copyWith(isPrimary: false) : farm,
          )
          .toList();

      if (createdFarm.isPrimary) {
        nextFarms.insert(0, createdFarm);
      } else {
        nextFarms.add(createdFarm);
      }

      _farms = _sortFarms(nextFarms);
      _lastUpdated = DateTime.now();
      _errorMessage = null;

      return createdFarm;
    } finally {
      _isCreating = false;
      notifyListeners();
    }
  }

  Future<FarmModel> setPrimary(String farmId) async {
    final normalizedFarmId = farmId.trim();

    if (_settingPrimaryFarmId != null) {
      throw Exception(
        'Another farm is already being set as primary. Please wait.',
      );
    }

    if (!_hasLoaded) {
      throw Exception('Load your farms before choosing a primary farm.');
    }

    FarmModel? selectedFarm;

    for (final farm in _farms) {
      if (farm.id == normalizedFarmId) {
        selectedFarm = farm;
        break;
      }
    }

    if (selectedFarm == null) {
      throw Exception('This farm could not be found. Refresh and try again.');
    }

    if (selectedFarm.isPrimary) {
      return selectedFarm;
    }

    _settingPrimaryFarmId = normalizedFarmId;
    notifyListeners();

    try {
      final updatedFarm = await _repository.setPrimary(normalizedFarmId);
      final primaryFarm = updatedFarm.copyWith(isPrimary: true);

      final nextFarms = _farms
          .map(
            (farm) => farm.id == primaryFarm.id
                ? primaryFarm
                : farm.copyWith(isPrimary: false),
          )
          .toList();

      _farms = _sortFarms(nextFarms);
      _lastUpdated = DateTime.now();
      _errorMessage = null;

      return primaryFarm;
    } finally {
      _settingPrimaryFarmId = null;
      notifyListeners();
    }
  }

  List<FarmModel> _sortFarms(List<FarmModel> farms) {
    final primaryFarms = farms.where((farm) => farm.isPrimary).toList();
    final otherFarms = farms.where((farm) => !farm.isPrimary).toList();

    return [...primaryFarms, ...otherFarms];
  }

  String _cleanError(Object error) {
    var message = error.toString().trim();

    while (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length).trim();
    }

    return message.isEmpty
        ? 'Unable to load your farms. Please try again.'
        : message;
  }
}

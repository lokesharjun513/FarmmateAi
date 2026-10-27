import 'package:flutter/foundation.dart';

import '../data/crop_repository.dart';
import '../data/models/crop_recommendation_model.dart';

class CropRecommendationProvider extends ChangeNotifier {
  CropRecommendationProvider({CropRepository? repository})
    : _repository = repository ?? CropRepository();

  final CropRepository _repository;

  int _requestId = 0;
  String? _farmId;
  CropRecommendationModel? _recommendation;
  bool _isLoading = false;
  bool _hasLoaded = false;
  bool _isDisposed = false;
  String? _errorMessage;

  String? get farmId => _farmId;

  CropRecommendationModel? get recommendation => _recommendation;

  List<RecommendedCropModel> get recommendedCrops =>
      List.unmodifiable(_recommendation?.recommendedCrops ?? const []);

  DateTime? get recommendedSowingDate => _recommendation?.recommendedSowingDate;

  bool get isLoading => _isLoading;

  bool get hasLoaded => _hasLoaded;

  bool get hasError =>
      _errorMessage != null && _errorMessage!.trim().isNotEmpty;

  String? get errorMessage => _errorMessage;

  bool get isEmpty => _hasLoaded && recommendedCrops.isEmpty;

  bool get isInitialLoading => _isLoading && !_hasLoaded;

  Future<void> loadRecommendations(
    String farmId, {
    bool forceRefresh = false,
  }) async {
    final normalizedFarmId = farmId.trim();

    if (normalizedFarmId.isEmpty) {
      _requestId += 1;
      _farmId = null;
      _recommendation = null;
      _isLoading = false;
      _hasLoaded = false;
      _errorMessage = 'Select a farm to get crop recommendations.';
      _notifyListeners();
      return;
    }

    if (!forceRefresh &&
        normalizedFarmId == _farmId &&
        (_isLoading || _hasLoaded)) {
      return;
    }

    final requestId = ++_requestId;

    _farmId = normalizedFarmId;
    _recommendation = null;
    _isLoading = true;
    _hasLoaded = false;
    _errorMessage = null;
    _notifyListeners();

    try {
      final recommendation = await _repository.getCropRecommendations(
        normalizedFarmId,
      );

      if (!_isCurrent(requestId, normalizedFarmId)) {
        return;
      }

      _recommendation = recommendation;
      _hasLoaded = true;
      _errorMessage = null;
    } catch (error) {
      if (!_isCurrent(requestId, normalizedFarmId)) {
        return;
      }

      _recommendation = null;
      _hasLoaded = false;
      _errorMessage = _cleanError(error);
    } finally {
      if (_isCurrent(requestId, normalizedFarmId)) {
        _isLoading = false;
        _notifyListeners();
      }
    }
  }

  Future<void> retry() async {
    final farmId = _farmId;

    if (farmId == null || farmId.isEmpty || _isLoading) {
      return;
    }

    await loadRecommendations(farmId, forceRefresh: true);
  }

  void clear() {
    _requestId += 1;
    _farmId = null;
    _recommendation = null;
    _isLoading = false;
    _hasLoaded = false;
    _errorMessage = null;
    _notifyListeners();
  }

  @override
  void dispose() {
    _isDisposed = true;
    _requestId += 1;
    super.dispose();
  }

  bool _isCurrent(int requestId, String farmId) {
    return !_isDisposed && requestId == _requestId && _farmId == farmId;
  }

  void _notifyListeners() {
    if (!_isDisposed) {
      notifyListeners();
    }
  }

  String _cleanError(Object error) {
    var message = error.toString().trim();

    while (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length).trim();
    }

    return message.isEmpty
        ? 'Unable to generate crop recommendations. Please try again.'
        : message;
  }
}

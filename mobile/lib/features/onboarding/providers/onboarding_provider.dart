import 'package:flutter/material.dart';

import '../data/onboarding_repository.dart';

enum OnboardingStatus { initial, loading, completed, required, error }

class OnboardingProvider extends ChangeNotifier {
  final OnboardingRepository _repository;

  OnboardingStatus _status = OnboardingStatus.initial;

  bool _hasProfile = false;
  String? _errorMessage;

  OnboardingProvider({required this._repository});

  // ============================================================
  // GETTERS
  // ============================================================

  OnboardingStatus get status => _status;

  bool get hasProfile => _hasProfile;

  bool get needsOnboarding => !_hasProfile;

  String? get errorMessage => _errorMessage;

  bool get isLoading => _status == OnboardingStatus.loading;

  bool get hasError => _status == OnboardingStatus.error;

  bool get isCompleted => _status == OnboardingStatus.completed;

  // ============================================================
  // CHECK PROFILE
  // ============================================================

  Future<bool> checkProfileExists() async {
    _status = OnboardingStatus.loading;
    _errorMessage = null;

    notifyListeners();

    try {
      _hasProfile = await _repository.checkProfileExists();

      _status = _hasProfile
          ? OnboardingStatus.completed
          : OnboardingStatus.required;

      notifyListeners();

      return _hasProfile;
    } catch (e) {
      _hasProfile = false;

      _errorMessage = e.toString().replaceFirst('Exception: ', '');

      _status = OnboardingStatus.error;

      notifyListeners();

      return false;
    }
  }

  // ============================================================
  // REFRESH PROFILE STATUS
  // ============================================================

  Future<bool> refresh() async {
    return checkProfileExists();
  }

  // ============================================================
  // MARK ONBOARDING COMPLETE
  // ============================================================

  void markOnboardingComplete() {
    _hasProfile = true;
    _errorMessage = null;
    _status = OnboardingStatus.completed;

    notifyListeners();
  }

  // ============================================================
  // RESET
  // ============================================================

  void reset() {
    _hasProfile = false;
    _errorMessage = null;
    _status = OnboardingStatus.initial;

    notifyListeners();
  }

  // ============================================================
  // CLEAR ERROR
  // ============================================================

  void clearError() {
    _errorMessage = null;

    if (_status == OnboardingStatus.error) {
      _status = _hasProfile
          ? OnboardingStatus.completed
          : OnboardingStatus.required;
    }

    notifyListeners();
  }
}

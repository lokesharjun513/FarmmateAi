import 'package:flutter/material.dart';

import '../farmer_repository.dart';
import '../../data/models/farmer_profile_model.dart';

class FarmerProvider extends ChangeNotifier {
  final FarmerRepository _farmerRepository;

  FarmerProfileModel? _profile;

  bool _isLoading = false;
  bool _isSaving = false;

  String? _errorMessage;

  FarmerProvider({FarmerRepository? farmerRepository})
    : _farmerRepository = farmerRepository ?? FarmerRepository();

  FarmerProfileModel? get profile => _profile;

  bool get isLoading => _isLoading;

  bool get isSaving => _isSaving;

  String? get errorMessage => _errorMessage;

  // ------------------------------------------------------------
  // GET PROFILE
  // ------------------------------------------------------------

  Future<bool> loadProfile() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final profile = await _farmerRepository.getProfile();

      _profile = profile;
      _isLoading = false;

      notifyListeners();

      return profile != null;
    } catch (e) {
      _errorMessage = e.toString().replaceFirst('Exception: ', '');

      _isLoading = false;

      notifyListeners();

      return false;
    }
  }

  // ------------------------------------------------------------
  // UPDATE PROFILE
  // ------------------------------------------------------------

  Future<bool> updateProfile({
    required String preferredLanguage,
    required int experienceYears,
  }) async {
    _isSaving = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final updatedProfile = await _farmerRepository.updateProfile(
        preferredLanguage: preferredLanguage,
        experienceYears: experienceYears,
      );

      _profile = updatedProfile;

      _isSaving = false;

      notifyListeners();

      return true;
    } catch (e) {
      _errorMessage = e.toString().replaceFirst('Exception: ', '');

      _isSaving = false;

      notifyListeners();

      return false;
    }
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  void clearProfile() {
    _profile = null;
    _errorMessage = null;
    _isLoading = false;
    _isSaving = false;

    notifyListeners();
  }
}

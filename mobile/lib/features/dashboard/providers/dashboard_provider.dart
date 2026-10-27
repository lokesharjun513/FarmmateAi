// lib/features/dashboard/providers/dashboard_provider.dart

import 'package:flutter/foundation.dart';

import '../data/models/dashboard_model.dart';
import '../data/repositories/dashboard_repository.dart';

class DashboardProvider extends ChangeNotifier {
  final DashboardRepository _repository;

  DashboardProvider({DashboardRepository? repository})
    : _repository = repository ?? DashboardRepository();

  // ============================================================
  // STATE
  // ============================================================

  DashboardModel? _dashboard;

  bool _isLoading = false;
  bool _hasLoaded = false;

  String? _errorMessage;

  DateTime? _lastUpdated;

  // ============================================================
  // GETTERS
  // ============================================================

  DashboardModel? get dashboard => _dashboard;

  bool get isLoading => _isLoading;

  bool get hasLoaded => _hasLoaded;

  bool get hasDashboard => _dashboard != null;

  bool get hasError =>
      _errorMessage != null && _errorMessage!.trim().isNotEmpty;

  String? get errorMessage => _errorMessage;

  DateTime? get lastUpdated => _lastUpdated;

  bool get isRefreshing => _isLoading && _dashboard != null;

  bool get isInitialLoading => _isLoading && _dashboard == null;

  // ============================================================
  // LOAD DASHBOARD
  // ============================================================

  Future<void> loadDashboard({bool forceRefresh = false}) async {
    // ----------------------------------------------------------
    // Prevent duplicate requests
    // ----------------------------------------------------------

    if (_isLoading) {
      return;
    }

    // ----------------------------------------------------------
    // Do not request again if dashboard is already loaded
    // unless explicitly requested.
    // ----------------------------------------------------------

    if (_hasLoaded && !forceRefresh) {
      return;
    }

    _isLoading = true;

    // Clear the previous error when starting a new request.
    _errorMessage = null;

    notifyListeners();

    try {
      final result = await _repository.getDashboard();

      // --------------------------------------------------------
      // SUCCESS
      // --------------------------------------------------------

      _dashboard = result;

      _hasLoaded = true;

      _lastUpdated = DateTime.now();

      _errorMessage = null;
    } catch (error) {
      // --------------------------------------------------------
      // FAILURE
      // --------------------------------------------------------

      _errorMessage = _cleanError(error);

      // --------------------------------------------------------
      // IMPORTANT:
      //
      // Do NOT clear the existing dashboard when refresh fails.
      //
      // This means:
      //
      // Existing dashboard
      //        +
      // Refresh fails
      //        ↓
      // Existing dashboard remains visible
      //        +
      // Error available to UI
      //
      // This is much better UX for mobile.
      // --------------------------------------------------------
    } finally {
      _isLoading = false;

      notifyListeners();
    }
  }

  // ============================================================
  // INITIAL LOAD
  // ============================================================

  Future<void> initialize() async {
    await loadDashboard(forceRefresh: false);
  }

  // ============================================================
  // REFRESH
  // ============================================================

  Future<void> refreshDashboard() async {
    await loadDashboard(forceRefresh: true);
  }

  // ============================================================
  // RELOAD
  // ============================================================
  //
  // Convenience method for UI/navigation code.
  //
  // Example:
  //
  // provider.reload();
  //
  // ============================================================

  Future<void> reload() async {
    await refreshDashboard();
  }

  // ============================================================
  // RETRY
  // ============================================================

  Future<void> retry() async {
    await refreshDashboard();
  }

  // ============================================================
  // CLEAR DASHBOARD
  // ============================================================
  //
  // Useful during:
  //
  // - Logout
  // - Account switching
  // - Farmer switching
  // - Authentication reset
  //
  // ============================================================

  void clear() {
    _dashboard = null;

    _hasLoaded = false;

    _errorMessage = null;

    _lastUpdated = null;

    _isLoading = false;

    notifyListeners();
  }

  // ============================================================
  // CLEAR ERROR
  // ============================================================

  void clearError() {
    if (_errorMessage == null) {
      return;
    }

    _errorMessage = null;

    notifyListeners();
  }

  // ============================================================
  // RESET
  // ============================================================
  //
  // Completely resets provider state.
  //
  // ============================================================

  void reset() {
    _dashboard = null;

    _isLoading = false;

    _hasLoaded = false;

    _errorMessage = null;

    _lastUpdated = null;

    notifyListeners();
  }

  // ============================================================
  // ERROR CLEANUP
  // ============================================================

  String _cleanError(Object error) {
    var message = error.toString().trim();

    // ----------------------------------------------------------
    // Remove Dart Exception prefix
    // ----------------------------------------------------------

    if (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length);
    }

    // ----------------------------------------------------------
    // Remove repeated Exception prefixes
    // ----------------------------------------------------------

    while (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length);
    }

    // ----------------------------------------------------------
    // Fallback
    // ----------------------------------------------------------

    if (message.isEmpty) {
      return 'Unable to load dashboard.';
    }

    return message;
  }
}

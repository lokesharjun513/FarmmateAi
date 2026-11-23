import 'package:flutter/material.dart';

import '../../../core/storage/token_storage.dart';
import '../../onboarding/providers/onboarding_provider.dart';
import '../data/auth_repository.dart';
import '../data/models/user_model.dart';

// ============================================================
// PASSWORD RESET STATUS
// ============================================================

enum PasswordResetStatus {
  initial,
  sendingOtp,
  verified,
  resendingOtp,
  resetSuccessful,
}

// ============================================================
// AUTH PROVIDER
// ============================================================

enum AuthStatus { initial, loading, unauthenticated, authenticated }

// ============================================================
// AUTH PROVIDER
// ============================================================

class AuthProvider extends ChangeNotifier {
  final AuthRepository _authRepository;
  final TokenStorage _tokenStorage;
  final OnboardingProvider _onboardingProvider;
  final Future<void> Function()? onBeforeLogout;

  AuthStatus _status = AuthStatus.initial;

  UserModel? _user;

  String? _errorMessage;

  bool _hasFarmerProfile = false;

  // In-memory cooldown tracking for OTP resend (per email address)
  final Map<String, DateTime> _resendCooldownUntil = {};

  // ============================================================
  // CONSTRUCTOR
  // ============================================================

  AuthProvider({
    AuthRepository? authRepository,
    TokenStorage? tokenStorage,
    required OnboardingProvider onboardingProvider,
    this.onBeforeLogout,
  }) : _authRepository = authRepository ?? AuthRepository(),
       _tokenStorage = tokenStorage ?? TokenStorage(),
       // ignore: prefer_initializing_formals
       _onboardingProvider = onboardingProvider;

  // ============================================================
  // GETTERS
  // ============================================================

  AuthStatus get status => _status;

  UserModel? get user => _user;

  String? get errorMessage => _errorMessage;

  bool get isAuthenticated => _status == AuthStatus.authenticated;

  bool get isUnauthenticated => _status == AuthStatus.unauthenticated;

  bool get isLoading => _status == AuthStatus.loading;

  bool get isInitial => _status == AuthStatus.initial;

  bool get hasUser => _user != null;

  bool get hasFarmerProfile => _hasFarmerProfile;

  bool get needsFarmerOnboarding => isAuthenticated && !_hasFarmerProfile;

  // ============================================================
  // CHECK AUTH STATUS
  // ============================================================

  Future<void> checkAuthStatus() async {
    _setLoading();

    try {
      // --------------------------------------------------------
      // 1. Check stored JWT
      // --------------------------------------------------------

      final token = await _tokenStorage.getToken();

      if (token == null || token.trim().isEmpty) {
        _clearInMemoryState();

        _status = AuthStatus.unauthenticated;

        notifyListeners();

        return;
      }

      // --------------------------------------------------------
      // 2. Validate JWT using /auth/me
      // --------------------------------------------------------

      final userModel = await _authRepository.getMe();

      _user = userModel;

      // --------------------------------------------------------
      // 3. Check farmer profile
      // --------------------------------------------------------
      //
      // Authentication and farmer onboarding are separate.
      //
      // Valid JWT + valid user:
      //
      //     authenticated = true
      //
      // Profile exists:
      //
      //     hasFarmerProfile = true
      //
      // Profile doesn't exist:
      //
      //     hasFarmerProfile = false
      //
      // --------------------------------------------------------

      _hasFarmerProfile = await _checkFarmerProfileSafely();

      // --------------------------------------------------------
      // 4. Authentication successful
      // --------------------------------------------------------

      _errorMessage = null;

      _status = AuthStatus.authenticated;

      notifyListeners();
    } catch (e) {
      // --------------------------------------------------------
      // JWT invalid / expired / /auth/me failed
      // --------------------------------------------------------

      await _runBeforeLogoutSafely();

      await _clearStoredTokenSafely();

      _clearInMemoryState();

      _errorMessage = _extractErrorMessage(e);

      _status = AuthStatus.unauthenticated;

      notifyListeners();
    }
  }

  // ============================================================
  // FORGOT PASSWORD
  // ============================================================

  Future<Map<String, dynamic>> forgotPassword({
    required String email,
  }) async {
    _setLoading();

    try {
      final cleanEmail = email.trim();

      final authResponse =
          await _authRepository.forgotPassword(email: cleanEmail);

      if (authResponse['success'] == true) {
        _startResendCooldown(cleanEmail);
        return authResponse;
      } else {
        return authResponse;
      }
    } catch (e) {
      return {'status': 'error', 'detail': 'Something went wrong. Please try again.'};
    } finally {
      _clearInMemoryState();
    }
  }

  // ============================================================
  // VERIFY RESET OTP
  // ============================================================

  Future<Map<String, dynamic>> verifyResetOtp({
    required String email,
    required String otp,
  }) async {
    _setLoading();

    try {
      return await _authRepository.verifyResetOtp(
        email: email.trim().toLowerCase(),
        otp: otp,
      );
    } catch (e) {
      return {'status': 'error', 'detail': 'Something went wrong. Please try again.'};
    } finally {
      _clearInMemoryState();
    }
  }

  // ============================================================
  // RESET PASSWORD
  // ============================================================

  Future<Map<String, dynamic>> resetPassword({
    required String resetToken,
    required String newPassword,
  }) async {
    _setLoading();

    try {
      if (newPassword.trim().length < 8) {
        _setUnauthenticated(
          errorMessage: 'Password must be at least 8 characters.',
        );
        return {'status': 'error', 'detail': 'Password must be at least 8 characters.'};
      }

      return await _authRepository.resetPassword(
        resetToken: resetToken,
        newPassword: newPassword,
      );
    } catch (e) {
      return {'status': 'error', 'detail': 'Something went wrong. Please try again.'};
    } finally {
      _clearInMemoryState();
    }
  }

  // ============================================================
  // RESEND RESET OTP
  // ============================================================

  Future<Map<String, dynamic>> resendResetOtp({
    required String email,
  }) async {
    _setLoading();

    try {
      return await _authRepository.resendResetOtp(
        email: email.trim().toLowerCase(),
      );
    } catch (e) {
      return {'status': 'error', 'detail': 'Something went wrong. Please try again.'};
    } finally {
      _clearInMemoryState();
    }
  }

  // ============================================================
  // CAN RESEND RESET OTP
  // ============================================================

  /// Returns true if no cooldown is active (or cooldown has expired) for
  /// the given email.  A 60-second cooldown starts after each OTP send.
  bool canResendResetOtp(String email) {
    final cooldown = _resendCooldownUntil[email.trim().toLowerCase()];
    if (cooldown == null) {
      return true;
    }
    return DateTime.now().isAfter(cooldown);
  }

  // ============================================================
  // RESEND COOLDOWN TEXT
  // ============================================================

  /// Human-readable remaining cooldown time for the given email.
  String resendCooldownText(String email) {
    final cooldown = _resendCooldownUntil[email.trim().toLowerCase()];
    if (cooldown == null) {
      return '';
    }
    final remaining = cooldown.difference(DateTime.now()).inSeconds;
    if (remaining <= 0) {
      return '';
    }
    return '$remaining second${remaining == 1 ? '' : 's'}';
  }

  void _startResendCooldown(String email) {
    _resendCooldownUntil[email.trim().toLowerCase()] =
        DateTime.now().add(const Duration(seconds: 60));
  }

// ============================================================
// LOGIN
// ============================================================

Future<bool> login({
    required String identifier,
    required String password,
  }) async {
    _setLoading();

    try {
      // --------------------------------------------------------
      // 1. Clean input
      // --------------------------------------------------------

      final cleanIdentifier = identifier.trim();

      if (cleanIdentifier.isEmpty) {
        _setUnauthenticated(
          errorMessage: 'Please enter your mobile number or email.',
        );

        return false;
      }

      if (password.trim().isEmpty) {
        _setUnauthenticated(errorMessage: 'Please enter your password.');

        return false;
      }

      // --------------------------------------------------------
      // 2. Login
      // --------------------------------------------------------

      final loginData = await _authRepository.login(
        identifier: cleanIdentifier,
        password: password,
      );

      // --------------------------------------------------------
      // 3. Save access token
      // --------------------------------------------------------

      final accessToken = loginData.accessToken.trim();

      if (accessToken.isEmpty) {
        throw Exception('Login succeeded but no access token was received.');
      }

      await _tokenStorage.saveToken(accessToken);

      // --------------------------------------------------------
      // 4. Get authenticated user
      // --------------------------------------------------------

      final userModel = await _authRepository.getMe();

      _user = userModel;

      // --------------------------------------------------------
      // 5. Check farmer profile
      // --------------------------------------------------------

      _hasFarmerProfile = await _checkFarmerProfileSafely();

      // --------------------------------------------------------
      // 6. Authentication complete
      // --------------------------------------------------------

      _errorMessage = null;

      _status = AuthStatus.authenticated;

      notifyListeners();

      return true;
    } catch (e) {
      // --------------------------------------------------------
      // Login failed.
      //
      // If token was already saved, remove it.
      // --------------------------------------------------------

      await _clearStoredTokenSafely();

      _clearInMemoryState();

      _errorMessage = _extractErrorMessage(e);

      _status = AuthStatus.unauthenticated;

      notifyListeners();

      return false;
    }
  }

  // ============================================================
  // REGISTER
  // ============================================================

  Future<bool> register({
    required String fullName,
    required String mobile,
    required String email,
    required String password,
  }) async {
    _setLoading();

    try {
      // --------------------------------------------------------
      // Clean input
      // --------------------------------------------------------

      final cleanFullName = fullName.trim();

      final cleanMobile = mobile.trim();

      final cleanEmail = email.trim();

      if (cleanFullName.isEmpty) {
        _setUnauthenticated(errorMessage: 'Please enter your full name.');

        return false;
      }

      if (cleanMobile.isEmpty) {
        _setUnauthenticated(errorMessage: 'Please enter your mobile number.');

        return false;
      }

      if (cleanEmail.isEmpty) {
        _setUnauthenticated(errorMessage: 'Please enter your email address.');

        return false;
      }

      if (password.trim().isEmpty) {
        _setUnauthenticated(errorMessage: 'Please enter a password.');

        return false;
      }

      // --------------------------------------------------------
      // Register user
      // --------------------------------------------------------

      await _authRepository.register(
        fullName: cleanFullName,
        mobile: cleanMobile,
        email: cleanEmail,
        password: password,
      );

      // --------------------------------------------------------
      // Registration does not automatically authenticate.
      // --------------------------------------------------------

      _clearInMemoryState();

      _errorMessage = null;

      _status = AuthStatus.unauthenticated;

      notifyListeners();

      return true;
    } catch (e) {
      _setUnauthenticated(errorMessage: _extractErrorMessage(e));

      return false;
    }
  }

  // ============================================================
  // REFRESH FARMER PROFILE
  // ============================================================

  Future<bool> refreshFarmerProfile() async {
    if (!isAuthenticated) {
      return false;
    }

    _errorMessage = null;

    try {
      final exists = await _onboardingProvider.checkProfileExists();

      _hasFarmerProfile = exists;

      notifyListeners();

      return exists;
    } catch (e) {
      _errorMessage = _extractErrorMessage(e);

      notifyListeners();

      return false;
    }
  }

  // ============================================================
  // MARK FARMER PROFILE CREATED
  // ============================================================
  //
  // Call this after successful farmer-profile creation.
  //
  // This avoids making another API request immediately after
  // onboarding succeeds.
  // ============================================================

  void markFarmerProfileCreated() {
    _hasFarmerProfile = true;

    _errorMessage = null;

    notifyListeners();
  }

  // ============================================================
  // LOGOUT
  // ============================================================

  Future<void> logout() async {
    _status = AuthStatus.loading;

    _errorMessage = null;

    notifyListeners();

    await _runBeforeLogoutSafely();

    await _clearStoredTokenSafely();

    _clearInMemoryState();

    _onboardingProvider.reset();

    _status = AuthStatus.unauthenticated;

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
  // FARMER PROFILE CHECK
  // ============================================================

  Future<bool> _checkFarmerProfileSafely() async {
    try {
      return await _onboardingProvider.checkProfileExists();
    } catch (_) {
      // --------------------------------------------------------
      // IMPORTANT:
      //
      // A farmer-profile failure must NOT log the user out.
      //
      // Authentication and onboarding are independent states.
      // --------------------------------------------------------

      return false;
    }
  }

  // ============================================================
  // SET LOADING
  // ============================================================

  void _setLoading() {
    _status = AuthStatus.loading;

    _errorMessage = null;

    notifyListeners();
  }

  // ============================================================
  // SET UNAUTHENTICATED
  // ============================================================

  void _setUnauthenticated({String? errorMessage}) {
    _status = AuthStatus.unauthenticated;

    _errorMessage = errorMessage;

    notifyListeners();
  }

  // ============================================================
  // CLEAR IN-MEMORY STATE
  // ============================================================

  void _clearInMemoryState() {
    _user = null;
    _hasFarmerProfile = false;
    _status = AuthStatus.unauthenticated;
  }

  // ============================================================
  // BEFORE LOGOUT
  // ============================================================

  Future<void> _runBeforeLogoutSafely() async {
    final callback = onBeforeLogout;

    if (callback == null) {
      return;
    }

    try {
      await callback().timeout(const Duration(seconds: 4));
    } catch (_) {
      // Device-registration cleanup must never block sign-out.
    }
  }

  // ============================================================
  // CLEAR STORED TOKEN
  // ============================================================

  Future<void> _clearStoredTokenSafely() async {
    try {
      await _tokenStorage.deleteToken();
    } catch (_) {
      // Ignore local storage errors.
      //
      // Authentication state is still cleared in memory.
    }
  }

  // ============================================================
  // EXTRACT ERROR MESSAGE
  // ============================================================

  String _extractErrorMessage(Object error) {
    var message = error.toString().trim();

    if (message.isEmpty) {
      return 'Something went wrong. Please try again.';
    }

    const prefixes = ['Exception: ', 'Error: '];

    for (final prefix in prefixes) {
      if (message.startsWith(prefix)) {
        message = message.substring(prefix.length).trim();
        break;
      }
    }

    if (message.isEmpty) {
      return 'Something went wrong. Please try again.';
    }

    return message;
  }
}

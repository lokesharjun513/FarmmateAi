import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';

import '../data/device_token_repository.dart';
import 'push_message.dart';
import 'push_messaging_client.dart';

typedef FirebaseInitializer = Future<void> Function();

class PushNotificationService {
  PushNotificationService({
    required this.deviceRepository,
    PushMessagingClient? messaging,
    FirebaseInitializer? initializeFirebase,
  }) : _messaging = messaging ?? FirebasePushMessagingClient(),
       _initializeFirebase =
           initializeFirebase ?? _initializeDefaultFirebaseApp;

  final DeviceTokenRepository deviceRepository;
  final PushMessagingClient _messaging;
  final FirebaseInitializer _initializeFirebase;

  final _foregroundMessages = StreamController<PushMessage>.broadcast();
  final _openedMessages = StreamController<PushMessage>.broadcast();

  StreamSubscription<String>? _registrationSubscription;
  StreamSubscription<PushMessage>? _foregroundSubscription;
  StreamSubscription<PushMessage>? _openedSubscription;

  Listenable? _authListenable;
  bool Function()? _isAuthenticated;
  bool _lastAuthenticated = false;

  bool _initializationAttempted = false;
  bool _available = false;
  bool _listenersAttached = false;
  bool _initialMessageChecked = false;
  bool _registering = false;
  bool _permissionGranted = false;

  String? _currentFid;
  String? _registeredFid;

  Stream<PushMessage> get foregroundMessages => _foregroundMessages.stream;

  Stream<PushMessage> get openedMessages => _openedMessages.stream;

  bool get isAvailable => _available;

  static Future<void> _initializeDefaultFirebaseApp() async {
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp();
    }
  }

  Future<bool> initialize() async {
    if (_initializationAttempted) {
      return _available;
    }

    _initializationAttempted = true;

    try {
      await _initializeFirebase();
      _available = true;
    } catch (error) {
      _available = false;
      debugPrint('Firebase initialization failed: $error');
      return false;
    }

    try {
      await _messaging.configureForegroundPresentation();
    } catch (error) {
      debugPrint('Unable to configure foreground notification display: $error');
    }

    _attachListeners();

    return true;
  }

  void bind({
    required Listenable authListenable,
    required bool Function() isAuthenticated,
  }) {
    _isAuthenticated = isAuthenticated;

    if (identical(_authListenable, authListenable)) {
      return;
    }

    _authListenable?.removeListener(_handleAuthChanged);
    _authListenable = authListenable;
    authListenable.addListener(_handleAuthChanged);
    _lastAuthenticated = isAuthenticated();
  }

  Future<void> syncAuthState() async {
    final authenticated = _isAuthenticated?.call() ?? false;
    _lastAuthenticated = authenticated;

    if (authenticated) {
      await registerCurrentDevice(force: true);
    }
  }

  Future<void> registerCurrentDevice({bool force = false}) async {
    if (!_available) {
      return;
    }

    if (!(_isAuthenticated?.call() ?? false) || _registering) {
      return;
    }

    _registering = true;

    try {
      final permissionGranted = await _messaging.requestPermission();
      _permissionGranted = permissionGranted;

      if (!permissionGranted) {
        return;
      }

      final fid = (await _messaging.registerForFid())?.trim();

      if (fid == null || fid.isEmpty) {
        return;
      }

      _currentFid = fid;

      if (!force && fid == _registeredFid) {
        return;
      }

      await deviceRepository.registerDevice(
        fid: fid,
        deviceName: _deviceName(),
      );

      _registeredFid = fid;
    } catch (error) {
      debugPrint('FCM registration failed: $error');
    } finally {
      _registering = false;
    }
  }

  Future<void> unregisterCurrentDevice() async {
    final fid = _currentFid;

    _currentFid = null;
    _registeredFid = null;

    if (fid != null && fid.isNotEmpty) {
      try {
        await deviceRepository.deactivateDevice(fid);
      } catch (error) {
        debugPrint('FCM device deactivation failed: $error');
      }
    }

    try {
      await _messaging.unregister();
    } catch (error) {
      debugPrint('FCM local unregistration failed: $error');
    }
  }

  Future<void> handleInitialMessage() async {
    if (!_available || _initialMessageChecked) {
      return;
    }

    _initialMessageChecked = true;

    try {
      final message = await _messaging.getInitialMessage();

      if (message != null) {
        _openedMessages.add(message);
      }
    } catch (error) {
      debugPrint('Unable to read the initial FCM message: $error');
    }
  }

  void _attachListeners() {
    if (_listenersAttached) {
      return;
    }

    _listenersAttached = true;

    _registrationSubscription = _messaging.onRegistered.listen(
      _handleRegistration,
    );
    _foregroundSubscription = _messaging.onMessage.listen((message) {
      _foregroundMessages.add(message);
    });
    _openedSubscription = _messaging.onMessageOpenedApp.listen((message) {
      _openedMessages.add(message);
    });
  }

  void _handleAuthChanged() {
    final authenticated = _isAuthenticated?.call() ?? false;

    if (authenticated) {
      if (!_lastAuthenticated) {
        _lastAuthenticated = true;
        unawaited(registerCurrentDevice(force: true));
      }

      return;
    }

    _lastAuthenticated = false;
    _registeredFid = null;
  }

  void _handleRegistration(String fid) {
    final cleanFid = fid.trim();

    if (cleanFid.isEmpty) {
      return;
    }

    _currentFid = cleanFid;

    if (!(_isAuthenticated?.call() ?? false) || !_permissionGranted) {
      return;
    }

    unawaited(_registerRegistration(cleanFid));
  }

  Future<void> _registerRegistration(String fid) async {
    if (_registering || fid == _registeredFid) {
      return;
    }

    _registering = true;

    try {
      await deviceRepository.registerDevice(
        fid: fid,
        deviceName: _deviceName(),
      );

      _registeredFid = fid;
    } catch (error) {
      debugPrint('FCM registration refresh failed: $error');
    } finally {
      _registering = false;
    }
  }

  String? _deviceName() {
    if (kIsWeb) {
      return 'FarmMate Web';
    }

    return switch (defaultTargetPlatform) {
      TargetPlatform.android => 'Android',
      TargetPlatform.iOS => 'iOS',
      TargetPlatform.macOS => 'macOS',
      TargetPlatform.windows => 'Windows',
      TargetPlatform.linux => 'Linux',
      TargetPlatform.fuchsia => 'Fuchsia',
    };
  }

  void dispose() {
    _authListenable?.removeListener(_handleAuthChanged);
    _registrationSubscription?.cancel();
    _foregroundSubscription?.cancel();
    _openedSubscription?.cancel();
    _foregroundMessages.close();
    _openedMessages.close();
  }
}

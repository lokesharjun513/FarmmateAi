import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/features/notifications/data/device_token_repository.dart';
import 'package:mobile/features/notifications/services/notification_navigation.dart';
import 'package:mobile/features/notifications/services/push_message.dart';
import 'package:mobile/features/notifications/services/push_messaging_client.dart';
import 'package:mobile/features/notifications/services/push_notification_service.dart';

class FakeDeviceRepository extends DeviceTokenRepository {
  FakeDeviceRepository() : super(apiClient: ApiClient());

  final registrations = <String>[];
  final deactivations = <String>[];
  bool failDeactivation = false;

  @override
  Future<void> registerDevice({required String fid, String? deviceName}) async {
    registrations.add(fid);
  }

  @override
  Future<void> deactivateDevice(String fid) async {
    deactivations.add(fid);

    if (failDeactivation) {
      throw Exception('Backend unavailable.');
    }
  }
}

class FakeMessagingClient implements PushMessagingClient {
  bool permissionGranted = true;
  String? fid = 'fid-1';
  PushMessage? initialMessage;

  int permissionRequests = 0;
  int unregisterCalls = 0;
  int foregroundConfigurationCalls = 0;

  final _registered = StreamController<String>.broadcast();
  final _messages = StreamController<PushMessage>.broadcast();
  final _opened = StreamController<PushMessage>.broadcast();

  @override
  Future<bool> requestPermission() async {
    permissionRequests += 1;
    return permissionGranted;
  }

  @override
  Future<String?> registerForFid() async {
    if (fid != null) {
      _registered.add(fid!);
    }

    return fid;
  }

  @override
  Future<void> unregister() async {
    unregisterCalls += 1;
  }

  @override
  Stream<String> get onRegistered => _registered.stream;

  @override
  Stream<PushMessage> get onMessage => _messages.stream;

  @override
  Stream<PushMessage> get onMessageOpenedApp => _opened.stream;

  @override
  Future<PushMessage?> getInitialMessage() async => initialMessage;

  @override
  Future<void> configureForegroundPresentation() async {
    foregroundConfigurationCalls += 1;
  }

  void emitForeground(PushMessage message) {
    _messages.add(message);
  }

  void emitOpened(PushMessage message) {
    _opened.add(message);
  }

  void emitRegistered(String value) {
    _registered.add(value);
  }

  Future<void> close() async {
    await _registered.close();
    await _messages.close();
    await _opened.close();
  }
}

class FakeAuthState extends ChangeNotifier {
  FakeAuthState(this.authenticated);

  bool authenticated;

  void setAuthenticated(bool value) {
    authenticated = value;
    notifyListeners();
  }
}

Future<PushNotificationService> buildService({
  FakeDeviceRepository? repository,
  FakeMessagingClient? messaging,
  bool initializeSucceeds = true,
}) async {
  final service = PushNotificationService(
    deviceRepository: repository ?? FakeDeviceRepository(),
    messaging: messaging ?? FakeMessagingClient(),
    initializeFirebase: () async {
      if (!initializeSucceeds) {
        throw Exception('Firebase unavailable.');
      }
    },
  );

  await service.initialize();

  return service;
}

void main() {
  test('Firebase initialization failure is non-fatal', () async {
    final repository = FakeDeviceRepository();
    final messaging = FakeMessagingClient();
    final service = await buildService(
      repository: repository,
      messaging: messaging,
      initializeSucceeds: false,
    );

    expect(service.isAvailable, isFalse);

    final auth = FakeAuthState(true);
    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();

    expect(repository.registrations, isEmpty);
    expect(messaging.permissionRequests, 0);

    service.dispose();
  });

  test('denied permission does not register a device', () async {
    final repository = FakeDeviceRepository();
    final messaging = FakeMessagingClient()..permissionGranted = false;
    final service = await buildService(
      repository: repository,
      messaging: messaging,
    );
    final auth = FakeAuthState(true);

    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();

    expect(messaging.permissionRequests, 1);
    expect(repository.registrations, isEmpty);

    service.dispose();
  });

  test('authenticated device registration is deduplicated', () async {
    final repository = FakeDeviceRepository();
    final messaging = FakeMessagingClient();
    final service = await buildService(
      repository: repository,
      messaging: messaging,
    );
    final auth = FakeAuthState(true);

    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();
    await service.registerCurrentDevice();

    expect(repository.registrations, ['fid-1']);

    service.dispose();
  });

  test('forced registration supports account switching', () async {
    final repository = FakeDeviceRepository();
    final service = await buildService(repository: repository);
    final auth = FakeAuthState(true);

    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();
    await service.registerCurrentDevice(force: true);

    expect(repository.registrations, ['fid-1', 'fid-1']);

    service.dispose();
  });

  test('auth transition registers after login', () async {
    final repository = FakeDeviceRepository();
    final service = await buildService(repository: repository);
    final auth = FakeAuthState(false);

    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();

    expect(repository.registrations, isEmpty);

    auth.setAuthenticated(true);
    await Future<void>.delayed(const Duration(milliseconds: 10));

    expect(repository.registrations, ['fid-1']);

    service.dispose();
  });

  test('FID refresh registers the new registration', () async {
    final repository = FakeDeviceRepository();
    final messaging = FakeMessagingClient();
    final service = await buildService(
      repository: repository,
      messaging: messaging,
    );
    final auth = FakeAuthState(true);

    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();

    messaging.fid = 'fid-2';
    messaging.emitRegistered('fid-2');
    await Future<void>.delayed(const Duration(milliseconds: 10));

    expect(repository.registrations, ['fid-1', 'fid-2']);

    service.dispose();
  });

  test('logout deactivates the device even when the backend fails', () async {
    final repository = FakeDeviceRepository()..failDeactivation = true;
    final messaging = FakeMessagingClient();
    final service = await buildService(
      repository: repository,
      messaging: messaging,
    );
    final auth = FakeAuthState(true);

    service.bind(
      authListenable: auth,
      isAuthenticated: () => auth.authenticated,
    );
    await service.syncAuthState();
    await service.unregisterCurrentDevice();

    expect(repository.deactivations, ['fid-1']);
    expect(messaging.unregisterCalls, 1);

    service.dispose();
  });

  test('foreground and opened messages are exposed once', () async {
    final messaging = FakeMessagingClient();
    final service = await buildService(messaging: messaging);
    final received = <PushMessage>[];
    final opened = <PushMessage>[];

    final foregroundSubscription = service.foregroundMessages.listen(
      received.add,
    );
    final openedSubscription = service.openedMessages.listen(opened.add);

    final message = const PushMessage(
      title: 'Weather alert',
      body: 'Rain expected.',
    );

    messaging.emitForeground(message);
    messaging.emitOpened(message);
    await Future<void>.delayed(Duration.zero);

    expect(received, [message]);
    expect(opened, [message]);

    await foregroundSubscription.cancel();
    await openedSubscription.cancel();
    service.dispose();
    await messaging.close();
  });

  test('initial notification tap is emitted', () async {
    final messaging = FakeMessagingClient()
      ..initialMessage = const PushMessage(title: 'Alert', body: 'Open me');
    final service = await buildService(messaging: messaging);
    final opened = <PushMessage>[];

    final subscription = service.openedMessages.listen(opened.add);

    await service.handleInitialMessage();
    await Future<void>.delayed(Duration.zero);

    expect(opened.single.title, 'Alert');

    await subscription.cancel();
    service.dispose();
    await messaging.close();
  });

  test(
    'notification navigation rejects unknown and unauthenticated routes',
    () {
      const unknown = PushMessage(
        title: 'Alert',
        body: 'Body',
        data: {'route': '/admin'},
      );
      const ask = PushMessage(
        title: 'Advisor',
        body: 'Body',
        data: {'route': '/ask-fm'},
      );

      expect(
        NotificationNavigation.resolveRoute(unknown, isAuthenticated: true),
        '/dashboard',
      );
      expect(
        NotificationNavigation.resolveRoute(ask, isAuthenticated: false),
        isNull,
      );
      expect(
        NotificationNavigation.resolveRoute(ask, isAuthenticated: true),
        '/ask-fm',
      );
    },
  );
}

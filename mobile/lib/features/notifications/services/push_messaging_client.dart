import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'push_message.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp();
    }
  } catch (_) {
    // A background delivery must never crash the application isolate.
  }
}

abstract interface class PushMessagingClient {
  Future<bool> requestPermission();

  Future<String?> registerForFid();

  Future<void> unregister();

  Stream<String> get onRegistered;

  Stream<PushMessage> get onMessage;

  Stream<PushMessage> get onMessageOpenedApp;

  Future<PushMessage?> getInitialMessage();

  Future<void> configureForegroundPresentation();
}

class FirebasePushMessagingClient implements PushMessagingClient {
  FirebasePushMessagingClient({FirebaseMessaging? messaging})
    : _messaging = messaging ?? FirebaseMessaging.instance;

  final FirebaseMessaging _messaging;

  @override
  Future<bool> requestPermission() async {
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    return settings.authorizationStatus == AuthorizationStatus.authorized ||
        settings.authorizationStatus == AuthorizationStatus.provisional;
  }

  @override
  Future<String?> registerForFid() async {
    final fid = Completer<String?>();
    final subscription = _messaging.onRegistered.listen((value) {
      if (!fid.isCompleted) {
        fid.complete(value);
      }
    });

    try {
      await _messaging.register();
      return await fid.future.timeout(
        const Duration(seconds: 10),
        onTimeout: () => null,
      );
    } catch (_) {
      return null;
    } finally {
      await subscription.cancel();
    }
  }

  @override
  Future<void> unregister() {
    return _messaging.unregister();
  }

  @override
  Stream<String> get onRegistered => _messaging.onRegistered;

  @override
  Stream<PushMessage> get onMessage {
    return FirebaseMessaging.onMessage.map(_mapMessage);
  }

  @override
  Stream<PushMessage> get onMessageOpenedApp {
    return FirebaseMessaging.onMessageOpenedApp.map(_mapMessage);
  }

  @override
  Future<PushMessage?> getInitialMessage() async {
    final message = await _messaging.getInitialMessage();

    return message == null ? null : _mapMessage(message);
  }

  @override
  Future<void> configureForegroundPresentation() {
    return _messaging.setForegroundNotificationPresentationOptions(
      alert: false,
      badge: false,
      sound: false,
    );
  }

  PushMessage _mapMessage(RemoteMessage message) {
    final notification = message.notification;

    return PushMessage(
      title: notification?.title ?? message.data['title'] ?? 'FarmMate AI',
      body:
          notification?.body ??
          message.data['body'] ??
          message.data['message'] ??
          '',
      data: Map<String, String>.from(message.data),
      messageId: message.messageId,
    );
  }
}

import 'push_message.dart';

class NotificationNavigation {
  NotificationNavigation._();

  static const Set<String> _allowedRoutes = {'/dashboard', '/ask-fm'};

  static String? resolveRoute(
    PushMessage message, {
    required bool isAuthenticated,
  }) {
    if (!isAuthenticated) {
      return null;
    }

    final requestedRoute = message.requestedRoute;

    if (requestedRoute != null && _allowedRoutes.contains(requestedRoute)) {
      return requestedRoute;
    }

    if (message.type == 'AI_ADVISOR') {
      return '/ask-fm';
    }

    return '/dashboard';
  }
}

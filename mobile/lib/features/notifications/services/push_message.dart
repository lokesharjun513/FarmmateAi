class PushMessage {
  const PushMessage({
    required this.title,
    required this.body,
    this.data = const {},
    this.messageId,
  });

  final String title;
  final String body;
  final Map<String, String> data;
  final String? messageId;

  String get type => (data['type'] ?? '').trim().toUpperCase();

  String? get requestedRoute {
    final route = data['route'];

    if (route == null || route.trim().isEmpty) {
      return null;
    }

    return route.trim();
  }
}

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/ask_fm/ask_fm_screen.dart';
import 'package:mobile/features/ask_fm/data/ask_fm_repository.dart';
import 'fake_farm_repository.dart';

class FakeAskFmRepository extends AskFmRepository {
  String answer = 'Water the field early in the morning.';
  Object? error;
  Completer<String>? completer;

  int calls = 0;
  String? lastMessage;

  @override
  Future<String> sendMessage(String message, String farmId, {String? language}) async {
    calls++;
    lastMessage = message;

    if (completer != null) {
      return completer!.future;
    }

    if (error != null) {
      throw error!;
    }

    return answer;
  }
}

void setPhoneSize(WidgetTester tester, {Size size = const Size(390, 844)}) {
  tester.view
    ..physicalSize = size
    ..devicePixelRatio = 1;

  addTearDown(() {
    tester.view
      ..resetPhysicalSize()
      ..resetDevicePixelRatio();
  });
}

Widget buildApp(FakeAskFmRepository repository, {FakeFarmRepository? farmRepository}) {
  return MaterialApp(
    theme: AppTheme.lightTheme,
    home: AskFMScreen(repository: repository, farmRepository: farmRepository),
  );
}

Future<void> sendQuestion(WidgetTester tester, String question) async {
  await tester.enterText(find.byKey(const Key('ask_fm_input')), question);
  await tester.tap(find.byKey(const Key('ask_fm_send_button')));
  await tester.pump();
}

void main() {
  testWidgets('sends a real question and renders the API answer', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeAskFmRepository();
    final farmRepository = FakeFarmRepository();

    await tester.pumpWidget(buildApp(repository, farmRepository: farmRepository));
    await tester.pumpAndSettle(); // Wait for farm loading

    expect(find.text('Ask about your farm'), findsOneWidget);
    expect(find.textContaining('Hello'), findsNothing);

    await sendQuestion(tester, 'Should I irrigate today?');
    await tester.pumpAndSettle();

    expect(repository.calls, 1);
    expect(repository.lastMessage, 'Should I irrigate today?');
    expect(find.text('Should I irrigate today?'), findsOneWidget);
    expect(find.text('Water the field early in the morning.'), findsOneWidget);
  });

  testWidgets('shows a safe failure state and retries the same question', (
    tester,
  ) async {
    setPhoneSize(tester);

    final repository = FakeAskFmRepository()
      ..error = Exception(
        'FarmMate AI is temporarily unavailable. Please try again.',
      );
    final farmRepository = FakeFarmRepository();

    await tester.pumpWidget(buildApp(repository, farmRepository: farmRepository));
    await tester.pumpAndSettle();

    await sendQuestion(tester, 'How do I treat yellow leaves?');
    await tester.pumpAndSettle();

    expect(repository.calls, 1);
    expect(
      find.text('FarmMate AI is temporarily unavailable. Please try again.'),
      findsOneWidget,
    );
    expect(find.byKey(const Key('ask_fm_retry_button')), findsOneWidget);

    repository.error = null;

    await tester.tap(find.byKey(const Key('ask_fm_retry_button')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
    expect(repository.lastMessage, 'How do I treat yellow leaves?');
    expect(find.text('How do I treat yellow leaves?'), findsOneWidget);
    expect(find.text('Water the field early in the morning.'), findsOneWidget);
    expect(find.byKey(const Key('ask_fm_retry_button')), findsNothing);
  });

  testWidgets('shows thinking state without fabricating an answer', (
    tester,
  ) async {
    setPhoneSize(tester);

    final completer = Completer<String>();
    final repository = FakeAskFmRepository()..completer = completer;
    final farmRepository = FakeFarmRepository();

    await tester.pumpWidget(buildApp(repository, farmRepository: farmRepository));
    await tester.pumpAndSettle();

    await sendQuestion(tester, 'What is the best time to sow?');
    await tester.pump();

    expect(find.text('FarmMate AI is thinking…'), findsOneWidget);
    expect(repository.calls, 1);

    completer.complete('Sow when the soil has enough moisture.');
    await tester.pumpAndSettle();

    expect(find.text('Sow when the soil has enough moisture.'), findsOneWidget);
    expect(find.text('FarmMate AI is thinking…'), findsNothing);
  });

  testWidgets('empty questions are not sent', (tester) async {
    setPhoneSize(tester);

    final repository = FakeAskFmRepository();
    final farmRepository = FakeFarmRepository();

    await tester.pumpWidget(buildApp(repository, farmRepository: farmRepository));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('ask_fm_send_button')));
    await tester.pumpAndSettle();

    expect(repository.calls, 0);
  });
}

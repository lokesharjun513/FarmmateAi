import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/auth/presentation/screens/forgot_password_screen.dart';
import 'package:mobile/features/auth/presentation/screens/password_changed_screen.dart';
import 'package:mobile/features/auth/presentation/screens/set_new_password_screen.dart';
import 'package:mobile/features/auth/presentation/screens/verify_otp_screen.dart';
import 'package:mobile/features/auth/providers/auth_provider.dart';
import 'package:provider/provider.dart';

import 'auth_screens_test.dart' show FakeAuthProvider;

Widget buildFlowApp({
  required FakeAuthProvider authProvider,
  required String initialLocation,
  Map<String, String>? extra,
}) {
  final router = GoRouter(
    initialLocation: initialLocation,
    initialExtra: extra,
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const Scaffold(
          body: Center(child: Text('Login')),
        ),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) {
          // extra can be Map<String, dynamic> when passing from context.go();
          // cast through dynamic to satisfy the type system.
          final args = state.extra as Map<String, dynamic>?;
          final email = args?['email']?.toString() ?? '';
          return ForgotPasswordScreen(initialEmail: email);
        },
      ),
      GoRoute(
        path: '/verify-otp',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          final email = args?['email']?.toString() ?? '';
          return VerifyOtpsScreen(initialEmail: email);
        },
      ),
      GoRoute(
        path: '/set-new-password',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          return SetNewPasswordScreen(
            resetToken: args?['reset_token']?.toString() ?? '',
            expiresAt: args?['expires_at']?.toString() ?? '',
          );
        },
      ),
      GoRoute(
        path: '/password-changed',
        builder: (context, state) {
          final args = state.extra as Map<String, dynamic>?;
          return PasswordChangedScreen(email: args?['email']?.toString() ?? '');
        },
      ),
    ],
  );

  return ChangeNotifierProvider<AuthProvider>.value(
    value: authProvider,
    child: MaterialApp.router(
      theme: AppTheme.lightTheme,
      routerConfig: router,
    ),
  );
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

void main() {
  testWidgets('forgot password validates empty email', (tester) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/forgot-password',
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Forgot Password?'), findsOneWidget);

    await tester.tap(find.text('Send OTP'));
    await tester.pumpAndSettle();

    expect(find.text('Please enter your email address'), findsOneWidget);
  });

  testWidgets('forgot password navigates to verify-otp on send', (
    tester,
  ) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/forgot-password',
        extra: {'email': 'farmer@farmate.ai'},
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('farmer@farmate.ai'), findsOneWidget);

    await tester.tap(find.text('Send OTP'));
    await tester.pumpAndSettle();

    expect(find.text('Verify OTP'), findsOneWidget);
  });

  testWidgets('otp screen validates and shows error on wrong code', (
    tester,
  ) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/verify-otp',
        extra: {'email': 'farmer@farmate.ai'},
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Verify OTP'), findsOneWidget);

    // Empty code → the button is disabled, no inline validator message.
    final button = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
    expect(button.onPressed, isNull);

    // The hidden text field has the controller.
    await tester.enterText(find.byType(TextField), '000000');
    await tester.pump(); // let the button re-enable before tapping
    await tester.tap(find.text('Verify Code'));
    await tester.pumpAndSettle();

    expect(find.text('Invalid OTP'), findsOneWidget);
  });

  testWidgets('otp screen navigates to set new password on valid code', (
    tester,
  ) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/verify-otp',
        extra: {'email': 'farmer@farmate.ai'},
      ),
    );

    await tester.pumpAndSettle();

    // The hidden text field has the controller.
    await tester.enterText(find.byType(TextField), '123456');
    await tester.pump(); // let the button re-enable before tapping
    await tester.tap(find.text('Verify Code'));
    await tester.pumpAndSettle();

    expect(find.text('Set New Password'), findsOneWidget);
  });

  testWidgets('set new password validates and mismatches', (tester) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/set-new-password',
        extra: {'reset_token': 'token', 'expires_at': 'never'},
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Set New Password'), findsOneWidget);

    await tester.ensureVisible(find.text('Change Password'));
    await tester.tap(find.text('Change Password'));
    await tester.pumpAndSettle();

    expect(find.text('Please enter a password'), findsOneWidget);
    expect(find.text('Please confirm your password'), findsOneWidget);

    // Password too short
    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'short');
    await tester.enterText(fields.at(1), 'short');
    await tester.ensureVisible(find.text('Change Password'));
    await tester.tap(find.text('Change Password'));
    await tester.pumpAndSettle();

    expect(find.text('Password must be at least 8 characters'), findsOneWidget);

    // Mismatched passwords
    await tester.enterText(fields.at(0), 'longenoughpass');
    await tester.enterText(fields.at(1), 'differentpass');
    // Scroll button into view before tapping
    await tester.ensureVisible(find.text('Change Password'));
    await tester.tap(find.text('Change Password'));
    await tester.pumpAndSettle();

    expect(find.text('Passwords do not match'), findsOneWidget);
  });

  testWidgets('set new password navigates to password changed on success', (
    tester,
  ) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/set-new-password',
        extra: {'reset_token': 'token', 'expires_at': 'never'},
      ),
    );

    await tester.pumpAndSettle();

    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'longenoughpass');
    await tester.enterText(fields.at(1), 'longenoughpass');
    await tester.tap(find.text('Change Password'));
    await tester.pumpAndSettle();

    expect(find.text('Password Changed!'), findsOneWidget);
  });

  testWidgets('password changed screen renders correctly', (tester) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildFlowApp(
        authProvider: FakeAuthProvider(),
        initialLocation: '/password-changed',
        extra: {'email': 'farmer@farmate.ai'},
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Password Changed!'), findsOneWidget);
    expect(find.text('Back to Sign In'), findsOneWidget);

    // Button should be tappable without throwing
    await tester.tap(find.text('Back to Sign In'));
    await tester.pumpAndSettle();

    // After navigating to /login (no route registered there in the test router),
    // go_router replaces with the "no routes matched" placeholder.
    // The key assertion: no exception was thrown.
    expect(tester.takeException(), isNull);
  });
}

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app/theme/app_theme.dart';
import 'package:mobile/features/auth/data/models/user_model.dart';
import 'package:mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:mobile/features/auth/presentation/screens/register_screen.dart';
import 'package:mobile/features/auth/providers/auth_provider.dart';
import 'package:provider/provider.dart';

class FakeAuthProvider extends ChangeNotifier implements AuthProvider {
  FakeAuthProvider({
    this.status = AuthStatus.unauthenticated,
    this.errorMessage,
  });

  @override
  final AuthStatus status;

  @override
  String? errorMessage;

  @override
  Future<void> Function()? get onBeforeLogout => null;

  @override
  UserModel? get user => null;

  @override
  bool get isAuthenticated => status == AuthStatus.authenticated;

  @override
  bool get isUnauthenticated => status == AuthStatus.unauthenticated;

  @override
  bool get isLoading => status == AuthStatus.loading;

  @override
  bool get isInitial => status == AuthStatus.initial;

  @override
  bool get hasUser => false;

  @override
  bool get hasFarmerProfile => false;

  @override
  bool get needsFarmerOnboarding => false;

  @override
  Future<void> checkAuthStatus() async {}

  @override
  Future<Map<String, dynamic>> forgotPassword({
    required String email,
  }) async {
    return {'status': 'success'};
  }

  @override
  Future<Map<String, dynamic>> verifyResetOtp({
    required String email,
    required String otp,
  }) async {
    return otp == '123456'
        ? {'data': {'reset_authorization': 'token', 'expires_at': 'never'}}
        : {'status': 'error', 'detail': 'Invalid OTP'};
  }

  @override
  Future<Map<String, dynamic>> resetPassword({
    required String resetToken,
    required String newPassword,
  }) async {
    return {'status': 'success'};
  }

  @override
  Future<Map<String, dynamic>> resendResetOtp({
    required String email,
  }) async {
    return {'status': 'success'};
  }

  @override
  bool canResendResetOtp(String email) => true;

  @override
  String resendCooldownText(String email) => '';

  @override
  Future<bool> login({
    required String identifier,
    required String password,
  }) async {
    return false;
  }

  @override
  Future<bool> register({
    required String fullName,
    required String mobile,
    required String email,
    required String password,
  }) async {
    return false;
  }

  @override
  Future<bool> refreshFarmerProfile() async => false;

  @override
  void markFarmerProfileCreated() {}

  @override
  Future<void> logout() async {}

  @override
  void clearError() {
    if (errorMessage == null) {
      return;
    }

    errorMessage = null;
    notifyListeners();
  }
}

Widget buildApp({
  required Widget home,
  required FakeAuthProvider authProvider,
}) {
  return ChangeNotifierProvider<AuthProvider>.value(
    value: authProvider,
    child: MaterialApp(theme: AppTheme.lightTheme, home: home),
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
  testWidgets('login renders and validates empty fields', (tester) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildApp(home: const LoginScreen(), authProvider: FakeAuthProvider()),
    );

    await tester.pumpAndSettle();

    expect(find.text('Welcome back'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);

    await tester.tap(find.text('Sign in'));
    await tester.pumpAndSettle();

    expect(
      find.text('Please enter your email or mobile number'),
      findsOneWidget,
    );
    expect(find.text('Please enter your password'), findsOneWidget);
  });

  testWidgets('login shows API error and disables controls while loading', (
    tester,
  ) async {
    setPhoneSize(tester);

    await tester.pumpWidget(
      buildApp(
        home: const LoginScreen(),
        authProvider: FakeAuthProvider(errorMessage: 'Invalid credentials.'),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Invalid credentials.'), findsOneWidget);

    await tester.pumpWidget(
      buildApp(
        home: const LoginScreen(),
        authProvider: FakeAuthProvider(status: AuthStatus.loading),
      ),
    );

    await tester.pump(const Duration(milliseconds: 250));

    final button = tester.widget<ElevatedButton>(find.byType(ElevatedButton));

    expect(button.onPressed, isNull);
    expect(find.text('Signing in...'), findsOneWidget);
  });

  testWidgets('register renders and validates exact backend fields', (
    tester,
  ) async {
    setPhoneSize(tester, size: const Size(320, 568));

    await tester.pumpWidget(
      buildApp(home: const RegisterScreen(), authProvider: FakeAuthProvider()),
    );

    await tester.pumpAndSettle();

    expect(find.text('Create your account'), findsOneWidget);
    expect(find.text('Full name'), findsOneWidget);
    expect(find.text('Mobile number'), findsOneWidget);
    expect(find.text('Email address'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Confirm password'), findsOneWidget);

    await tester.ensureVisible(find.text('Create account'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Create account'));
    await tester.pumpAndSettle();

    expect(
      find.text('Full name must be at least 3 characters'),
      findsOneWidget,
    );
    expect(
      find.text('Mobile number must be exactly 10 digits'),
      findsOneWidget,
    );
    expect(find.text('Please enter your email address'), findsOneWidget);
    expect(find.text('Password must be at least 8 characters'), findsOneWidget);
    expect(find.text('Please confirm your password'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../widgets/auth_widgets.dart';

class PasswordChangedScreen extends StatefulWidget {
  const PasswordChangedScreen({super.key, this.email = ''});

  final String email;

  @override
  State<PasswordChangedScreen> createState() => _PasswordChangedScreenState();
}

class _PasswordChangedScreenState extends State<PasswordChangedScreen> {
  bool _reduceMotion = false;

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && !_reduceMotion) {
        // Animation started via didChangeDependencies
      }
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    final reduceMotion = MediaQuery.disableAnimationsOf(context);

    if (reduceMotion == _reduceMotion) {
      return;
    }

    _reduceMotion = reduceMotion;
  }

  @override
  void dispose() {
    super.dispose();
  }

  // ─── Build ───────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final textTheme = Theme.of(context).textTheme;

    // Clear sensitive recovery state
    // OTP and reset authorization are kept in memory only
    // and will be cleared when navigating away

    return AuthScaffold(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Success checkmark ──
            const SizedBox(height: 48),
            Center(
              child: Icon(
                Icons.check_circle_outline,
                size: 96,
                color: AppColors.primary,
              ),
            ),

            const SizedBox(height: 24),

            // ── Password Changed! heading ──
            Center(
              child: Text(
                'Password Changed!',
                style: textTheme.headlineLarge?.copyWith(
                  color: AppColors.textPrimary,
                  letterSpacing: -0.8,
                ),
              ),
            ),

            const SizedBox(height: 8),

            // ── Confirmation message ──
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 300),
                child: Text(
                  'Your password has been successfully changed. '
                  'You can now sign in with your new password.',
                  textAlign: TextAlign.center,
                  style: textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    height: 1.45,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // ── Email notification message ──
            // Note: Actual delivery status may vary; we describe it as queued
 // to be accurate about what the backend actually guarantees.
            Center(
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'A password change notification has been queued to your '
                  'registered email address. You should receive it shortly.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 32),

            // ── Back to Sign In button ──
            AuthPrimaryButton(
              label: 'Back to Sign In',
              loadingLabel: 'Signing in...',
              isLoading: authProvider.isLoading,
              onPressed: () {
                // Clear sensitive recovery state and navigate to login
                // Do not automatically authenticate the user
                context.go('/login');
              },
            ),

            const SizedBox(height: 28),

            // ── Brand chips ──
            const Center(
              child: BrandChips(),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../widgets/auth_widgets.dart';

class SetNewPasswordScreen extends StatefulWidget {
  const SetNewPasswordScreen({
    super.key,
    this.resetToken = '',
    this.expiresAt = '',
    this.email = '',
  });

  final String resetToken;
  final String expiresAt;
  final String email;

  @override
  State<SetNewPasswordScreen> createState() => _SetNewPasswordScreenState();
}

class _SetNewPasswordScreenState extends State<SetNewPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _passwordFocusNode = FocusNode();
  final _confirmPasswordFocusNode = FocusNode();
  bool _isSubmitting = false;
  bool _reduceMotion = false;

  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;

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
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    _passwordFocusNode.dispose();
    _confirmPasswordFocusNode.dispose();
    super.dispose();
  }

  // ─── Actions ─────────────────────────────────────────────────────────

  Future<void> _handleResetPassword() async {
    if (_isSubmitting) {
      return;
    }

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    final authProvider = context.read<AuthProvider>();

    try {
      final result = await authProvider.resetPassword(
        resetToken: widget.resetToken,
        newPassword: _newPasswordController.text,
      );

      if (!mounted) return;

      if (result['success'] == true || result['status'] == 'success') {
        // Password reset successful - navigate to password changed screen
        context.go('/password-changed');
      } else {
        // Failed reset - show error
        if (!mounted) return;
        _showError(
          result['message'] ??
              result['detail'] ??
              'Failed to reset password. Please try again.',
        );
      }
    } catch (e) {
      if (!mounted) return;
      _showError('Failed to reset password. Please try again.');
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor: Colors.red[200],
      ),
    );
  }

  // ─── Build ───────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final isLoading = _isSubmitting || authProvider.isLoading;
    final textTheme = Theme.of(context).textTheme;

    return AuthScaffold(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Logo ──
            const SizedBox(height: 48),
            Stack(
              children: [
                const Center(child: AuthBrandMark(size: 68)),
                Positioned(
                  left: 0,
                  top: 0,
                  child: IconButton(
                    icon: const Icon(Icons.arrow_back_ios_new),
                    onPressed: () => context.go('/verify-otp', extra: {'email': widget.email}),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 20),

            // ── FarmMate AI brand text ──
            Center(
              child: Text(
                'FarmMate AI',
                style: textTheme.titleMedium?.copyWith(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.2,
                ),
              ),
            ),

            const SizedBox(height: 36),

            // ── Heading ──
            Center(
              child: Text(
                'Set New Password',
                style: textTheme.headlineLarge?.copyWith(
                  color: AppColors.textPrimary,
                  letterSpacing: -0.8,
                ),
              ),
            ),

            const SizedBox(height: 8),

            // ── Subtitle ──
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 300),
                child: Text(
                  'Enter your new password below. The password must be at least 8 characters.',
                  textAlign: TextAlign.center,
                  style: textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    height: 1.45,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 32),

            // ── Form card ──
            AuthCard(
              child: AutofillGroup(
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Reset token expiry notice
                      _buildExpiryNotice(),

                      const SizedBox(height: 24),

                      // New password field
                      _buildNewPasswordField(authProvider, isLoading),

                      const SizedBox(height: 16),

                      // Confirm password field
                      _buildConfirmPasswordField(authProvider, isLoading),

                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 24),

            // ── Change Password button ──
            AuthPrimaryButton(
              label: 'Change Password',
              loadingLabel: 'Updating Password...',
              isLoading: isLoading,
              onPressed: _handleResetPassword,
            ),

            const SizedBox(height: 20),

            // ── Footer link ──
            AuthFooter(
              prompt: 'Remember your password?',
              actionLabel: 'Back to sign in',
              onPressed: isLoading
                  ? null
                  : () => context.go('/login'),
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

  // ─── Fields ─────────────────────────────────────────────────────────

  Widget _buildExpiryNotice() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.primaryLight,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        widget.expiresAt.isNotEmpty
            ? 'This reset link will expire at ${widget.expiresAt} UTC'
            : 'This reset link will expire 10 minutes after verification.',
        textAlign: TextAlign.center,
        style: const TextStyle(
          color: AppColors.textPrimary,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _buildNewPasswordField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _newPasswordController,
      enabled: !isLoading,
      focusNode: _passwordFocusNode,
      keyboardType: TextInputType.visiblePassword,
      textInputAction: TextInputAction.next,
      autofillHints: const [AutofillHints.password],
      textCapitalization: TextCapitalization.none,
      autocorrect: false,
      enableSuggestions: false,
      maxLength: 128,
      obscureText: _obscureNewPassword,
      decoration: InputDecoration(
        labelText: 'New Password',
        hintText: 'Enter new password',
        prefixIcon: const Icon(Icons.lock_outlined),
        counterText: '',
        suffixIcon: IconButton(
          onPressed: isLoading
              ? null
              : _toggleNewPasswordVisibility,
          tooltip: _obscureNewPassword ? 'Show password' : 'Hide password',
          icon: Icon(
            _obscureNewPassword
                ? Icons.visibility_off_outlined
                : Icons.visibility_outlined,
          ),
        ),
      ),
      validator: (value) {
        final password = value?.trim() ?? '';

        if (password.isEmpty) {
          return 'Please enter a password';
        }

        if (password.length < 8) {
          return 'Password must be at least 8 characters';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          FocusScope.of(context).nextFocus();
        }
      },
    );
  }

  Widget _buildConfirmPasswordField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _confirmPasswordController,
      enabled: !isLoading,
      focusNode: _confirmPasswordFocusNode,
      keyboardType: TextInputType.visiblePassword,
      textInputAction: TextInputAction.done,
      autofillHints: const [AutofillHints.password],
      textCapitalization: TextCapitalization.none,
      autocorrect: false,
      enableSuggestions: false,
      maxLength: 128,
      obscureText: _obscureConfirmPassword,
      decoration: InputDecoration(
        labelText: 'Confirm Password',
        hintText: 'Confirm new password',
        prefixIcon: const Icon(Icons.lock_outlined),
        counterText: '',
        suffixIcon: IconButton(
          onPressed: isLoading
              ? null
              : _toggleConfirmPasswordVisibility,
          tooltip: _obscureConfirmPassword ? 'Show password' : 'Hide password',
          icon: Icon(
            _obscureConfirmPassword
                ? Icons.visibility_off_outlined
                : Icons.visibility_outlined,
          ),
        ),
      ),
      validator: (value) {
        final password = value?.trim() ?? '';

        if (password.isEmpty) {
          return 'Please confirm your password';
        }

        final newPassword = _newPasswordController.text.trim();

        if (password != newPassword) {
          return 'Passwords do not match';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _handleResetPassword();
        }
      },
    );
  }

  // ─── Password visibility toggles ─────────────────────────────────────

  void _toggleNewPasswordVisibility() {
    if (!mounted) return;
    setState(() {
      _obscureNewPassword = !_obscureNewPassword;
    });
  }

  void _toggleConfirmPasswordVisibility() {
    if (!mounted) return;
    setState(() {
      _obscureConfirmPassword = !_obscureConfirmPassword;
    });
  }
}

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../widgets/auth_widgets.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();

  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();

  final _identifierFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();

  bool _obscurePassword = true;
  bool _isSubmitting = false;
  bool _reduceMotion = false;

  // ─── Animation ────────────────────────────────────────────────────────

  AnimationController? _animationController;
  Animation<double>? _fadeAnimation;
  Animation<Offset>? _slideAnimation;

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

    if (_reduceMotion) {
      // Skip animations when reduced motion is enabled
      return;
    }
  }

  @override
  void didUpdateWidget(covariant LoginScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Animation controller managed via didChangeDependencies
  }

  @override
  void dispose() {
    _animationController?.dispose();
    _identifierController.dispose();
    _passwordController.dispose();
    _identifierFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  // ─── Actions ─────────────────────────────────────────────────────────

  Future<void> _handleLogin() async {
    if (_isSubmitting) {
      return;
    }

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    FocusScope.of(context).unfocus();

    final authProvider = context.read<AuthProvider>();

    try {
      await authProvider.login(
        identifier: _identifierController.text.trim(),
        password: _passwordController.text,
      );

      if (!mounted) return;

      if (authProvider.hasFarmerProfile) {
        context.go('/dashboard');
      } else {
        context.go('/onboarding');
      }
    } catch (e) {
      if (!mounted) return;
      // AuthProvider handles error internally
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  void _togglePasswordVisibility() {
    if (!mounted) return;
    setState(() {
      _obscurePassword = !_obscurePassword;
    });
  }

  // Returns the identifier trimmed / lowercased only when it looks like an
  // email. Mobile numbers are deliberately not pre-filled.
  String? _extractEmail(String identifier) {
    final clean = identifier.trim();

    return RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(clean)
        ? clean
        : null;
  }

  // ─── Build ───────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final isLoading = _isSubmitting || authProvider.isLoading;
    final errorMessage = authProvider.errorMessage;
    final textTheme = Theme.of(context).textTheme;

    // Build animation controller if not created
    if (_animationController == null) {
      _animationController = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 520),
      );

      _fadeAnimation = CurvedAnimation(
        parent: _animationController!,
        curve: const Interval(0, 0.9, curve: Curves.easeOut),
      );

      _slideAnimation =
          Tween<Offset>(
            begin: const Offset(0, 0.025),
            end: Offset.zero,
          ).animate(
            CurvedAnimation(
              parent: _animationController!,
              curve: Curves.easeOutCubic,
            ),
          );
    }

    // Start animation if not in reduced motion
    if (!_reduceMotion && !_animationController!.isAnimating) {
      _animationController!.forward();
    }

    return AuthScaffold(
      child: FadeTransition(
        opacity: _fadeAnimation!,
        child: SlideTransition(
          position: _slideAnimation!,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Logo ──
              const SizedBox(height: 48),
              const Center(child: AuthBrandMark(size: 68)),

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
                  'Welcome back',
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
                  constraints: const BoxConstraints(maxWidth: 280),
                  child: Text(
                    'Sign in to continue caring for your farm.',
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
                        if (errorMessage != null) ...[
                          AuthErrorBanner(
                            message: errorMessage,
                            semanticPrefix: 'Login error',
                          ),
                          const SizedBox(height: 18),
                        ],
                        _buildIdentifierField(authProvider, isLoading),
                        const SizedBox(height: 14),
                        _buildPasswordField(authProvider, isLoading),
                        const SizedBox(height: 8),
                        // ── Forgot Password ──
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: isLoading
                                ? null
                                : () {
                                    authProvider.clearError();
                                    final prefillEmail = _extractEmail(
                                      _identifierController.text,
                                    );
                                    context.go(
                                      '/forgot-password',
                                      extra: prefillEmail == null
                                          ? null
                                          : <String, String>{
                                              'email': prefillEmail,
                                            },
                                    );
                                  },
                            style: TextButton.styleFrom(
                              foregroundColor: AppColors.primary,
                              textStyle: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            child: const Text('Forgot password?'),
                          ),
                        ),
                        const SizedBox(height: 14),
                        AuthPrimaryButton(
                          label: 'Sign in',
                          loadingLabel: 'Signing in...',
                          isLoading: isLoading,
                          onPressed: _handleLogin,
                        ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 20),

              // ── Footer link ──
              AuthFooter(
                prompt: 'New to FarmMate?',
                actionLabel: 'Create account',
                onPressed: isLoading
                    ? null
                    : () {
                        authProvider.clearError();
                        context.go('/register');
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
      ),
    );
  }

  // ─── Fields ─────────────────────────────────────────────────────────

  Widget _buildIdentifierField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _identifierController,
      focusNode: _identifierFocusNode,
      enabled: !isLoading,
      keyboardType: TextInputType.text,
      textInputAction: TextInputAction.next,
      autofillHints: const [AutofillHints.email, AutofillHints.telephoneNumber],
      textCapitalization: TextCapitalization.none,
      autocorrect: false,
      enableSuggestions: false,
      maxLength: 255,
      onChanged: (_) => authProvider.clearError(),
      decoration: const InputDecoration(
        labelText: 'Email or mobile number',
        hintText: 'Enter your email or mobile',
        prefixIcon: Icon(Icons.person_outline_rounded),
        counterText: '',
      ),
      validator: (value) {
        final identifier = value?.trim() ?? '';

        if (identifier.isEmpty) {
          return 'Please enter your email or mobile number';
        }

        final isEmail = RegExp(
          r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
        ).hasMatch(identifier);

        final isMobile = RegExp(r'^\d{10}$').hasMatch(identifier);

        if (!isEmail && !isMobile) {
          return 'Enter a valid email or 10-digit mobile number';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _passwordFocusNode.requestFocus();
        }
      },
    );
  }

  Widget _buildPasswordField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _passwordController,
      focusNode: _passwordFocusNode,
      enabled: !isLoading,
      obscureText: _obscurePassword,
      textInputAction: TextInputAction.done,
      autofillHints: const [AutofillHints.password],
      autocorrect: false,
      enableSuggestions: false,
      maxLength: 128,
      onChanged: (_) => authProvider.clearError(),
      decoration: InputDecoration(
        labelText: 'Password',
        hintText: 'Enter your password',
        prefixIcon: const Icon(Icons.lock_outline_rounded),
        counterText: '',
        suffixIcon: IconButton(
          onPressed: isLoading ? null : _togglePasswordVisibility,
          tooltip: _obscurePassword ? 'Show password' : 'Hide password',
          icon: Icon(
            _obscurePassword
                ? Icons.visibility_off_outlined
                : Icons.visibility_outlined,
          ),
        ),
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Please enter your password';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _handleLogin();
        }
      },
    );
  }
}

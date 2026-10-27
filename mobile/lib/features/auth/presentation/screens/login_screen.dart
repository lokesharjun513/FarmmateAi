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

  late final AnimationController _animationController;
  late final Animation<double> _fadeAnimation;
  late final Animation<Offset> _slideAnimation;

  bool _obscurePassword = true;
  bool _isSubmitting = false;
  bool _reduceMotion = false;

  @override
  void initState() {
    super.initState();

    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 520),
    );

    _fadeAnimation = CurvedAnimation(
      parent: _animationController,
      curve: const Interval(0, 0.9, curve: Curves.easeOut),
    );

    _slideAnimation =
        Tween<Offset>(begin: const Offset(0, 0.025), end: Offset.zero).animate(
          CurvedAnimation(
            parent: _animationController,
            curve: Curves.easeOutCubic,
          ),
        );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && !_reduceMotion) {
        _animationController.forward();
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
      _animationController.value = 1;
      return;
    }

    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _identifierController.dispose();
    _passwordController.dispose();
    _identifierFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

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

    var success = false;

    try {
      success = await authProvider.login(
        identifier: _identifierController.text.trim(),
        password: _passwordController.text,
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }

    if (!mounted || !success) {
      return;
    }

    if (authProvider.hasFarmerProfile) {
      context.go('/dashboard');
    } else {
      context.go('/onboarding');
    }
  }

  void _togglePasswordVisibility() {
    if (!mounted) {
      return;
    }

    setState(() {
      _obscurePassword = !_obscurePassword;
    });
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final isLoading = _isSubmitting || authProvider.isLoading;
    final textTheme = Theme.of(context).textTheme;
    final errorMessage = authProvider.errorMessage;

    return AuthScaffold(
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: SlideTransition(
          position: _slideAnimation,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildHeader(textTheme),
              const SizedBox(height: 30),
              AuthCard(
                child: AutofillGroup(
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 180),
                          child: errorMessage == null
                              ? const SizedBox.shrink()
                              : Column(
                                  key: ValueKey(errorMessage),
                                  children: [
                                    AuthErrorBanner(
                                      message: errorMessage,
                                      semanticPrefix: 'Login error',
                                    ),
                                    const SizedBox(height: 18),
                                  ],
                                ),
                        ),
                        _buildIdentifierField(authProvider, isLoading),
                        const SizedBox(height: 14),
                        _buildPasswordField(authProvider, isLoading),
                        const SizedBox(height: 22),
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
              const SizedBox(height: 22),
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
              const SizedBox(height: 30),
              Text(
                'FARMING • INTELLIGENCE • SIMPLICITY',
                textAlign: TextAlign.center,
                style: textTheme.bodySmall?.copyWith(
                  color: AppColors.textHint.withValues(alpha: 0.72),
                  fontSize: 8.5,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.25,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(TextTheme textTheme) {
    return Column(
      children: [
        const AuthBrandMark(size: 68),
        const SizedBox(height: 22),
        Text(
          'Welcome back',
          textAlign: TextAlign.center,
          style: textTheme.headlineLarge?.copyWith(
            color: AppColors.textPrimary,
            letterSpacing: -0.8,
          ),
        ),
        const SizedBox(height: 8),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 300),
          child: Text(
            'Sign in to continue caring for your farm.',
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textSecondary,
              height: 1.45,
            ),
          ),
        ),
      ],
    );
  }

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
          icon: AnimatedSwitcher(
            duration: const Duration(milliseconds: 160),
            child: Icon(
              _obscurePassword
                  ? Icons.visibility_off_outlined
                  : Icons.visibility_outlined,
              key: ValueKey(_obscurePassword),
            ),
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

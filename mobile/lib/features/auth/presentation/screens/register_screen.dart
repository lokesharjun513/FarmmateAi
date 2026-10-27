import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../widgets/auth_widgets.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();

  final _fullNameController = TextEditingController();
  final _mobileController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  final _fullNameFocusNode = FocusNode();
  final _mobileFocusNode = FocusNode();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  final _confirmPasswordFocusNode = FocusNode();

  late final AnimationController _animationController;
  late final Animation<double> _headerFade;
  late final Animation<Offset> _headerSlide;
  late final Animation<double> _formFade;
  late final Animation<Offset> _formSlide;
  late final Animation<double> _footerFade;

  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _isSubmitting = false;
  bool _reduceMotion = false;

  @override
  void initState() {
    super.initState();

    _passwordController.addListener(_onPasswordChanged);
    _confirmPasswordController.addListener(_onConfirmPasswordChanged);

    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 580),
    );

    _headerFade = CurvedAnimation(
      parent: _animationController,
      curve: const Interval(0, 0.6, curve: Curves.easeOut),
    );

    _headerSlide = Tween<Offset>(begin: const Offset(0, 0.04), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _animationController,
            curve: const Interval(0, 0.7, curve: Curves.easeOutCubic),
          ),
        );

    _formFade = CurvedAnimation(
      parent: _animationController,
      curve: const Interval(0.12, 0.9, curve: Curves.easeOut),
    );

    _formSlide = Tween<Offset>(begin: const Offset(0, 0.035), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _animationController,
            curve: const Interval(0.1, 0.9, curve: Curves.easeOutCubic),
          ),
        );

    _footerFade = CurvedAnimation(
      parent: _animationController,
      curve: const Interval(0.5, 1, curve: Curves.easeOut),
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

  void _onPasswordChanged() {
    if (!mounted) {
      return;
    }

    setState(() {});
  }

  void _onConfirmPasswordChanged() {
    if (!mounted) {
      return;
    }

    setState(() {});
  }

  @override
  void dispose() {
    _passwordController.removeListener(_onPasswordChanged);
    _confirmPasswordController.removeListener(_onConfirmPasswordChanged);

    _animationController.dispose();

    _fullNameController.dispose();
    _mobileController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();

    _fullNameFocusNode.dispose();
    _mobileFocusNode.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    _confirmPasswordFocusNode.dispose();

    super.dispose();
  }

  Future<void> _handleRegister() async {
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
      success = await authProvider.register(
        fullName: _fullNameController.text.trim(),
        mobile: _mobileController.text.trim(),
        email: _emailController.text.trim(),
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

    final messenger = ScaffoldMessenger.of(context);

    messenger
      ..clearSnackBars()
      ..showSnackBar(
        const SnackBar(
          content: Row(
            children: [
              Icon(
                Icons.check_circle_outline_rounded,
                size: 20,
                color: Colors.white,
              ),
              SizedBox(width: 10),
              Expanded(child: Text('Account created. Sign in to continue.')),
            ],
          ),
        ),
      );

    context.go('/login');
  }

  void _togglePasswordVisibility() {
    if (!mounted) {
      return;
    }

    setState(() {
      _obscurePassword = !_obscurePassword;
    });
  }

  void _toggleConfirmPasswordVisibility() {
    if (!mounted) {
      return;
    }

    setState(() {
      _obscureConfirmPassword = !_obscureConfirmPassword;
    });
  }

  int _passwordStrengthScore(String password) {
    if (password.isEmpty) {
      return 0;
    }

    var score = 0;

    if (password.length >= 8) {
      score++;
    }

    if (RegExp(r'[a-z]').hasMatch(password)) {
      score++;
    }

    if (RegExp(r'[A-Z]').hasMatch(password)) {
      score++;
    }

    if (RegExp(r'\d').hasMatch(password)) {
      score++;
    }

    if (RegExp(r'[^\w\s]').hasMatch(password)) {
      score++;
    }

    return score;
  }

  String _passwordStrengthLabel(int score) {
    if (score <= 1) {
      return 'Weak';
    }

    if (score <= 3) {
      return 'Good';
    }

    return 'Strong';
  }

  Color _passwordStrengthColor(int score) {
    if (score <= 1) {
      return AppColors.error;
    }

    if (score <= 3) {
      return AppColors.warning;
    }

    return AppColors.success;
  }

  bool get _hasPasswordMatchText {
    return _confirmPasswordController.text.isNotEmpty;
  }

  bool get _passwordsMatch {
    return _hasPasswordMatchText &&
        _passwordController.text == _confirmPasswordController.text;
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final isLoading = _isSubmitting || authProvider.isLoading;
    final textTheme = Theme.of(context).textTheme;
    final isCompact = MediaQuery.sizeOf(context).width < 380;

    return AuthScaffold(
      maxWidth: 460,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          FadeTransition(
            opacity: _headerFade,
            child: SlideTransition(
              position: _headerSlide,
              child: _buildHeader(textTheme),
            ),
          ),
          const SizedBox(height: 28),
          FadeTransition(
            opacity: _formFade,
            child: SlideTransition(
              position: _formSlide,
              child: AuthCard(
                padding: EdgeInsets.all(isCompact ? 20 : 24),
                child: AutofillGroup(
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 180),
                          child: authProvider.errorMessage == null
                              ? const SizedBox.shrink()
                              : Column(
                                  key: ValueKey(authProvider.errorMessage),
                                  children: [
                                    AuthErrorBanner(
                                      message: authProvider.errorMessage!,
                                      semanticPrefix: 'Registration error',
                                    ),
                                    const SizedBox(height: 20),
                                  ],
                                ),
                        ),
                        _buildSectionLabel(textTheme, 'Your details'),
                        const SizedBox(height: 14),
                        _buildFullNameField(authProvider, isLoading),
                        const SizedBox(height: 14),
                        _buildMobileField(authProvider, isLoading),
                        const SizedBox(height: 14),
                        _buildEmailField(authProvider, isLoading),
                        const SizedBox(height: 26),
                        const Divider(height: 1),
                        const SizedBox(height: 24),
                        _buildSectionLabel(textTheme, 'Secure your account'),
                        const SizedBox(height: 14),
                        _buildPasswordField(authProvider, isLoading),
                        if (_passwordController.text.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          _buildPasswordStrength(textTheme),
                        ],
                        const SizedBox(height: 14),
                        _buildConfirmPasswordField(authProvider, isLoading),
                        if (_hasPasswordMatchText) ...[
                          const SizedBox(height: 10),
                          _buildPasswordMatchFeedback(textTheme),
                        ],
                        const SizedBox(height: 24),
                        AuthPrimaryButton(
                          label: 'Create account',
                          loadingLabel: 'Creating account...',
                          isLoading: isLoading,
                          onPressed: _handleRegister,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 22),
          FadeTransition(
            opacity: _footerFade,
            child: AuthFooter(
              prompt: 'Already have an account?',
              actionLabel: 'Sign in',
              onPressed: isLoading
                  ? null
                  : () {
                      authProvider.clearError();
                      context.go('/login');
                    },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(TextTheme textTheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const AuthBrandMark(size: 46),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'FarmMate AI',
                style: textTheme.titleMedium?.copyWith(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.2,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 26),
        Text(
          'Create your account',
          style: textTheme.headlineLarge?.copyWith(
            color: AppColors.textPrimary,
            letterSpacing: -0.8,
          ),
        ),
        const SizedBox(height: 9),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 360),
          child: Text(
            'A few details to personalise your farming experience.',
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textSecondary,
              height: 1.45,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSectionLabel(TextTheme textTheme, String label) {
    return Text(
      label,
      style: textTheme.labelLarge?.copyWith(
        color: AppColors.textPrimary,
        fontWeight: FontWeight.w700,
        letterSpacing: 0.1,
      ),
    );
  }

  Widget _buildFullNameField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _fullNameController,
      focusNode: _fullNameFocusNode,
      enabled: !isLoading,
      keyboardType: TextInputType.name,
      textInputAction: TextInputAction.next,
      textCapitalization: TextCapitalization.words,
      autofillHints: const [AutofillHints.name],
      maxLength: 100,
      onChanged: (_) => authProvider.clearError(),
      decoration: const InputDecoration(
        labelText: 'Full name',
        hintText: 'Enter your full name',
        prefixIcon: Icon(Icons.person_outline_rounded),
        counterText: '',
      ),
      validator: (value) {
        final name = value?.trim() ?? '';

        if (name.length < 3) {
          return 'Full name must be at least 3 characters';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _mobileFocusNode.requestFocus();
        }
      },
    );
  }

  Widget _buildMobileField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _mobileController,
      focusNode: _mobileFocusNode,
      enabled: !isLoading,
      keyboardType: TextInputType.phone,
      textInputAction: TextInputAction.next,
      autofillHints: const [AutofillHints.telephoneNumber],
      maxLength: 10,
      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
      onChanged: (_) => authProvider.clearError(),
      decoration: const InputDecoration(
        labelText: 'Mobile number',
        hintText: '10-digit mobile number',
        prefixIcon: Icon(Icons.phone_outlined),
        counterText: '',
      ),
      validator: (value) {
        final mobile = value?.trim() ?? '';

        if (!RegExp(r'^\d{10}$').hasMatch(mobile)) {
          return 'Mobile number must be exactly 10 digits';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _emailFocusNode.requestFocus();
        }
      },
    );
  }

  Widget _buildEmailField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _emailController,
      focusNode: _emailFocusNode,
      enabled: !isLoading,
      keyboardType: TextInputType.emailAddress,
      textInputAction: TextInputAction.next,
      autofillHints: const [AutofillHints.email],
      autocorrect: false,
      enableSuggestions: false,
      textCapitalization: TextCapitalization.none,
      onChanged: (_) => authProvider.clearError(),
      decoration: const InputDecoration(
        labelText: 'Email address',
        hintText: 'name@example.com',
        prefixIcon: Icon(Icons.email_outlined),
      ),
      validator: (value) {
        final email = value?.trim() ?? '';

        if (email.isEmpty) {
          return 'Please enter your email address';
        }

        final emailValid = RegExp(
          r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
        ).hasMatch(email);

        if (!emailValid) {
          return 'Please enter a valid email address';
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
      textInputAction: TextInputAction.next,
      autofillHints: const [AutofillHints.newPassword],
      autocorrect: false,
      enableSuggestions: false,
      maxLength: 128,
      onChanged: (_) => authProvider.clearError(),
      decoration: InputDecoration(
        labelText: 'Password',
        hintText: 'At least 8 characters',
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
        if (value == null || value.length < 8) {
          return 'Password must be at least 8 characters';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _confirmPasswordFocusNode.requestFocus();
        }
      },
    );
  }

  Widget _buildConfirmPasswordField(AuthProvider authProvider, bool isLoading) {
    return TextFormField(
      controller: _confirmPasswordController,
      focusNode: _confirmPasswordFocusNode,
      enabled: !isLoading,
      obscureText: _obscureConfirmPassword,
      textInputAction: TextInputAction.done,
      autofillHints: const [AutofillHints.newPassword],
      autocorrect: false,
      enableSuggestions: false,
      maxLength: 128,
      onChanged: (_) => authProvider.clearError(),
      decoration: InputDecoration(
        labelText: 'Confirm password',
        hintText: 'Re-enter your password',
        prefixIcon: const Icon(Icons.lock_reset_outlined),
        counterText: '',
        suffixIcon: IconButton(
          onPressed: isLoading ? null : _toggleConfirmPasswordVisibility,
          tooltip: _obscureConfirmPassword
              ? 'Show confirmation password'
              : 'Hide confirmation password',
          icon: AnimatedSwitcher(
            duration: const Duration(milliseconds: 160),
            child: Icon(
              _obscureConfirmPassword
                  ? Icons.visibility_off_outlined
                  : Icons.visibility_outlined,
              key: ValueKey(_obscureConfirmPassword),
            ),
          ),
        ),
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Please confirm your password';
        }

        if (value != _passwordController.text) {
          return 'Passwords do not match';
        }

        return null;
      },
      onFieldSubmitted: (_) {
        if (!isLoading) {
          _handleRegister();
        }
      },
    );
  }

  Widget _buildPasswordStrength(TextTheme textTheme) {
    final password = _passwordController.text;
    final score = _passwordStrengthScore(password);
    final strengthColor = _passwordStrengthColor(score);
    final label = _passwordStrengthLabel(score);

    return Semantics(
      liveRegion: true,
      label: 'Password strength: $label',
      child: AnimatedSize(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOutCubic,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Password strength',
                    style: textTheme.bodySmall?.copyWith(
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 160),
                  child: Text(
                    label,
                    key: ValueKey(label),
                    style: textTheme.bodySmall?.copyWith(
                      color: strengthColor,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: List.generate(5, (index) {
                final isActive = index < score;

                return Expanded(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    curve: Curves.easeOutCubic,
                    height: 4,
                    margin: EdgeInsets.only(right: index == 4 ? 0 : 4),
                    decoration: BoxDecoration(
                      color: isActive
                          ? strengthColor
                          : AppColors.borderLight.withValues(alpha: 0.72),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPasswordMatchFeedback(TextTheme textTheme) {
    final matches = _passwordsMatch;

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 180),
      child: Row(
        key: ValueKey(matches),
        children: [
          Icon(
            matches
                ? Icons.check_circle_outline_rounded
                : Icons.info_outline_rounded,
            size: 17,
            color: matches ? AppColors.success : AppColors.error,
          ),
          const SizedBox(width: 7),
          Expanded(
            child: Text(
              matches ? 'Passwords match' : 'Passwords do not match',
              style: textTheme.bodySmall?.copyWith(
                color: matches ? AppColors.success : AppColors.error,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

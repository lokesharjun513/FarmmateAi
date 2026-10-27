import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../auth/providers/auth_provider.dart';
import '../widgets/auth_widgets.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  static const _minimumSplashDuration = Duration(milliseconds: 1800);

  late final AnimationController _entranceController;
  late final AnimationController _breathingController;
  late final AnimationController _loadingController;

  late final Animation<double> _fadeAnimation;
  late final Animation<double> _contentSlideAnimation;
  late final Animation<double> _contentScaleAnimation;
  late final Animation<double> _brandScaleAnimation;

  bool _reduceMotion = false;

  @override
  void initState() {
    super.initState();

    _entranceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 720),
    );

    _breathingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 4200),
    )..repeat(reverse: true);

    _loadingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat();

    final entranceCurve = CurvedAnimation(
      parent: _entranceController,
      curve: Curves.easeOutCubic,
    );

    _fadeAnimation = CurvedAnimation(
      parent: _entranceController,
      curve: const Interval(0, 0.78, curve: Curves.easeOut),
    );

    _contentSlideAnimation = Tween<double>(
      begin: 16,
      end: 0,
    ).animate(entranceCurve);

    _contentScaleAnimation = Tween<double>(
      begin: 0.985,
      end: 1,
    ).animate(entranceCurve);

    _brandScaleAnimation = Tween<double>(begin: 0.92, end: 1).animate(
      CurvedAnimation(
        parent: _entranceController,
        curve: const Interval(0, 0.7, curve: Curves.easeOutCubic),
      ),
    );

    _entranceController.forward();
    _navigateToNext();
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
      _entranceController.value = 1;
      _breathingController.stop();
      _loadingController.stop();
      return;
    }

    _entranceController.forward();
    _breathingController.repeat(reverse: true);
    _loadingController.repeat();
  }

  @override
  void dispose() {
    _entranceController.dispose();
    _breathingController.dispose();
    _loadingController.dispose();
    super.dispose();
  }

  Future<void> _navigateToNext() async {
    final startTime = DateTime.now();
    final authProvider = context.read<AuthProvider>();

    while (authProvider.isInitial || authProvider.isLoading) {
      await Future.delayed(const Duration(milliseconds: 100));

      if (!mounted) {
        return;
      }
    }

    final elapsed = DateTime.now().difference(startTime);
    final remaining = _minimumSplashDuration - elapsed;

    if (remaining > Duration.zero) {
      await Future.delayed(remaining);
    }

    if (!mounted) {
      return;
    }

    if (authProvider.isAuthenticated) {
      if (authProvider.hasFarmerProfile) {
        context.go('/dashboard');
      } else {
        context.go('/onboarding');
      }
    } else {
      context.go('/login');
    }
  }

  String _loadingLabel(AuthProvider authProvider) {
    if (authProvider.isInitial || authProvider.isLoading) {
      return 'Restoring your session';
    }

    if (authProvider.isAuthenticated) {
      return 'Welcome back';
    }

    return 'Preparing your experience';
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final textTheme = Theme.of(context).textTheme;
    final loadingLabel = _loadingLabel(authProvider);

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.dark,
        statusBarBrightness: Brightness.light,
        systemNavigationBarColor: AppColors.backgroundLight,
        systemNavigationBarIconBrightness: Brightness.dark,
      ),
      child: Scaffold(
        backgroundColor: AppColors.backgroundLight,
        body: SafeArea(
          child: Stack(
            children: [
              const _SplashBackground(),
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 30),
                  child: AnimatedBuilder(
                    animation: Listenable.merge([
                      _entranceController,
                      _breathingController,
                    ]),
                    builder: (context, child) {
                      final breathing = _reduceMotion
                          ? 1.0
                          : Tween<double>(begin: 0.992, end: 1.008).evaluate(
                              CurvedAnimation(
                                parent: _breathingController,
                                curve: Curves.easeInOut,
                              ),
                            );

                      return Opacity(
                        opacity: _fadeAnimation.value,
                        child: Transform.translate(
                          offset: Offset(0, _contentSlideAnimation.value),
                          child: Transform.scale(
                            scale: _contentScaleAnimation.value,
                            child: Transform.scale(
                              scale: breathing,
                              child: child,
                            ),
                          ),
                        ),
                      );
                    },
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AnimatedBuilder(
                          animation: _entranceController,
                          builder: (context, child) {
                            return Transform.scale(
                              scale: _brandScaleAnimation.value,
                              child: child,
                            );
                          },
                          child: const _SplashBrand(),
                        ),
                        const SizedBox(height: 30),
                        Text(
                          'FarmMate AI',
                          textAlign: TextAlign.center,
                          style: textTheme.displayMedium?.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w700,
                            letterSpacing: -1.0,
                          ),
                        ),
                        const SizedBox(height: 10),
                        ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 280),
                          child: Text(
                            'Smarter decisions, healthier harvests.',
                            textAlign: TextAlign.center,
                            style: textTheme.bodyLarge?.copyWith(
                              color: AppColors.textSecondary,
                              height: 1.45,
                            ),
                          ),
                        ),
                        const SizedBox(height: 52),
                        _SplashLoadingIndicator(
                          controller: _loadingController,
                          reduceMotion: _reduceMotion,
                          label: loadingLabel,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              Positioned(
                left: 0,
                right: 0,
                bottom: 22,
                child: Text(
                  'FARMING • INTELLIGENCE • SIMPLICITY',
                  textAlign: TextAlign.center,
                  style: textTheme.bodySmall?.copyWith(
                    color: AppColors.textHint.withValues(alpha: 0.72),
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.35,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SplashBrand extends StatelessWidget {
  const _SplashBrand();

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 132,
          height: 132,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.primarySurface.withValues(alpha: 0.54),
          ),
        ),
        Container(
          width: 104,
          height: 104,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: AppColors.primaryLight.withValues(alpha: 0.18),
            ),
          ),
        ),
        const AuthBrandMark(size: 88),
      ],
    );
  }
}

class _SplashBackground extends StatelessWidget {
  const _SplashBackground();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: ExcludeSemantics(
        child: Stack(
          children: [
            Positioned(
              top: -170,
              right: -145,
              child: _SplashOrb(
                size: 350,
                color: AppColors.primarySurface.withValues(alpha: 0.7),
              ),
            ),
            Positioned(
              bottom: -210,
              left: -165,
              child: _SplashOrb(
                size: 390,
                color: AppColors.primarySurface.withValues(alpha: 0.48),
              ),
            ),
            Positioned(
              top: 180,
              left: -75,
              child: _SplashOrb(
                size: 150,
                color: AppColors.primaryLight.withValues(alpha: 0.05),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SplashOrb extends StatelessWidget {
  const _SplashOrb({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: [color, color.withValues(alpha: 0)]),
      ),
    );
  }
}

class _SplashLoadingIndicator extends StatelessWidget {
  const _SplashLoadingIndicator({
    required this.controller,
    required this.reduceMotion,
    required this.label,
  });

  final AnimationController controller;
  final bool reduceMotion;
  final String label;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Semantics(
      liveRegion: true,
      label: label,
      child: SizedBox(
        width: 152,
        child: Column(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: AnimatedBuilder(
                animation: controller,
                builder: (context, child) {
                  final progress = reduceMotion
                      ? 0.62
                      : Curves.easeInOut.transform(controller.value);

                  return LinearProgressIndicator(
                    value: progress,
                    minHeight: 3,
                    backgroundColor: AppColors.borderLight.withValues(
                      alpha: 0.72,
                    ),
                    color: AppColors.primary,
                  );
                },
              ),
            ),
            const SizedBox(height: 14),
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 220),
              child: Text(
                label,
                key: ValueKey(label),
                textAlign: TextAlign.center,
                style: textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontSize: 11,
                  fontWeight: FontWeight.w500,
                  letterSpacing: 0.1,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

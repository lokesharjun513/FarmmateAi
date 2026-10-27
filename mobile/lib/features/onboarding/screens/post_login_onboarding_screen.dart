import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../features/weather/location_service.dart';
import '../../auth/providers/auth_provider.dart';
import '../../farm/data/farm_repository.dart';
import '../../farm/data/models/farm_model.dart';
import '../../farm/presentation/widgets/add_farm_form.dart';
import '../../farmer/data/farmer_repository.dart';

class PostLoginOnboardingScreen extends StatefulWidget {
  const PostLoginOnboardingScreen({
    super.key,
    this.locationService,
    this.farmerRepository,
    this.farmRepository,
  });

  final LocationService? locationService;
  final FarmerRepository? farmerRepository;
  final FarmRepository? farmRepository;

  @override
  State<PostLoginOnboardingScreen> createState() =>
      _PostLoginOnboardingScreenState();
}

class _PostLoginOnboardingScreenState extends State<PostLoginOnboardingScreen>
    with SingleTickerProviderStateMixin {
  late final LocationService _locationService;
  late final FarmerRepository _farmerRepository;

  late final AnimationController _animationController;

  int _step = 0;

  String? _selectedLanguage;
  String? _selectedExperience;

  LocationData? _locationData;

  bool _locationLoading = false;
  bool _locationCompleted = false;
  bool _isSubmitting = false;
  String? _locationError;

  final List<String> _languages = const [
    'English',
    'Telugu',
    'Hindi',
    'Tamil',
    'Kannada',
    'Malayalam',
  ];

  final List<_ExperienceOption> _experiences = const [
    _ExperienceOption(
      title: 'Just getting started',
      subtitle: 'I am new to farming',
      icon: Icons.spa_rounded,
      years: 0,
    ),
    _ExperienceOption(
      title: '1–3 years',
      subtitle: 'I am learning and gaining experience',
      icon: Icons.eco_rounded,
      years: 2,
    ),
    _ExperienceOption(
      title: '3–10 years',
      subtitle: 'I have good farming experience',
      icon: Icons.agriculture_rounded,
      years: 6,
    ),
    _ExperienceOption(
      title: '10+ years',
      subtitle: 'I am an experienced farmer',
      icon: Icons.landscape_rounded,
      years: 10,
    ),
  ];

  @override
  void initState() {
    super.initState();

    _locationService = widget.locationService ?? const LocationService();
    _farmerRepository = widget.farmerRepository ?? FarmerRepository();

    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 450),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;

      _animationController.forward();
      _requestLocation();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  // ============================================================
  // LOCATION
  // ============================================================

  Future<void> _requestLocation() async {
    if (_locationLoading || _locationCompleted) {
      return;
    }

    setState(() {
      _locationLoading = true;
      _locationError = null;
    });

    try {
      final location = await _locationService.getCurrentLocation();

      if (!mounted) return;

      _locationData = location;

      if (location != null) {
        debugPrint('--------------------------------');
        debugPrint('FarmMate Onboarding Location');
        debugPrint('Location: ${location.locationName}');
        debugPrint('Latitude: ${location.latitude}');
        debugPrint('Longitude: ${location.longitude}');
        debugPrint('State: ${location.state}');
        debugPrint('District: ${location.district}');
        debugPrint('Mandal: ${location.mandal}');
        debugPrint('Village: ${location.village}');
        debugPrint('--------------------------------');
      }
    } catch (e) {
      if (!mounted) return;

      _locationError = _extractErrorMessage(e);

      debugPrint('Location error: $_locationError');
    }

    if (!mounted) return;

    setState(() {
      _locationLoading = false;
      _locationCompleted = true;
      _step = 1;
    });

    _restartAnimation();
  }

  String _extractErrorMessage(Object error) {
    final message = error.toString().trim();

    if (message.startsWith('Exception: ')) {
      return message.substring('Exception: '.length).trim();
    }

    return message.isEmpty ? 'Unable to detect your location.' : message;
  }

  // ============================================================
  // NEXT
  // ============================================================

  void _next() {
    // ----------------------------------------------------------
    // LANGUAGE
    // ----------------------------------------------------------

    if (_step == 1) {
      if (_selectedLanguage == null) {
        return;
      }

      setState(() {
        _step = 2;
      });

      _restartAnimation();
      return;
    }

    // ----------------------------------------------------------
    // EXPERIENCE
    // ----------------------------------------------------------

    if (_step == 2) {
      if (_selectedExperience == null) {
        return;
      }

      setState(() {
        _step = 3;
      });

      _restartAnimation();
      return;
    }

    // ----------------------------------------------------------
    // FARM SETUP
    // ----------------------------------------------------------

    if (_step == 3) {
      _showFarmChoiceSheet();
    }
  }

  // ============================================================
  // BACK
  // ============================================================

  void _back() {
    if (_step <= 1) {
      return;
    }

    setState(() {
      _step--;
    });

    _restartAnimation();
  }

  // ============================================================
  // ANIMATION
  // ============================================================

  void _restartAnimation() {
    _animationController
      ..reset()
      ..forward();
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final horizontalPadding = constraints.maxWidth < 380 ? 20.0 : 28.0;

            return Padding(
              padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
              child: Column(
                children: [
                  _buildTopBar(),

                  Expanded(
                    child: AnimatedBuilder(
                      animation: _animationController,
                      builder: (context, child) {
                        final animation = CurvedAnimation(
                          parent: _animationController,
                          curve: Curves.easeOutCubic,
                        );

                        return FadeTransition(
                          opacity: animation,
                          child: SlideTransition(
                            position: Tween<Offset>(
                              begin: const Offset(0, 0.025),
                              end: Offset.zero,
                            ).animate(animation),
                            child: child,
                          ),
                        );
                      },
                      child: _buildCurrentStep(),
                    ),
                  ),

                  _buildBottomButton(),

                  const SizedBox(height: 18),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  // ============================================================
  // TOP BAR
  // ============================================================

  Widget _buildTopBar() {
    return SizedBox(
      height: 64,
      child: Row(
        children: [
          if (_step > 1) _buildBackButton() else const SizedBox(width: 44),

          Expanded(
            child: Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: AppColors.primarySurface,
                      borderRadius: BorderRadius.circular(9),
                    ),
                    child: const Icon(
                      Icons.auto_awesome_rounded,
                      color: AppColors.primary,
                      size: 16,
                    ),
                  ),

                  const SizedBox(width: 8),

                  const Text(
                    'FarmMate AI',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.2,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(width: 44),
        ],
      ),
    );
  }

  Widget _buildBackButton() {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: _back,
        borderRadius: BorderRadius.circular(22),
        child: Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: AppColors.surfaceLight,
            shape: BoxShape.circle,
            border: Border.all(
              color: AppColors.borderLight.withValues(alpha: 0.8),
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.06),
                blurRadius: 14,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: const Icon(
            Icons.arrow_back_rounded,
            size: 20,
            color: AppColors.textPrimary,
          ),
        ),
      ),
    );
  }

  // ============================================================
  // CURRENT STEP
  // ============================================================

  Widget _buildCurrentStep() {
    switch (_step) {
      case 0:
        return _buildLocationStep();

      case 1:
        return _buildLanguageStep();

      case 2:
        return _buildExperienceStep();

      case 3:
        return _buildFarmSetupStep();

      case 4:
        return _buildFarmFormStep();

      default:
        return const SizedBox.shrink();
    }
  }

  // ============================================================
  // LOCATION
  // ============================================================

  Widget _buildLocationStep() {
    return Center(
      child: SingleChildScrollView(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildLargeIcon(
              Icons.location_on_rounded,
              AppColors.primarySurface,
            ),

            const SizedBox(height: 28),

            const Text(
              'Let’s get your location',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 26,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.7,
              ),
            ),

            const SizedBox(height: 10),

            const Text(
              'Your location helps FarmMate provide more relevant weather insights and local farming guidance.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 14,
                height: 1.5,
              ),
            ),

            const SizedBox(height: 30),

            if (_locationLoading)
              _buildLocationLoading()
            else if (_locationData != null)
              _buildDetectedLocation(_locationData!)
            else
              _buildLocationUnavailable(),

            const SizedBox(height: 18),

            const Text(
              'You can continue even if location access is unavailable.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textHint,
                fontSize: 11.5,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationLoading() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: const Row(
        children: [
          SizedBox(
            width: 23,
            height: 23,
            child: CircularProgressIndicator(
              strokeWidth: 2.3,
              color: AppColors.primary,
            ),
          ),

          SizedBox(width: 13),

          Expanded(
            child: Text(
              'Finding your location...',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetectedLocation(LocationData location) {
    final parts = <String>[
      if (location.village?.trim().isNotEmpty == true) location.village!.trim(),
      if (location.mandal?.trim().isNotEmpty == true) location.mandal!.trim(),
      if (location.district?.trim().isNotEmpty == true)
        location.district!.trim(),
      if (location.state?.trim().isNotEmpty == true) location.state!.trim(),
    ];

    final displayLocation = parts.isNotEmpty
        ? parts.join(', ')
        : location.locationName;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.18)),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.06),
            blurRadius: 20,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Icon(
              Icons.location_on_rounded,
              color: AppColors.primary,
              size: 23,
            ),
          ),

          const SizedBox(width: 13),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Location detected',
                  style: TextStyle(
                    color: AppColors.primary,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.2,
                  ),
                ),

                const SizedBox(height: 4),

                Text(
                  displayLocation,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w700,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),

          const Icon(
            Icons.check_circle_rounded,
            color: AppColors.primary,
            size: 22,
          ),
        ],
      ),
    );
  }

  Widget _buildLocationUnavailable() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: AppColors.backgroundLight,
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Icon(
              Icons.location_off_rounded,
              color: AppColors.textSecondary,
              size: 22,
            ),
          ),

          const SizedBox(width: 13),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Location unavailable',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),

                const SizedBox(height: 4),

                Text(
                  _locationError ??
                      'You can continue and add your location later.',
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11.5,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // LANGUAGE
  // ============================================================

  Widget _buildLanguageStep() {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 30),

          _buildStepLabel('STEP 1 OF 3'),

          const SizedBox(height: 12),

          const Text(
            'Which language\nfeels natural to you?',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 28,
              fontWeight: FontWeight.w800,
              height: 1.12,
              letterSpacing: -0.8,
            ),
          ),

          const SizedBox(height: 10),

          const Text(
            'FarmMate will use this language when talking with you.',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
              height: 1.4,
            ),
          ),

          const SizedBox(height: 28),

          ..._languages.map(_buildLanguageOption),
        ],
      ),
    );
  }

  Widget _buildLanguageOption(String language) {
    final selected = _selectedLanguage == language;

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedLanguage = language;
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOutCubic,
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        decoration: BoxDecoration(
          color: selected ? AppColors.primarySurface : AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: selected
                ? AppColors.primary.withValues(alpha: 0.50)
                : AppColors.borderLight,
            width: selected ? 1.3 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.primaryDark.withValues(
                alpha: selected ? 0.08 : 0.035,
              ),
              blurRadius: selected ? 18 : 12,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                language,
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 15,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                ),
              ),
            ),

            AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: selected ? AppColors.primary : Colors.transparent,
                border: Border.all(
                  color: selected ? AppColors.primary : AppColors.borderLight,
                  width: 1.5,
                ),
              ),
              child: selected
                  ? const Icon(
                      Icons.check_rounded,
                      size: 15,
                      color: Colors.white,
                    )
                  : null,
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // EXPERIENCE
  // ============================================================

  Widget _buildExperienceStep() {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 30),

          _buildStepLabel('STEP 2 OF 3'),

          const SizedBox(height: 12),

          const Text(
            'Tell me about\nyour farming experience.',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 28,
              fontWeight: FontWeight.w800,
              height: 1.12,
              letterSpacing: -0.8,
            ),
          ),

          const SizedBox(height: 10),

          const Text(
            'This helps me adjust how I guide and explain things to you.',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 14,
              height: 1.4,
            ),
          ),

          const SizedBox(height: 28),

          ..._experiences.map(_buildExperienceOption),
        ],
      ),
    );
  }

  Widget _buildExperienceOption(_ExperienceOption experience) {
    final selected = _selectedExperience == experience.title;

    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedExperience = experience.title;
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOutCubic,
        margin: const EdgeInsets.only(bottom: 11),
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(
          color: selected ? AppColors.primarySurface : AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(19),
          border: Border.all(
            color: selected
                ? AppColors.primary.withValues(alpha: 0.50)
                : AppColors.borderLight,
            width: selected ? 1.3 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.primaryDark.withValues(
                alpha: selected ? 0.08 : 0.035,
              ),
              blurRadius: selected ? 18 : 12,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: selected
                    ? AppColors.primary.withValues(alpha: 0.12)
                    : AppColors.backgroundLight,
                borderRadius: BorderRadius.circular(15),
              ),
              child: Icon(experience.icon, color: AppColors.primary, size: 23),
            ),

            const SizedBox(width: 14),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    experience.title,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),

                  const SizedBox(height: 3),

                  Text(
                    experience.subtitle,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                      height: 1.3,
                    ),
                  ),
                ],
              ),
            ),

            AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: selected
                  ? const Icon(
                      Icons.check_circle_rounded,
                      key: ValueKey('selected'),
                      color: AppColors.primary,
                      size: 23,
                    )
                  : const Icon(
                      Icons.radio_button_unchecked_rounded,
                      key: ValueKey('unselected'),
                      color: AppColors.borderLight,
                      size: 23,
                    ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // FARM SETUP
  // ============================================================

  Widget _buildFarmSetupStep() {
    return Center(
      child: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 12),

            _buildFarmHero(),

            const SizedBox(height: 30),

            const Text(
              'Let’s make FarmMate\ntruly yours.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 29,
                fontWeight: FontWeight.w800,
                height: 1.12,
                letterSpacing: -0.9,
              ),
            ),

            const SizedBox(height: 12),

            const Text(
              'Add your farm and I can give you advice that is specific to your land, crops, soil and local conditions.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 14,
                height: 1.5,
              ),
            ),

            const SizedBox(height: 26),

            _buildPersonalizationCard(),

            const SizedBox(height: 18),

            const Text(
              'You can always add your farm later.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textHint, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFarmFormStep() {
    return AddFarmForm(
      repository: widget.farmRepository,
      initialLocation: _locationData,
      successActionLabel: 'Go to dashboard',
      onContinue: _finishOnboardingWithFarm,
    );
  }

  void _finishOnboardingWithFarm(FarmModel farm) {
    if (!mounted) {
      return;
    }

    context.read<AuthProvider>().markFarmerProfileCreated();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('${farm.farmName} added successfully.'),
        behavior: SnackBarBehavior.floating,
      ),
    );

    context.go('/dashboard');
  }

  Widget _buildFarmHero() {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 150,
          height: 150,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.primary.withValues(alpha: 0.045),
          ),
        ),

        Container(
          width: 112,
          height: 112,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.primarySurface,
            border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.12),
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.10),
                blurRadius: 30,
                offset: const Offset(0, 12),
              ),
            ],
          ),
          child: const Icon(
            Icons.agriculture_rounded,
            color: AppColors.primary,
            size: 52,
          ),
        ),

        Positioned(
          right: 4,
          top: 8,
          child: Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: AppColors.surfaceLight,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: AppColors.primaryDark.withValues(alpha: 0.10),
                  blurRadius: 12,
                ),
              ],
            ),
            child: const Icon(
              Icons.auto_awesome_rounded,
              color: AppColors.primary,
              size: 17,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPersonalizationCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.055),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          _buildBenefitRow(
            icon: Icons.psychology_alt_rounded,
            title: 'Personalized AI guidance',
            subtitle: 'Advice based on your farm.',
          ),

          const SizedBox(height: 14),

          _buildBenefitRow(
            icon: Icons.eco_rounded,
            title: 'Crop-aware support',
            subtitle: 'Better recommendations for your crops.',
          ),

          const SizedBox(height: 14),

          _buildBenefitRow(
            icon: Icons.cloud_rounded,
            title: 'Local farming insights',
            subtitle: 'Weather and conditions that matter to you.',
          ),
        ],
      ),
    );
  }

  Widget _buildBenefitRow({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Row(
      children: [
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: AppColors.primarySurface,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon, color: AppColors.primary, size: 21),
        ),

        const SizedBox(width: 12),

        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w700,
                ),
              ),

              const SizedBox(height: 2),

              Text(
                subtitle,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 11.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ============================================================
  // BOTTOM BUTTON
  // ============================================================

  Widget _buildBottomButton() {
    if (_step == 0) {
      return const SizedBox(height: 52);
    }

    if (_step == 4) {
      return const SizedBox.shrink();
    }

    final enabled =
        !_isSubmitting &&
        (_step == 1
            ? _selectedLanguage != null
            : _step == 2
            ? _selectedExperience != null
            : true);

    return SizedBox(
      width: double.infinity,
      height: 54,
      child: ElevatedButton(
        onPressed: enabled ? _next : null,
        style: ElevatedButton.styleFrom(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(17),
          ),
        ),
        child: _isSubmitting
            ? const SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(
                  strokeWidth: 2.2,
                  color: Colors.white,
                ),
              )
            : const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    'Continue',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800),
                  ),

                  SizedBox(width: 8),

                  Icon(Icons.arrow_forward_rounded, size: 18),
                ],
              ),
      ),
    );
  }

  // ============================================================
  // FARM CHOICE
  // ============================================================

  Future<void> _showFarmChoiceSheet() async {
    final result = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (sheetContext) {
        return _buildFarmChoiceSheet(sheetContext);
      },
    );

    if (!mounted || result == null) return;

    if (result) {
      await _completeOnboarding(showFarmSetupMessage: true);
      return;
    }

    await _openFarmForm();
  }

  Future<void> _openFarmForm() async {
    if (_isSubmitting) return;

    setState(() {
      _isSubmitting = true;
    });

    final saved = await _saveFarmerProfile();

    if (!mounted) return;

    setState(() {
      _isSubmitting = false;

      if (saved) {
        _step = 4;
      }
    });

    if (saved) {
      _restartAnimation();
    }
  }

  Future<void> _completeOnboarding({required bool showFarmSetupMessage}) async {
    if (_isSubmitting) return;

    setState(() {
      _isSubmitting = true;
    });

    final saved = await _saveFarmerProfile();

    if (!mounted) return;

    if (!saved) {
      setState(() {
        _isSubmitting = false;
      });

      return;
    }

    context.read<AuthProvider>().markFarmerProfileCreated();

    if (showFarmSetupMessage) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Profile saved. You can add your farm anytime from your Home dashboard.',
          ),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }

    context.go('/dashboard');
  }

  Future<bool> _saveFarmerProfile() async {
    final language = _selectedLanguage;
    final experienceTitle = _selectedExperience;

    if (language == null || experienceTitle == null) {
      return false;
    }

    final experience = _experiences.firstWhere(
      (option) => option.title == experienceTitle,
    );

    try {
      final existingProfile = await _farmerRepository.getProfile();

      if (existingProfile == null) {
        await _farmerRepository.createProfile(
          preferredLanguage: language,
          experienceYears: experience.years,
        );
      } else {
        await _farmerRepository.updateProfile(
          preferredLanguage: language,
          experienceYears: experience.years,
        );
      }

      return true;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_extractErrorMessage(e)),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }

      return false;
    }
  }

  Widget _buildFarmChoiceSheet(BuildContext sheetContext) {
    return Container(
      padding: const EdgeInsets.fromLTRB(22, 10, 22, 24),
      decoration: const BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 42,
              height: 4,
              decoration: BoxDecoration(
                color: AppColors.borderLight,
                borderRadius: BorderRadius.circular(10),
              ),
            ),

            const SizedBox(height: 24),

            Container(
              width: 62,
              height: 62,
              decoration: const BoxDecoration(
                color: AppColors.primarySurface,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.agriculture_outlined,
                color: AppColors.primary,
                size: 29,
              ),
            ),

            const SizedBox(height: 18),

            const Text(
              'Skip adding your farm?',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 21,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.4,
              ),
            ),

            const SizedBox(height: 9),

            const Text(
              'You can explore FarmMate now. Adding your farm later will unlock more personalized AI guidance.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                height: 1.5,
              ),
            ),

            const SizedBox(height: 22),

            _buildSkipInfo(),

            const SizedBox(height: 22),

            // --------------------------------------------------
            // CONFIRM SKIP
            // --------------------------------------------------
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(sheetContext, true);
                },
                child: const Text(
                  'Yes, Go to Dashboard',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
            ),

            const SizedBox(height: 10),

            // --------------------------------------------------
            // ADD FARM
            // --------------------------------------------------
            SizedBox(
              width: double.infinity,
              height: 50,
              child: OutlinedButton(
                onPressed: () {
                  Navigator.pop(sheetContext, false);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.textPrimary,
                  side: const BorderSide(color: AppColors.borderLight),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text(
                  'Add My Farm',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSkipInfo() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.backgroundLight,
        borderRadius: BorderRadius.circular(17),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline_rounded, color: AppColors.primary, size: 20),

          SizedBox(width: 10),

          Expanded(
            child: Text(
              'Your account will remain active. You can add your farm anytime from your Home dashboard.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 11.5,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // UI HELPERS
  // ============================================================

  Widget _buildStepLabel(String text) {
    return Text(
      text,
      style: const TextStyle(
        color: AppColors.primary,
        fontSize: 10,
        fontWeight: FontWeight.w800,
        letterSpacing: 1.3,
      ),
    );
  }

  Widget _buildLargeIcon(IconData icon, Color background) {
    return Container(
      width: 84,
      height: 84,
      decoration: BoxDecoration(
        color: background,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.08),
            blurRadius: 25,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Icon(icon, size: 39, color: AppColors.primary),
    );
  }
}

// ============================================================
// EXPERIENCE MODEL
// ============================================================

class _ExperienceOption {
  final String title;
  final String subtitle;
  final IconData icon;
  final int years;

  const _ExperienceOption({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.years,
  });
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../../app/theme/app_colors.dart';
import '../../../data/models/dashboard_model.dart';
import '../../../providers/dashboard_provider.dart';

class DashboardTab extends StatefulWidget {
  final bool hasFarmProfile;

  const DashboardTab({super.key, required this.hasFarmProfile});

  @override
  State<DashboardTab> createState() => _DashboardTabState();
}

class _DashboardTabState extends State<DashboardTab>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animationController;

  @override
  void initState() {
    super.initState();

    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;

      _loadDashboard();
      _animationController.forward();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  // ============================================================
  // DASHBOARD
  // ============================================================

  Future<void> _loadDashboard({bool forceRefresh = false}) async {
    if (!mounted) return;

    await context.read<DashboardProvider>().loadDashboard(
      forceRefresh: forceRefresh,
    );
  }

  Future<void> _refresh() async {
    await _loadDashboard(forceRefresh: true);
  }

  // ============================================================
  // BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DashboardProvider>();

    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(child: _buildBody(provider)),
    );
  }

  Widget _buildBody(DashboardProvider provider) {
    if (provider.isLoading && provider.dashboard == null) {
      return _buildLoading();
    }

    if (provider.errorMessage != null && provider.dashboard == null) {
      return _buildError(provider);
    }

    final dashboard = provider.dashboard;

    if (dashboard == null) {
      return _buildEmpty();
    }

    return RefreshIndicator(
      color: AppColors.primary,
      backgroundColor: AppColors.surfaceLight,
      onRefresh: _refresh,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(
          parent: BouncingScrollPhysics(),
        ),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 18, 20, 34),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _animated(0.00, _buildHeader(dashboard)),

                const SizedBox(height: 22),

                _animated(0.08, _buildFarmCard(dashboard.farm)),

                const SizedBox(height: 16),

                _animated(0.16, _buildWeatherCard(dashboard.weather)),

                const SizedBox(height: 16),

                _animated(0.24, _buildAdvisorCard(dashboard.advisor)),

                const SizedBox(height: 28),

                _animated(
                  0.32,
                  _buildSectionTitle('Today at a glance', 'Your farm activity'),
                ),

                const SizedBox(height: 12),

                _animated(0.38, _buildStatsCard(dashboard.stats)),

                const SizedBox(height: 28),

                _animated(0.46, _buildCropSection(dashboard.activeCrop)),

                const SizedBox(height: 24),

                _animated(0.54, _buildAskFarmate(dashboard.askFm)),

                const SizedBox(height: 28),

                _animated(0.62, _buildActivitySection(dashboard.activities)),

                if (provider.isLoading) ...[
                  const SizedBox(height: 20),
                  const Center(
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ],
              ]),
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // PREMIUM ANIMATION
  // ============================================================

  Widget _animated(double begin, Widget child) {
    final animation = CurvedAnimation(
      parent: _animationController,
      curve: Interval(
        begin.clamp(0.0, 0.85),
        (begin + 0.35).clamp(0.0, 1.0),
        curve: Curves.easeOutCubic,
      ),
    );

    return AnimatedBuilder(
      animation: animation,
      child: child,
      builder: (context, child) {
        final value = animation.value;

        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, 18 * (1 - value)),
            child: child,
          ),
        );
      },
    );
  }

  // ============================================================
  // HEADER
  // ============================================================

  Widget _buildHeader(DashboardModel dashboard) {
    final farmerName = dashboard.farmer.fullName.trim().isEmpty
        ? 'Farmer'
        : dashboard.farmer.fullName.trim();

    final greeting = dashboard.greeting.trim().isEmpty
        ? 'Good day'
        : dashboard.greeting.trim();

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                greeting,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),

              const SizedBox(height: 3),

              Text(
                '$farmerName 👋',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.primaryDark,
                  fontSize: 27,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.8,
                ),
              ),

              const SizedBox(height: 5),

              const Text(
                'Here’s what’s happening on your farm today.',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(width: 14),

        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: AppColors.surfaceLight,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.borderLight),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.06),
                blurRadius: 14,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: const Icon(
            Icons.notifications_none_rounded,
            color: AppColors.primaryDark,
            size: 23,
          ),
        ),
      ],
    );
  }

  // ============================================================
  // FARM
  // ============================================================

  Widget _buildFarmCard(FarmDashboard? farm) {
    if (farm == null) {
      return _buildNoFarmCard();
    }

    final farmName = farm.farmName.trim().isEmpty
        ? 'My Farm'
        : farm.farmName.trim();

    final location = farm.displayLocation.trim();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.primaryDark, AppColors.primary],
        ),
        borderRadius: BorderRadius.circular(26),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.18),
            blurRadius: 24,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            right: -35,
            top: -45,
            child: Container(
              width: 145,
              height: 145,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.055),
                shape: BoxShape.circle,
              ),
            ),
          ),

          Positioned(
            right: 35,
            bottom: -65,
            child: Container(
              width: 105,
              height: 105,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.045),
                shape: BoxShape.circle,
              ),
            ),
          ),

          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.13),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(
                      Icons.agriculture_rounded,
                      color: Colors.white,
                      size: 25,
                    ),
                  ),

                  const SizedBox(width: 13),

                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'PRIMARY FARM',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.68),
                            fontSize: 9,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.1,
                          ),
                        ),

                        const SizedBox(height: 4),

                        Text(
                          farmName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              if (location.isNotEmpty) ...[
                const SizedBox(height: 18),

                Row(
                  children: [
                    Icon(
                      Icons.location_on_outlined,
                      color: Colors.white.withValues(alpha: 0.75),
                      size: 17,
                    ),

                    const SizedBox(width: 6),

                    Expanded(
                      child: Text(
                        location,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.84),
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ],

              const SizedBox(height: 18),

              Row(
                children: [
                  _farmInfo(Icons.square_foot_rounded, farm.formattedLandArea),

                  const SizedBox(width: 8),

                  _farmInfo(
                    Icons.landscape_outlined,
                    farm.soilType ?? 'Soil --',
                  ),

                  const SizedBox(width: 8),

                  _farmInfo(
                    Icons.water_drop_outlined,
                    farm.waterSource ?? 'Water --',
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNoFarmCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.agriculture_outlined,
              color: AppColors.primary,
              size: 25,
            ),
          ),

          const SizedBox(width: 13),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Complete your farm profile',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),

                const SizedBox(height: 5),

                Text(
                  widget.hasFarmProfile
                      ? 'Your farm profile is being prepared.'
                      : 'Add your farm details to unlock personalized guidance.',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11.5,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _farmInfo(IconData icon, String text) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 9),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(13),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.white.withValues(alpha: 0.85), size: 14),

            const SizedBox(width: 5),

            Expanded(
              child: Text(
                text,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 9.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // WEATHER
  // ============================================================

  Widget _buildWeatherCard(WeatherDashboard weather) {
    final available = weather.isAvailable;

    return _surfaceCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconContainer(
                available ? Icons.wb_sunny_rounded : Icons.cloud_off_rounded,
              ),

              const SizedBox(width: 12),

              const Expanded(
                child: Text(
                  "Today's Weather",
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),

              if (available)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.primarySurface,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'TODAY',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontSize: 8,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
            ],
          ),

          const SizedBox(height: 18),

          if (!available)
            const Text(
              'Weather information is currently unavailable.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
            )
          else ...[
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${weather.temperature.round()}°',
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontSize: 44,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -2,
                  ),
                ),

                const SizedBox(width: 12),

                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    weather.condition,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 18),

            Row(
              children: [
                _weatherMetric(
                  Icons.water_drop_outlined,
                  '${weather.humidity}%',
                  'Humidity',
                ),

                const SizedBox(width: 10),

                _weatherMetric(
                  Icons.umbrella_outlined,
                  weather.rainProbabilityLabel,
                  'Rain chance',
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _weatherMetric(IconData icon, String value, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.primarySurface.withValues(alpha: 0.48),
          borderRadius: BorderRadius.circular(15),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppColors.primary, size: 19),

            const SizedBox(width: 8),

            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                    ),
                  ),

                  const SizedBox(height: 2),

                  Text(
                    label,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 9.5,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // AI ADVISOR
  // ============================================================

  Widget _buildAdvisorCard(AdvisorDashboard advisor) {
    final hasAdvice = advisor.hasRecommendation;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.aiBubbleBg,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.14)),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 45,
                height: 45,
                decoration: BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(15),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.18),
                      blurRadius: 12,
                      offset: const Offset(0, 5),
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: Colors.white,
                  size: 22,
                ),
              ),

              const SizedBox(width: 12),

              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'FARMATE AI',
                      style: TextStyle(
                        color: AppColors.primaryDark,
                        fontSize: 10,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1,
                      ),
                    ),

                    SizedBox(height: 3),

                    Text(
                      'Your farming advisor',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 10.5,
                      ),
                    ),
                  ],
                ),
              ),

              _priorityBadge(advisor.priority),
            ],
          ),

          const SizedBox(height: 17),

          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.65),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              hasAdvice
                  ? advisor.summary
                  : 'No recommendation is available right now. Start your farming season to receive personalized guidance.',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 12.5,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _priorityBadge(String priority) {
    final value = priority.trim().isEmpty
        ? 'LOW'
        : priority.trim().toUpperCase();

    Color badgeColor = AppColors.primarySurface;
    Color textColor = AppColors.primary;

    if (value == 'HIGH') {
      badgeColor = AppColors.error.withValues(alpha: 0.09);
      textColor = AppColors.error;
    } else if (value == 'MEDIUM') {
      badgeColor = AppColors.warning.withValues(alpha: 0.10);
      textColor = AppColors.warning;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: badgeColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        value,
        style: TextStyle(
          color: textColor,
          fontSize: 8,
          fontWeight: FontWeight.w900,
          letterSpacing: 0.4,
        ),
      ),
    );
  }

  // ============================================================
  // STATS
  // ============================================================

  Widget _buildStatsCard(DashboardStats stats) {
    return Row(
      children: [
        Expanded(
          child: _statCard(
            icon: Icons.today_rounded,
            value: stats.todayTasks,
            label: 'Today',
          ),
        ),

        const SizedBox(width: 10),

        Expanded(
          child: _statCard(
            icon: Icons.pending_actions_rounded,
            value: stats.pendingTasks,
            label: 'Pending',
          ),
        ),

        const SizedBox(width: 10),

        Expanded(
          child: _statCard(
            icon: Icons.check_circle_rounded,
            value: stats.completedTasks,
            label: 'Completed',
          ),
        ),
      ],
    );
  }

  Widget _statCard({
    required IconData icon,
    required int value,
    required String label,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 17, horizontal: 7),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(19),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.025),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: AppColors.primary, size: 18),
          ),

          const SizedBox(height: 9),

          Text(
            '$value',
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),

          const SizedBox(height: 2),

          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 9.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // CROP
  // ============================================================

  Widget _buildCropSection(ActiveCrop? crop) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle(
          'Your crop',
          crop == null ? 'No active crop' : crop.stage,
        ),

        const SizedBox(height: 12),

        crop == null ? _buildNoCropCard() : _buildActiveCropCard(crop),
      ],
    );
  }

  Widget _buildNoCropCard() {
    return _surfaceCard(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          _iconContainer(Icons.grass_rounded),

          const SizedBox(width: 13),

          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'No active crop',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  'Start a crop season to receive crop-specific tasks and AI guidance.',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11.5,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(width: 8),

          const Icon(Icons.chevron_right_rounded, color: AppColors.textHint),
        ],
      ),
    );
  }

  Widget _buildActiveCropCard(ActiveCrop crop) {
    return _surfaceCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 54,
                height: 54,
                decoration: BoxDecoration(
                  color: AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(17),
                ),
                child: const Icon(
                  Icons.grass_rounded,
                  color: AppColors.primary,
                  size: 28,
                ),
              ),

              const SizedBox(width: 14),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      crop.cropName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),

                    if (crop.hasVariety) ...[
                      const SizedBox(height: 3),

                      Text(
                        crop.cropVariety!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11.5,
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              if (crop.hasProgress)
                Text(
                  '${crop.progressPercentage}%',
                  style: const TextStyle(
                    color: AppColors.primary,
                    fontSize: 13,
                    fontWeight: FontWeight.w900,
                  ),
                ),
            ],
          ),

          if (crop.hasProgress) ...[
            const SizedBox(height: 17),

            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: LinearProgressIndicator(
                value: crop.progress,
                minHeight: 7,
                backgroundColor: AppColors.primarySurface,
                color: AppColors.primary,
              ),
            ),
          ],

          const SizedBox(height: 15),

          Row(
            children: [
              Expanded(
                child: _cropMetric(Icons.timeline_rounded, 'Stage', crop.stage),
              ),

              Expanded(
                child: _cropMetric(
                  Icons.calendar_today_outlined,
                  'Age',
                  crop.hasAge ? '${crop.cropAgeDays} days' : '--',
                ),
              ),

              Expanded(
                child: _cropMetric(
                  Icons.schedule_outlined,
                  'Duration',
                  crop.hasDuration
                      ? '${crop.estimatedDurationDays} days'
                      : '--',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _cropMetric(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, color: AppColors.primary, size: 16),

        const SizedBox(width: 5),

        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                ),
              ),

              const SizedBox(height: 2),

              Text(
                label,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 8.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ============================================================
  // ASK FARMATE
  // ============================================================

  Widget _buildAskFarmate(AskFarmateDashboard askFm) {
    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(24),
      child: InkWell(
        onTap: () {
          // Ask FarmMate navigation will be connected later.
        },
        borderRadius: BorderRadius.circular(24),
        child: Ink(
          width: double.infinity,
          padding: const EdgeInsets.all(19),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [AppColors.primaryDark, AppColors.primary],
            ),
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.16),
                blurRadius: 20,
                offset: const Offset(0, 9),
              ),
            ],
          ),
          child: Stack(
            children: [
              Positioned(
                right: -35,
                top: -50,
                child: Container(
                  width: 130,
                  height: 130,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.055),
                    shape: BoxShape.circle,
                  ),
                ),
              ),

              Row(
                children: [
                  Container(
                    width: 49,
                    height: 49,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.13),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(
                      Icons.auto_awesome_rounded,
                      color: Colors.white,
                      size: 24,
                    ),
                  ),

                  const SizedBox(width: 13),

                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Ask FarmMate AI',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.w800,
                          ),
                        ),

                        const SizedBox(height: 4),

                        Text(
                          askFm.activeSession
                              ? 'Continue your farming conversation'
                              : 'Ask anything about your farm',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.76),
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                  ),

                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.11),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.arrow_forward_rounded,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ============================================================
  // ACTIVITIES
  // ============================================================

  Widget _buildActivitySection(List<ActivityDashboard> activities) {
    final visibleActivities = activities.take(5).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionTitle(
          'Recent activity',
          visibleActivities.isEmpty
              ? 'Nothing yet'
              : '${visibleActivities.length} recent',
        ),

        const SizedBox(height: 12),

        if (visibleActivities.isEmpty)
          _buildEmptyActivity()
        else
          ...visibleActivities.asMap().entries.map(
            (entry) => _buildActivityItem(entry.value, entry.key),
          ),
      ],
    );
  }

  Widget _buildActivityItem(ActivityDashboard activity, int index) {
    final title = activity.title.trim().isEmpty
        ? 'Farm activity'
        : activity.title.trim();

    return Container(
      margin: const EdgeInsets.only(bottom: 9),
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: activity.isCompleted
                      ? AppColors.primarySurface
                      : AppColors.primarySurface.withValues(alpha: 0.6),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  activity.isCompleted
                      ? Icons.check_rounded
                      : Icons.schedule_rounded,
                  color: AppColors.primary,
                  size: 19,
                ),
              ),

              if (index < 4 && index < 4)
                Container(
                  width: 1,
                  height: 20,
                  margin: const EdgeInsets.only(top: 5),
                  color: AppColors.borderLight,
                ),
            ],
          ),

          const SizedBox(width: 12),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),

                const SizedBox(height: 6),

                Row(
                  children: [
                    if (activity.activityType.isNotEmpty) ...[
                      Text(
                        activity.displayActivityType,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 10,
                        ),
                      ),

                      const SizedBox(width: 7),

                      Container(
                        width: 3,
                        height: 3,
                        decoration: const BoxDecoration(
                          color: AppColors.textHint,
                          shape: BoxShape.circle,
                        ),
                      ),

                      const SizedBox(width: 7),
                    ],

                    Text(
                      activity.displayStatus,
                      style: TextStyle(
                        color: activity.isCompleted
                            ? AppColors.success
                            : AppColors.textSecondary,
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(width: 6),

          _smallPriority(activity.priority),
        ],
      ),
    );
  }

  Widget _smallPriority(String priority) {
    final value = priority.trim().isEmpty
        ? 'LOW'
        : priority.trim().toUpperCase();

    Color color = AppColors.textHint;

    if (value == 'HIGH') {
      color = AppColors.error;
    } else if (value == 'MEDIUM') {
      color = AppColors.warning;
    } else if (value == 'LOW') {
      color = AppColors.success;
    }

    return Container(
      width: 7,
      height: 7,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }

  Widget _buildEmptyActivity() {
    return _surfaceCard(
      padding: const EdgeInsets.all(22),
      child: Column(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: const BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.history_rounded,
              color: AppColors.primary,
              size: 23,
            ),
          ),

          const SizedBox(height: 11),

          const Text(
            'No recent activity',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 13,
              fontWeight: FontWeight.w800,
            ),
          ),

          const SizedBox(height: 4),

          const Text(
            'Your farming activities will appear here.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary, fontSize: 11),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // SECTION TITLE
  // ============================================================

  Widget _buildSectionTitle(String title, String? subtitle) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Text(
            title,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.3,
            ),
          ),
        ),

        if (subtitle != null && subtitle.isNotEmpty)
          Text(
            subtitle,
            style: const TextStyle(
              color: AppColors.textHint,
              fontSize: 9.5,
              fontWeight: FontWeight.w600,
            ),
          ),
      ],
    );
  }

  // ============================================================
  // COMMON UI
  // ============================================================

  Widget _surfaceCard({
    required Widget child,
    EdgeInsets padding = const EdgeInsets.all(18),
  }) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(23),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.035),
            blurRadius: 15,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: child,
    );
  }

  Widget _iconContainer(IconData icon) {
    return Container(
      width: 45,
      height: 45,
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(15),
      ),
      child: Icon(icon, color: AppColors.primary, size: 23),
    );
  }

  // ============================================================
  // LOADING
  // ============================================================

  Widget _buildLoading() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 76,
            height: 76,
            decoration: const BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
            ),
            child: const Padding(
              padding: EdgeInsets.all(23),
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                color: AppColors.primary,
              ),
            ),
          ),

          const SizedBox(height: 20),

          const Text(
            'Preparing your farm',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 16,
              fontWeight: FontWeight.w800,
            ),
          ),

          const SizedBox(height: 6),

          const Text(
            'Getting your latest farming information...',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // ERROR
  // ============================================================

  Widget _buildError(DashboardProvider provider) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.all(28),
      children: [
        const SizedBox(height: 110),

        Container(
          width: 76,
          height: 76,
          decoration: BoxDecoration(
            color: AppColors.error.withValues(alpha: 0.07),
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.cloud_off_rounded,
            color: AppColors.error,
            size: 34,
          ),
        ),

        const SizedBox(height: 20),

        const Text(
          'Unable to load dashboard',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),

        const SizedBox(height: 8),

        Text(
          provider.errorMessage ?? 'Something went wrong.',
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12.5,
            height: 1.5,
          ),
        ),

        const SizedBox(height: 22),

        ElevatedButton.icon(
          onPressed: provider.isLoading
              ? null
              : () => _loadDashboard(forceRefresh: true),
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Try Again'),
        ),
      ],
    );
  }

  // ============================================================
  // EMPTY
  // ============================================================

  Widget _buildEmpty() {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.all(28),
      children: [
        const SizedBox(height: 120),

        Container(
          width: 76,
          height: 76,
          decoration: const BoxDecoration(
            color: AppColors.primarySurface,
            shape: BoxShape.circle,
          ),
          child: const Icon(
            Icons.agriculture_rounded,
            color: AppColors.primary,
            size: 36,
          ),
        ),

        const SizedBox(height: 20),

        const Text(
          'Welcome to FarmMate AI',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 20,
            fontWeight: FontWeight.w800,
          ),
        ),

        const SizedBox(height: 8),

        const Text(
          'Your personalized farming dashboard will appear here.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12.5,
            height: 1.5,
          ),
        ),

        const SizedBox(height: 22),

        ElevatedButton.icon(
          onPressed: _refresh,
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Load Dashboard'),
        ),
      ],
    );
  }
}

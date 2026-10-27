import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../data/models/dashboard_model.dart';
import '../../providers/dashboard_provider.dart';

class HomeTab extends StatefulWidget {
  const HomeTab({
    super.key,
    this.onOpenProfile,
    this.onOpenFarms,
    this.onFarmCreated,
  });

  final VoidCallback? onOpenProfile;
  final VoidCallback? onOpenFarms;
  final VoidCallback? onFarmCreated;

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  static const double _horizontalPadding = 20;
  static const double _sectionGap = 24;

  Future<void> _refresh() async {
    await context.read<DashboardProvider>().refreshDashboard();
  }

  Future<void> _openAddFarm() async {
    final created = await context.push<bool>('/add-farm');

    if (!mounted || created != true) {
      return;
    }

    final dashboardProvider = context.read<DashboardProvider>();

    await dashboardProvider.refreshDashboard();

    if (!mounted) {
      return;
    }

    widget.onFarmCreated?.call();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          dashboardProvider.hasError
              ? 'Farm added, but the dashboard could not refresh. Pull down to try again.'
              : 'Farm added successfully.',
        ),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _openAskFarmMate() {
    context.push('/ask-fm');
  }

  void _openEditProfile() {
    context.push('/edit-profile');
  }

  @override
  Widget build(BuildContext context) {
    final dashboardProvider = context.watch<DashboardProvider>();
    final dashboard = dashboardProvider.dashboard;

    if (dashboardProvider.isInitialLoading) {
      return const _DashboardLoadingView();
    }

    if (dashboardProvider.hasError && dashboard == null) {
      return _DashboardErrorView(provider: dashboardProvider);
    }

    if (dashboard == null) {
      return _DashboardEmptyView(provider: dashboardProvider);
    }

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: _refresh,
      child: CustomScrollView(
        key: const Key('home_dashboard_scroll'),
        physics: const AlwaysScrollableScrollPhysics(
          parent: BouncingScrollPhysics(),
        ),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(
              _horizontalPadding,
              12,
              _horizontalPadding,
              28,
            ),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _HomeHeader(
                  greeting: dashboard.greeting,
                  fullName: dashboard.farmer.fullName,
                  onOpenProfile: widget.onOpenProfile,
                ),

                if (dashboardProvider.hasError) ...[
                  const SizedBox(height: 16),
                  _StaleDataBanner(
                    provider: dashboardProvider,
                    onRetry: _refresh,
                  ),
                ],

                const SizedBox(height: 20),

                _FarmOverviewCard(
                  farm: dashboard.farm,
                  onAddFarm: _openAddFarm,
                  onViewFarms: widget.onOpenFarms,
                ),

                const SizedBox(height: _sectionGap),

                _WeatherCard(
                  weather: dashboard.weather,
                  isRefreshing: dashboardProvider.isRefreshing,
                  onRefresh: dashboardProvider.refreshDashboard,
                ),

                const SizedBox(height: _sectionGap),

                _AdvisorCard(
                  advisor: dashboard.advisor,
                  hasActiveCrop: dashboard.activeCrop != null,
                  isRefreshing: dashboardProvider.isRefreshing,
                  onRetry: dashboardProvider.refreshDashboard,
                ),

                const SizedBox(height: _sectionGap),

                _CropSection(crop: dashboard.activeCrop),

                const SizedBox(height: _sectionGap),

                _TasksSection(
                  stats: dashboard.stats,
                  activities: dashboard.activities,
                  hasActiveCrop: dashboard.activeCrop != null,
                ),

                const SizedBox(height: _sectionGap),

                _AskFarmMateCard(
                  hasActiveSession: dashboard.askFm.activeSession,
                  onTap: _openAskFarmMate,
                ),

                const SizedBox(height: _sectionGap),

                _QuickActionsSection(
                  provider: dashboardProvider,
                  onEditProfile: _openEditProfile,
                ),

                if (dashboardProvider.lastUpdated != null) ...[
                  const SizedBox(height: 18),
                  _UpdatedLabel(lastUpdated: dashboardProvider.lastUpdated!),
                ],

                const SizedBox(height: 8),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _HomeHeader extends StatelessWidget {
  const _HomeHeader({
    required this.greeting,
    required this.fullName,
    required this.onOpenProfile,
  });

  final String greeting;
  final String fullName;
  final VoidCallback? onOpenProfile;

  @override
  Widget build(BuildContext context) {
    final name = fullName.trim().isEmpty ? 'Farmer' : fullName.trim();
    final firstName = name.split(RegExp(r'\s+')).first;
    final cleanGreeting = greeting.trim().replaceAll(RegExp(r'[!,.]+$'), '');
    final displayGreeting = cleanGreeting.isEmpty ? 'Hello' : cleanGreeting;
    final initials = _initials(name);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _formatDate(DateTime.now()),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.7,
                ),
              ),

              const SizedBox(height: 6),

              Text(
                '$displayGreeting, $firstName',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.primaryDark,
                  fontSize: 23,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.6,
                  height: 1.1,
                ),
              ),

              const SizedBox(height: 4),

              const Text(
                'Your farm at a glance.',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),

        const SizedBox(width: 14),

        _ProfileAvatar(initials: initials, onTap: onOpenProfile),
      ],
    );
  }
}

class _ProfileAvatar extends StatelessWidget {
  const _ProfileAvatar({required this.initials, required this.onTap});

  final String initials;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final avatar = Container(
      width: 46,
      height: 46,
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        shape: BoxShape.circle,
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.16)),
      ),
      alignment: Alignment.center,
      child: Text(
        initials,
        style: const TextStyle(
          color: AppColors.primaryDark,
          fontSize: 14,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.2,
        ),
      ),
    );

    if (onTap == null) {
      return avatar;
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        key: const Key('home_profile_button'),
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: avatar,
      ),
    );
  }
}

class _StaleDataBanner extends StatelessWidget {
  const _StaleDataBanner({required this.provider, required this.onRetry});

  final DashboardProvider provider;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 10, 10),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.20)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.cloud_off_rounded,
            color: AppColors.warning,
            size: 18,
          ),

          const SizedBox(width: 9),

          const Expanded(
            child: Text(
              'Couldn’t refresh. Showing your last loaded dashboard.',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 11.5,
                height: 1.35,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),

          if (provider.isRefreshing)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.warning,
                ),
              ),
            )
          else
            TextButton(
              key: const Key('home_stale_retry_button'),
              onPressed: () {
                onRetry();
              },
              style: TextButton.styleFrom(
                foregroundColor: AppColors.warning,
                minimumSize: const Size(48, 40),
                padding: const EdgeInsets.symmetric(horizontal: 8),
              ),
              child: const Text(
                'Retry',
                style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700),
              ),
            ),
        ],
      ),
    );
  }
}

class _FarmOverviewCard extends StatelessWidget {
  const _FarmOverviewCard({
    required this.farm,
    required this.onAddFarm,
    required this.onViewFarms,
  });

  final FarmDashboard? farm;
  final Future<void> Function() onAddFarm;
  final VoidCallback? onViewFarms;

  @override
  Widget build(BuildContext context) {
    final activeFarm = farm;

    if (activeFarm == null) {
      return _SurfaceCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _IconTile(icon: Icons.agriculture_outlined),

                const SizedBox(width: 12),

                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Your farm is not set up yet',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                        ),
                      ),

                      SizedBox(height: 4),

                      Text(
                        'Add your farm details to receive guidance for your land.',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 14),

            ElevatedButton.icon(
              key: const Key('home_add_farm_button'),
              onPressed: () {
                onAddFarm();
              },
              icon: const Icon(Icons.add_rounded, size: 19),
              label: const Text('Add Farm'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(46),
              ),
            ),
          ],
        ),
      );
    }

    final location = activeFarm.displayLocation.trim().isEmpty
        ? 'Location unavailable'
        : activeFarm.displayLocation.trim();

    final facts = <Widget>[
      if (activeFarm.landArea > 0)
        _FarmFact(
          icon: Icons.square_foot_rounded,
          label: activeFarm.formattedLandArea,
        ),
      if (activeFarm.soilType != null)
        _FarmFact(icon: Icons.layers_outlined, label: activeFarm.soilType!),
      if (activeFarm.waterSource != null)
        _FarmFact(
          icon: Icons.water_drop_outlined,
          label: activeFarm.waterSource!,
        ),
    ];

    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _IconTile(icon: Icons.agriculture_rounded),

              const SizedBox(width: 12),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      activeFarm.farmName.trim().isEmpty
                          ? 'My Farm'
                          : activeFarm.farmName.trim(),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                        height: 1.2,
                      ),
                    ),

                    const SizedBox(height: 5),

                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Padding(
                          padding: EdgeInsets.only(top: 1),
                          child: Icon(
                            Icons.location_on_outlined,
                            color: AppColors.textSecondary,
                            size: 14,
                          ),
                        ),

                        const SizedBox(width: 4),

                        Expanded(
                          child: Text(
                            location,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 11.5,
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),

          if (facts.isNotEmpty) ...[
            const SizedBox(height: 14),

            Wrap(spacing: 7, runSpacing: 7, children: facts),
          ],

          if (onViewFarms != null) ...[
            const SizedBox(height: 14),

            OutlinedButton.icon(
              key: const Key('home_view_farms_button'),
              onPressed: onViewFarms,
              icon: const Icon(Icons.arrow_forward_rounded, size: 18),
              label: const Text('View farms'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(44),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _FarmFact extends StatelessWidget {
  const _FarmFact({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      constraints: const BoxConstraints(maxWidth: 160),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppColors.primary, size: 13),

          const SizedBox(width: 5),

          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 10.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _WeatherCard extends StatelessWidget {
  const _WeatherCard({
    required this.weather,
    required this.isRefreshing,
    required this.onRefresh,
  });

  final WeatherDashboard weather;
  final bool isRefreshing;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    if (!weather.isAvailable) {
      return _SurfaceCard(
        child: Row(
          children: [
            const _IconTile(
              icon: Icons.cloud_off_rounded,
              color: AppColors.textSecondary,
            ),

            const SizedBox(width: 12),

            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Weather unavailable',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                    ),
                  ),

                  SizedBox(height: 3),

                  Text(
                    'Current conditions are not available right now.',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11.5,
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 8),

            IconButton(
              key: const Key('home_weather_refresh_button'),
              onPressed: isRefreshing
                  ? null
                  : () {
                      onRefresh();
                    },
              tooltip: 'Refresh weather',
              icon: isRefreshing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.primary,
                      ),
                    )
                  : const Icon(
                      Icons.refresh_rounded,
                      color: AppColors.primary,
                      size: 21,
                    ),
            ),
          ],
        ),
      );
    }

    final metrics = <Widget>[
      _WeatherMetric(
        icon: Icons.water_drop_outlined,
        label: 'Humidity',
        value: weather.humidityLabel,
      ),
      if (weather.hasRainProbability)
        _WeatherMetric(
          icon: Icons.umbrella_outlined,
          label: 'Rain',
          value: weather.rainProbabilityLabel,
        ),
    ];

    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _IconTile(icon: _weatherIcon(weather.condition)),

              const SizedBox(width: 12),

              const Expanded(
                child: Text(
                  'Weather',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),

              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.surfaceMuted,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Text(
                  'NOW',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 8.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                '${weather.temperature.round()}°',
                style: const TextStyle(
                  color: AppColors.primaryDark,
                  fontSize: 38,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -1.4,
                  height: 1,
                ),
              ),

              const SizedBox(width: 12),

              Expanded(
                child: Text(
                  weather.condition,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    height: 1.25,
                  ),
                ),
              ),
            ],
          ),

          if (metrics.isNotEmpty) ...[
            const SizedBox(height: 14),

            Wrap(spacing: 8, runSpacing: 8, children: metrics),
          ],
        ],
      ),
    );
  }
}

class _WeatherMetric extends StatelessWidget {
  const _WeatherMetric({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(11),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppColors.primary, size: 14),

          const SizedBox(width: 5),

          Text(
            value,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),

          const SizedBox(width: 4),

          Text(
            label,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 10,
            ),
          ),
        ],
      ),
    );
  }
}

class _AdvisorCard extends StatelessWidget {
  const _AdvisorCard({
    required this.advisor,
    required this.hasActiveCrop,
    required this.isRefreshing,
    required this.onRetry,
  });

  final AdvisorDashboard advisor;
  final bool hasActiveCrop;
  final bool isRefreshing;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    final unavailable = !advisor.isAvailable;

    final String title;
    final String summary;

    if (unavailable) {
      title = hasActiveCrop ? 'Advice unavailable' : 'No crop advice yet';
      summary = hasActiveCrop
          ? 'FarmMate AI could not generate advice for your crop right now.'
          : 'Start a crop season to receive crop-specific guidance.';
    } else {
      title = 'FarmMate advice';
      summary = advisor.hasRecommendation
          ? advisor.summary
          : 'No recommendation is available right now.';
    }

    final showPriority = advisor.isAvailable && advisor.hasRecommendation;

    return _SurfaceCard(
      color: AppColors.aiBubbleBg,
      borderColor: AppColors.primary.withValues(alpha: 0.10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _IconTile(
                icon: unavailable
                    ? Icons.auto_awesome_outlined
                    : Icons.auto_awesome_rounded,
              ),

              const SizedBox(width: 12),

              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),

              if (showPriority) ...[
                const SizedBox(width: 8),
                _PriorityPill(priority: advisor.priority),
              ],
            ],
          ),

          const SizedBox(height: 12),

          Text(
            summary,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 12.5,
              height: 1.5,
            ),
          ),

          if (unavailable && hasActiveCrop) ...[
            const SizedBox(height: 8),

            TextButton.icon(
              key: const Key('home_advisor_retry_button'),
              onPressed: isRefreshing
                  ? null
                  : () {
                      onRetry();
                    },
              style: TextButton.styleFrom(
                foregroundColor: AppColors.primary,
                padding: EdgeInsets.zero,
                minimumSize: const Size(48, 40),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              icon: isRefreshing
                  ? const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.primary,
                      ),
                    )
                  : const Icon(Icons.refresh_rounded, size: 16),
              label: Text(
                isRefreshing ? 'Retrying…' : 'Try again',
                style: const TextStyle(
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PriorityPill extends StatelessWidget {
  const _PriorityPill({required this.priority});

  final String priority;

  @override
  Widget build(BuildContext context) {
    final normalized = priority.trim().toUpperCase();
    final Color background;
    final Color foreground;

    switch (normalized) {
      case 'HIGH':
        background = AppColors.warning.withValues(alpha: 0.13);
        foreground = AppColors.warning;
        break;
      case 'MEDIUM':
        background = AppColors.primary.withValues(alpha: 0.10);
        foreground = AppColors.primary;
        break;
      default:
        background = AppColors.surfaceMuted;
        foreground = AppColors.textSecondary;
    }

    final label = normalized.isEmpty
        ? 'Low'
        : normalized[0] + normalized.substring(1).toLowerCase();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: foreground,
          fontSize: 9.5,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _CropSection extends StatelessWidget {
  const _CropSection({required this.crop});

  final ActiveCrop? crop;

  @override
  Widget build(BuildContext context) {
    final activeCrop = crop;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(
          title: 'Active crop',
          trailing: activeCrop != null && activeCrop.hasSeason
              ? _SeasonPill(season: activeCrop.season)
              : null,
        ),

        const SizedBox(height: 10),

        if (activeCrop == null)
          const _SurfaceCard(
            child: Row(
              children: [
                _IconTile(icon: Icons.grass_rounded),

                SizedBox(width: 12),

                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'No active crop',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                        ),
                      ),

                      SizedBox(height: 3),

                      Text(
                        'Crop stage and progress appear when a season is active.',
                        style: TextStyle(
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
          )
        else
          _CropCard(crop: activeCrop),
      ],
    );
  }
}

class _CropCard extends StatelessWidget {
  const _CropCard({required this.crop});

  final ActiveCrop crop;

  @override
  Widget build(BuildContext context) {
    final hasStage = crop.stage.trim().isNotEmpty && crop.stage != 'Unknown';
    final facts = <Widget>[
      if (crop.hasAge)
        _FarmFact(icon: Icons.calendar_today_outlined, label: crop.ageLabel),
      if (crop.hasDuration)
        _FarmFact(icon: Icons.timelapse_rounded, label: crop.durationLabel),
    ];

    return _SurfaceCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _IconTile(icon: Icons.grass_rounded),

              const SizedBox(width: 12),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      crop.cropName.trim().isEmpty ? 'Crop' : crop.cropName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                        height: 1.2,
                      ),
                    ),

                    if (crop.hasVariety) ...[
                      const SizedBox(height: 4),
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

                    if (hasStage) ...[
                      const SizedBox(height: 7),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.primarySurface,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          crop.stage,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.primaryDark,
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),

          if (crop.hasProgress) ...[
            const SizedBox(height: 16),

            Row(
              children: [
                const Text(
                  'Season progress',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),

                const Spacer(),

                Text(
                  '${crop.progressPercentage}%',
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),

            const SizedBox(height: 7),

            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: LinearProgressIndicator(
                value: crop.progress,
                minHeight: 6,
                backgroundColor: AppColors.primarySurface,
                color: AppColors.primary,
              ),
            ),
          ],

          if (facts.isNotEmpty) ...[
            const SizedBox(height: 14),
            Wrap(spacing: 7, runSpacing: 7, children: facts),
          ],
        ],
      ),
    );
  }
}

class _SeasonPill extends StatelessWidget {
  const _SeasonPill({required this.season});

  final String season;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      constraints: const BoxConstraints(maxWidth: 118),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        season,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
          color: AppColors.primaryDark,
          fontSize: 9.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _TasksSection extends StatelessWidget {
  const _TasksSection({
    required this.stats,
    required this.activities,
    required this.hasActiveCrop,
  });

  final DashboardStats stats;
  final List<ActivityDashboard> activities;
  final bool hasActiveCrop;

  @override
  Widget build(BuildContext context) {
    final visibleActivities = activities.take(3).toList();
    final totalActivities = activities.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(
          title: 'Farm tasks',
          subtitle: hasActiveCrop
              ? 'Today’s schedule and active-crop totals.'
              : 'Today’s scheduled activity.',
        ),

        const SizedBox(height: 10),

        _SurfaceCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (hasActiveCrop) ...[
                Row(
                  children: [
                    Expanded(
                      child: _TaskMetric(
                        value: '${stats.todayTasks}',
                        label: 'Today',
                      ),
                    ),
                    const _TaskDivider(),
                    Expanded(
                      child: _TaskMetric(
                        value: '${stats.pendingTasks}',
                        label: 'Crop pending',
                      ),
                    ),
                    const _TaskDivider(),
                    Expanded(
                      child: _TaskMetric(
                        value: '${stats.completedTasks}',
                        label: 'Crop completed',
                      ),
                    ),
                  ],
                ),

                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 14),
                  child: Divider(
                    height: 1,
                    thickness: 0.7,
                    color: AppColors.borderLight,
                  ),
                ),
              ] else ...[
                const SizedBox(height: 2),
              ],

              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Today’s activity',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),

                  if (totalActivities > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceMuted,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        totalActivities > visibleActivities.length
                            ? '${visibleActivities.length} of $totalActivities'
                            : '$totalActivities scheduled',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                ],
              ),

              const SizedBox(height: 10),

              if (visibleActivities.isEmpty)
                const _EmptyActivityRow()
              else
                ...visibleActivities.asMap().entries.map((entry) {
                  final index = entry.key;
                  final activity = entry.value;

                  return Column(
                    children: [
                      if (index > 0)
                        const Divider(
                          height: 17,
                          thickness: 0.7,
                          color: AppColors.borderLight,
                        ),
                      _ActivityRow(activity: activity),
                    ],
                  );
                }),
            ],
          ),
        ),
      ],
    );
  }
}

class _TaskMetric extends StatelessWidget {
  const _TaskMetric({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: AppColors.primaryDark,
            fontSize: 21,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.4,
            height: 1,
          ),
        ),

        const SizedBox(height: 5),

        Text(
          label,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 9.5,
            fontWeight: FontWeight.w600,
            height: 1.25,
          ),
        ),
      ],
    );
  }
}

class _TaskDivider extends StatelessWidget {
  const _TaskDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 0.7,
      height: 32,
      margin: const EdgeInsets.symmetric(horizontal: 8),
      color: AppColors.borderLight,
    );
  }
}

class _EmptyActivityRow extends StatelessWidget {
  const _EmptyActivityRow();

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: [
        Icon(
          Icons.event_available_outlined,
          color: AppColors.textSecondary,
          size: 18,
        ),

        SizedBox(width: 9),

        Expanded(
          child: Text(
            'No activities are scheduled for today.',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11.5,
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}

class _ActivityRow extends StatelessWidget {
  const _ActivityRow({required this.activity});

  final ActivityDashboard activity;

  @override
  Widget build(BuildContext context) {
    final statusColor = activity.isCompleted
        ? AppColors.success
        : activity.isCancelled
        ? AppColors.error
        : AppColors.textSecondary;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: AppColors.primarySurface,
            shape: BoxShape.circle,
          ),
          child: Icon(
            activity.isCompleted ? Icons.check_rounded : Icons.schedule_rounded,
            color: AppColors.primary,
            size: 17,
          ),
        ),

        const SizedBox(width: 10),

        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                activity.title.trim().isEmpty
                    ? 'Farm activity'
                    : activity.title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  height: 1.3,
                ),
              ),

              const SizedBox(height: 4),

              Row(
                children: [
                  if (activity.activityType.trim().isNotEmpty)
                    Expanded(
                      child: Text(
                        activity.displayActivityType,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 10,
                        ),
                      ),
                    ),

                  if (activity.activityType.trim().isNotEmpty)
                    const SizedBox(width: 8),

                  Text(
                    activity.displayStatus,
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 9.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _AskFarmMateCard extends StatelessWidget {
  const _AskFarmMateCard({required this.hasActiveSession, required this.onTap});

  final bool hasActiveSession;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        key: const Key('home_ask_farmmate_button'),
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.16),
                blurRadius: 18,
                offset: const Offset(0, 7),
              ),
            ],
          ),
          child: Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.auto_awesome_rounded,
                  color: Colors.white,
                  size: 22,
                ),
              ),

              const SizedBox(width: 12),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Ask FarmMate',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.1,
                      ),
                    ),

                    const SizedBox(height: 3),

                    Text(
                      hasActiveSession
                          ? 'Continue your conversation with FarmMate AI.'
                          : 'Ask about pests, weather, or crop health.',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.78),
                        fontSize: 11,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 10),

              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.arrow_forward_rounded,
                  color: Colors.white,
                  size: 17,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickActionsSection extends StatelessWidget {
  const _QuickActionsSection({
    required this.provider,
    required this.onEditProfile,
  });

  final DashboardProvider provider;
  final VoidCallback onEditProfile;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionHeader(title: 'Quick actions'),

        const SizedBox(height: 10),

        Row(
          children: [
            Expanded(
              child: _QuickAction(
                key: const Key('home_quick_edit_profile'),
                icon: Icons.person_outline_rounded,
                label: 'Edit profile',
                onTap: onEditProfile,
              ),
            ),

            const SizedBox(width: 10),

            Expanded(
              child: _QuickAction(
                key: const Key('home_quick_refresh'),
                icon: Icons.refresh_rounded,
                label: provider.isRefreshing ? 'Refreshing' : 'Refresh',
                onTap: provider.isRefreshing
                    ? null
                    : () {
                        provider.refreshDashboard();
                      },
                showProgress: provider.isRefreshing,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    super.key,
    required this.icon,
    required this.label,
    required this.onTap,
    this.showProgress = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final bool showProgress;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          height: 84,
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.surfaceLight,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.borderLight),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (showProgress)
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppColors.primary,
                  ),
                )
              else
                Icon(icon, color: AppColors.primary, size: 21),

              const SizedBox(height: 7),

              Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _UpdatedLabel extends StatelessWidget {
  const _UpdatedLabel({required this.lastUpdated});

  final DateTime lastUpdated;

  @override
  Widget build(BuildContext context) {
    final hour = lastUpdated.hour % 12 == 0 ? 12 : lastUpdated.hour % 12;
    final minute = lastUpdated.minute.toString().padLeft(2, '0');
    final period = lastUpdated.hour >= 12 ? 'PM' : 'AM';

    return Center(
      child: Text(
        'Last updated $hour:$minute $period',
        style: const TextStyle(
          color: AppColors.textHint,
          fontSize: 10,
          fontWeight: FontWeight.w500,
          letterSpacing: 0.2,
        ),
      ),
    );
  }
}

class _DashboardLoadingView extends StatelessWidget {
  const _DashboardLoadingView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppColors.primary.withValues(alpha: 0.10),
                ),
              ),
              padding: const EdgeInsets.all(20),
              child: const CircularProgressIndicator(
                strokeWidth: 2.4,
                color: AppColors.primary,
              ),
            ),

            const SizedBox(height: 18),

            const Text(
              'Preparing your dashboard',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w800,
              ),
            ),

            const SizedBox(height: 6),

            const Text(
              'Loading your latest farm information.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _DashboardErrorView extends StatelessWidget {
  const _DashboardErrorView({required this.provider});

  final DashboardProvider provider;

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.fromLTRB(24, 72, 24, 28),
      children: [
        Center(
          child: Container(
            width: 68,
            height: 68,
            decoration: BoxDecoration(
              color: AppColors.error.withValues(alpha: 0.08),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.cloud_off_rounded,
              color: AppColors.error,
              size: 30,
            ),
          ),
        ),

        const SizedBox(height: 18),

        const Text(
          'Dashboard unavailable',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.2,
          ),
        ),

        const SizedBox(height: 7),

        Text(
          provider.errorMessage ?? 'Something went wrong.',
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12.5,
            height: 1.45,
          ),
        ),

        const SizedBox(height: 22),

        ElevatedButton.icon(
          key: const Key('home_dashboard_retry_button'),
          onPressed: provider.isLoading
              ? null
              : () {
                  provider.refreshDashboard();
                },
          icon: const Icon(Icons.refresh_rounded),
          label: Text(provider.isLoading ? 'Retrying…' : 'Try again'),
        ),
      ],
    );
  }
}

class _DashboardEmptyView extends StatelessWidget {
  const _DashboardEmptyView({required this.provider});

  final DashboardProvider provider;

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.fromLTRB(24, 72, 24, 28),
      children: [
        Center(
          child: Container(
            width: 68,
            height: 68,
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
              border: Border.all(
                color: AppColors.primary.withValues(alpha: 0.10),
              ),
            ),
            child: const Icon(
              Icons.agriculture_rounded,
              color: AppColors.primary,
              size: 30,
            ),
          ),
        ),

        const SizedBox(height: 18),

        const Text(
          'Welcome to FarmMate AI',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.2,
          ),
        ),

        const SizedBox(height: 7),

        const Text(
          'Load your dashboard to see your farm, weather and crop guidance.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12.5,
            height: 1.45,
          ),
        ),

        const SizedBox(height: 22),

        ElevatedButton(
          key: const Key('home_dashboard_load_button'),
          onPressed: provider.isLoading
              ? null
              : () {
                  provider.refreshDashboard();
                },
          child: const Text('Load dashboard'),
        ),
      ],
    );
  }
}

class _SurfaceCard extends StatelessWidget {
  const _SurfaceCard({
    required this.child,
    this.color = AppColors.surfaceLight,
    this.borderColor = AppColors.borderLight,
  });

  final Widget child;
  final Color color;
  final Color borderColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: borderColor),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.035),
            blurRadius: 14,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _IconTile extends StatelessWidget {
  const _IconTile({required this.icon, this.color = AppColors.primary});

  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 44,
      height: 44,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Icon(icon, color: color, size: 21),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, this.subtitle, this.trailing});

  final String title;
  final String? subtitle;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.3,
                  height: 1.2,
                ),
              ),

              if (subtitle != null) ...[
                const SizedBox(height: 3),
                Text(
                  subtitle!,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                    height: 1.35,
                  ),
                ),
              ],
            ],
          ),
        ),

        if (trailing != null) ...[
          const SizedBox(width: 10),
          Padding(padding: const EdgeInsets.only(top: 1), child: trailing),
        ],
      ],
    );
  }
}

String _initials(String name) {
  final parts = name
      .trim()
      .split(RegExp(r'\s+'))
      .where((part) => part.isNotEmpty)
      .toList();

  if (parts.isEmpty) {
    return 'F';
  }

  if (parts.length == 1) {
    return parts.first.substring(0, 1).toUpperCase();
  }

  return '${parts.first.substring(0, 1)}${parts.last.substring(0, 1)}'
      .toUpperCase();
}

String _formatDate(DateTime date) {
  const weekdays = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
  ];
  const months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];

  return '${weekdays[date.weekday - 1]}, ${date.day} ${months[date.month - 1]}'
      .toUpperCase();
}

IconData _weatherIcon(String condition) {
  final value = condition.toLowerCase();

  if (value.contains('thunder') || value.contains('storm')) {
    return Icons.thunderstorm_rounded;
  }

  if (value.contains('snow')) {
    return Icons.ac_unit_rounded;
  }

  if (value.contains('rain') ||
      value.contains('drizzle') ||
      value.contains('shower')) {
    return Icons.water_drop_rounded;
  }

  if (value.contains('fog') ||
      value.contains('mist') ||
      value.contains('haze')) {
    return Icons.foggy;
  }

  if (value.contains('cloud') || value.contains('overcast')) {
    return Icons.cloud_rounded;
  }

  if (value.contains('clear') || value.contains('sun')) {
    return Icons.wb_sunny_rounded;
  }

  return Icons.wb_cloudy_rounded;
}

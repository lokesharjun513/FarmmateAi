import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../data/models/dashboard_model.dart';
import '../../providers/dashboard_provider.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  // ============================================================
  // LIFECYCLE
  // ============================================================

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;

      _loadDashboard();
    });
  }

  // ============================================================
  // DASHBOARD ACTIONS
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

  // ============================================================
  // BODY
  // ============================================================

  Widget _buildBody(DashboardProvider provider) {
    // ----------------------------------------------------------
    // INITIAL LOADING
    // ----------------------------------------------------------

    if (provider.isLoading && !provider.hasDashboard) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.primary),
      );
    }

    // ----------------------------------------------------------
    // ERROR WITHOUT EXISTING DATA
    // ----------------------------------------------------------

    if (provider.hasError && !provider.hasDashboard) {
      return _buildError(provider);
    }

    // ----------------------------------------------------------
    // NO DASHBOARD
    // ----------------------------------------------------------

    final dashboard = provider.dashboard;

    if (dashboard == null) {
      return _buildEmpty();
    }

    // ----------------------------------------------------------
    // DASHBOARD CONTENT
    // ----------------------------------------------------------

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: _refresh,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(
          parent: BouncingScrollPhysics(),
        ),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // ------------------------------------------------
                // GREETING
                // ------------------------------------------------
                _buildGreeting(dashboard),

                const SizedBox(height: 22),

                // ------------------------------------------------
                // FARM
                // ------------------------------------------------
                if (dashboard.farm != null)
                  _buildFarmCard(dashboard.farm!)
                else
                  _buildNoFarmCard(),

                const SizedBox(height: 18),

                // ------------------------------------------------
                // WEATHER
                // ------------------------------------------------
                _buildWeatherCard(dashboard.weather),

                const SizedBox(height: 18),

                // ------------------------------------------------
                // ADVISOR
                // ------------------------------------------------
                _buildAdvisorCard(dashboard.advisor),

                const SizedBox(height: 22),

                // ------------------------------------------------
                // TODAY
                // ------------------------------------------------
                _buildSectionTitle('Today'),

                const SizedBox(height: 12),

                _buildStats(dashboard.stats),

                const SizedBox(height: 18),

                // ------------------------------------------------
                // ACTIVE CROP
                // ------------------------------------------------
                _buildCropCard(dashboard.activeCrop),

                const SizedBox(height: 22),

                // ------------------------------------------------
                // RECENT ACTIVITY
                // ------------------------------------------------
                _buildSectionTitle('Recent Activity'),

                const SizedBox(height: 12),

                _buildActivities(dashboard.activities),

                const SizedBox(height: 22),

                // ------------------------------------------------
                // ASK FARMATE
                // ------------------------------------------------
                _buildAskFarmate(dashboard.askFm),

                // ------------------------------------------------
                // BACKGROUND REFRESH
                // ------------------------------------------------
                if (provider.isLoading) ...[
                  const SizedBox(height: 18),

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
  // GREETING
  // ============================================================

  Widget _buildGreeting(DashboardModel dashboard) {
    final farmerName = dashboard.farmer.fullName.trim().isEmpty
        ? 'Farmer'
        : dashboard.farmer.fullName.trim();

    final greeting = dashboard.greeting.trim().isEmpty
        ? 'Hello'
        : dashboard.greeting.trim();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          greeting,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),

        const SizedBox(height: 4),

        Text(
          '$farmerName 👋',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            color: AppColors.primaryDark,
            fontSize: 28,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.7,
          ),
        ),

        const SizedBox(height: 5),

        const Text(
          'Here’s what’s happening on your farm today.',
          style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
        ),
      ],
    );
  }

  // ============================================================
  // FARM
  // ============================================================

  Widget _buildFarmCard(FarmDashboard farm) {
    final location = [farm.village, farm.mandal, farm.district]
        .map((value) => value.trim())
        .where((value) => value.isNotEmpty)
        .join(', ');

    final farmName = farm.farmName.trim().isEmpty
        ? 'My Farm'
        : farm.farmName.trim();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primaryDark, AppColors.primary],
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.15),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.agriculture_rounded,
                  color: Colors.white,
                  size: 24,
                ),
              ),

              const SizedBox(width: 12),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Your Farm',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),

                    const SizedBox(height: 2),

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
            const SizedBox(height: 16),

            Row(
              children: [
                const Icon(
                  Icons.location_on_outlined,
                  color: Colors.white70,
                  size: 17,
                ),

                const SizedBox(width: 6),

                Expanded(
                  child: Text(
                    location,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ),
              ],
            ),
          ],

          const SizedBox(height: 16),

          Row(
            children: [
              _farmInfo(
                Icons.square_foot_rounded,
                '${_formatNumber(farm.landArea)} ${farm.landUnit}',
              ),

              const SizedBox(width: 10),

              _farmInfo(Icons.landscape_outlined, farm.soilType ?? 'Soil --'),

              const SizedBox(width: 10),

              _farmInfo(
                Icons.water_drop_outlined,
                farm.waterSource ?? 'Water --',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNoFarmCard() {
    return _card(
      child: Row(
        children: [
          _iconBox(Icons.agriculture_outlined),

          const SizedBox(width: 12),

          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'No Farm Profile',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),

                SizedBox(height: 5),

                Text(
                  'Add your farm details to receive personalized farming guidance.',
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
    );
  }

  Widget _farmInfo(IconData icon, String text) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 9),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.white, size: 15),

            const SizedBox(width: 5),

            Expanded(
              child: Text(
                text,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w600,
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
    final unavailable = !weather.isAvailable;

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconBox(
                unavailable
                    ? Icons.cloud_off_outlined
                    : Icons.wb_sunny_outlined,
              ),

              const SizedBox(width: 12),

              const Expanded(
                child: Text(
                  'Today’s Weather',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 18),

          if (unavailable)
            const Text(
              'Weather information is currently unavailable.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            )
          else
            Row(
              children: [
                Text(
                  '${weather.temperature.toStringAsFixed(0)}°',
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontSize: 36,
                    fontWeight: FontWeight.w800,
                  ),
                ),

                const SizedBox(width: 12),

                Expanded(
                  child: Text(
                    weather.condition,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),

          if (!unavailable) ...[
            const SizedBox(height: 16),

            Row(
              children: [
                _weatherInfo(
                  Icons.water_drop_outlined,
                  '${weather.humidity.toStringAsFixed(0)}%',
                  'Humidity',
                ),

                const SizedBox(width: 12),

                _weatherInfo(
                  Icons.umbrella_outlined,
                  weather.rainProbability == null
                      ? '--'
                      : '${weather.rainProbability!.toStringAsFixed(0)}%',
                  'Rain',
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _weatherInfo(IconData icon, String value, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.primarySurface.withValues(alpha: 0.45),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Row(
          children: [
            Icon(icon, color: AppColors.primary, size: 18),

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

                  Text(
                    label,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 10,
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
  // ADVISOR
  // ============================================================

  Widget _buildAdvisorCard(AdvisorDashboard advisor) {
    final summary = advisor.hasRecommendation
        ? advisor.summary
        : 'No recommendation is available right now.';

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _iconBox(Icons.auto_awesome_rounded),

              const SizedBox(width: 12),

              const Expanded(
                child: Text(
                  'FarmMate AI',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),

              _priorityBadge(advisor.priority),
            ],
          ),

          const SizedBox(height: 16),

          Text(
            summary,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
              height: 1.5,
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

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        value,
        style: const TextStyle(
          color: AppColors.primary,
          fontSize: 9,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }

  // ============================================================
  // STATS
  // ============================================================

  Widget _buildStats(DashboardStats stats) {
    return Row(
      children: [
        _statCard('Today', stats.todayTasks, Icons.today_outlined),

        const SizedBox(width: 10),

        _statCard(
          'Pending',
          stats.pendingTasks,
          Icons.pending_actions_outlined,
        ),

        const SizedBox(width: 10),

        _statCard(
          'Done',
          stats.completedTasks,
          Icons.check_circle_outline_rounded,
        ),
      ],
    );
  }

  Widget _statCard(String label, int value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
        decoration: BoxDecoration(
          color: AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.borderLight),
        ),
        child: Column(
          children: [
            Icon(icon, color: AppColors.primary, size: 21),

            const SizedBox(height: 7),

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
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ============================================================
  // CROP
  // ============================================================

  Widget _buildCropCard(ActiveCrop? crop) {
    return _card(
      child: crop == null
          ? Row(
              children: [
                _iconBox(Icons.eco_outlined),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Active Crop',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      SizedBox(height: 5),
                      Text(
                        'No active crop yet. Start a crop season to receive personalized farming tasks.',
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
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _iconBox(Icons.eco_rounded),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Text(
                        'Active Crop',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 14),

                Text(
                  crop.cropName,
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                  ),
                ),

                if (crop.hasVariety) ...[
                  const SizedBox(height: 3),
                  Text(
                    crop.cropVariety!,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                ],

                if (crop.stage.trim().isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Stage: ${crop.stage}',
                    style: const TextStyle(
                      color: AppColors.primary,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ],
            ),
    );
  }

  // ============================================================
  // ACTIVITIES
  // ============================================================

  Widget _buildActivities(List<ActivityDashboard> activities) {
    if (activities.isEmpty) {
      return _card(
        child: const Row(
          children: [
            Icon(
              Icons.history_rounded,
              color: AppColors.textSecondary,
              size: 24,
            ),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                'No recent farm activities yet.',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
              ),
            ),
          ],
        ),
      );
    }

    final visibleActivities = activities.take(5).toList();

    return Column(
      children: visibleActivities.map((activity) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _card(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _iconBox(
                  activity.isCompleted
                      ? Icons.check_rounded
                      : Icons.schedule_rounded,
                ),

                const SizedBox(width: 12),

                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        activity.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),

                      const SizedBox(height: 5),

                      Row(
                        children: [
                          if (activity.activityType.isNotEmpty)
                            Expanded(
                              child: Text(
                                activity.displayActivityType,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 11,
                                ),
                              ),
                            ),

                          const SizedBox(width: 8),

                          Text(
                            activity.displayStatus,
                            style: TextStyle(
                              color: activity.isCompleted
                                  ? AppColors.primary
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
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  // ============================================================
  // ASK FARMATE
  // ============================================================

  Widget _buildAskFarmate(AskFarmateDashboard askFm) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primaryDark, AppColors.primary],
        ),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(
              Icons.chat_bubble_outline_rounded,
              color: Colors.white,
            ),
          ),

          const SizedBox(width: 12),

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
                      ? 'Continue your conversation.'
                      : 'Ask anything about your farm.',
                  style: const TextStyle(color: Colors.white70, fontSize: 11),
                ),
              ],
            ),
          ),

          const Icon(Icons.arrow_forward_rounded, color: Colors.white),
        ],
      ),
    );
  }

  // ============================================================
  // COMMON CARD
  // ============================================================

  Widget _card({required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
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

  // ============================================================
  // ICON BOX
  // ============================================================

  Widget _iconBox(IconData icon) {
    return Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(13),
      ),
      child: Icon(icon, color: AppColors.primary, size: 21),
    );
  }

  // ============================================================
  // SECTION TITLE
  // ============================================================

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        color: AppColors.primaryDark,
        fontSize: 18,
        fontWeight: FontWeight.w800,
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
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 100),

        const Icon(Icons.cloud_off_rounded, color: AppColors.primary, size: 42),

        const SizedBox(height: 16),

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
            fontSize: 13,
            height: 1.4,
          ),
        ),

        const SizedBox(height: 18),

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
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 120),

        const Icon(
          Icons.dashboard_outlined,
          color: AppColors.primary,
          size: 44,
        ),

        const SizedBox(height: 16),

        const Text(
          'Dashboard unavailable',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),

        const SizedBox(height: 8),

        const Text(
          'No dashboard information is available for your account.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 13,
            height: 1.4,
          ),
        ),

        const SizedBox(height: 18),

        ElevatedButton.icon(
          onPressed: () => _loadDashboard(forceRefresh: true),
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Load Dashboard'),
        ),
      ],
    );
  }

  // ============================================================
  // HELPERS
  // ============================================================

  String _formatNumber(double value) {
    if (value == value.roundToDouble()) {
      return value.toInt().toString();
    }

    return value.toStringAsFixed(1);
  }
}

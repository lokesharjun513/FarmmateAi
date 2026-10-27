import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../data/models/farm_model.dart';
import '../../providers/farm_provider.dart';
import '../widgets/add_farm_sheet.dart';

class FarmTab extends StatefulWidget {
  const FarmTab({super.key, this.onFarmCreated, this.onPrimaryChanged});

  final ValueChanged<FarmModel>? onFarmCreated;
  final ValueChanged<FarmModel>? onPrimaryChanged;

  @override
  State<FarmTab> createState() => _FarmTabState();
}

class _FarmTabState extends State<FarmTab> {
  static const double _horizontalPadding = 20;

  final Set<String> _expandedFarmIds = {};

  Future<void> _refresh() async {
    await context.read<FarmProvider>().refreshFarms();
  }

  void _handleFarmCreated(FarmModel farm) {
    if (!mounted) {
      return;
    }

    setState(() {
      _expandedFarmIds.add(farm.id);
    });

    widget.onFarmCreated?.call(farm);
  }

  Future<void> _openAddFarm() async {
    final provider = context.read<FarmProvider>();

    if (!provider.canCreateFarm) {
      return;
    }

    final createdFarm = await showAddFarmSheet(
      context,
      provider: provider,
      onCreated: _handleFarmCreated,
    );

    if (!mounted || createdFarm == null) {
      return;
    }

    setState(() {
      _expandedFarmIds.add(createdFarm.id);
    });
  }

  void _toggleFarm(String farmId) {
    setState(() {
      if (!_expandedFarmIds.add(farmId)) {
        _expandedFarmIds.remove(farmId);
      }
    });
  }

  Future<void> _setPrimary(FarmModel farm) async {
    final provider = context.read<FarmProvider>();

    try {
      final primaryFarm = await provider.setPrimary(farm.id);

      if (!mounted) {
        return;
      }

      widget.onPrimaryChanged?.call(primaryFarm);

      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text('${primaryFarm.farmName} is now your primary farm.'),
            behavior: SnackBarBehavior.floating,
          ),
        );
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(_cleanError(error)),
            behavior: SnackBarBehavior.floating,
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<FarmProvider>();

    if (provider.hasError && !provider.hasLoaded) {
      return _FarmErrorView(
        message: provider.errorMessage,
        isRetrying: provider.isLoading,
        onRetry: () {
          provider.refreshFarms();
        },
      );
    }

    if (!provider.hasLoaded) {
      return const _FarmLoadingView();
    }

    if (provider.isEmpty) {
      return _FarmEmptyView(
        provider: provider,
        onRefresh: _refresh,
        onAddFarm: _openAddFarm,
      );
    }

    return _FarmPortfolioView(
      provider: provider,
      expandedFarmIds: _expandedFarmIds,
      onRefresh: _refresh,
      onAddFarm: _openAddFarm,
      onToggleFarm: _toggleFarm,
      onSetPrimary: _setPrimary,
    );
  }
}

class _FarmPortfolioView extends StatelessWidget {
  const _FarmPortfolioView({
    required this.provider,
    required this.expandedFarmIds,
    required this.onRefresh,
    required this.onAddFarm,
    required this.onToggleFarm,
    required this.onSetPrimary,
  });

  final FarmProvider provider;
  final Set<String> expandedFarmIds;
  final Future<void> Function() onRefresh;
  final VoidCallback onAddFarm;
  final ValueChanged<String> onToggleFarm;
  final ValueChanged<FarmModel> onSetPrimary;

  @override
  Widget build(BuildContext context) {
    final farms = provider.farms;
    final primaryFarm = _primaryFarm(farms);

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: onRefresh,
      child: CustomScrollView(
        key: const Key('farm_tab_scroll'),
        physics: const AlwaysScrollableScrollPhysics(
          parent: BouncingScrollPhysics(),
        ),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(
              _FarmTabState._horizontalPadding,
              14,
              _FarmTabState._horizontalPadding,
              30,
            ),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _FarmHeader(
                  canAddFarm: provider.canCreateFarm,
                  onAddFarm: onAddFarm,
                ),

                if (provider.hasError) ...[
                  const SizedBox(height: 14),
                  _FarmStaleBanner(
                    isRefreshing: provider.isRefreshing,
                    onRetry: () {
                      provider.refreshFarms();
                    },
                  ),
                ],

                const SizedBox(height: 18),

                _FarmPortfolioSummary(farms: farms, primaryFarm: primaryFarm),

                const SizedBox(height: 22),

                Row(
                  children: [
                    const Expanded(
                      child: Text(
                        'Your farms',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.3,
                        ),
                      ),
                    ),
                    if (provider.isRefreshing)
                      const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: AppColors.primary,
                        ),
                      ),
                  ],
                ),

                const SizedBox(height: 10),

                ...farms.map((farm) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 11),
                    child: _FarmCard(
                      farm: farm,
                      expanded: expandedFarmIds.contains(farm.id),
                      isSettingPrimary: provider.isSettingPrimaryFor(farm.id),
                      onToggle: () {
                        onToggleFarm(farm.id);
                      },
                      onSetPrimary: () {
                        onSetPrimary(farm);
                      },
                    ),
                  );
                }),

                const SizedBox(height: 8),

                _FarmFooter(provider: provider),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _FarmHeader extends StatelessWidget {
  const _FarmHeader({required this.canAddFarm, required this.onAddFarm});

  final bool canAddFarm;
  final VoidCallback onAddFarm;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'My farms',
                    style: TextStyle(
                      color: AppColors.primaryDark,
                      fontSize: 26,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.7,
                      height: 1.1,
                    ),
                  ),
                  SizedBox(height: 5),
                  Text(
                    'Your land, water and farm profile in one place.',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            _AddFarmButton(
              key: const Key('farm_tab_add_button'),
              enabled: canAddFarm,
              onTap: onAddFarm,
            ),
          ],
        ),
      ],
    );
  }
}

class _AddFarmButton extends StatelessWidget {
  const _AddFarmButton({super.key, required this.enabled, required this.onTap});

  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: enabled ? onTap : null,
      icon: const Icon(Icons.add_rounded, size: 18),
      label: const Text('Add farm'),
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(0, 44),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    );
  }
}

class _FarmPortfolioSummary extends StatelessWidget {
  const _FarmPortfolioSummary({required this.farms, required this.primaryFarm});

  final List<FarmModel> farms;
  final FarmModel? primaryFarm;

  @override
  Widget build(BuildContext context) {
    final landTotals = _landTotals(farms);
    final primaryName = primaryFarm?.farmName.trim() ?? '';
    final metrics = <Widget>[
      _SummaryMetric(
        icon: Icons.agriculture_rounded,
        value: '${farms.length}',
        label: farms.length == 1 ? 'Farm' : 'Farms',
      ),
      ...landTotals.map(
        (total) => _SummaryMetric(
          icon: Icons.square_foot_rounded,
          value: _formatNumber(total.area),
          label: total.unit,
        ),
      ),
    ];

    return Container(
      key: const Key('farm_portfolio_summary'),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.primaryDark,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.18),
            blurRadius: 22,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.11),
                  borderRadius: BorderRadius.circular(13),
                ),
                child: const Icon(
                  Icons.landscape_rounded,
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
                      'Farm portfolio',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.2,
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'A quick view of all your registered land.',
                      style: TextStyle(
                        color: Color(0xFFC7D8CB),
                        fontSize: 11,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          if (primaryName.isNotEmpty) ...[
            const SizedBox(height: 13),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.star_rounded,
                    color: AppColors.accentAmber,
                    size: 14,
                  ),
                  const SizedBox(width: 5),
                  Flexible(
                    child: Text(
                      'Primary · $primaryName',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 16),

          Wrap(spacing: 8, runSpacing: 8, children: metrics),
        ],
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    required this.icon,
    required this.value,
    required this.label,
  });

  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 190),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: const Color(0xFFD8E9DC), size: 14),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 4),
          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Color(0xFFC7D8CB),
                fontSize: 10,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FarmCard extends StatelessWidget {
  const _FarmCard({
    required this.farm,
    required this.expanded,
    required this.isSettingPrimary,
    required this.onToggle,
    required this.onSetPrimary,
  });

  final FarmModel farm;
  final bool expanded;
  final bool isSettingPrimary;
  final VoidCallback onToggle;
  final VoidCallback onSetPrimary;

  @override
  Widget build(BuildContext context) {
    final location = farm.locationLabel.trim();
    final details = _farmDetails(farm);

    return Container(
      key: Key('farm_card_${farm.id}'),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(
          color: farm.isPrimary
              ? AppColors.primary.withValues(alpha: 0.30)
              : AppColors.borderLight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              key: Key('farm_card_toggle_${farm.id}'),
              onTap: onToggle,
              borderRadius: BorderRadius.circular(22),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(
                        color: AppColors.primarySurface,
                        borderRadius: BorderRadius.circular(15),
                      ),
                      child: const Icon(
                        Icons.agriculture_rounded,
                        color: AppColors.primary,
                        size: 23,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Text(
                                  farm.farmName.trim().isEmpty
                                      ? 'My Farm'
                                      : farm.farmName.trim(),
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
                              ),
                              if (farm.isPrimary) ...[
                                const SizedBox(width: 8),
                                const _PrimaryBadge(),
                              ],
                            ],
                          ),
                          if (location.isNotEmpty) ...[
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
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    AnimatedRotation(
                      turns: expanded ? 0.5 : 0,
                      duration: const Duration(milliseconds: 220),
                      curve: Curves.easeOutCubic,
                      child: const Icon(
                        Icons.keyboard_arrow_down_rounded,
                        color: AppColors.textSecondary,
                        size: 24,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          AnimatedSize(
            duration: const Duration(milliseconds: 240),
            curve: Curves.easeOutCubic,
            alignment: Alignment.topCenter,
            child: expanded
                ? Container(
                    key: Key('farm_card_details_${farm.id}'),
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: Column(
                      children: [
                        const Divider(
                          height: 1,
                          thickness: 0.7,
                          color: AppColors.borderLight,
                        ),
                        const SizedBox(height: 13),
                        ...details,
                        if (!farm.isPrimary) ...[
                          const SizedBox(height: 2),
                          SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              key: Key('farm_set_primary_${farm.id}'),
                              onPressed: isSettingPrimary ? null : onSetPrimary,
                              icon: isSettingPrimary
                                  ? const SizedBox(
                                      width: 15,
                                      height: 15,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                        color: AppColors.primary,
                                      ),
                                    )
                                  : const Icon(
                                      Icons.star_outline_rounded,
                                      size: 18,
                                    ),
                              label: Text(
                                isSettingPrimary
                                    ? 'Setting as primary…'
                                    : 'Set as primary',
                              ),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: AppColors.primary,
                                minimumSize: const Size(0, 44),
                                side: BorderSide(
                                  color: AppColors.primary.withValues(
                                    alpha: 0.28,
                                  ),
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(13),
                                ),
                                textStyle: const TextStyle(
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ),
                        ],
                        const SizedBox(height: 10),
                        const Row(
                          children: [
                            Icon(
                              Icons.visibility_outlined,
                              color: AppColors.textHint,
                              size: 14,
                            ),
                            SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                'Farm details are view-only.',
                                style: TextStyle(
                                  color: AppColors.textHint,
                                  fontSize: 10.5,
                                  height: 1.35,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  )
                : const SizedBox(width: double.infinity),
          ),
        ],
      ),
    );
  }
}

class _PrimaryBadge extends StatelessWidget {
  const _PrimaryBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.star_rounded, color: AppColors.primary, size: 12),
          SizedBox(width: 3),
          Text(
            'Primary',
            style: TextStyle(
              color: AppColors.primaryDark,
              fontSize: 9,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _FarmDetailRow extends StatelessWidget {
  const _FarmDetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 30,
            height: 30,
            decoration: BoxDecoration(
              color: AppColors.surfaceMuted,
              borderRadius: BorderRadius.circular(9),
            ),
            child: Icon(icon, color: AppColors.primary, size: 15),
          ),
          const SizedBox(width: 9),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.textHint,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
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
}

class _FarmStaleBanner extends StatelessWidget {
  const _FarmStaleBanner({required this.isRefreshing, required this.onRetry});

  final bool isRefreshing;
  final VoidCallback onRetry;

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
              'Couldn’t refresh. Showing your last loaded farms.',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 11.5,
                height: 1.35,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          if (isRefreshing)
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
              key: const Key('farm_tab_stale_retry_button'),
              onPressed: onRetry,
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

class _FarmFooter extends StatelessWidget {
  const _FarmFooter({required this.provider});

  final FarmProvider provider;

  @override
  Widget build(BuildContext context) {
    final lastUpdated = provider.lastUpdated;

    if (lastUpdated == null) {
      return const SizedBox(height: 4);
    }

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

class _FarmLoadingView extends StatelessWidget {
  const _FarmLoadingView();

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('farm_tab_loading'),
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.fromLTRB(
        _FarmTabState._horizontalPadding,
        18,
        _FarmTabState._horizontalPadding,
        28,
      ),
      children: const [
        _SkeletonBox(width: 150, height: 30),
        SizedBox(height: 9),
        _SkeletonBox(width: 250, height: 13),
        SizedBox(height: 22),
        _SkeletonCard(),
        SizedBox(height: 12),
        _SkeletonCard(),
        SizedBox(height: 12),
        _SkeletonCard(),
      ],
    );
  }
}

class _SkeletonCard extends StatelessWidget {
  const _SkeletonCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _SkeletonBox(width: 46, height: 46, radius: 15),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _SkeletonBox(width: 150, height: 16),
                    SizedBox(height: 8),
                    _SkeletonBox(width: 210, height: 12),
                  ],
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          _SkeletonBox(width: 100, height: 24, radius: 12),
        ],
      ),
    );
  }
}

class _SkeletonBox extends StatelessWidget {
  const _SkeletonBox({
    required this.width,
    required this.height,
    this.radius = 7,
  });

  final double width;
  final double height;
  final double radius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }
}

class _FarmErrorView extends StatelessWidget {
  const _FarmErrorView({
    required this.message,
    required this.isRetrying,
    required this.onRetry,
  });

  final String? message;
  final bool isRetrying;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      key: const Key('farm_tab_error'),
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
          'Couldn’t load your farms',
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
          message ?? 'Something went wrong. Please try again.',
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12.5,
            height: 1.45,
          ),
        ),
        const SizedBox(height: 22),
        ElevatedButton.icon(
          key: const Key('farm_tab_retry_button'),
          onPressed: isRetrying ? null : onRetry,
          icon: const Icon(Icons.refresh_rounded),
          label: Text(isRetrying ? 'Retrying…' : 'Try again'),
        ),
      ],
    );
  }
}

class _FarmEmptyView extends StatelessWidget {
  const _FarmEmptyView({
    required this.provider,
    required this.onRefresh,
    required this.onAddFarm,
  });

  final FarmProvider provider;
  final Future<void> Function() onRefresh;
  final VoidCallback onAddFarm;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: onRefresh,
      child: ListView(
        key: const Key('farm_tab_empty'),
        physics: const AlwaysScrollableScrollPhysics(
          parent: BouncingScrollPhysics(),
        ),
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 28),
        children: [
          const Text(
            'My farms',
            style: TextStyle(
              color: AppColors.primaryDark,
              fontSize: 26,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.7,
            ),
          ),
          const SizedBox(height: 44),
          Center(
            child: Container(
              width: 94,
              height: 94,
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppColors.primary.withValues(alpha: 0.12),
                ),
              ),
              child: const Icon(
                Icons.agriculture_rounded,
                color: AppColors.primary,
                size: 42,
              ),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'No farms yet',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 22,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.4,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Add your first farm to keep land, water and crop guidance in one place.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
              height: 1.5,
            ),
          ),
          if (provider.hasError) ...[
            const SizedBox(height: 18),
            _FarmStaleBanner(
              isRefreshing: provider.isRefreshing,
              onRetry: () {
                provider.refreshFarms();
              },
            ),
          ],
          const SizedBox(height: 24),
          ElevatedButton.icon(
            key: const Key('farm_tab_empty_add_button'),
            onPressed: provider.canCreateFarm ? onAddFarm : null,
            icon: const Icon(Icons.add_rounded),
            label: const Text('Add your first farm'),
          ),
        ],
      ),
    );
  }
}

List<_FarmDetailRow> _farmDetails(FarmModel farm) {
  final details = <_FarmDetailRow>[
    _FarmDetailRow(
      icon: Icons.square_foot_rounded,
      label: 'Land area',
      value: farm.landArea > 0
          ? '${_formatNumber(farm.landArea)} ${farm.landUnit.trim()}'
          : 'Not provided',
    ),
  ];

  if (farm.soilType != null) {
    details.add(
      _FarmDetailRow(
        icon: Icons.layers_outlined,
        label: 'Soil type',
        value: farm.soilType!,
      ),
    );
  }

  if (farm.waterSource != null) {
    details.add(
      _FarmDetailRow(
        icon: Icons.water_drop_outlined,
        label: 'Water source',
        value: farm.waterSource!,
      ),
    );
  }

  if (farm.waterAvailability != null) {
    details.add(
      _FarmDetailRow(
        icon: Icons.water_outlined,
        label: 'Water availability',
        value: _humanize(farm.waterAvailability!),
      ),
    );
  }

  if (farm.irrigationMethod != null) {
    details.add(
      _FarmDetailRow(
        icon: Icons.water_rounded,
        label: 'Irrigation method',
        value: farm.irrigationMethod!,
      ),
    );
  }

  if (farm.latitude != null && farm.longitude != null) {
    details.add(
      _FarmDetailRow(
        icon: Icons.my_location_rounded,
        label: 'Coordinates',
        value:
            '${farm.latitude!.toStringAsFixed(5)}, ${farm.longitude!.toStringAsFixed(5)}',
      ),
    );
  }

  return details;
}

FarmModel? _primaryFarm(List<FarmModel> farms) {
  for (final farm in farms) {
    if (farm.isPrimary) {
      return farm;
    }
  }

  return null;
}

List<_LandTotal> _landTotals(List<FarmModel> farms) {
  final totals = <String, double>{};

  for (final farm in farms) {
    if (farm.landArea <= 0) {
      continue;
    }

    final unit = farm.landUnit.trim().isEmpty ? 'Acres' : farm.landUnit.trim();
    totals[unit] = (totals[unit] ?? 0) + farm.landArea;
  }

  return totals.entries
      .map((entry) => _LandTotal(unit: entry.key, area: entry.value))
      .toList(growable: false);
}

String _humanize(String value) {
  final normalized = value.trim().replaceAll('_', ' ').toLowerCase();

  if (normalized == 'rain fed') {
    return 'Rain-fed';
  }

  return normalized
      .split(RegExp(r'\s+'))
      .where((part) => part.isNotEmpty)
      .map((part) => part[0].toUpperCase() + part.substring(1))
      .join(' ');
}

String _cleanError(Object error) {
  var message = error.toString().trim();

  while (message.startsWith('Exception: ')) {
    message = message.substring('Exception: '.length).trim();
  }

  return message.isEmpty
      ? 'Unable to set your primary farm. Please try again.'
      : message;
}

String _formatNumber(double value) {
  if (value == value.roundToDouble()) {
    return value.toInt().toString();
  }

  return value.toStringAsFixed(2).replaceFirst(RegExp(r'0+$'), '');
}

class _LandTotal {
  const _LandTotal({required this.unit, required this.area});

  final String unit;
  final double area;
}

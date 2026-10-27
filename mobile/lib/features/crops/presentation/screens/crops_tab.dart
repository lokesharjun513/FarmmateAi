import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../farm/data/models/farm_model.dart';
import '../../data/models/crop_season_model.dart';
import '../../providers/crop_provider.dart';
import '../../providers/crop_recommendation_provider.dart';
import 'add_crop_screen.dart';
import 'crop_detail_screen.dart';

class CropsTab extends StatelessWidget {
  const CropsTab({super.key});

  static const double _horizontalPadding = 20;

  Future<void> _openCreateCrop(BuildContext context) async {
    final provider = context.read<CropProvider>();

    if (provider.farms.isEmpty) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          const SnackBar(content: Text('Add a farm before creating a crop.')),
        );
      return;
    }

    await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => MultiProvider(
          providers: [
            ChangeNotifierProvider<CropProvider>.value(value: provider),
            ChangeNotifierProvider<CropRecommendationProvider>(
              create: (_) => CropRecommendationProvider(),
            ),
          ],
          child: const AddCropScreen(),
        ),
      ),
    );

    if (!context.mounted) {
      return;
    }

    await provider.refreshCrops();
  }

  Future<void> _openCropDetails(
    BuildContext context,
    FarmModel farm,
    CropSeasonModel crop,
  ) async {
    final provider = context.read<CropProvider>();

    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => ChangeNotifierProvider<CropProvider>.value(
          value: provider,
          child: CropDetailScreen(farm: farm, crop: crop),
        ),
      ),
    );

    if (!context.mounted) {
      return;
    }

    await provider.refreshCrops();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CropProvider>();

    if (provider.isInitialLoading) {
      return const _CropsLoadingView();
    }

    if (provider.hasError && !provider.hasLoaded) {
      return _CropsErrorView(provider: provider);
    }

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: provider.refreshCrops,
      child: CustomScrollView(
        key: const Key('crops_scroll'),
        physics: const AlwaysScrollableScrollPhysics(
          parent: BouncingScrollPhysics(),
        ),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(
              _horizontalPadding,
              20,
              _horizontalPadding,
              32,
            ),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _CropsHeader(
                  provider: provider,
                  onCreate: () => _openCreateCrop(context),
                ),

                if (provider.isShowingStaleData) ...[
                  const SizedBox(height: 16),
                  _StaleDataBanner(provider: provider),
                ],

                if (provider.isEmpty)
                  _CropsEmptyView(onCreate: () => _openCreateCrop(context))
                else ...[
                  const SizedBox(height: 20),
                  _CropSummary(provider: provider),
                  const SizedBox(height: 24),
                  for (final group in provider.groups) ...[
                    _FarmCropSection(
                      group: group,
                      onOpenCrop: (crop) =>
                          _openCropDetails(context, group.farm, crop),
                    ),
                    const SizedBox(height: 24),
                  ],
                ],
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

class _CropsHeader extends StatelessWidget {
  const _CropsHeader({required this.provider, required this.onCreate});

  final CropProvider provider;
  final VoidCallback onCreate;

  @override
  Widget build(BuildContext context) {
    final subtitle = provider.hasMultipleFarms
        ? 'Your crop seasons across ${provider.farmCount} farms'
        : 'Plan and manage your crop seasons';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Text(
                'Crops',
                style: TextStyle(
                  color: AppColors.primaryDark,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.6,
                ),
              ),
            ),
            TextButton.icon(
              key: const Key('crops_create_button'),
              onPressed: onCreate,
              icon: const Icon(Icons.add_rounded, size: 18),
              label: const Text('New crop'),
              style: TextButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(
                  horizontal: 13,
                  vertical: 10,
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
          ],
        ),
        const SizedBox(height: 6),
        Text(
          subtitle,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 13,
            height: 1.4,
          ),
        ),
      ],
    );
  }
}

class _CropSummary extends StatelessWidget {
  const _CropSummary({required this.provider});

  final CropProvider provider;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 16),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.10)),
      ),
      child: Row(
        children: [
          Expanded(
            child: _SummaryMetric(
              key: const Key('summary_metric_total'),
              value: provider.totalCrops,
              label: 'Total',
              color: AppColors.primaryDark,
            ),
          ),
          const _SummaryDivider(),
          Expanded(
            child: _SummaryMetric(
              value: provider.activeCropCount,
              label: 'Active',
              color: AppColors.primary,
            ),
          ),
          const _SummaryDivider(),
          Expanded(
            child: _SummaryMetric(
              value: provider.plannedCropCount,
              label: 'Planned',
              color: AppColors.warning,
            ),
          ),
          const _SummaryDivider(),
          Expanded(
            child: _SummaryMetric(
              value: provider.harvestedCropCount,
              label: 'Harvested',
              color: AppColors.info,
            ),
          ),
        ],
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  const _SummaryMetric({
    super.key,
    required this.value,
    required this.label,
    required this.color,
  });

  final int value;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          '$value',
          style: TextStyle(
            color: color,
            fontSize: 24,
            fontWeight: FontWeight.w800,
            height: 1,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 11.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _SummaryDivider extends StatelessWidget {
  const _SummaryDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 34,
      color: AppColors.primary.withValues(alpha: 0.12),
    );
  }
}

class _StaleDataBanner extends StatelessWidget {
  const _StaleDataBanner({required this.provider});

  final CropProvider provider;

  @override
  Widget build(BuildContext context) {
    final failedFarms = provider.failedFarmNames;
    final shouldNameFarms =
        provider.isShowingStaleData &&
        failedFarms.isNotEmpty &&
        (provider.hasPartialFailure || provider.farmCount > 1);
    final message = shouldNameFarms
        ? 'Could not refresh ${failedFarms.join(', ')}. Showing the latest available data.'
        : provider.errorMessage ?? 'Showing saved crops. Refresh to try again.';

    return Container(
      key: const Key('crops_stale_banner'),
      padding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.20)),
      ),
      child: Row(
        children: [
          const Icon(
            Icons.cloud_off_rounded,
            color: AppColors.warning,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                height: 1.35,
              ),
            ),
          ),
          TextButton(
            onPressed: provider.isRefreshing ? null : provider.retry,
            style: TextButton.styleFrom(
              foregroundColor: AppColors.warning,
              textStyle: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}

class _FarmCropSection extends StatelessWidget {
  const _FarmCropSection({required this.group, required this.onOpenCrop});

  final CropFarmGroup group;
  final ValueChanged<CropSeasonModel> onOpenCrop;

  @override
  Widget build(BuildContext context) {
    final farm = group.farm;
    final location = farm.locationLabel;
    final cropCount = group.crops.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                borderRadius: BorderRadius.circular(13),
              ),
              child: const Icon(
                Icons.agriculture_rounded,
                color: AppColors.primary,
                size: 21,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          farm.farmName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      if (farm.isPrimary) ...[
                        const SizedBox(width: 7),
                        const _PrimaryBadge(),
                      ],
                    ],
                  ),
                  if (location.isNotEmpty) ...[
                    const SizedBox(height: 3),
                    Text(
                      location,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textHint,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              '$cropCount ${cropCount == 1 ? 'crop' : 'crops'}',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (!group.hasCrops)
          const _FarmCropsEmptyView()
        else
          for (var index = 0; index < group.crops.length; index++) ...[
            _CropSeasonCard(
              crop: group.crops[index],
              onTap: () => onOpenCrop(group.crops[index]),
            ),
            if (index != group.crops.length - 1) const SizedBox(height: 11),
          ],
      ],
    );
  }
}

class _PrimaryBadge extends StatelessWidget {
  const _PrimaryBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(7),
      ),
      child: const Text(
        'Primary',
        style: TextStyle(
          color: AppColors.primary,
          fontSize: 9.5,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.2,
        ),
      ),
    );
  }
}

class _CropSeasonCard extends StatelessWidget {
  const _CropSeasonCard({required this.crop, required this.onTap});

  final CropSeasonModel crop;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(crop.status);
    final variety = crop.cropVariety;
    final expectedHarvestDate = crop.expectedHarvestDate;
    final harvestedDate = crop.harvestedDate;
    final cancellationReason = crop.cancellationReason;

    return Material(
      key: Key('crop_card_${crop.id}'),
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(19),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(19),
        child: Container(
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(
            color: AppColors.surfaceLight,
            borderRadius: BorderRadius.circular(19),
            border: Border.all(color: AppColors.borderLight),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.04),
                blurRadius: 14,
                offset: const Offset(0, 5),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          crop.cropName,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.2,
                            height: 1.2,
                          ),
                        ),
                        if (variety != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            variety,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  _StatusChip(status: crop.status, color: statusColor),
                ],
              ),

              const SizedBox(height: 14),

              Wrap(
                spacing: 7,
                runSpacing: 7,
                children: [
                  _MetaPill(
                    icon: Icons.eco_outlined,
                    label: '${crop.season.label} ${crop.year}',
                  ),
                  if (crop.landArea > 0)
                    _MetaPill(
                      icon: Icons.straighten_rounded,
                      label: '${_formatNumber(crop.landArea)} ${crop.landUnit}',
                    ),
                ],
              ),

              const SizedBox(height: 14),
              const Divider(height: 1, color: AppColors.borderLight),
              const SizedBox(height: 12),

              _DateLine(
                icon: Icons.spa_outlined,
                label: 'Sown',
                value: _formatDate(crop.sowingDate),
              ),

              if (expectedHarvestDate != null) ...[
                const SizedBox(height: 8),
                _DateLine(
                  icon: Icons.event_outlined,
                  label: 'Expected harvest',
                  value: _formatDate(expectedHarvestDate),
                  color: statusColor,
                ),
              ],

              if (harvestedDate != null) ...[
                const SizedBox(height: 8),
                _DateLine(
                  icon: Icons.task_alt_rounded,
                  label: 'Harvested',
                  value: _formatDate(harvestedDate),
                  color: statusColor,
                ),
              ],

              if (crop.isCancelled && cancellationReason != null) ...[
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 11,
                    vertical: 9,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.error.withValues(alpha: 0.06),
                    borderRadius: BorderRadius.circular(11),
                  ),
                  child: Text(
                    cancellationReason,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11.5,
                      height: 1.35,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status, required this.color});

  final CropSeasonStatus status;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: color.withValues(alpha: 0.16)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Text(
            status.label,
            style: TextStyle(
              color: color,
              fontSize: 10.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}

class _MetaPill extends StatelessWidget {
  const _MetaPill({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(9),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppColors.textSecondary, size: 13),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 10.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _DateLine extends StatelessWidget {
  const _DateLine({
    required this.icon,
    required this.label,
    required this.value,
    this.color = AppColors.textHint,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: color, size: 15),
        const SizedBox(width: 7),
        Expanded(
          child: Text(
            label,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11.5,
            ),
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 11.5,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _FarmCropsEmptyView extends StatelessWidget {
  const _FarmCropsEmptyView();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(15),
      ),
      child: const Row(
        children: [
          Icon(Icons.grass_outlined, color: AppColors.textHint, size: 18),
          SizedBox(width: 9),
          Expanded(
            child: Text(
              'No crop seasons recorded for this farm.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CropsEmptyView extends StatelessWidget {
  const _CropsEmptyView({required this.onCreate});

  final VoidCallback onCreate;

  @override
  Widget build(BuildContext context) {
    return Padding(
      key: const Key('crops_empty_view'),
      padding: const EdgeInsets.only(top: 58, left: 12, right: 12),
      child: Column(
        children: [
          Container(
            width: 82,
            height: 82,
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
              border: Border.all(
                color: AppColors.primary.withValues(alpha: 0.12),
              ),
            ),
            child: const Icon(
              Icons.grass_rounded,
              color: AppColors.primary,
              size: 36,
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'No crop seasons yet',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.primaryDark,
              fontSize: 20,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Add a crop to start planning seasons for your farms.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            key: const Key('crops_empty_add_button'),
            onPressed: onCreate,
            icon: const Icon(Icons.add_rounded, size: 18),
            label: const Text('Add Crop'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(13),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CropsLoadingView extends StatelessWidget {
  const _CropsLoadingView();

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      key: const Key('crops_loading'),
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Expanded(child: _SkeletonBox(width: 110, height: 30, radius: 9)),
              SizedBox(width: 24),
              _SkeletonBox(width: 96, height: 38, radius: 13),
            ],
          ),
          const SizedBox(height: 12),
          const _SkeletonBox(width: 220, height: 14, radius: 7),
          const SizedBox(height: 26),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              borderRadius: BorderRadius.circular(22),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _SkeletonBox(width: 44, height: 38, radius: 9),
                _SkeletonBox(width: 44, height: 38, radius: 9),
                _SkeletonBox(width: 44, height: 38, radius: 9),
                _SkeletonBox(width: 44, height: 38, radius: 9),
              ],
            ),
          ),
          const SizedBox(height: 28),
          const _SkeletonBox(width: 170, height: 18, radius: 8),
          const SizedBox(height: 13),
          for (var index = 0; index < 2; index++) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surfaceLight,
                borderRadius: BorderRadius.circular(19),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: _SkeletonBox(
                          width: double.infinity,
                          height: 20,
                          radius: 7,
                        ),
                      ),
                      SizedBox(width: 32),
                      _SkeletonBox(width: 72, height: 22, radius: 9),
                    ],
                  ),
                  SizedBox(height: 16),
                  _SkeletonBox(width: 160, height: 13, radius: 6),
                  SizedBox(height: 18),
                  _SkeletonBox(width: double.infinity, height: 12, radius: 6),
                  SizedBox(height: 10),
                  _SkeletonBox(width: double.infinity, height: 12, radius: 6),
                ],
              ),
            ),
            if (index == 0) const SizedBox(height: 12),
          ],
          const SizedBox(height: 18),
          const Center(
            child: Text(
              'Loading your crops...',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _SkeletonBox extends StatelessWidget {
  const _SkeletonBox({
    required this.width,
    required this.height,
    required this.radius,
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

class _CropsErrorView extends StatelessWidget {
  const _CropsErrorView({required this.provider});

  final CropProvider provider;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return SingleChildScrollView(
          key: const Key('crops_error_view'),
          physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics(),
          ),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight),
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
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
                        size: 32,
                      ),
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Crops unavailable',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.primaryDark,
                        fontSize: 21,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      provider.errorMessage ??
                          'Unable to load your crops. Please try again.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 13,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton.icon(
                      onPressed: provider.retry,
                      icon: const Icon(Icons.refresh_rounded, size: 18),
                      label: const Text('Retry'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 22,
                          vertical: 13,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(13),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

Color _statusColor(CropSeasonStatus status) {
  return switch (status) {
    CropSeasonStatus.planned => AppColors.warning,
    CropSeasonStatus.active => AppColors.primary,
    CropSeasonStatus.harvested => AppColors.info,
    CropSeasonStatus.cancelled => AppColors.error,
  };
}

String _formatDate(DateTime date) {
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];

  return '${date.day} ${months[date.month - 1]} ${date.year}';
}

String _formatNumber(double value) {
  if (value == value.roundToDouble()) {
    return value.toStringAsFixed(0);
  }

  return value
      .toStringAsFixed(2)
      .replaceFirst(RegExp(r'0+$'), '')
      .replaceFirst(RegExp(r'\.$'), '');
}

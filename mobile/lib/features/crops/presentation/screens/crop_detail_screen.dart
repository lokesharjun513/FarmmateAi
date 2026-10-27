import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../farm/data/models/farm_model.dart';
import '../../data/models/crop_plan_models.dart';
import '../../data/models/crop_season_model.dart';
import '../../providers/crop_provider.dart';
import 'edit_crop_screen.dart';

enum _ActivityAction { start, complete, reschedule, skip, delete }

class CropDetailScreen extends StatefulWidget {
  const CropDetailScreen({super.key, required this.farm, required this.crop});

  final FarmModel farm;
  final CropSeasonModel crop;

  @override
  State<CropDetailScreen> createState() => _CropDetailScreenState();
}

class _CropDetailScreenState extends State<CropDetailScreen> {
  late CropSeasonModel _crop;
  bool _isLoading = false;
  bool _isGeneratingPlan = false;
  bool _generationFailed = false;
  String? _actionId;
  String? _errorMessage;

  bool get _isBusy => _isLoading || _isGeneratingPlan || _actionId != null;

  @override
  void initState() {
    super.initState();
    _crop = widget.crop;
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadPlan());
  }

  Future<void> _loadPlan({bool force = false}) async {
    if (!mounted || (!force && _isBusy)) {
      return;
    }

    setState(() {
      _isLoading = true;
      _generationFailed = false;
      _errorMessage = null;
    });

    try {
      await context.read<CropProvider>().loadCropPlan(
        _crop.id,
        allowEmpty: true,
      );
    } catch (error) {
      if (mounted) {
        setState(() {
          _errorMessage = _cleanError(error);
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _generatePlan() async {
    if (!mounted || _isBusy) {
      return;
    }

    setState(() {
      _isGeneratingPlan = true;
      _generationFailed = false;
      _errorMessage = null;
    });

    final provider = context.read<CropProvider>();

    try {
      await provider.generateCropPlan(crop: _crop, farm: widget.farm);

      if (!mounted) {
        return;
      }

      await provider.loadCropPlan(_crop.id, allowEmpty: true);
    } catch (error) {
      if (!mounted) {
        return;
      }

      try {
        await provider.loadCropPlan(_crop.id, allowEmpty: true);
      } catch (_) {
        // Keep the original generation error below.
      }

      if (!mounted) {
        return;
      }

      final planExists =
          provider.planStages.isNotEmpty ||
          provider.planActivities.isNotEmpty ||
          provider.hasGeneratedPlan;

      setState(() {
        _generationFailed = !planExists;
        _errorMessage = planExists ? null : _cleanError(error);
      });
    } finally {
      if (mounted) {
        setState(() {
          _isGeneratingPlan = false;
        });
      }
    }
  }

  Future<void> _runCropAction({
    required String key,
    required Future<CropSeasonModel> Function() action,
    required String successMessage,
  }) async {
    if (!mounted || _isBusy) {
      return;
    }

    setState(() {
      _actionId = key;
    });

    try {
      final updated = await action();

      if (!mounted) {
        return;
      }

      setState(() {
        _crop = updated;
      });

      await _loadPlan(force: true);

      if (mounted) {
        _showMessage(successMessage);
      }
    } catch (error) {
      if (mounted) {
        _showMessage(_cleanError(error), isError: true);
      }
    } finally {
      if (mounted) {
        setState(() {
          _actionId = null;
        });
      }
    }
  }

  Future<void> _runPlanAction({
    required String key,
    required Future<Object?> Function() action,
    required String successMessage,
  }) async {
    if (!mounted || _isBusy) {
      return;
    }

    setState(() {
      _actionId = key;
    });

    try {
      await action();

      if (!mounted) {
        return;
      }

      await _loadPlan(force: true);

      if (mounted) {
        _showMessage(successMessage);
      }
    } catch (error) {
      if (mounted) {
        _showMessage(_cleanError(error), isError: true);
      }
    } finally {
      if (mounted) {
        setState(() {
          _actionId = null;
        });
      }
    }
  }

  Future<void> _startCrop() async {
    await _runCropAction(
      key: 'crop-start',
      action: () => context.read<CropProvider>().activateCropSeason(_crop.id),
      successMessage: 'Crop started.',
    );
  }

  Future<void> _harvestCrop() async {
    var harvestedDate = DateTime.now();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Mark crop as harvested?'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'This closes the crop season. All stages and activities '
                'must already be completed or skipped.',
              ),
              const SizedBox(height: 12),
              TextButton.icon(
                key: const Key('crop_detail_harvest_date_button'),
                onPressed: () async {
                  final picked = await showDatePicker(
                    context: context,
                    initialDate: harvestedDate,
                    firstDate: _crop.sowingDate,
                    lastDate: DateTime.now(),
                  );

                  if (picked != null) {
                    setDialogState(() {
                      harvestedDate = picked;
                    });
                  }
                },
                icon: const Icon(Icons.event_rounded, size: 18),
                label: Text('Harvest date: ${_formatDate(harvestedDate)}'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Keep growing'),
            ),
            ElevatedButton(
              key: const Key('crop_detail_harvest_confirm_button'),
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Mark harvested'),
            ),
          ],
        ),
      ),
    );

    if (confirmed != true || !mounted) {
      return;
    }

    await _runCropAction(
      key: 'crop-harvest',
      action: () => context.read<CropProvider>().harvestCropSeason(
        _crop.id,
        harvestedDate: harvestedDate,
      ),
      successMessage: 'Crop marked as harvested.',
    );
  }

  Future<void> _cancelCrop() async {
    var reason = '';

    final result = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Cancel this crop?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Cancelling stops this crop season. It will remain in your '
              'history with the recorded reason.',
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('crop_detail_cancel_reason_field'),
              onChanged: (value) => reason = value,
              maxLength: 1000,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Reason (optional)',
                hintText: 'For example: heavy rain damaged the nursery',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Keep crop'),
          ),
          ElevatedButton(
            key: const Key('crop_detail_cancel_confirm_button'),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            onPressed: () => Navigator.pop(dialogContext, reason.trim()),
            child: const Text('Cancel crop'),
          ),
        ],
      ),
    );

    if (result == null || !mounted) {
      return;
    }

    await _runCropAction(
      key: 'crop-cancel',
      action: () => context.read<CropProvider>().cancelCropSeason(
        _crop.id,
        reason: result.isEmpty ? null : result,
      ),
      successMessage: 'Crop cancelled.',
    );
  }

  Future<void> _deleteCrop() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete this crop?'),
        content: const Text(
          'This permanently removes the crop and its plan. '
          'This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Keep crop'),
          ),
          ElevatedButton(
            key: const Key('crop_detail_delete_confirm_button'),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted || _isBusy) {
      return;
    }

    setState(() {
      _actionId = 'crop-delete';
    });

    try {
      await context.read<CropProvider>().deleteCropSeason(_crop.id);

      if (mounted) {
        Navigator.pop(context, true);
      }
    } catch (error) {
      if (mounted) {
        _showMessage(_cleanError(error), isError: true);
      }
    } finally {
      if (mounted) {
        setState(() {
          _actionId = null;
        });
      }
    }
  }

  Future<void> _editCrop() async {
    final updated = await Navigator.of(context).push<CropSeasonModel>(
      MaterialPageRoute(
        builder: (_) => ChangeNotifierProvider<CropProvider>.value(
          value: context.read<CropProvider>(),
          child: EditCropScreen(farm: widget.farm, crop: _crop),
        ),
      ),
    );

    if (updated != null && mounted) {
      setState(() {
        _crop = updated;
      });
    }
  }

  Future<void> _handleStageAction(CropStageModel stage, bool complete) async {
    if (!complete) {
      final confirmed = await _confirm(
        title: 'Skip this stage?',
        message:
            'Skipping "${stage.name}" moves the crop to the next stage '
            'without completing its remaining work.',
        confirmLabel: 'Skip stage',
      );

      if (!confirmed || !mounted) {
        return;
      }
    }

    final provider = context.read<CropProvider>();

    await _runPlanAction(
      key: 'stage-${stage.id}',
      action: () => complete
          ? provider.completeCropStage(stage.id)
          : provider.skipCropStage(stage.id),
      successMessage: complete ? 'Stage completed.' : 'Stage skipped.',
    );
  }

  Future<void> _handleActivityAction(
    CropActivityModel activity,
    _ActivityAction action,
  ) async {
    final provider = context.read<CropProvider>();

    switch (action) {
      case _ActivityAction.start:
        await _runPlanAction(
          key: 'activity-${activity.id}',
          action: () => provider.startActivity(activity.id),
          successMessage: 'Activity started.',
        );
        return;

      case _ActivityAction.complete:
        await _runPlanAction(
          key: 'activity-${activity.id}',
          action: () => provider.completeActivity(activity.id),
          successMessage: 'Activity completed.',
        );
        return;

      case _ActivityAction.reschedule:
        final picked = await _pickDate(
          title: 'Reschedule activity',
          initialDate: activity.scheduledDate,
        );

        if (picked == null || !mounted) {
          return;
        }

        await _runPlanAction(
          key: 'activity-${activity.id}',
          action: () => provider.rescheduleActivity(activity.id, picked),
          successMessage: 'Activity rescheduled.',
        );
        return;

      case _ActivityAction.skip:
        final confirmed = await _confirm(
          title: 'Skip this activity?',
          message:
              '"${activity.title}" will be marked as skipped. '
              'Skipped activities count as finished for stage completion.',
          confirmLabel: 'Skip activity',
        );

        if (!confirmed || !mounted) {
          return;
        }

        await _runPlanAction(
          key: 'activity-${activity.id}',
          action: () => provider.skipActivity(activity.id),
          successMessage: 'Activity skipped.',
        );
        return;

      case _ActivityAction.delete:
        final confirmed = await _confirm(
          title: 'Delete this activity?',
          message: '"${activity.title}" will be permanently removed.',
          confirmLabel: 'Delete',
          destructive: true,
        );

        if (!confirmed || !mounted) {
          return;
        }

        await _runPlanAction(
          key: 'activity-${activity.id}',
          action: () => provider.deleteActivity(activity.id),
          successMessage: 'Activity deleted.',
        );
        return;
    }
  }

  Future<bool> _confirm({
    required String title,
    required String message,
    required String confirmLabel,
    bool destructive = false,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Keep'),
          ),
          ElevatedButton(
            style: destructive
                ? ElevatedButton.styleFrom(backgroundColor: AppColors.error)
                : null,
            onPressed: () => Navigator.pop(dialogContext, true),
            child: Text(confirmLabel),
          ),
        ],
      ),
    );

    return result == true;
  }

  Future<DateTime?> _pickDate({
    required String title,
    required DateTime initialDate,
  }) {
    return showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(initialDate.year - 2),
      lastDate: DateTime(initialDate.year + 3),
      helpText: title,
    );
  }

  void _showMessage(String message, {bool isError = false}) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: isError ? AppColors.error : null,
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CropProvider>();
    final canEdit = _crop.isPlanned && provider.planStages.isEmpty;
    final canCancel = _crop.isPlanned || _crop.isActiveSeason;
    final canDelete = _crop.isPlanned || _crop.isCancelled;
    final hasMenu = canEdit || canCancel || canDelete;

    return Scaffold(
      key: const Key('crop_detail_screen'),
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.backgroundLight,
        elevation: 0,
        title: const Text('Crop details'),
        actions: [
          if (hasMenu)
            PopupMenuButton<String>(
              key: const Key('crop_detail_actions_button'),
              enabled: !_isBusy,
              onSelected: (value) {
                switch (value) {
                  case 'edit':
                    _editCrop();
                    return;
                  case 'cancel':
                    _cancelCrop();
                    return;
                  case 'delete':
                    _deleteCrop();
                    return;
                }
              },
              itemBuilder: (_) => [
                if (canEdit)
                  const PopupMenuItem<String>(
                    key: Key('crop_detail_edit_action'),
                    value: 'edit',
                    child: Text('Edit crop details'),
                  ),
                if (canCancel)
                  const PopupMenuItem<String>(
                    key: Key('crop_detail_cancel_action'),
                    value: 'cancel',
                    child: Text('Cancel crop'),
                  ),
                if (canDelete)
                  const PopupMenuItem<String>(
                    key: Key('crop_detail_delete_action'),
                    value: 'delete',
                    child: Text('Delete crop'),
                  ),
              ],
            ),
          IconButton(
            key: const Key('crop_detail_refresh_button'),
            onPressed: _isBusy ? null : _loadPlan,
            tooltip: 'Refresh crop plan',
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.primary,
        onRefresh: _loadPlan,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics(),
          ),
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            _CropHeaderCard(farm: widget.farm, crop: _crop),
            if (_crop.isPlanned && provider.planStages.isNotEmpty) ...[
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  key: const Key('crop_detail_start_button'),
                  onPressed: _isBusy ? null : _startCrop,
                  icon: _actionId == 'crop-start'
                      ? const SizedBox(
                          width: 17,
                          height: 17,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.play_arrow_rounded, size: 20),
                  label: const Text('Start farming'),
                ),
              ),
            ],
            if (_crop.isActiveSeason) ...[
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  key: const Key('crop_detail_harvest_button'),
                  onPressed: _isBusy ? null : _harvestCrop,
                  icon: _actionId == 'crop-harvest'
                      ? const SizedBox(
                          width: 17,
                          height: 17,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.agriculture_rounded, size: 19),
                  label: const Text('Mark harvested'),
                ),
              ),
            ],
            const SizedBox(height: 16),
            _CropTimelineCard(crop: _crop),
            const SizedBox(height: 24),
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Crop plan',
                    style: TextStyle(
                      color: AppColors.primaryDark,
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.3,
                    ),
                  ),
                ),
                if (!_isBusy && _errorMessage == null)
                  Text(
                    '${provider.planStages.length} ${provider.planStages.length == 1 ? 'stage' : 'stages'}',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            if (_isGeneratingPlan)
              const _PlanLoadingCard(message: 'Generating the crop plan...')
            else if (_isLoading)
              const _PlanLoadingCard()
            else if (_errorMessage != null)
              _PlanErrorCard(
                message: _errorMessage!,
                onRetry: _generationFailed ? _generatePlan : _loadPlan,
              )
            else if (provider.planStages.isEmpty &&
                provider.planActivities.isEmpty)
              _PlanEmptyCard(
                canGenerate: _crop.isPlanned,
                onGenerate: _generatePlan,
                onRefresh: _loadPlan,
              )
            else
              _PlanTimeline(
                sowingDate: _crop.sowingDate,
                stages: provider.planStages,
                activities: provider.planActivities,
                actionId: _actionId,
                canManage: _crop.isActiveSeason,
                onStageAction: _handleStageAction,
                onActivityAction: _handleActivityAction,
              ),
            if (!_isBusy &&
                _errorMessage == null &&
                provider.planStages.isNotEmpty &&
                _crop.notes != null) ...[
              const SizedBox(height: 16),
              _NotesCard(notes: _crop.notes!),
            ],
          ],
        ),
      ),
    );
  }
}

class _CropHeaderCard extends StatelessWidget {
  const _CropHeaderCard({required this.farm, required this.crop});

  final FarmModel farm;
  final CropSeasonModel crop;

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(crop.status);
    final location = farm.locationLabel;

    return Container(
      key: const Key('crop_detail_header'),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.borderLight),
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
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      crop.cropName,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 25,
                        fontWeight: FontWeight.w800,
                        height: 1.15,
                        letterSpacing: -0.5,
                      ),
                    ),
                    if (crop.cropVariety != null) ...[
                      const SizedBox(height: 5),
                      Text(
                        crop.cropVariety!,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 10),
              _StatusPill(status: crop.status, color: statusColor),
            ],
          ),
          const SizedBox(height: 15),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              borderRadius: BorderRadius.circular(13),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.agriculture_rounded,
                  color: AppColors.primary,
                  size: 19,
                ),
                const SizedBox(width: 8),
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
                                color: AppColors.primaryDark,
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ),
                          if (farm.isPrimary) ...[
                            const SizedBox(width: 6),
                            const Text(
                              'Primary',
                              style: TextStyle(
                                color: AppColors.primary,
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ],
                      ),
                      if (location.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          location,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _InfoPill(
                icon: Icons.eco_outlined,
                label: '${crop.season.label} ${crop.year}',
              ),
              if (crop.landArea > 0)
                _InfoPill(
                  icon: Icons.straighten_rounded,
                  label: '${_formatNumber(crop.landArea)} ${crop.landUnit}',
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CropTimelineCard extends StatelessWidget {
  const _CropTimelineCard({required this.crop});

  final CropSeasonModel crop;

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(crop.status);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Column(
        children: [
          _DetailRow(
            icon: Icons.spa_outlined,
            label: 'Sown',
            value: _formatDate(crop.sowingDate),
          ),
          if (crop.expectedHarvestDate != null) ...[
            const SizedBox(height: 10),
            _DetailRow(
              icon: Icons.event_outlined,
              label: 'Expected harvest',
              value: _formatDate(crop.expectedHarvestDate!),
              color: statusColor,
            ),
          ],
          if (crop.harvestedDate != null) ...[
            const SizedBox(height: 10),
            _DetailRow(
              icon: Icons.task_alt_rounded,
              label: 'Harvested',
              value: _formatDate(crop.harvestedDate!),
              color: statusColor,
            ),
          ],
          if (crop.isCancelled && crop.cancellationReason != null) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(11),
              decoration: BoxDecoration(
                color: AppColors.error.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(11),
              ),
              child: Text(
                crop.cancellationReason!,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 11.5,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PlanTimeline extends StatelessWidget {
  const _PlanTimeline({
    required this.sowingDate,
    required this.stages,
    required this.activities,
    required this.actionId,
    required this.canManage,
    required this.onStageAction,
    required this.onActivityAction,
  });

  final DateTime sowingDate;
  final List<CropStageModel> stages;
  final List<CropActivityModel> activities;
  final String? actionId;
  final bool canManage;
  final Future<void> Function(CropStageModel stage, bool complete)
  onStageAction;
  final Future<void> Function(
    CropActivityModel activity,
    _ActivityAction action,
  )
  onActivityAction;

  @override
  Widget build(BuildContext context) {
    final activitiesByStage = <String?, List<CropActivityModel>>{};

    for (final activity in activities) {
      activitiesByStage.putIfAbsent(activity.stageId, () => []).add(activity);
    }

    final knownStageIds = stages.map((stage) => stage.id).toSet();
    final unassignedActivities = activities
        .where(
          (activity) =>
              activity.stageId == null ||
              !knownStageIds.contains(activity.stageId),
        )
        .toList(growable: false);

    return Column(
      key: const Key('crop_detail_plan'),
      children: [
        for (var index = 0; index < stages.length; index++) ...[
          _StageCard(
            stage: stages[index],
            sowingDate: sowingDate,
            activities:
                activitiesByStage[stages[index].id] ??
                const <CropActivityModel>[],
            isLast: index == stages.length - 1 && unassignedActivities.isEmpty,
            actionId: actionId,
            canManage: canManage,
            onStageAction: onStageAction,
            onActivityAction: onActivityAction,
          ),
          if (index != stages.length - 1) const SizedBox(height: 12),
        ],
        if (unassignedActivities.isNotEmpty) ...[
          if (stages.isNotEmpty) const SizedBox(height: 12),
          _UnassignedActivities(
            activities: unassignedActivities,
            actionId: actionId,
            canManage: canManage,
            onActivityAction: onActivityAction,
          ),
        ],
      ],
    );
  }
}

class _StageCard extends StatelessWidget {
  const _StageCard({
    required this.stage,
    required this.sowingDate,
    required this.activities,
    required this.isLast,
    required this.actionId,
    required this.canManage,
    required this.onStageAction,
    required this.onActivityAction,
  });

  final CropStageModel stage;
  final DateTime sowingDate;
  final List<CropActivityModel> activities;
  final bool isLast;
  final String? actionId;
  final bool canManage;
  final Future<void> Function(CropStageModel stage, bool complete)
  onStageAction;
  final Future<void> Function(
    CropActivityModel activity,
    _ActivityAction action,
  )
  onActivityAction;

  @override
  Widget build(BuildContext context) {
    final color = _stageStatusColor(stage.status);
    final startDate = _stageDate(sowingDate, stage.startDay);
    final endDate = _stageDate(sowingDate, stage.endDay);

    return Container(
      key: Key('crop_detail_stage_${stage.id}'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 34,
                height: 34,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Center(
                  child: Text(
                    '${stage.stageOrder}',
                    style: TextStyle(
                      color: color,
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      stage.name,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${_formatDate(startDate)} - ${_formatDate(endDate)}',
                      style: const TextStyle(
                        color: AppColors.textHint,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _SmallStatusPill(status: stage.status.label, color: color),
            ],
          ),
          if (stage.description != null) ...[
            const SizedBox(height: 11),
            Text(
              stage.description!,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                height: 1.45,
              ),
            ),
          ],
          if (activities.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Divider(height: 1, color: AppColors.borderLight),
            const SizedBox(height: 10),
            for (var index = 0; index < activities.length; index++) ...[
              _ActivityRow(
                activity: activities[index],
                actionId: actionId,
                canManage: canManage,
                onAction: onActivityAction,
              ),
              if (index != activities.length - 1) const SizedBox(height: 8),
            ],
          ],
          if (canManage && stage.status == CropStageStatus.active) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    key: Key('crop_stage_complete_${stage.id}'),
                    onPressed: actionId == null
                        ? () => onStageAction(stage, true)
                        : null,
                    child: const Text('Complete stage'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextButton(
                    key: Key('crop_stage_skip_${stage.id}'),
                    onPressed: actionId == null
                        ? () => onStageAction(stage, false)
                        : null,
                    child: const Text('Skip stage'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _ActivityRow extends StatelessWidget {
  const _ActivityRow({
    required this.activity,
    required this.actionId,
    required this.canManage,
    required this.onAction,
  });

  final CropActivityModel activity;
  final String? actionId;
  final bool canManage;
  final Future<void> Function(
    CropActivityModel activity,
    _ActivityAction action,
  )
  onAction;

  bool get _isActionable =>
      activity.status == CropActivityStatus.pending ||
      activity.status == CropActivityStatus.inProgress;

  @override
  Widget build(BuildContext context) {
    final color = _activityStatusColor(activity.status);
    final isBusy = actionId == 'activity-${activity.id}';

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 7,
          height: 7,
          margin: const EdgeInsets.only(top: 5),
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      activity.title,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatDate(activity.scheduledDate),
                    style: const TextStyle(
                      color: AppColors.textHint,
                      fontSize: 10.5,
                    ),
                  ),
                  if (canManage && _isActionable)
                    SizedBox(
                      width: 32,
                      height: 28,
                      child: isBusy
                          ? const Padding(
                              padding: EdgeInsets.all(7),
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : PopupMenuButton<_ActivityAction>(
                              key: Key('crop_activity_actions_${activity.id}'),
                              padding: EdgeInsets.zero,
                              iconSize: 18,
                              onSelected: (action) =>
                                  onAction(activity, action),
                              itemBuilder: (_) => [
                                if (activity.status ==
                                    CropActivityStatus.pending)
                                  const PopupMenuItem<_ActivityAction>(
                                    value: _ActivityAction.start,
                                    child: Text('Start activity'),
                                  ),
                                if (activity.status ==
                                    CropActivityStatus.inProgress)
                                  const PopupMenuItem<_ActivityAction>(
                                    value: _ActivityAction.complete,
                                    child: Text('Complete activity'),
                                  ),
                                const PopupMenuItem<_ActivityAction>(
                                  value: _ActivityAction.reschedule,
                                  child: Text('Reschedule'),
                                ),
                                const PopupMenuItem<_ActivityAction>(
                                  value: _ActivityAction.skip,
                                  child: Text('Skip activity'),
                                ),
                                const PopupMenuItem<_ActivityAction>(
                                  value: _ActivityAction.delete,
                                  child: Text('Delete activity'),
                                ),
                              ],
                            ),
                    ),
                ],
              ),
              const SizedBox(height: 2),
              Text(
                '${activity.status.label} · '
                '${_activityTimingLabel(activity)} · '
                '${activity.priority.label} priority',
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 10.5,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _UnassignedActivities extends StatelessWidget {
  const _UnassignedActivities({
    required this.activities,
    required this.actionId,
    required this.canManage,
    required this.onActivityAction,
  });

  final List<CropActivityModel> activities;
  final String? actionId;
  final bool canManage;
  final Future<void> Function(
    CropActivityModel activity,
    _ActivityAction action,
  )
  onActivityAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Other activities',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 12),
          for (var index = 0; index < activities.length; index++) ...[
            _ActivityRow(
              activity: activities[index],
              actionId: actionId,
              canManage: canManage,
              onAction: onActivityAction,
            ),
            if (index != activities.length - 1) const SizedBox(height: 8),
          ],
        ],
      ),
    );
  }
}

class _PlanLoadingCard extends StatelessWidget {
  const _PlanLoadingCard({this.message = 'Loading the crop plan...'});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('crop_detail_loading'),
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Column(
        children: [
          const SizedBox(
            width: 26,
            height: 26,
            child: CircularProgressIndicator(
              color: AppColors.primary,
              strokeWidth: 2.4,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 12.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _PlanErrorCard extends StatelessWidget {
  const _PlanErrorCard({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('crop_detail_error'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.22)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.cloud_off_rounded,
                color: AppColors.warning,
                size: 21,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Plan unavailable',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      message,
                      style: const TextStyle(
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
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              key: const Key('crop_detail_retry_button'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: const Text('Retry'),
            ),
          ),
        ],
      ),
    );
  }
}

class _PlanEmptyCard extends StatelessWidget {
  const _PlanEmptyCard({
    required this.canGenerate,
    required this.onGenerate,
    required this.onRefresh,
  });

  final bool canGenerate;
  final Future<void> Function() onGenerate;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('crop_detail_empty'),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.borderLight),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.calendar_month_outlined,
            color: AppColors.textHint,
            size: 34,
          ),
          const SizedBox(height: 10),
          const Text(
            'No plan available yet',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            canGenerate
                ? 'Generate a crop plan to see stages and scheduled activities.'
                : 'Plans can only be generated while this crop is planned.',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              key: const Key('crop_detail_generate_button'),
              onPressed: canGenerate ? onGenerate : null,
              icon: const Icon(Icons.auto_awesome_rounded, size: 18),
              label: const Text('Generate Crop Plan'),
            ),
          ),
          const SizedBox(height: 8),
          TextButton.icon(
            key: const Key('crop_detail_empty_refresh_button'),
            onPressed: onRefresh,
            icon: const Icon(Icons.refresh_rounded, size: 17),
            label: const Text('Refresh'),
          ),
        ],
      ),
    );
  }
}

class _NotesCard extends StatelessWidget {
  const _NotesCard({required this.notes});

  final String notes;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Notes',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 13,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            notes,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 12,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.status, required this.color});

  final CropSeasonStatus status;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.16)),
      ),
      child: Text(
        status.label,
        style: TextStyle(
          color: color,
          fontSize: 10.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _SmallStatusPill extends StatelessWidget {
  const _SmallStatusPill({required this.status, required this.color});

  final String status;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.09),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        status,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _InfoPill extends StatelessWidget {
  const _InfoPill({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(9),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppColors.textSecondary, size: 13),
          const SizedBox(width: 5),
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

class _DetailRow extends StatelessWidget {
  const _DetailRow({
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
        Icon(icon, color: color, size: 16),
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

String _cleanError(Object error) {
  var message = error.toString().trim();

  while (message.startsWith('Exception: ')) {
    message = message.substring('Exception: '.length).trim();
  }

  return message.isEmpty
      ? 'Unable to load the crop plan. Please try again.'
      : message;
}

String _activityTimingLabel(CropActivityModel activity) {
  if (activity.status == CropActivityStatus.completed) {
    return 'Completed';
  }

  if (activity.status == CropActivityStatus.skipped) {
    return 'Skipped';
  }

  final now = DateTime.now();
  final today = DateTime(now.year, now.month, now.day);
  final scheduled = DateTime(
    activity.scheduledDate.year,
    activity.scheduledDate.month,
    activity.scheduledDate.day,
  );
  final daysUntil = scheduled.difference(today).inDays;

  if (daysUntil < 0) {
    return 'Overdue';
  }

  if (daysUntil == 0) {
    return 'Due today';
  }

  return 'Upcoming';
}

Color _statusColor(CropSeasonStatus status) {
  return switch (status) {
    CropSeasonStatus.planned => AppColors.warning,
    CropSeasonStatus.active => AppColors.primary,
    CropSeasonStatus.harvested => AppColors.info,
    CropSeasonStatus.cancelled => AppColors.error,
  };
}

Color _stageStatusColor(CropStageStatus status) {
  return switch (status) {
    CropStageStatus.pending => AppColors.textHint,
    CropStageStatus.active => AppColors.primary,
    CropStageStatus.completed => AppColors.success,
    CropStageStatus.skipped => AppColors.error,
  };
}

Color _activityStatusColor(CropActivityStatus status) {
  return switch (status) {
    CropActivityStatus.pending => AppColors.warning,
    CropActivityStatus.inProgress => AppColors.primary,
    CropActivityStatus.completed => AppColors.success,
    CropActivityStatus.skipped => AppColors.error,
  };
}

DateTime _stageDate(DateTime sowingDate, int day) {
  return sowingDate.add(Duration(days: day - 1));
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

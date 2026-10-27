import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../farm/data/models/farm_model.dart';
import '../../data/models/crop_plan_models.dart';
import '../../data/models/crop_season_create_input.dart';
import '../../data/models/crop_season_model.dart';
import '../../providers/crop_provider.dart';
import '../crop_creation_outcome.dart';
import 'crop_detail_screen.dart';

enum _PlanPhase { form, loading, review, error }

class CropCreateScreen extends StatefulWidget {
  const CropCreateScreen({
    super.key,
    required this.farm,
    required this.initialCropName,
    this.initialSowingDate,
  });

  final FarmModel farm;
  final String initialCropName;
  final DateTime? initialSowingDate;

  @override
  State<CropCreateScreen> createState() => _CropCreateScreenState();
}

class _CropCreateScreenState extends State<CropCreateScreen> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _cropNameController;
  late final TextEditingController _varietyController;
  late final TextEditingController _yearController;
  late final TextEditingController _landAreaController;
  late final TextEditingController _notesController;

  FarmModel? _selectedFarm;
  late FarmingSeason _season;
  late DateTime _sowingDate;
  DateTime? _expectedHarvestDate;
  String _landUnit = 'Acres';

  _PlanPhase _phase = _PlanPhase.form;
  bool _isSubmitting = false;
  String? _createError;
  CropSeasonModel? _createdCrop;

  @override
  void initState() {
    super.initState();

    final farm = widget.farm;
    final initialSowingDate = widget.initialSowingDate;
    final sowingDate = initialSowingDate == null
        ? _dateOnly(DateTime.now())
        : _dateOnly(initialSowingDate);

    _selectedFarm = farm;
    _season = _seasonForDate(sowingDate);
    _sowingDate = sowingDate;
    _landUnit = _normalizeLandUnit(farm.landUnit);

    _cropNameController = TextEditingController(
      text: widget.initialCropName.trim(),
    );
    _varietyController = TextEditingController();
    _yearController = TextEditingController(text: '${sowingDate.year}');
    _landAreaController = TextEditingController(text: _farmAreaText(farm));
    _notesController = TextEditingController();
  }

  @override
  void dispose() {
    _cropNameController.dispose();
    _varietyController.dispose();
    _yearController.dispose();
    _landAreaController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  bool get _isBusy => _isSubmitting || _phase == _PlanPhase.loading;

  Future<void> _submit() async {
    if (_isBusy) {
      return;
    }

    FocusManager.instance.primaryFocus?.unfocus();

    final farm = _selectedFarm;

    if (farm == null) {
      setState(() {
        _createError = 'Select a farm before creating a crop.';
      });
      return;
    }

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    final landArea = double.parse(_landAreaController.text.trim());

    final input = CropSeasonCreateInput(
      cropName: _cropNameController.text,
      cropVariety: _varietyController.text,
      season: _season,
      year: int.parse(_yearController.text.trim()),
      sowingDate: _sowingDate,
      expectedHarvestDate: _expectedHarvestDate,
      landArea: landArea,
      landUnit: _landUnit,
      notes: _notesController.text,
    );

    setState(() {
      _isSubmitting = true;
      _createError = null;
    });

    try {
      final crop = await context.read<CropProvider>().createCropSeason(
        farmId: farm.id,
        input: input,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _createdCrop = crop;
        _isSubmitting = false;
        _phase = _PlanPhase.loading;
      });

      await _generatePlan(crop, farm);
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isSubmitting = false;
        _createError = _cleanError(error);
      });
    }
  }

  Future<void> _generatePlan(CropSeasonModel crop, FarmModel farm) async {
    final provider = context.read<CropProvider>();

    try {
      await provider.generateCropPlan(crop: crop, farm: farm);
      await provider.loadCropPlan(crop.id);

      if (!mounted) {
        return;
      }

      setState(() {
        _phase = _PlanPhase.review;
      });

      unawaited(provider.refreshCrops());
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        _phase = _PlanPhase.error;
      });
    }
  }

  Future<void> _retryPlan() async {
    final crop = _createdCrop;
    final farm = _selectedFarm;

    if (crop == null || farm == null || _isBusy) {
      return;
    }

    setState(() {
      _phase = _PlanPhase.loading;
    });

    final provider = context.read<CropProvider>();

    try {
      if (!provider.hasGeneratedPlan) {
        await provider.generateCropPlan(crop: crop, farm: farm);
      }

      await provider.loadCropPlan(crop.id);

      if (!mounted) {
        return;
      }

      setState(() {
        _phase = _PlanPhase.review;
      });

      unawaited(provider.refreshCrops());
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        _phase = _PlanPhase.error;
      });
    }
  }

  Future<void> _checkSavedPlan() async {
    final crop = _createdCrop;

    if (crop == null || _isBusy) {
      return;
    }

    setState(() {
      _phase = _PlanPhase.loading;
    });

    final provider = context.read<CropProvider>();

    try {
      await provider.loadCropPlan(crop.id);

      if (!mounted) {
        return;
      }

      setState(() {
        _phase = _PlanPhase.review;
      });

      unawaited(provider.refreshCrops());
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        _phase = _PlanPhase.error;
      });
    }
  }

  Future<void> _pickSowingDate() async {
    if (_isBusy) {
      return;
    }

    final picked = await showDatePicker(
      context: context,
      initialDate: _sowingDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
      helpText: 'Select sowing date',
    );

    if (picked == null || !mounted) {
      return;
    }

    final normalized = _dateOnly(picked);

    setState(() {
      _sowingDate = normalized;
      _yearController.text = '${normalized.year}';

      if (_expectedHarvestDate != null &&
          _expectedHarvestDate!.isBefore(normalized)) {
        _expectedHarvestDate = null;
      }
    });
  }

  Future<void> _pickExpectedHarvestDate() async {
    if (_isBusy) {
      return;
    }

    final picked = await showDatePicker(
      context: context,
      initialDate: _expectedHarvestDate ?? _sowingDate,
      firstDate: _sowingDate,
      lastDate: DateTime(2100),
      helpText: 'Select expected harvest date',
    );

    if (picked == null || !mounted) {
      return;
    }

    setState(() {
      _expectedHarvestDate = _dateOnly(picked);
    });
  }

  CropCreationOutcome get _outcome {
    if (_createdCrop == null) {
      return CropCreationOutcome.none;
    }

    return _phase == _PlanPhase.review
        ? CropCreationOutcome.planReady
        : CropCreationOutcome.planFailed;
  }

  void _close() {
    if (_isBusy) {
      return;
    }

    Navigator.of(context).pop(_outcome);
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CropProvider>();

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) {
          _close();
        }
      },
      child: Scaffold(
        backgroundColor: AppColors.backgroundLight,
        appBar: AppBar(
          backgroundColor: AppColors.backgroundLight,
          elevation: 0,
          leading: IconButton(
            key: const Key('crop_create_back_button'),
            onPressed: _isBusy ? null : _close,
            icon: const Icon(
              Icons.arrow_back_rounded,
              color: AppColors.primaryDark,
            ),
          ),
          title: Text(_phase == _PlanPhase.form ? 'New crop' : 'Crop plan'),
        ),
        body: SafeArea(
          top: false,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final horizontalPadding = constraints.maxWidth < 380
                  ? 20.0
                  : 24.0;

              return Padding(
                padding: EdgeInsets.fromLTRB(
                  horizontalPadding,
                  8,
                  horizontalPadding,
                  0,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 560),
                    child: _buildBody(provider),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Future<void> _viewCropDetails() async {
    final crop = _createdCrop;

    if (crop == null) {
      return;
    }

    final provider = context.read<CropProvider>();

    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => ChangeNotifierProvider<CropProvider>.value(
          value: provider,
          child: CropDetailScreen(farm: widget.farm, crop: crop),
        ),
      ),
    );
  }

  Widget _buildBody(CropProvider provider) {
    if (_phase == _PlanPhase.loading) {
      return _PlanLoadingView(
        crop: _createdCrop,
        isGenerating: provider.isGeneratingPlan,
      );
    }

    if (_phase == _PlanPhase.review) {
      return _PlanReviewView(
        crop: _createdCrop!,
        summary: provider.planSummary,
        stages: provider.planStages,
        activities: provider.planActivities,
        onViewDetails: _viewCropDetails,
        onDone: _close,
      );
    }

    if (_phase == _PlanPhase.error) {
      return _PlanErrorView(
        crop: _createdCrop,
        hasGeneratedPlan: provider.hasGeneratedPlan,
        message: provider.planErrorMessage,
        onRetry: _retryPlan,
        onCheckSavedPlan: _checkSavedPlan,
        onClose: _close,
      );
    }

    return _buildForm();
  }

  Widget _buildForm() {
    final farm = _selectedFarm;
    final soilType = farm?.soilType?.trim();
    final location = _farmLocation(farm);

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        key: const Key('crop_create_scroll'),
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.only(top: 12, bottom: 28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Plan your next crop',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 26,
                fontWeight: FontWeight.w800,
                height: 1.14,
                letterSpacing: -0.7,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Add the crop season, then FarmMate will build a stage-by-stage plan from your farm details.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13.5,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 22),
            if (_createError != null) ...[
              _ErrorBanner(message: _createError!),
              const SizedBox(height: 16),
            ],
            _FormSection(
              title: 'Farm and crop',
              child: Column(
                children: [
                  if (farm != null)
                    Container(
                      key: const Key('crop_selected_farm'),
                      padding: const EdgeInsets.all(13),
                      decoration: BoxDecoration(
                        color: AppColors.primarySurface,
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 38,
                            height: 38,
                            decoration: BoxDecoration(
                              color: AppColors.surfaceLight,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.agriculture_rounded,
                              color: AppColors.primary,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 11),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Farm',
                                  style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 10.5,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  farm.farmName,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                if (location.isNotEmpty) ...[
                                  const SizedBox(height: 2),
                                  Text(
                                    location,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(
                                      color: AppColors.textSecondary,
                                      fontSize: 10.5,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 13),
                  TextFormField(
                    key: const Key('crop_name_field'),
                    controller: _cropNameController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'Crop name *',
                      hintText: 'e.g. Rice, Cotton, Tomato',
                      counterText: '',
                    ),
                    validator: (value) => _requiredText(
                      value,
                      label: 'Crop name',
                      minLength: 2,
                      maxLength: 100,
                    ),
                  ),
                  const SizedBox(height: 13),
                  TextFormField(
                    key: const Key('crop_variety_field'),
                    controller: _varietyController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'Variety (optional)',
                      hintText: 'e.g. BPT 5204',
                      counterText: '',
                    ),
                    validator: (value) => _optionalText(
                      value,
                      label: 'Variety',
                      minLength: 2,
                      maxLength: 100,
                    ),
                  ),
                  const SizedBox(height: 13),
                  DropdownButtonFormField<FarmingSeason>(
                    key: const Key('crop_season_field'),
                    initialValue: _season,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Season *'),
                    items: FarmingSeason.values
                        .map(
                          (season) => DropdownMenuItem(
                            value: season,
                            child: Text(season.label),
                          ),
                        )
                        .toList(growable: false),
                    onChanged: _isSubmitting
                        ? null
                        : (season) {
                            if (season == null) {
                              return;
                            }

                            setState(() {
                              _season = season;
                            });
                          },
                  ),
                  const SizedBox(height: 13),
                  TextFormField(
                    key: const Key('crop_year_field'),
                    controller: _yearController,
                    enabled: !_isSubmitting,
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.next,
                    maxLength: 4,
                    decoration: const InputDecoration(
                      labelText: 'Year *',
                      hintText: 'e.g. 2026',
                      counterText: '',
                    ),
                    validator: _validateYear,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _FormSection(
              title: 'Season timeline',
              child: Column(
                children: [
                  _DateField(
                    key: const Key('crop_sowing_date_field'),
                    label: 'Sowing date *',
                    value: _sowingDate,
                    icon: Icons.spa_outlined,
                    onTap: _isSubmitting ? null : _pickSowingDate,
                  ),
                  const SizedBox(height: 13),
                  _DateField(
                    key: const Key('crop_expected_harvest_field'),
                    label: 'Expected harvest (optional)',
                    value: _expectedHarvestDate,
                    icon: Icons.event_outlined,
                    onTap: _isSubmitting ? null : _pickExpectedHarvestDate,
                    onClear: _expectedHarvestDate == null || _isSubmitting
                        ? null
                        : () {
                            setState(() {
                              _expectedHarvestDate = null;
                            });
                          },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _FormSection(
              title: 'Land and notes',
              child: Column(
                children: [
                  TextFormField(
                    key: const Key('crop_land_area_field'),
                    controller: _landAreaController,
                    enabled: !_isSubmitting,
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(
                      labelText: 'Land area *',
                      hintText: 'e.g. 2.5',
                    ),
                    validator: _validateLandArea,
                  ),
                  const SizedBox(height: 13),
                  DropdownButtonFormField<String>(
                    key: const Key('crop_land_unit_field'),
                    initialValue: _landUnit,
                    isExpanded: true,
                    decoration: const InputDecoration(labelText: 'Land unit'),
                    items: const [
                      DropdownMenuItem(value: 'Acres', child: Text('Acres')),
                      DropdownMenuItem(
                        value: 'Hectares',
                        child: Text('Hectares'),
                      ),
                    ],
                    onChanged: _isSubmitting
                        ? null
                        : (unit) {
                            if (unit == null) {
                              return;
                            }

                            setState(() {
                              _landUnit = unit;
                            });
                          },
                  ),
                  const SizedBox(height: 13),
                  TextFormField(
                    key: const Key('crop_notes_field'),
                    controller: _notesController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.sentences,
                    minLines: 3,
                    maxLines: 5,
                    maxLength: 1000,
                    decoration: const InputDecoration(
                      labelText: 'Notes (optional)',
                      hintText:
                          'Anything FarmMate should know about this crop?',
                      alignLabelWithHint: true,
                    ),
                    validator: (value) =>
                        _optionalText(value, label: 'Notes', maxLength: 1000),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.auto_awesome_rounded,
                    color: AppColors.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _planContextText(
                        farmName: farm?.farmName,
                        location: location,
                        soilType: soilType,
                      ),
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12.5,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                key: const Key('crop_create_submit_button'),
                onPressed: _isSubmitting ? null : _submit,
                child: _isSubmitting
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 19,
                            height: 19,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.2,
                              color: Colors.white,
                            ),
                          ),
                          SizedBox(width: 10),
                          Text('Creating crop...'),
                        ],
                      )
                    : const Text('Create crop and generate plan'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String? _requiredText(
    String? value, {
    required String label,
    required int minLength,
    required int maxLength,
  }) {
    final text = value?.trim() ?? '';

    if (text.isEmpty) {
      return '$label is required';
    }

    if (text.length < minLength) {
      return '$label must be at least $minLength characters';
    }

    if (text.length > maxLength) {
      return '$label must be $maxLength characters or fewer';
    }

    return null;
  }

  String? _optionalText(
    String? value, {
    required String label,
    int? minLength,
    required int maxLength,
  }) {
    final text = value?.trim() ?? '';

    if (text.isEmpty) {
      return null;
    }

    final minimum = minLength ?? 0;

    if (minimum > 0 && text.length < minimum) {
      return '$label must be at least $minimum characters';
    }

    if (text.length > maxLength) {
      return '$label must be $maxLength characters or fewer';
    }

    return null;
  }

  String? _validateYear(String? value) {
    final text = value?.trim() ?? '';

    if (text.isEmpty) {
      return 'Year is required';
    }

    final year = int.tryParse(text);

    if (year == null || year < 2000 || year > 2100) {
      return 'Enter a year between 2000 and 2100';
    }

    return null;
  }

  String? _validateLandArea(String? value) {
    final text = value?.trim() ?? '';

    if (text.isEmpty) {
      return 'Land area is required';
    }

    final area = double.tryParse(text);

    if (area == null || area <= 0) {
      return 'Enter a land area greater than 0';
    }

    final farm = _selectedFarm;

    if (farm != null &&
        farm.landArea > 0 &&
        _sameLandUnit(farm.landUnit, _landUnit) &&
        area > farm.landArea) {
      return 'This is more than the farm area of ${_formatNumber(farm.landArea)} ${farm.landUnit}';
    }

    return null;
  }

  String _cleanError(Object error) {
    var message = error.toString().trim();

    while (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length).trim();
    }

    return message.isEmpty
        ? 'Unable to create your crop. Please try again.'
        : message;
  }
}

class _FormSection extends StatelessWidget {
  const _FormSection({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.045),
            blurRadius: 18,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 15),
          child,
        ],
      ),
    );
  }
}

class _DateField extends StatelessWidget {
  const _DateField({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    required this.onTap,
    this.onClear,
  });

  final String label;
  final DateTime? value;
  final IconData icon;
  final VoidCallback? onTap;
  final VoidCallback? onClear;

  @override
  Widget build(BuildContext context) {
    final date = value;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(icon),
          suffixIcon: onClear == null
              ? const Icon(Icons.calendar_today_outlined, size: 18)
              : IconButton(
                  onPressed: onClear,
                  tooltip: 'Clear date',
                  icon: const Icon(Icons.close_rounded, size: 18),
                ),
        ),
        child: Text(
          date == null ? 'Not set' : _formatDate(date),
          style: TextStyle(
            color: date == null ? AppColors.textHint : AppColors.textPrimary,
            fontSize: 15,
            fontWeight: date == null ? FontWeight.w400 : FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

class _PlanLoadingView extends StatelessWidget {
  const _PlanLoadingView({required this.crop, required this.isGenerating});

  final CropSeasonModel? crop;
  final bool isGenerating;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('crop_plan_loading'),
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(vertical: 32),
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
                  color: AppColors.primary,
                  strokeWidth: 2.6,
                ),
              ),
            ),
            const SizedBox(height: 22),
            Text(
              isGenerating
                  ? 'Generating your crop plan'
                  : 'Loading your crop plan',
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.primaryDark,
                fontSize: 21,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              crop == null
                  ? 'FarmMate is preparing your plan.'
                  : '${crop!.cropName} was added. FarmMate is preparing its stages and activities.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 18),
            const Text(
              'This can take a few seconds.',
              style: TextStyle(color: AppColors.textHint, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanReviewView extends StatelessWidget {
  const _PlanReviewView({
    required this.crop,
    required this.summary,
    required this.stages,
    required this.activities,
    required this.onViewDetails,
    required this.onDone,
  });

  final CropSeasonModel crop;
  final CropPlanSummary? summary;
  final List<CropStageModel> stages;
  final List<CropActivityModel> activities;
  final Future<void> Function() onViewDetails;
  final VoidCallback onDone;

  @override
  Widget build(BuildContext context) {
    final duration =
        summary?.estimatedDurationDays ?? _durationFromStages(stages);
    final activitiesByStage = <String, List<CropActivityModel>>{};

    for (final activity in activities) {
      final stageId = activity.stageId;

      if (stageId == null) {
        continue;
      }

      activitiesByStage.putIfAbsent(stageId, () => []).add(activity);
    }

    return CustomScrollView(
      key: const Key('crop_plan_review'),
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.only(top: 12, bottom: 28),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              const Text(
                'Your crop plan is ready',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  height: 1.14,
                  letterSpacing: -0.7,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Review the stages and activities before you start farming.',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 13.5,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 20),
              _PlanSummaryCard(
                crop: crop,
                durationDays: duration,
                stageCount: summary?.stagesCreated ?? stages.length,
                activityCount: summary?.activitiesCreated ?? activities.length,
              ),
              const SizedBox(height: 20),
              const Text(
                'Crop stages',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 5),
              const Text(
                'Stage dates are estimated from your sowing date.',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
              const SizedBox(height: 14),
              for (var index = 0; index < stages.length; index++) ...[
                _StageCard(
                  stage: stages[index],
                  activities: activitiesByStage[stages[index].id] ?? const [],
                  sowingDate: crop.sowingDate,
                  isLast: index == stages.length - 1,
                ),
                if (index != stages.length - 1) const SizedBox(height: 12),
              ],
              const SizedBox(height: 22),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  key: const Key('crop_plan_view_details_button'),
                  onPressed: onViewDetails,
                  icon: const Icon(Icons.visibility_outlined, size: 18),
                  label: const Text('View Crop Details'),
                ),
              ),
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  key: const Key('crop_plan_done_button'),
                  onPressed: onDone,
                  child: const Text('Go to Crops'),
                ),
              ),
            ]),
          ),
        ),
      ],
    );
  }
}

class _PlanSummaryCard extends StatelessWidget {
  const _PlanSummaryCard({
    required this.crop,
    required this.durationDays,
    required this.stageCount,
    required this.activityCount,
  });

  final CropSeasonModel crop;
  final int durationDays;
  final int stageCount;
  final int activityCount;

  @override
  Widget build(BuildContext context) {
    final variety = crop.cropVariety;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.05),
            blurRadius: 18,
            offset: const Offset(0, 7),
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
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(15),
                ),
                child: const Icon(
                  Icons.grass_rounded,
                  color: AppColors.primary,
                  size: 25,
                ),
              ),
              const SizedBox(width: 13),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      crop.cropName,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    if (variety != null) ...[
                      const SizedBox(height: 3),
                      Text(
                        variety,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                    ],
                    const SizedBox(height: 4),
                    Text(
                      '${crop.season.label} ${crop.year}',
                      style: const TextStyle(
                        color: AppColors.textHint,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _SummaryPill(
                icon: Icons.timelapse_rounded,
                label: '$durationDays days',
              ),
              _SummaryPill(
                icon: Icons.account_tree_outlined,
                label: '$stageCount stages',
              ),
              _SummaryPill(
                icon: Icons.checklist_rounded,
                label: '$activityCount activities',
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              const Icon(
                Icons.spa_outlined,
                color: AppColors.textHint,
                size: 15,
              ),
              const SizedBox(width: 7),
              const Text(
                'Sowing date',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 11.5,
                ),
              ),
              const Spacer(),
              Text(
                _formatDate(crop.sowingDate),
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 11.5,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SummaryPill extends StatelessWidget {
  const _SummaryPill({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: AppColors.textSecondary, size: 14),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _StageCard extends StatelessWidget {
  const _StageCard({
    required this.stage,
    required this.activities,
    required this.sowingDate,
    required this.isLast,
  });

  final CropStageModel stage;
  final List<CropActivityModel> activities;
  final DateTime sowingDate;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final statusColor = _stageColor(stage.status);
    final startDate = _stageDate(sowingDate, stage.startDay);
    final endDate = _stageDate(sowingDate, stage.endDay);
    final description = stage.description;

    return Container(
      key: Key('crop_stage_${stage.id}'),
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
                  color: statusColor.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Center(
                  child: Text(
                    '${stage.stageOrder}',
                    style: TextStyle(
                      color: statusColor,
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      stage.name,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15.5,
                        fontWeight: FontWeight.w800,
                        height: 1.25,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_formatDate(startDate)} - ${_formatDate(endDate)}',
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _StageChip(status: stage.status, color: statusColor),
            ],
          ),
          if (description != null) ...[
            const SizedBox(height: 11),
            Text(
              description,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12.5,
                height: 1.4,
              ),
            ),
          ],
          if (activities.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Divider(height: 1, color: AppColors.borderLight),
            const SizedBox(height: 12),
            for (var index = 0; index < activities.length; index++) ...[
              _ActivityRow(activity: activities[index]),
              if (index != activities.length - 1) const SizedBox(height: 11),
            ],
          ],
        ],
      ),
    );
  }
}

class _StageChip extends StatelessWidget {
  const _StageChip({required this.status, required this.color});

  final CropStageStatus status;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        status.label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _ActivityRow extends StatelessWidget {
  const _ActivityRow({required this.activity});

  final CropActivityModel activity;

  @override
  Widget build(BuildContext context) {
    final priorityColor = _priorityColor(activity.priority);
    final description = activity.description;
    final duration = activity.estimatedDurationMinutes;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 5),
          child: Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: priorityColor,
              shape: BoxShape.circle,
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      activity.title,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        height: 1.3,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatDate(activity.scheduledDate),
                    style: const TextStyle(
                      color: AppColors.textHint,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 3),
              Text(
                [
                  _humanizeWire(activity.activityType),
                  activity.priority.label,
                  if (duration != null) '$duration min',
                ].join(' • '),
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 10.5,
                ),
              ),
              if (description != null) ...[
                const SizedBox(height: 4),
                Text(
                  description,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textHint,
                    fontSize: 11,
                    height: 1.35,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _PlanErrorView extends StatelessWidget {
  const _PlanErrorView({
    required this.crop,
    required this.hasGeneratedPlan,
    required this.message,
    required this.onRetry,
    required this.onCheckSavedPlan,
    required this.onClose,
  });

  final CropSeasonModel? crop;
  final bool hasGeneratedPlan;
  final String? message;
  final Future<void> Function() onRetry;
  final Future<void> Function() onCheckSavedPlan;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final cropName = crop?.cropName;

    return SingleChildScrollView(
      key: const Key('crop_plan_error'),
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(vertical: 34),
      child: Column(
        children: [
          Container(
            width: 78,
            height: 78,
            decoration: BoxDecoration(
              color: AppColors.error.withValues(alpha: 0.07),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.cloud_off_rounded,
              color: AppColors.error,
              size: 33,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            cropName == null
                ? 'Crop not created'
                : hasGeneratedPlan
                ? 'Plan created, review unavailable'
                : 'Crop added, plan not generated',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.primaryDark,
              fontSize: 21,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            message ??
                (cropName == null
                    ? 'FarmMate could not create this crop. Please try again.'
                    : 'Your crop was saved. FarmMate could not finish the plan.'),
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
              height: 1.5,
            ),
          ),
          if (cropName != null) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Text(
                '$cropName is saved as a planned crop.',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppColors.primary,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
          const SizedBox(height: 22),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              key: const Key('crop_plan_retry_button'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded, size: 19),
              label: Text(
                hasGeneratedPlan ? 'Retry loading review' : 'Retry plan',
              ),
            ),
          ),
          if (cropName != null) ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                key: const Key('crop_plan_check_button'),
                onPressed: onCheckSavedPlan,
                child: const Text('Check saved plan'),
              ),
            ),
          ],
          const SizedBox(height: 8),
          TextButton(
            key: const Key('crop_plan_error_close_button'),
            onPressed: onClose,
            child: const Text('Back to crops'),
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.28)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.error_outline_rounded,
            color: AppColors.error,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppColors.error,
                fontSize: 12.5,
                height: 1.4,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

int _durationFromStages(List<CropStageModel> stages) {
  if (stages.isEmpty) {
    return 0;
  }

  return stages
      .map((stage) => stage.endDay)
      .reduce((current, value) => value > current ? value : current);
}

DateTime _stageDate(DateTime sowingDate, int day) {
  return sowingDate.add(Duration(days: day - 1));
}

DateTime _dateOnly(DateTime date) {
  return DateTime(date.year, date.month, date.day);
}

FarmingSeason _seasonForDate(DateTime date) {
  if (date.month >= 6 && date.month <= 10) {
    return FarmingSeason.kharif;
  }

  if (date.month == 11 || date.month <= 3) {
    return FarmingSeason.rabi;
  }

  return FarmingSeason.zaid;
}

String _normalizeLandUnit(String? unit) {
  final normalized = unit?.trim().toLowerCase();

  if (normalized == 'hectares' || normalized == 'hectare') {
    return 'Hectares';
  }

  return 'Acres';
}

bool _sameLandUnit(String first, String second) {
  return _normalizeLandUnit(first) == _normalizeLandUnit(second);
}

String _farmAreaText(FarmModel? farm) {
  if (farm == null || farm.landArea <= 0) {
    return '';
  }

  return _formatNumber(farm.landArea);
}

String _farmLocation(FarmModel? farm) {
  if (farm == null) {
    return '';
  }

  return [
    farm.village,
    farm.mandal,
    farm.district,
    farm.state,
  ].map((value) => value.trim()).where((value) => value.isNotEmpty).join(', ');
}

String _planContextText({
  required String? farmName,
  required String location,
  required String? soilType,
}) {
  final farm = farmName?.trim();

  if (farm == null || farm.isEmpty) {
    return 'FarmMate uses your farm location and soil details to build the plan.';
  }

  final parts = <String>['FarmMate will plan for $farm'];

  if (location.isNotEmpty) {
    parts.add('at $location');
  }

  if (soilType != null && soilType.isNotEmpty) {
    parts.add('with $soilType soil');
  }

  return '${parts.join(' ')}.';
}

Color _stageColor(CropStageStatus status) {
  return switch (status) {
    CropStageStatus.pending => AppColors.warning,
    CropStageStatus.active => AppColors.primary,
    CropStageStatus.completed => AppColors.info,
    CropStageStatus.skipped => AppColors.textHint,
  };
}

Color _priorityColor(CropActivityPriority priority) {
  return switch (priority) {
    CropActivityPriority.low => AppColors.textHint,
    CropActivityPriority.medium => AppColors.warning,
    CropActivityPriority.high => AppColors.error,
    CropActivityPriority.critical => AppColors.terracotta,
  };
}

String _humanizeWire(String value) {
  final words = value
      .trim()
      .toLowerCase()
      .split(RegExp(r'[_\s]+'))
      .where((word) => word.isNotEmpty)
      .toList();

  if (words.isEmpty) {
    return value;
  }

  final first = words.first;

  return [
    '${first[0].toUpperCase()}${first.substring(1)}',
    ...words.skip(1),
  ].join(' ');
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

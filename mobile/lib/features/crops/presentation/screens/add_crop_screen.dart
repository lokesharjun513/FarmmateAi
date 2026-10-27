import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../farm/data/models/farm_model.dart';
import '../../data/models/crop_recommendation_model.dart';
import '../../providers/crop_provider.dart';
import '../../providers/crop_recommendation_provider.dart';
import '../crop_creation_outcome.dart';
import 'crop_create_screen.dart';

class AddCropScreen extends StatefulWidget {
  const AddCropScreen({super.key});

  @override
  State<AddCropScreen> createState() => _AddCropScreenState();
}

class _AddCropScreenState extends State<AddCropScreen> {
  late final TextEditingController _manualCropController;
  late final FocusNode _manualFocusNode;
  late final ScrollController _scrollController;
  final GlobalKey _manualSectionKey = GlobalKey();

  FarmModel? _selectedFarm;
  String _selectedCropName = '';
  String? _selectedRecommendationName;
  RecommendedCropModel? _selectedRecommendation;
  DateTime? _selectedSowingDate;
  bool _isOpeningDetails = false;

  @override
  void initState() {
    super.initState();
    _manualCropController = TextEditingController();
    _manualFocusNode = FocusNode();
    _scrollController = ScrollController();
    _selectedSowingDate = _today();
  }

  @override
  void dispose() {
    _manualCropController.dispose();
    _manualFocusNode.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  bool get _canContinue {
    final cropName = _selectedCropName.trim();

    return _selectedFarm != null &&
        cropName.length >= 2 &&
        cropName.length <= 100 &&
        _isValidSowingDate(_selectedSowingDate) &&
        !_isOpeningDetails;
  }

  void _selectFarm(String? farmId) {
    if (farmId == null) {
      return;
    }

    final farms = context.read<CropProvider>().farms;
    FarmModel? farm;

    for (final item in farms) {
      if (item.id == farmId) {
        farm = item;
        break;
      }
    }

    if (farm == null) {
      return;
    }

    setState(() {
      _selectedFarm = farm;
      _selectedCropName = '';
      _selectedRecommendationName = null;
      _selectedRecommendation = null;
      _selectedSowingDate = _today();
      _manualCropController.clear();
    });

    context.read<CropRecommendationProvider>().loadRecommendations(farm.id);
  }

  void _selectRecommendation(
    RecommendedCropModel crop,
    CropRecommendationProvider provider,
  ) {
    final cropName = crop.cropName.trim();

    setState(() {
      _selectedCropName = cropName;
      _selectedRecommendationName = cropName;
      _selectedRecommendation = crop;
      _selectedSowingDate = _isValidSowingDate(provider.recommendedSowingDate)
          ? _dateOnly(provider.recommendedSowingDate!)
          : _today();
      _manualCropController.value = TextEditingValue(
        text: cropName,
        selection: TextSelection.collapsed(offset: cropName.length),
      );
    });
  }

  void _onManualCropChanged(String value) {
    final cropName = value.trim();

    setState(() {
      _selectedCropName = cropName;

      if (_selectedRecommendationName != cropName) {
        _selectedRecommendationName = null;
        _selectedRecommendation = null;
      }
    });
  }

  void _clearCropSelection() {
    setState(() {
      _selectedCropName = '';
      _selectedRecommendationName = null;
      _selectedRecommendation = null;
      _manualCropController.clear();
    });
  }

  void _chooseManually() {
    _manualFocusNode.requestFocus();

    final manualContext = _manualSectionKey.currentContext;

    if (manualContext != null) {
      Scrollable.ensureVisible(
        manualContext,
        duration: const Duration(milliseconds: 280),
        curve: Curves.easeOutCubic,
        alignment: 0.18,
      );
    }
  }

  Future<void> _pickSowingDate() async {
    final initialDate = _selectedSowingDate ?? _today();
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
      helpText: 'Select sowing date',
    );

    if (picked == null || !mounted) {
      return;
    }

    setState(() {
      _selectedSowingDate = _dateOnly(picked);
    });
  }

  Future<void> _continueToDetails() async {
    if (!_canContinue) {
      return;
    }

    final farm = _selectedFarm;

    if (farm == null) {
      return;
    }

    FocusManager.instance.primaryFocus?.unfocus();

    final cropProvider = context.read<CropProvider>();
    final cropName = _selectedCropName.trim();
    final sowingDate = _selectedSowingDate;

    setState(() {
      _isOpeningDetails = true;
    });

    final outcome = await Navigator.of(context).push<CropCreationOutcome>(
      MaterialPageRoute(
        builder: (_) => ChangeNotifierProvider<CropProvider>.value(
          value: cropProvider,
          child: CropCreateScreen(
            farm: farm,
            initialCropName: cropName,
            initialSowingDate: sowingDate,
          ),
        ),
      ),
    );

    if (!mounted) {
      return;
    }

    setState(() {
      _isOpeningDetails = false;
    });

    final cropWasSaved =
        outcome?.cropWasSaved ?? cropProvider.createdCrop != null;

    if (cropWasSaved) {
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cropProvider = context.watch<CropProvider>();
    final recommendationProvider = context.watch<CropRecommendationProvider>();

    return PopScope(
      canPop: !_isOpeningDetails,
      child: Scaffold(
        backgroundColor: AppColors.backgroundLight,
        appBar: AppBar(
          backgroundColor: AppColors.backgroundLight,
          elevation: 0,
          leading: IconButton(
            key: const Key('add_crop_back_button'),
            onPressed: _isOpeningDetails
                ? null
                : () => Navigator.of(context).pop(false),
            icon: const Icon(
              Icons.arrow_back_rounded,
              color: AppColors.primaryDark,
            ),
          ),
          title: const Text('Add crop'),
        ),
        body: SafeArea(
          top: false,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final horizontalPadding = constraints.maxWidth < 380
                  ? 20.0
                  : 24.0;

              return SingleChildScrollView(
                key: const Key('add_crop_scroll'),
                controller: _scrollController,
                physics: const BouncingScrollPhysics(),
                padding: EdgeInsets.fromLTRB(
                  horizontalPadding,
                  12,
                  horizontalPadding,
                  28,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 560),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Text(
                          'Choose your crop',
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
                          'Select a farm to get AI recommendations, or enter the crop you want to grow.',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 13.5,
                            height: 1.45,
                          ),
                        ),
                        const SizedBox(height: 22),
                        _FarmSection(
                          farms: cropProvider.farms,
                          selectedFarm: _selectedFarm,
                          enabled: !_isOpeningDetails,
                          onChanged: _selectFarm,
                        ),
                        const SizedBox(height: 16),
                        if (_selectedFarm == null)
                          const _RecommendationInitial()
                        else ...[
                          _buildRecommendations(recommendationProvider),
                          const SizedBox(height: 16),
                          _ManualCropSection(
                            sectionKey: _manualSectionKey,
                            controller: _manualCropController,
                            focusNode: _manualFocusNode,
                            selectedCropName: _selectedCropName,
                            isSelectedRemotely:
                                _selectedRecommendationName != null,
                            enabled: !_isOpeningDetails,
                            onChanged: _onManualCropChanged,
                            onClear: _clearCropSelection,
                          ),
                          if (_selectedCropName.trim().isNotEmpty) ...[
                            const SizedBox(height: 16),
                            _SelectedCropSummary(
                              cropName: _selectedCropName.trim(),
                              recommendation: _selectedRecommendation,
                              enabled: !_isOpeningDetails,
                              onChange: _clearCropSelection,
                            ),
                          ],
                          const SizedBox(height: 16),
                          _SowingDateSection(
                            date: _selectedSowingDate,
                            isRecommended: _selectedRecommendation != null,
                            enabled: !_isOpeningDetails,
                            onPick: _pickSowingDate,
                          ),
                        ],
                        const SizedBox(height: 20),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            key: const Key(
                              'crop_recommendation_continue_button',
                            ),
                            onPressed: _canContinue ? _continueToDetails : null,
                            child: _isOpeningDetails
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
                                      Flexible(
                                        child: Text(
                                          'Opening crop details...',
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                    ],
                                  )
                                : const Text('Continue to crop details'),
                          ),
                        ),
                        if (_selectedFarm != null &&
                            _selectedCropName.trim().isEmpty) ...[
                          const SizedBox(height: 10),
                          const Text(
                            'Select a recommended crop or enter a crop name to continue.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: AppColors.textHint,
                              fontSize: 11.5,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildRecommendations(CropRecommendationProvider provider) {
    final farm = _selectedFarm;

    if (farm == null) {
      return const SizedBox.shrink();
    }

    if (provider.isInitialLoading) {
      return _RecommendationLoading(farmName: farm.farmName);
    }

    if (provider.hasError) {
      return _RecommendationError(
        message:
            provider.errorMessage ??
            'Unable to generate crop recommendations. Please try again.',
        onRetry: provider.retry,
        onChooseManually: _chooseManually,
      );
    }

    if (!provider.hasLoaded) {
      return _RecommendationLoading(farmName: farm.farmName);
    }

    final crops = provider.recommendedCrops.take(3).toList(growable: false);

    if (crops.isEmpty) {
      return _RecommendationEmpty(farmName: farm.farmName);
    }

    return Column(
      key: const Key('crop_recommendations'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Recommended for ${farm.farmName}',
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 16,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 5),
        const Text(
          'Confidence is FarmMate AI\'s estimated suitability for this farm, from 0 to 100. It is not a yield guarantee.',
          style: TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12,
            height: 1.4,
          ),
        ),
        const SizedBox(height: 13),
        for (var index = 0; index < crops.length; index++)
          Padding(
            padding: EdgeInsets.only(
              bottom: index == crops.length - 1 ? 0 : 11,
            ),
            child: _RecommendationCard(
              crop: crops[index],
              index: index,
              sowingDate: provider.recommendedSowingDate,
              isSelected:
                  _selectedRecommendationName == crops[index].cropName.trim(),
              onSelect: () => _selectRecommendation(crops[index], provider),
            ),
          ),
      ],
    );
  }
}

class _FarmSection extends StatelessWidget {
  const _FarmSection({
    required this.farms,
    required this.selectedFarm,
    required this.enabled,
    required this.onChanged,
  });

  final List<FarmModel> farms;
  final FarmModel? selectedFarm;
  final bool enabled;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Farm',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 12),
          if (farms.isEmpty)
            const Text(
              'Add a farm before choosing a crop.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            )
          else
            DropdownButtonFormField<String>(
              key: const Key('add_crop_farm_field'),
              initialValue: selectedFarm?.id,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Select a farm *'),
              hint: const Text('Select a farm'),
              items: farms
                  .map(
                    (farm) => DropdownMenuItem(
                      value: farm.id,
                      child: Text(
                        farm.farmName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  )
                  .toList(growable: false),
              onChanged: enabled ? onChanged : null,
            ),
          if (selectedFarm != null) ...[
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.location_on_outlined,
                  color: AppColors.textHint,
                  size: 16,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    [
                      selectedFarm!.locationLabel,
                      if (selectedFarm!.isPrimary) 'Primary farm',
                    ].where((value) => value.trim().isNotEmpty).join(' • '),
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11.5,
                      height: 1.4,
                    ),
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

class _RecommendationInitial extends StatelessWidget {
  const _RecommendationInitial();

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('crop_recommendation_initial'),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.auto_awesome_rounded, color: AppColors.primary, size: 21),
          SizedBox(width: 11),
          Expanded(
            child: Text(
              'Choose a farm to get crop recommendations based on its location, soil, water, and current weather.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12.5,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RecommendationLoading extends StatelessWidget {
  const _RecommendationLoading({required this.farmName});

  final String farmName;

  @override
  Widget build(BuildContext context) {
    return _Card(
      key: const Key('crop_recommendation_loading'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.auto_awesome_rounded,
                color: AppColors.primary,
                size: 21,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Finding suitable crops for $farmName...',
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13.5,
                    fontWeight: FontWeight.w700,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 13),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: const LinearProgressIndicator(
              minHeight: 4,
              color: AppColors.primary,
              backgroundColor: AppColors.surfaceMuted,
            ),
          ),
          const SizedBox(height: 9),
          const Text(
            'Checking farm location, soil, water and weather. This may take a few seconds.',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11.5,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _RecommendationEmpty extends StatelessWidget {
  const _RecommendationEmpty({required this.farmName});

  final String farmName;

  @override
  Widget build(BuildContext context) {
    return _Card(
      key: const Key('crop_recommendation_empty'),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline_rounded,
            color: AppColors.textSecondary,
            size: 21,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'No AI recommendations were returned for $farmName. You can enter the crop manually below.',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12.5,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RecommendationError extends StatelessWidget {
  const _RecommendationError({
    required this.message,
    required this.onRetry,
    required this.onChooseManually,
  });

  final String message;
  final Future<void> Function() onRetry;
  final VoidCallback onChooseManually;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('crop_recommendation_error'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.22)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.wb_cloudy_outlined,
                color: AppColors.warning,
                size: 20,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Recommendations unavailable',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 13.5,
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
              key: const Key('crop_recommendation_retry_button'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: const Text('Try again'),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: TextButton.icon(
              key: const Key('crop_recommendation_manual_button'),
              onPressed: onChooseManually,
              icon: const Icon(Icons.edit_outlined, size: 17),
              label: const Text('Choose manually'),
            ),
          ),
        ],
      ),
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({
    required this.crop,
    required this.index,
    required this.sowingDate,
    required this.isSelected,
    required this.onSelect,
  });

  final RecommendedCropModel crop;
  final int index;
  final DateTime? sowingDate;
  final bool isSelected;
  final VoidCallback onSelect;

  @override
  Widget build(BuildContext context) {
    final confidence = crop.confidence / 100;

    return Material(
      key: Key('crop_recommendation_card_$index'),
      color: AppColors.surfaceLight,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onSelect,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected ? AppColors.primary : AppColors.borderLight,
              width: isSelected ? 1.5 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 41,
                    height: 41,
                    decoration: BoxDecoration(
                      color: AppColors.primarySurface,
                      borderRadius: BorderRadius.circular(13),
                    ),
                    child: const Icon(
                      Icons.grass_rounded,
                      color: AppColors.primary,
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 11),
                  Expanded(
                    child: Text(
                      crop.cropName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                        height: 1.2,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (isSelected)
                    const Icon(
                      Icons.check_circle_rounded,
                      color: AppColors.primary,
                      size: 22,
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Suitability confidence',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${crop.confidence}/100',
                    style: const TextStyle(
                      color: AppColors.primary,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(5),
                child: LinearProgressIndicator(
                  value: confidence,
                  minHeight: 5,
                  backgroundColor: AppColors.surfaceMuted,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    AppColors.primary,
                  ),
                ),
              ),
              const SizedBox(height: 11),
              Text(
                crop.reason,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12.5,
                  height: 1.45,
                ),
              ),
              if (sowingDate != null) ...[
                const SizedBox(height: 11),
                Row(
                  children: [
                    const Icon(
                      Icons.event_outlined,
                      color: AppColors.textHint,
                      size: 15,
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Recommended sowing: ${_formatDate(sowingDate!)}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: AppColors.textHint,
                          fontSize: 11.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: onSelect,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: isSelected
                        ? AppColors.primary
                        : AppColors.textSecondary,
                    side: BorderSide(
                      color: isSelected
                          ? AppColors.primary
                          : AppColors.borderStrong,
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    textStyle: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: Text(isSelected ? 'Selected' : 'Select this crop'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ManualCropSection extends StatelessWidget {
  const _ManualCropSection({
    required this.sectionKey,
    required this.controller,
    required this.focusNode,
    required this.selectedCropName,
    required this.isSelectedRemotely,
    required this.enabled,
    required this.onChanged,
    required this.onClear,
  });

  final GlobalKey sectionKey;
  final TextEditingController controller;
  final FocusNode focusNode;
  final String selectedCropName;
  final bool isSelectedRemotely;
  final bool enabled;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final cropName = selectedCropName.trim();
    final isTooShort = cropName.isNotEmpty && cropName.length < 2;

    return _Card(
      key: sectionKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Manual crop name',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 5),
          const Text(
            'Enter any crop you plan to grow. A verified crop catalogue is not connected yet.',
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 13),
          TextField(
            key: const Key('crop_manual_name_field'),
            controller: controller,
            focusNode: focusNode,
            enabled: enabled,
            textCapitalization: TextCapitalization.words,
            textInputAction: TextInputAction.done,
            maxLength: 100,
            onChanged: onChanged,
            decoration: InputDecoration(
              labelText: 'Crop name *',
              hintText: 'e.g. Rice, Cotton, Tomato',
              counterText: '',
              errorText: isTooShort
                  ? 'Crop name must be at least 2 characters'
                  : null,
              suffixIcon: cropName.isEmpty
                  ? null
                  : IconButton(
                      key: const Key('crop_manual_clear_button'),
                      onPressed: enabled ? onClear : null,
                      tooltip: 'Clear crop',
                      icon: const Icon(Icons.close_rounded, size: 18),
                    ),
            ),
          ),
          if (isSelectedRemotely && cropName.isNotEmpty) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(
                  Icons.check_circle_rounded,
                  color: AppColors.primary,
                  size: 17,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Selected: $cropName',
                    style: const TextStyle(
                      color: AppColors.primary,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
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

class _SelectedCropSummary extends StatelessWidget {
  const _SelectedCropSummary({
    required this.cropName,
    required this.recommendation,
    required this.enabled,
    required this.onChange,
  });

  final String cropName;
  final RecommendedCropModel? recommendation;
  final bool enabled;
  final VoidCallback onChange;

  @override
  Widget build(BuildContext context) {
    final recommended = recommendation;

    return _Card(
      key: const Key('add_crop_selected_summary'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(13),
                ),
                child: const Icon(
                  Icons.check_circle_outline_rounded,
                  color: AppColors.primary,
                  size: 21,
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Selected crop',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      cropName,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              TextButton(
                key: const Key('add_crop_change_crop_button'),
                onPressed: enabled ? onChange : null,
                child: const Text('Change Crop'),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: BoxDecoration(
              color: recommended == null
                  ? AppColors.surfaceMuted
                  : AppColors.primary.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Icon(
                  recommended == null
                      ? Icons.edit_outlined
                      : Icons.auto_awesome_rounded,
                  color: recommended == null
                      ? AppColors.textSecondary
                      : AppColors.primary,
                  size: 15,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    recommended == null
                        ? 'Manual entry (unverified)'
                        : 'AI recommendation • ${recommended.confidence}/100 suitability',
                    style: TextStyle(
                      color: recommended == null
                          ? AppColors.textSecondary
                          : AppColors.primary,
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (recommended != null) ...[
            const SizedBox(height: 9),
            Text(
              recommended.reason,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 11.5,
                height: 1.4,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _SowingDateSection extends StatelessWidget {
  const _SowingDateSection({
    required this.date,
    required this.isRecommended,
    required this.enabled,
    required this.onPick,
  });

  final DateTime? date;
  final bool isRecommended;
  final bool enabled;
  final Future<void> Function() onPick;

  @override
  Widget build(BuildContext context) {
    final sowingDate = date;

    return _Card(
      key: const Key('add_crop_sowing_date_section'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Sowing date *',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              TextButton(
                key: const Key('add_crop_sowing_date_button'),
                onPressed: enabled ? onPick : null,
                child: Text(sowingDate == null ? 'Choose date' : 'Change'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.surfaceMuted,
              borderRadius: BorderRadius.circular(13),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.event_outlined,
                  color: AppColors.primary,
                  size: 18,
                ),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    sowingDate == null
                        ? 'Choose the planned sowing date'
                        : _formatDate(sowingDate),
                    style: TextStyle(
                      color: sowingDate == null
                          ? AppColors.textHint
                          : AppColors.textPrimary,
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            sowingDate == null
                ? 'A valid sowing date is required before continuing.'
                : isRecommended
                ? 'Prefilled from the recommendation. You can change it.'
                : 'Used to estimate the crop season and plan dates.',
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11.5,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.04),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: child,
    );
  }
}

DateTime _today() {
  return _dateOnly(DateTime.now());
}

DateTime _dateOnly(DateTime date) {
  return DateTime(date.year, date.month, date.day);
}

bool _isValidSowingDate(DateTime? date) {
  return date != null && date.year >= 2000 && date.year <= 2100;
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

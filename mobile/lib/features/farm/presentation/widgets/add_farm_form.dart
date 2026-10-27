import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../weather/location_service.dart';
import '../../data/farm_repository.dart';
import '../../data/models/farm_model.dart';

class AddFarmForm extends StatefulWidget {
  const AddFarmForm({
    super.key,
    required this.onContinue,
    this.initialLocation,
    this.repository,
    this.successActionLabel = 'Go to dashboard',
    this.isPrimary = true,
    this.createFarm,
    this.onCreated,
    this.onSubmittingChanged,
  });

  final ValueChanged<FarmModel> onContinue;
  final LocationData? initialLocation;
  final FarmRepository? repository;
  final String successActionLabel;
  final bool isPrimary;
  final Future<FarmModel> Function(FarmCreateInput input)? createFarm;
  final ValueChanged<FarmModel>? onCreated;
  final ValueChanged<bool>? onSubmittingChanged;

  @override
  State<AddFarmForm> createState() => _AddFarmFormState();
}

class _AddFarmFormState extends State<AddFarmForm> {
  final _formKey = GlobalKey<FormState>();

  late final FarmRepository _repository;
  late final Future<FarmModel> Function(FarmCreateInput input) _createFarm;

  late final TextEditingController _farmNameController;
  late final TextEditingController _stateController;
  late final TextEditingController _districtController;
  late final TextEditingController _mandalController;
  late final TextEditingController _villageController;
  late final TextEditingController _landAreaController;
  late final TextEditingController _soilTypeController;

  String _landUnit = 'Acres';
  String? _waterSource;
  String? _waterAvailability;
  String? _irrigationMethod;

  double? _latitude;
  double? _longitude;

  bool _isSubmitting = false;
  String? _errorMessage;
  FarmModel? _createdFarm;

  @override
  void initState() {
    super.initState();

    _repository = widget.repository ?? FarmRepository();
    _createFarm = widget.createFarm ?? _repository.createFarm;

    final location = widget.initialLocation;

    _farmNameController = TextEditingController();
    _stateController = TextEditingController(text: location?.state ?? '');
    _districtController = TextEditingController(text: location?.district ?? '');
    _mandalController = TextEditingController(text: location?.mandal ?? '');
    _villageController = TextEditingController(text: location?.village ?? '');
    _landAreaController = TextEditingController();
    _soilTypeController = TextEditingController();

    _latitude = location?.latitude;
    _longitude = location?.longitude;
  }

  @override
  void dispose() {
    _farmNameController.dispose();
    _stateController.dispose();
    _districtController.dispose();
    _mandalController.dispose();
    _villageController.dispose();
    _landAreaController.dispose();
    _soilTypeController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_isSubmitting || _createdFarm != null) {
      return;
    }

    FocusManager.instance.primaryFocus?.unfocus();

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    widget.onSubmittingChanged?.call(true);

    final landArea = double.parse(_landAreaController.text.trim());

    final input = FarmCreateInput(
      farmName: _farmNameController.text,
      state: _stateController.text,
      district: _districtController.text,
      mandal: _mandalController.text,
      village: _villageController.text,
      latitude: _latitude,
      longitude: _longitude,
      landArea: landArea,
      landUnit: _landUnit,
      soilType: _soilTypeController.text,
      waterSource: _waterSource,
      waterAvailability: _waterAvailability,
      irrigationMethod: _irrigationMethod,
      isPrimary: widget.isPrimary,
    );

    try {
      final farm = await _createFarm(input);

      if (!mounted) {
        return;
      }

      setState(() {
        _createdFarm = farm;
        _isSubmitting = false;
      });

      widget.onSubmittingChanged?.call(false);
      widget.onCreated?.call(farm);
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isSubmitting = false;
        _errorMessage = _cleanError(error);
      });

      widget.onSubmittingChanged?.call(false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final createdFarm = _createdFarm;

    if (createdFarm != null) {
      return _buildSuccess(createdFarm);
    }

    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.only(top: 12, bottom: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Tell us about your farm',
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
              'We use these details to personalize weather, crop guidance, and tasks for your land.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13.5,
                height: 1.45,
              ),
            ),

            const SizedBox(height: 22),

            if (_errorMessage != null) ...[
              _buildErrorBanner(_errorMessage!),
              const SizedBox(height: 16),
            ],

            _buildSection(
              title: 'Farm details',
              child: Column(
                children: [
                  TextFormField(
                    key: const Key('farm_name_field'),
                    controller: _farmNameController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'Farm name *',
                      hintText: 'e.g. North Field',
                      counterText: '',
                    ),
                    validator: (value) =>
                        _requiredField(value, label: 'Farm name'),
                  ),

                  const SizedBox(height: 13),

                  TextFormField(
                    key: const Key('farm_state_field'),
                    controller: _stateController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'State *',
                      hintText: 'e.g. Andhra Pradesh',
                      counterText: '',
                    ),
                    validator: (value) => _requiredField(value, label: 'State'),
                  ),

                  const SizedBox(height: 13),

                  TextFormField(
                    key: const Key('farm_district_field'),
                    controller: _districtController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'District *',
                      hintText: 'e.g. Nellore',
                      counterText: '',
                    ),
                    validator: (value) =>
                        _requiredField(value, label: 'District'),
                  ),

                  const SizedBox(height: 13),

                  TextFormField(
                    key: const Key('farm_mandal_field'),
                    controller: _mandalController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'Mandal *',
                      hintText: 'e.g. Kavali',
                      counterText: '',
                    ),
                    validator: (value) =>
                        _requiredField(value, label: 'Mandal'),
                  ),

                  const SizedBox(height: 13),

                  TextFormField(
                    key: const Key('farm_village_field'),
                    controller: _villageController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 100,
                    decoration: const InputDecoration(
                      labelText: 'Village *',
                      hintText: 'e.g. Ramapuram',
                      counterText: '',
                    ),
                    validator: (value) =>
                        _requiredField(value, label: 'Village'),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            _buildSection(
              title: 'Land details',
              child: Column(
                children: [
                  TextFormField(
                    key: const Key('farm_land_area_field'),
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
                    key: const Key('farm_land_unit_field'),
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
                        : (value) {
                            if (value == null) {
                              return;
                            }

                            setState(() {
                              _landUnit = value;
                            });
                          },
                  ),

                  const SizedBox(height: 13),

                  TextFormField(
                    key: const Key('farm_soil_type_field'),
                    controller: _soilTypeController,
                    enabled: !_isSubmitting,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.next,
                    maxLength: 50,
                    decoration: const InputDecoration(
                      labelText: 'Soil type (optional)',
                      hintText: 'e.g. Clay, Loam, Sandy',
                      counterText: '',
                    ),
                    validator: (value) => _optionalField(
                      value,
                      label: 'Soil type',
                      maxLength: 50,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            _buildSection(
              title: 'Water details',
              subtitle: 'Optional, but helps improve irrigation guidance.',
              child: Column(
                children: [
                  DropdownButtonFormField<String>(
                    key: const Key('farm_water_source_field'),
                    initialValue: _waterSource,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Water source (optional)',
                    ),
                    hint: const Text('Select water source'),
                    items: const [
                      DropdownMenuItem(
                        value: 'Borewell',
                        child: Text('Borewell'),
                      ),
                      DropdownMenuItem(value: 'Canal', child: Text('Canal')),
                      DropdownMenuItem(value: 'River', child: Text('River')),
                      DropdownMenuItem(value: 'Tank', child: Text('Tank')),
                      DropdownMenuItem(
                        value: 'Rain-fed',
                        child: Text('Rain-fed'),
                      ),
                    ],
                    onChanged: _isSubmitting
                        ? null
                        : (value) {
                            setState(() {
                              _waterSource = value;
                            });
                          },
                  ),

                  const SizedBox(height: 13),

                  DropdownButtonFormField<String>(
                    key: const Key('farm_water_availability_field'),
                    initialValue: _waterAvailability,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Water availability (optional)',
                    ),
                    hint: const Text('Select availability'),
                    items: const [
                      DropdownMenuItem(value: 'LOW', child: Text('Low')),
                      DropdownMenuItem(value: 'MEDIUM', child: Text('Medium')),
                      DropdownMenuItem(value: 'HIGH', child: Text('High')),
                      DropdownMenuItem(
                        value: 'RAIN_FED',
                        child: Text('Rain-fed'),
                      ),
                    ],
                    onChanged: _isSubmitting
                        ? null
                        : (value) {
                            setState(() {
                              _waterAvailability = value;
                            });
                          },
                  ),

                  const SizedBox(height: 13),

                  DropdownButtonFormField<String>(
                    key: const Key('farm_irrigation_method_field'),
                    initialValue: _irrigationMethod,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Irrigation method (optional)',
                    ),
                    hint: const Text('Select irrigation method'),
                    items: const [
                      DropdownMenuItem(value: 'Drip', child: Text('Drip')),
                      DropdownMenuItem(
                        value: 'Sprinkler',
                        child: Text('Sprinkler'),
                      ),
                      DropdownMenuItem(value: 'Flood', child: Text('Flood')),
                      DropdownMenuItem(value: 'Manual', child: Text('Manual')),
                      DropdownMenuItem(
                        value: 'Rain-fed',
                        child: Text('Rain-fed'),
                      ),
                    ],
                    onChanged: _isSubmitting
                        ? null
                        : (value) {
                            setState(() {
                              _irrigationMethod = value;
                            });
                          },
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            Container(
              key: const Key('add_farm_primary_note'),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.home_work_outlined,
                    color: AppColors.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      widget.isPrimary
                          ? 'This will be your primary farm and will appear on your Home dashboard.'
                          : 'This farm will be added to your farm profile. Your current primary farm will stay on Home.',
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
                key: const Key('add_farm_submit_button'),
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
                          Text('Adding farm...'),
                        ],
                      )
                    : const Text('Add Farm'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required Widget child,
    String? subtitle,
  }) {
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

          if (subtitle != null) ...[
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                height: 1.35,
              ),
            ),
          ],

          const SizedBox(height: 15),

          child,
        ],
      ),
    );
  }

  Widget _buildErrorBanner(String message) {
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

  Widget _buildSuccess(FarmModel farm) {
    final location = farm.locationLabel;

    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Center(
            child: Container(
              width: 82,
              height: 82,
              decoration: const BoxDecoration(
                color: AppColors.primarySurface,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_rounded,
                color: AppColors.primary,
                size: 42,
              ),
            ),
          ),

          const SizedBox(height: 22),

          const Text(
            'Farm added',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 27,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.6,
            ),
          ),

          const SizedBox(height: 9),

          const Text(
            'Your farm is ready. FarmMate will use it to personalize your dashboard.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13.5,
              height: 1.45,
            ),
          ),

          const SizedBox(height: 24),

          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: AppColors.surfaceLight,
              borderRadius: BorderRadius.circular(22),
              border: Border.all(color: AppColors.borderLight),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: AppColors.primarySurface,
                        borderRadius: BorderRadius.circular(15),
                      ),
                      child: const Icon(
                        Icons.agriculture_rounded,
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
                            farm.farmName,
                            style: const TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                            ),
                          ),

                          if (location.isNotEmpty) ...[
                            const SizedBox(height: 3),
                            Text(
                              location,
                              style: const TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 15),

                Text(
                  '${_formatNumber(farm.landArea)} ${farm.landUnit}',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              key: const Key('add_farm_continue_button'),
              onPressed: () => widget.onContinue(farm),
              child: Text(widget.successActionLabel),
            ),
          ),
        ],
      ),
    );
  }

  String? _requiredField(String? value, {required String label}) {
    final text = value?.trim() ?? '';

    if (text.isEmpty) {
      return '$label is required';
    }

    if (text.length < 2) {
      return '$label must be at least 2 characters';
    }

    if (text.length > 100) {
      return '$label must be 100 characters or fewer';
    }

    return null;
  }

  String? _optionalField(
    String? value, {
    required String label,
    required int maxLength,
  }) {
    final text = value?.trim() ?? '';

    if (text.length > maxLength) {
      return '$label must be $maxLength characters or fewer';
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

    return null;
  }

  String _cleanError(Object error) {
    var message = error.toString().trim();

    while (message.startsWith('Exception: ')) {
      message = message.substring('Exception: '.length).trim();
    }

    return message.isEmpty
        ? 'Unable to add your farm. Please try again.'
        : message;
  }

  String _formatNumber(double value) {
    if (value == value.roundToDouble()) {
      return value.toInt().toString();
    }

    return value.toStringAsFixed(2).replaceFirst(RegExp(r'0+$'), '');
  }
}

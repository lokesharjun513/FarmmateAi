import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../farm/data/models/farm_model.dart';
import '../../data/models/crop_season_create_input.dart';
import '../../data/models/crop_season_model.dart';
import '../../providers/crop_provider.dart';

class EditCropScreen extends StatefulWidget {
  const EditCropScreen({super.key, required this.farm, required this.crop});

  final FarmModel farm;
  final CropSeasonModel crop;

  @override
  State<EditCropScreen> createState() => _EditCropScreenState();
}

class _EditCropScreenState extends State<EditCropScreen> {
  final _formKey = GlobalKey<FormState>();

  late final TextEditingController _cropNameController;
  late final TextEditingController _cropVarietyController;
  late final TextEditingController _landAreaController;
  late final TextEditingController _notesController;

  late FarmingSeason _season;
  late String _landUnit;
  late DateTime _sowingDate;
  DateTime? _expectedHarvestDate;

  bool _isSaving = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _cropNameController = TextEditingController(text: widget.crop.cropName);
    _cropVarietyController = TextEditingController(
      text: widget.crop.cropVariety ?? '',
    );
    _landAreaController = TextEditingController(
      text: _formatNumber(widget.crop.landArea),
    );
    _notesController = TextEditingController(text: widget.crop.notes ?? '');
    _season = widget.crop.season;
    _landUnit = _normalizeLandUnit(widget.crop.landUnit);
    _sowingDate = widget.crop.sowingDate;
    _expectedHarvestDate = widget.crop.expectedHarvestDate;
  }

  @override
  void dispose() {
    _cropNameController.dispose();
    _cropVarietyController.dispose();
    _landAreaController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_isSaving || !_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      final variety = _cropVarietyController.text.trim();
      final updated = await context.read<CropProvider>().updateCropSeason(
        cropSeasonId: widget.crop.id,
        cropName: _cropNameController.text.trim(),
        cropVariety: variety.isEmpty ? null : variety,
        season: _season,
        sowingDate: _sowingDate,
        expectedHarvestDate: _expectedHarvestDate,
        landArea: double.parse(_landAreaController.text.trim()),
        landUnit: _landUnit,
        notes: _notesController.text.trim(),
      );

      if (mounted) {
        Navigator.pop(context, updated);
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _errorMessage = _cleanError(error);
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  Future<void> _pickSowingDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _sowingDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
      helpText: 'Select sowing date',
    );

    if (picked != null) {
      setState(() {
        _sowingDate = picked;

        if (_expectedHarvestDate != null &&
            _expectedHarvestDate!.isBefore(picked)) {
          _expectedHarvestDate = null;
        }
      });
    }
  }

  Future<void> _pickHarvestDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _expectedHarvestDate ?? _sowingDate,
      firstDate: _sowingDate,
      lastDate: DateTime(2100),
      helpText: 'Select expected harvest date',
    );

    if (picked != null) {
      setState(() {
        _expectedHarvestDate = picked;
      });
    }
  }

  String? _validateRequired(String? value, String label) {
    if (value == null || value.trim().isEmpty) {
      return '$label is required';
    }

    return null;
  }

  String? _validateLandArea(String? value) {
    final area = double.tryParse(value?.trim() ?? '');

    if (area == null || area <= 0) {
      return 'Enter a land area greater than 0';
    }

    if (widget.farm.landArea > 0 &&
        _sameLandUnit(widget.farm.landUnit, _landUnit) &&
        area > widget.farm.landArea) {
      return 'This is more than the farm area of '
          '${_formatNumber(widget.farm.landArea)} ${widget.farm.landUnit}';
    }

    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('edit_crop_screen'),
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.backgroundLight,
        elevation: 0,
        title: const Text('Edit crop'),
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
            children: [
              TextFormField(
                key: const Key('edit_crop_name_field'),
                controller: _cropNameController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Crop name *',
                  prefixIcon: Icon(Icons.eco_outlined),
                ),
                validator: (value) => _validateRequired(value, 'Crop name'),
              ),
              const SizedBox(height: 14),
              TextFormField(
                key: const Key('edit_crop_variety_field'),
                controller: _cropVarietyController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Variety (optional)',
                  prefixIcon: Icon(Icons.spa_outlined),
                ),
              ),
              const SizedBox(height: 14),
              DropdownButtonFormField<FarmingSeason>(
                key: const Key('edit_crop_season_field'),
                initialValue: _season,
                decoration: const InputDecoration(
                  labelText: 'Season *',
                  prefixIcon: Icon(Icons.wb_sunny_outlined),
                ),
                items: [
                  for (final season in FarmingSeason.values)
                    DropdownMenuItem(value: season, child: Text(season.label)),
                ],
                onChanged: _isSaving
                    ? null
                    : (value) {
                        if (value != null) {
                          setState(() {
                            _season = value;
                          });
                        }
                      },
              ),
              const SizedBox(height: 14),
              _DateField(
                key: const Key('edit_crop_sowing_date_field'),
                label: 'Sowing date',
                value: _sowingDate,
                onTap: _isSaving ? null : _pickSowingDate,
              ),
              const SizedBox(height: 14),
              _DateField(
                key: const Key('edit_crop_harvest_date_field'),
                label: 'Expected harvest (optional)',
                value: _expectedHarvestDate,
                onTap: _isSaving ? null : _pickHarvestDate,
                onClear: _expectedHarvestDate == null || _isSaving
                    ? null
                    : () {
                        setState(() {
                          _expectedHarvestDate = null;
                        });
                      },
              ),
              const SizedBox(height: 14),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 2,
                    child: TextFormField(
                      key: const Key('edit_crop_land_area_field'),
                      controller: _landAreaController,
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        labelText: 'Land area *',
                        prefixIcon: Icon(Icons.straighten_rounded),
                      ),
                      validator: _validateLandArea,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      key: const Key('edit_crop_land_unit_field'),
                      initialValue: _landUnit,
                      decoration: const InputDecoration(labelText: 'Unit'),
                      items: const [
                        DropdownMenuItem(value: 'Acres', child: Text('Acres')),
                        DropdownMenuItem(
                          value: 'Hectares',
                          child: Text('Hectares'),
                        ),
                      ],
                      onChanged: _isSaving
                          ? null
                          : (value) {
                              if (value != null) {
                                setState(() {
                                  _landUnit = value;
                                });
                              }
                            },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextFormField(
                key: const Key('edit_crop_notes_field'),
                controller: _notesController,
                maxLength: 1000,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Notes (optional)',
                  alignLabelWithHint: true,
                ),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.error.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(
                      color: AppColors.error,
                      fontSize: 12,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              ElevatedButton(
                key: const Key('edit_crop_save_button'),
                onPressed: _isSaving ? null : _save,
                child: _isSaving
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Save changes'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DateField extends StatelessWidget {
  const _DateField({
    super.key,
    required this.label,
    required this.value,
    required this.onTap,
    this.onClear,
  });

  final String label;
  final DateTime? value;
  final VoidCallback? onTap;
  final VoidCallback? onClear;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: const Icon(Icons.event_outlined),
          suffixIcon: onClear == null
              ? null
              : IconButton(
                  onPressed: onClear,
                  tooltip: 'Clear date',
                  icon: const Icon(Icons.close_rounded, size: 18),
                ),
        ),
        child: Text(
          value == null ? 'Not set' : _formatDate(value!),
          style: TextStyle(
            color: value == null ? AppColors.textHint : AppColors.textPrimary,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
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

String _cleanError(Object error) {
  var message = error.toString().trim();

  while (message.startsWith('Exception: ')) {
    message = message.substring('Exception: '.length).trim();
  }

  return message.isEmpty
      ? 'Unable to update this crop. Please try again.'
      : message;
}

String _formatDate(DateTime date) {
  return formatApiDate(date);
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

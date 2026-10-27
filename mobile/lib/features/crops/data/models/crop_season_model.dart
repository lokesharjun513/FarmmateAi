enum CropSeasonStatus {
  planned('PLANNED', 'Planned'),
  active('ACTIVE', 'Active'),
  harvested('HARVESTED', 'Harvested'),
  cancelled('CANCELLED', 'Cancelled');

  const CropSeasonStatus(this.wireValue, this.label);

  final String wireValue;
  final String label;

  static CropSeasonStatus fromJson(dynamic value) {
    final wireValue = value?.toString().trim().toUpperCase() ?? '';

    for (final status in values) {
      if (status.wireValue == wireValue) {
        return status;
      }
    }

    throw const FormatException('Invalid crop status received from server.');
  }
}

enum FarmingSeason {
  kharif('KHARIF', 'Kharif'),
  rabi('RABI', 'Rabi'),
  zaid('ZAID', 'Zaid');

  const FarmingSeason(this.wireValue, this.label);

  final String wireValue;
  final String label;

  static FarmingSeason fromJson(dynamic value) {
    final wireValue = value?.toString().trim().toUpperCase() ?? '';

    for (final season in values) {
      if (season.wireValue == wireValue) {
        return season;
      }
    }

    throw const FormatException('Invalid farming season received from server.');
  }
}

class CropSeasonModel {
  final String id;
  final String farmId;
  final String cropName;
  final String? cropVariety;
  final FarmingSeason season;
  final int year;
  final DateTime sowingDate;
  final DateTime? expectedHarvestDate;
  final DateTime? harvestedDate;
  final double landArea;
  final String landUnit;
  final CropSeasonStatus status;
  final bool isActive;
  final String? notes;
  final String? cancellationReason;

  const CropSeasonModel({
    required this.id,
    required this.farmId,
    required this.cropName,
    required this.cropVariety,
    required this.season,
    required this.year,
    required this.sowingDate,
    required this.expectedHarvestDate,
    required this.harvestedDate,
    required this.landArea,
    required this.landUnit,
    required this.status,
    required this.isActive,
    required this.notes,
    required this.cancellationReason,
  });

  factory CropSeasonModel.fromJson(Map<String, dynamic> json) {
    final id = json['id']?.toString().trim() ?? '';
    final farmId = json['farm_id']?.toString().trim() ?? '';
    final cropName = json['crop_name']?.toString().trim() ?? '';
    final sowingDate = _requiredDate(json['sowing_date']);

    if (id.isEmpty || farmId.isEmpty || cropName.isEmpty) {
      throw const FormatException(
        'Invalid crop season response received from server.',
      );
    }

    return CropSeasonModel(
      id: id,
      farmId: farmId,
      cropName: cropName,
      cropVariety: _nullableString(json['crop_variety']),
      season: FarmingSeason.fromJson(json['season']),
      year: _integer(json['year']) ?? sowingDate.year,
      sowingDate: sowingDate,
      expectedHarvestDate: _optionalDate(json['expected_harvest_date']),
      harvestedDate: _optionalDate(json['harvested_date']),
      landArea: _number(json['land_area']) ?? 0,
      landUnit: _nullableString(json['land_unit']) ?? 'Acres',
      status: CropSeasonStatus.fromJson(json['status']),
      isActive: json['is_active'] == true,
      notes: _nullableString(json['notes']),
      cancellationReason: _nullableString(json['cancellation_reason']),
    );
  }

  bool get isPlanned => status == CropSeasonStatus.planned;

  bool get isActiveSeason => status == CropSeasonStatus.active;

  bool get isHarvested => status == CropSeasonStatus.harvested;

  bool get isCancelled => status == CropSeasonStatus.cancelled;
}

String? _nullableString(dynamic value) {
  if (value == null) {
    return null;
  }

  final text = value.toString().trim();

  return text.isEmpty ? null : text;
}

double? _number(dynamic value) {
  if (value == null) {
    return null;
  }

  if (value is num) {
    return value.toDouble();
  }

  return double.tryParse(value.toString().trim());
}

int? _integer(dynamic value) {
  if (value is int) {
    return value;
  }

  if (value is num) {
    return value.toInt();
  }

  return int.tryParse(value?.toString().trim() ?? '');
}

DateTime _requiredDate(dynamic value) {
  final parsed = _optionalDate(value);

  if (parsed == null) {
    throw const FormatException('Invalid crop date received from server.');
  }

  return parsed;
}

DateTime? _optionalDate(dynamic value) {
  if (value == null) {
    return null;
  }

  final text = value.toString().trim();

  if (text.isEmpty) {
    return null;
  }

  return DateTime.tryParse(text);
}

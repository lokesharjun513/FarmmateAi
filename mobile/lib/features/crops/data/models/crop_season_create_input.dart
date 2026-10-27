import 'crop_season_model.dart';

class CropSeasonCreateInput {
  final String cropName;
  final String? cropVariety;
  final FarmingSeason season;
  final int year;
  final DateTime sowingDate;
  final DateTime? expectedHarvestDate;
  final double landArea;
  final String landUnit;
  final String? notes;

  const CropSeasonCreateInput({
    required this.cropName,
    required this.cropVariety,
    required this.season,
    required this.year,
    required this.sowingDate,
    required this.expectedHarvestDate,
    required this.landArea,
    this.landUnit = 'Acres',
    required this.notes,
  });

  Map<String, dynamic> toJson() {
    final payload = <String, dynamic>{
      'crop_name': cropName.trim(),
      'season': season.wireValue,
      'year': year,
      'sowing_date': formatApiDate(sowingDate),
      'land_area': landArea,
      'land_unit': landUnit.trim(),
    };

    _addOptional(payload, 'crop_variety', cropVariety);
    _addOptional(payload, 'notes', notes);

    if (expectedHarvestDate != null) {
      payload['expected_harvest_date'] = formatApiDate(expectedHarvestDate!);
    }

    return payload;
  }

  void _addOptional(Map<String, dynamic> payload, String key, String? value) {
    final trimmed = value?.trim();

    if (trimmed != null && trimmed.isNotEmpty) {
      payload[key] = trimmed;
    }
  }
}

String formatApiDate(DateTime date) {
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');

  return '${date.year}-$month-$day';
}

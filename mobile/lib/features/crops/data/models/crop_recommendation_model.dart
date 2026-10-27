class CropRecommendationModel {
  final String farmId;
  final DateTime? recommendedSowingDate;
  final List<RecommendedCropModel> recommendedCrops;

  const CropRecommendationModel({
    required this.farmId,
    required this.recommendedSowingDate,
    required this.recommendedCrops,
  });

  factory CropRecommendationModel.fromJson(Map<String, dynamic> json) {
    final farmId = json['farm_id']?.toString().trim() ?? '';
    final rawCrops = json['recommended_crops'];

    if (farmId.isEmpty) {
      throw const FormatException(
        'Farm information is missing from the recommendation response.',
      );
    }

    if (rawCrops is! List || rawCrops.isEmpty) {
      throw const FormatException(
        'No crop recommendations were returned. Please try again.',
      );
    }

    final recommendedCrops = rawCrops
        .map((item) {
          if (item is! Map) {
            throw const FormatException(
              'Invalid crop recommendation received from server.',
            );
          }

          return RecommendedCropModel.fromJson(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);

    return CropRecommendationModel(
      farmId: farmId,
      recommendedSowingDate: _parseSowingDate(json['recommended_sowing_date']),
      recommendedCrops: recommendedCrops,
    );
  }

  bool get hasSowingDate => recommendedSowingDate != null;

  bool get isEmpty => recommendedCrops.isEmpty;
}

class RecommendedCropModel {
  final String cropName;
  final int confidence;
  final String reason;

  const RecommendedCropModel({
    required this.cropName,
    required this.confidence,
    required this.reason,
  });

  factory RecommendedCropModel.fromJson(Map<String, dynamic> json) {
    final cropName = json['crop_name']?.toString().trim() ?? '';
    final reason = json['reason']?.toString().trim() ?? '';
    final confidence = _parseConfidence(json['confidence']);

    if (cropName.isEmpty || cropName.length > 100) {
      throw const FormatException('A recommended crop has an invalid name.');
    }

    if (confidence == null) {
      throw const FormatException(
        'A recommended crop has an invalid confidence score.',
      );
    }

    if (reason.isEmpty || reason.length > 1000) {
      throw const FormatException(
        'A recommended crop is missing its explanation.',
      );
    }

    return RecommendedCropModel(
      cropName: cropName,
      confidence: confidence,
      reason: reason,
    );
  }
}

int? _parseConfidence(dynamic value) {
  if (value is int) {
    return value >= 0 && value <= 100 ? value : null;
  }

  if (value is num && value == value.roundToDouble()) {
    final score = value.toInt();

    return score >= 0 && score <= 100 ? score : null;
  }

  final parsed = int.tryParse(value?.toString().trim() ?? '');

  if (parsed == null || parsed < 0 || parsed > 100) {
    return null;
  }

  return parsed;
}

DateTime? _parseSowingDate(dynamic value) {
  final text = value?.toString().trim() ?? '';

  if (!RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(text)) {
    return null;
  }

  final parsed = DateTime.tryParse(text);

  if (parsed == null) {
    return null;
  }

  final expected = _formatApiDate(parsed);

  return expected == text ? parsed : null;
}

String _formatApiDate(DateTime date) {
  final month = date.month.toString().padLeft(2, '0');
  final day = date.day.toString().padLeft(2, '0');

  return '${date.year}-$month-$day';
}

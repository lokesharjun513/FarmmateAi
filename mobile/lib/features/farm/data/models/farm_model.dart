class FarmModel {
  final String id;
  final String farmerId;
  final String farmName;
  final String state;
  final String district;
  final String mandal;
  final String village;
  final double? latitude;
  final double? longitude;
  final double landArea;
  final String landUnit;
  final String? soilType;
  final String? waterSource;
  final String? waterAvailability;
  final String? irrigationMethod;
  final bool isPrimary;

  const FarmModel({
    required this.id,
    required this.farmerId,
    required this.farmName,
    required this.state,
    required this.district,
    required this.mandal,
    required this.village,
    required this.latitude,
    required this.longitude,
    required this.landArea,
    required this.landUnit,
    required this.soilType,
    required this.waterSource,
    required this.waterAvailability,
    required this.irrigationMethod,
    required this.isPrimary,
  });

  factory FarmModel.fromJson(Map<String, dynamic> json) {
    final id = json['id']?.toString().trim() ?? '';
    final farmName = json['farm_name']?.toString().trim() ?? '';

    if (id.isEmpty || farmName.isEmpty) {
      throw const FormatException(
        'Invalid farm response received from server.',
      );
    }

    return FarmModel(
      id: id,
      farmerId: json['farmer_id']?.toString() ?? '',
      farmName: farmName,
      state: json['state']?.toString().trim() ?? '',
      district: json['district']?.toString().trim() ?? '',
      mandal: json['mandal']?.toString().trim() ?? '',
      village: json['village']?.toString().trim() ?? '',
      latitude: _toNullableDouble(json['latitude']),
      longitude: _toNullableDouble(json['longitude']),
      landArea: _toNullableDouble(json['land_area']) ?? 0,
      landUnit: json['land_unit']?.toString().trim().isNotEmpty == true
          ? json['land_unit'].toString().trim()
          : 'Acres',
      soilType: _toNullableString(json['soil_type']),
      waterSource: _toNullableString(json['water_source']),
      waterAvailability: _toNullableString(json['water_availability']),
      irrigationMethod: _toNullableString(json['irrigation_method']),
      isPrimary: json['is_primary'] == true,
    );
  }

  String get locationLabel {
    final parts = [
      village,
      mandal,
      district,
      state,
    ].map((value) => value.trim()).where((value) => value.isNotEmpty).toList();

    return parts.join(', ');
  }

  FarmModel copyWith({bool? isPrimary}) {
    return FarmModel(
      id: id,
      farmerId: farmerId,
      farmName: farmName,
      state: state,
      district: district,
      mandal: mandal,
      village: village,
      latitude: latitude,
      longitude: longitude,
      landArea: landArea,
      landUnit: landUnit,
      soilType: soilType,
      waterSource: waterSource,
      waterAvailability: waterAvailability,
      irrigationMethod: irrigationMethod,
      isPrimary: isPrimary ?? this.isPrimary,
    );
  }
}

class FarmCreateInput {
  final String farmName;
  final String state;
  final String district;
  final String mandal;
  final String village;
  final double? latitude;
  final double? longitude;
  final double landArea;
  final String landUnit;
  final String? soilType;
  final String? waterSource;
  final String? waterAvailability;
  final String? irrigationMethod;
  final bool isPrimary;

  const FarmCreateInput({
    required this.farmName,
    required this.state,
    required this.district,
    required this.mandal,
    required this.village,
    required this.latitude,
    required this.longitude,
    required this.landArea,
    this.landUnit = 'Acres',
    this.soilType,
    this.waterSource,
    this.waterAvailability,
    this.irrigationMethod,
    this.isPrimary = false,
  });

  Map<String, dynamic> toJson() {
    final payload = <String, dynamic>{
      'farm_name': farmName.trim(),
      'state': state.trim(),
      'district': district.trim(),
      'mandal': mandal.trim(),
      'village': village.trim(),
      'land_area': landArea,
      'land_unit': landUnit.trim(),
      'is_primary': isPrimary,
    };

    if (latitude != null) {
      payload['latitude'] = latitude;
    }

    if (longitude != null) {
      payload['longitude'] = longitude;
    }

    _addOptional(payload, 'soil_type', soilType);
    _addOptional(payload, 'water_source', waterSource);
    _addOptional(payload, 'water_availability', waterAvailability);
    _addOptional(payload, 'irrigation_method', irrigationMethod);

    return payload;
  }

  void _addOptional(Map<String, dynamic> payload, String key, String? value) {
    final trimmed = value?.trim();

    if (trimmed != null && trimmed.isNotEmpty) {
      payload[key] = trimmed;
    }
  }
}

String? _toNullableString(dynamic value) {
  if (value == null) {
    return null;
  }

  final text = value.toString().trim();

  return text.isEmpty ? null : text;
}

double? _toNullableDouble(dynamic value) {
  if (value == null) {
    return null;
  }

  if (value is num) {
    return value.toDouble();
  }

  return double.tryParse(value.toString().trim());
}

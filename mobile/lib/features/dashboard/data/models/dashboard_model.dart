// lib/features/dashboard/data/models/dashboard_model.dart

class DashboardModel {
  final String greeting;

  final FarmerDashboard farmer;

  final FarmDashboard? farm;

  final ActiveCrop? activeCrop;

  final WeatherDashboard weather;

  final AdvisorDashboard advisor;

  final DashboardStats stats;

  final List<ActivityDashboard> activities;

  final AskFarmateDashboard askFm;

  const DashboardModel({
    required this.greeting,
    required this.farmer,
    required this.farm,
    required this.activeCrop,
    required this.weather,
    required this.advisor,
    required this.stats,
    required this.activities,
    required this.askFm,
  });

  factory DashboardModel.fromJson(Map<String, dynamic> json) {
    return DashboardModel(
      greeting: json['greeting']?.toString() ?? 'Hello',

      farmer: FarmerDashboard.fromJson(_asMap(json['farmer'])),

      farm: json['farm'] is Map
          ? FarmDashboard.fromJson(_asMap(json['farm']))
          : null,

      activeCrop: json['active_crop'] is Map
          ? ActiveCrop.fromJson(_asMap(json['active_crop']))
          : null,

      weather: WeatherDashboard.fromJson(_asMap(json['weather'])),

      advisor: AdvisorDashboard.fromJson(_asMap(json['advisor'])),

      stats: DashboardStats.fromJson(_asMap(json['stats'])),

      activities: _parseActivities(json['activities']),

      askFm: AskFarmateDashboard.fromJson(_asMap(json['ask_fm'])),
    );
  }
}

// ============================================================
// FARMER
// ============================================================

class FarmerDashboard {
  final String id;

  final String fullName;

  final String preferredLanguage;

  const FarmerDashboard({
    required this.id,
    required this.fullName,
    required this.preferredLanguage,
  });

  factory FarmerDashboard.fromJson(Map<String, dynamic> json) {
    return FarmerDashboard(
      id: json['id']?.toString() ?? '',

      fullName: json['full_name']?.toString().trim().isNotEmpty == true
          ? json['full_name'].toString().trim()
          : 'Farmer',

      preferredLanguage:
          json['preferred_language']?.toString().trim().isNotEmpty == true
          ? json['preferred_language'].toString().trim()
          : 'English',
    );
  }

  bool get hasName {
    return fullName.trim().isNotEmpty && fullName.toLowerCase() != 'farmer';
  }
}

// ============================================================
// FARM
// ============================================================

class FarmDashboard {
  final String id;

  final String farmName;

  final String village;

  final String mandal;

  final String district;

  final String state;

  final String? soilType;

  final String? waterSource;

  final String? waterAvailability;

  final String? irrigationMethod;

  final double landArea;

  final String landUnit;

  const FarmDashboard({
    required this.id,
    required this.farmName,
    required this.village,
    required this.mandal,
    required this.district,
    required this.state,
    required this.soilType,
    required this.waterSource,
    required this.waterAvailability,
    required this.irrigationMethod,
    required this.landArea,
    required this.landUnit,
  });

  factory FarmDashboard.fromJson(Map<String, dynamic> json) {
    return FarmDashboard(
      id: json['id']?.toString() ?? '',

      farmName: json['farm_name']?.toString().trim().isNotEmpty == true
          ? json['farm_name'].toString().trim()
          : 'My Farm',

      village: json['village']?.toString().trim() ?? '',

      mandal: json['mandal']?.toString().trim() ?? '',

      district: json['district']?.toString().trim() ?? '',

      state: json['state']?.toString().trim() ?? '',

      soilType: _nullableString(json['soil_type']),

      waterSource: _nullableString(json['water_source']),

      waterAvailability: _nullableString(json['water_availability']),

      irrigationMethod: _nullableString(json['irrigation_method']),

      landArea: _toDouble(json['land_area']) ?? 0,

      landUnit: json['land_unit']?.toString().trim().isNotEmpty == true
          ? json['land_unit'].toString().trim()
          : 'Acres',
    );
  }

  // ==========================================================
  // LOCATION
  // ==========================================================

  String get location {
    final parts = [
      village,
      mandal,
      district,
    ].where((item) => item.trim().isNotEmpty);

    return parts.join(', ');
  }

  String get displayLocation {
    final value = location;

    if (value.isNotEmpty) {
      return value;
    }

    return state;
  }

  // ==========================================================
  // FORMATTED LAND
  // ==========================================================

  String get formattedLandArea {
    final area = landArea == landArea.roundToDouble()
        ? landArea.toInt().toString()
        : landArea.toStringAsFixed(1);

    return '$area $landUnit';
  }
}

// ============================================================
// ACTIVE CROP
// ============================================================

class ActiveCrop {
  final String id;

  final String cropName;

  final String? cropVariety;

  final String season;

  final int cropAgeDays;

  final int estimatedDurationDays;

  final int progressPercentage;

  final String stage;

  const ActiveCrop({
    required this.id,
    required this.cropName,
    required this.cropVariety,
    required this.season,
    required this.cropAgeDays,
    required this.estimatedDurationDays,
    required this.progressPercentage,
    required this.stage,
  });

  factory ActiveCrop.fromJson(Map<String, dynamic> json) {
    final progress = _toInt(json['progress_percentage']).clamp(0, 100);

    return ActiveCrop(
      id: json['id']?.toString() ?? '',

      // Backend:
      // crop_name
      cropName: json['crop_name']?.toString().trim().isNotEmpty == true
          ? json['crop_name'].toString().trim()
          : 'Crop',

      // Backend:
      // crop_variety
      cropVariety: _nullableString(json['crop_variety']),

      // Backend:
      // season
      season: json['season']?.toString().trim() ?? '',

      // Backend:
      // crop_age_days
      cropAgeDays: _toInt(json['crop_age_days']),

      // Backend:
      // estimated_duration_days
      estimatedDurationDays: _toInt(json['estimated_duration_days']),

      // Backend:
      // progress_percentage
      progressPercentage: progress,

      // Backend:
      // current_stage.name
      stage: _parseStage(json),
    );
  }

  static String _parseStage(Map<String, dynamic> json) {
    final currentStage = json['current_stage'];

    if (currentStage is Map) {
      final name = currentStage['name']?.toString().trim();

      if (name != null && name.isNotEmpty) {
        return name;
      }
    }

    final legacyStage = json['stage']?.toString().trim();

    if (legacyStage != null && legacyStage.isNotEmpty) {
      return legacyStage;
    }

    return 'Unknown';
  }

  // ==========================================================
  // PROGRESS
  // ==========================================================

  double get progress {
    return progressPercentage / 100.0;
  }

  bool get hasProgress {
    return progressPercentage > 0;
  }

  bool get isNearHarvest {
    return progressPercentage >= 80;
  }

  bool get isReadyForHarvest {
    return progressPercentage >= 100;
  }

  // ==========================================================
  // CROP AGE
  // ==========================================================

  bool get hasAge {
    return cropAgeDays > 0;
  }

  String get ageLabel {
    if (cropAgeDays <= 0) {
      return 'Age unavailable';
    }

    if (cropAgeDays == 1) {
      return '1 day old';
    }

    return '$cropAgeDays days old';
  }

  // ==========================================================
  // DURATION
  // ==========================================================

  bool get hasDuration {
    return estimatedDurationDays > 0;
  }

  String get durationLabel {
    if (estimatedDurationDays <= 0) {
      return 'Duration unavailable';
    }

    return '$estimatedDurationDays days';
  }

  // ==========================================================
  // VARIETY
  // ==========================================================

  bool get hasVariety {
    return cropVariety != null && cropVariety!.trim().isNotEmpty;
  }

  // ==========================================================
  // SEASON
  // ==========================================================

  bool get hasSeason {
    return season.trim().isNotEmpty;
  }
}

// ============================================================
// WEATHER
// ============================================================

class WeatherDashboard {
  final double temperature;

  final int humidity;

  final String condition;

  final int? rainProbability;

  final bool isAvailable;

  const WeatherDashboard({
    required this.temperature,
    required this.humidity,
    required this.condition,
    required this.rainProbability,
    required this.isAvailable,
  });

  factory WeatherDashboard.fromJson(Map<String, dynamic> json) {
    final parsedTemperature = _toDouble(json['temperature']);

    final condition = json['condition']?.toString().trim().isNotEmpty == true
        ? json['condition'].toString().trim()
        : 'Unavailable';

    final hasUsableWeather =
        parsedTemperature != null && condition.toLowerCase() != 'unavailable';

    final availability = json['is_available'];

    return WeatherDashboard(
      temperature: parsedTemperature ?? 0,

      humidity: _toInt(json['humidity']).clamp(0, 100),

      condition: condition,

      rainProbability: _nullableInt(json['rain_probability']),

      isAvailable: availability is bool
          ? availability && hasUsableWeather
          : hasUsableWeather,
    );
  }

  // ==========================================================
  // RAIN
  // ==========================================================

  bool get hasRainProbability {
    return rainProbability != null;
  }

  bool get rainLikely {
    return rainProbability != null && rainProbability! >= 50;
  }

  // ==========================================================
  // FORMATTED VALUES
  // ==========================================================

  String get temperatureLabel {
    return '${temperature.round()}°C';
  }

  String get humidityLabel {
    return '$humidity%';
  }

  String get rainProbabilityLabel {
    if (rainProbability == null) {
      return '--';
    }

    return '$rainProbability%';
  }
}

// ============================================================
// ADVISOR
// ============================================================

class AdvisorDashboard {
  final String summary;

  final String priority;

  final bool isAvailable;

  const AdvisorDashboard({
    required this.summary,
    required this.priority,
    required this.isAvailable,
  });

  factory AdvisorDashboard.fromJson(Map<String, dynamic> json) {
    final summary = json['summary']?.toString().trim().isNotEmpty == true
        ? json['summary'].toString().trim()
        : 'No recommendation available.';

    final hasUsableSummary =
        summary.toLowerCase() != 'no recommendation available.';

    final availability = json['available'];

    return AdvisorDashboard(
      summary: summary,

      priority: json['priority']?.toString().trim().isNotEmpty == true
          ? json['priority'].toString().trim().toUpperCase()
          : 'LOW',

      isAvailable: availability is bool ? availability : hasUsableSummary,
    );
  }

  bool get hasRecommendation {
    return isAvailable &&
        summary.trim().isNotEmpty &&
        summary.toLowerCase() != 'no recommendation available.';
  }

  bool get isHighPriority {
    return priority == 'HIGH';
  }

  bool get isMediumPriority {
    return priority == 'MEDIUM';
  }

  bool get isLowPriority {
    return priority == 'LOW';
  }
}

// ============================================================
// DASHBOARD STATS
// ============================================================

class DashboardStats {
  final int totalTasks;

  final int pendingTasks;

  final int completedTasks;

  final int todayTasks;

  const DashboardStats({
    required this.totalTasks,
    required this.pendingTasks,
    required this.completedTasks,
    required this.todayTasks,
  });

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      totalTasks: _nonNegativeInt(json['total_tasks']),

      pendingTasks: _nonNegativeInt(json['pending_tasks']),

      completedTasks: _nonNegativeInt(json['completed_tasks']),

      todayTasks: _nonNegativeInt(json['today_tasks']),
    );
  }

  // ==========================================================
  // HELPERS
  // ==========================================================

  bool get hasTasks {
    return totalTasks > 0;
  }

  bool get hasPendingTasks {
    return pendingTasks > 0;
  }

  bool get hasCompletedTasks {
    return completedTasks > 0;
  }

  double get completionRate {
    if (totalTasks <= 0) {
      return 0;
    }

    return completedTasks / totalTasks;
  }

  int get completionPercentage {
    return (completionRate * 100).round().clamp(0, 100);
  }
}

// ============================================================
// ACTIVITY
// ============================================================

class ActivityDashboard {
  final String id;

  final String title;

  final String activityType;

  final String priority;

  final String status;

  final String scheduledDate;

  const ActivityDashboard({
    required this.id,
    required this.title,
    required this.activityType,
    required this.priority,
    required this.status,
    required this.scheduledDate,
  });

  factory ActivityDashboard.fromJson(Map<String, dynamic> json) {
    return ActivityDashboard(
      id: json['id']?.toString() ?? '',

      // Backend:
      // title
      title: json['title']?.toString().trim().isNotEmpty == true
          ? json['title'].toString().trim()
          : 'Farm activity',

      // Backend:
      // activity_type
      activityType: json['activity_type']?.toString().trim() ?? '',

      // Backend:
      // priority
      priority: json['priority']?.toString().trim().toUpperCase() ?? 'LOW',

      // Backend:
      // status
      status: json['status']?.toString().trim().toUpperCase() ?? 'PENDING',

      // Backend:
      // scheduled_date
      scheduledDate: json['scheduled_date']?.toString().trim() ?? '',
    );
  }

  // ==========================================================
  // STATUS
  // ==========================================================

  bool get isCompleted {
    return status == 'COMPLETED';
  }

  bool get isPending {
    return status == 'PENDING';
  }

  bool get isCancelled {
    return status == 'CANCELLED';
  }

  bool get isInProgress {
    return status == 'IN_PROGRESS';
  }

  // ==========================================================
  // PRIORITY
  // ==========================================================

  bool get isHighPriority {
    return priority == 'HIGH';
  }

  bool get isMediumPriority {
    return priority == 'MEDIUM';
  }

  bool get isLowPriority {
    return priority == 'LOW';
  }

  // ==========================================================
  // DATE
  // ==========================================================

  DateTime? get scheduledDateTime {
    if (scheduledDate.isEmpty) {
      return null;
    }

    return DateTime.tryParse(scheduledDate);
  }

  // ==========================================================
  // DISPLAY HELPERS
  // ==========================================================

  String get displayActivityType {
    if (activityType.trim().isEmpty) {
      return 'Farm Activity';
    }

    return _formatEnum(activityType);
  }

  String get displayPriority {
    if (priority.trim().isEmpty) {
      return 'Low';
    }

    return _formatEnum(priority);
  }

  String get displayStatus {
    if (status.trim().isEmpty) {
      return 'Pending';
    }

    return _formatEnum(status);
  }
}

// ============================================================
// ASK FARMATE
// ============================================================

class AskFarmateDashboard {
  final bool activeSession;

  const AskFarmateDashboard({required this.activeSession});

  factory AskFarmateDashboard.fromJson(Map<String, dynamic> json) {
    return AskFarmateDashboard(activeSession: json['active_session'] == true);
  }

  bool get canContinue {
    return activeSession;
  }
}

// ============================================================
// HELPERS
// ============================================================

Map<String, dynamic> _asMap(dynamic value) {
  if (value is Map) {
    return Map<String, dynamic>.from(value);
  }

  return <String, dynamic>{};
}

List<ActivityDashboard> _parseActivities(dynamic value) {
  if (value is! List) {
    return <ActivityDashboard>[];
  }

  return value
      .whereType<Map>()
      .map(
        (item) => ActivityDashboard.fromJson(Map<String, dynamic>.from(item)),
      )
      .toList();
}

double? _toDouble(dynamic value) {
  if (value == null) {
    return null;
  }

  if (value is num) {
    return value.toDouble();
  }

  return double.tryParse(value.toString().trim());
}

int _toInt(dynamic value) {
  if (value == null) {
    return 0;
  }

  if (value is num) {
    return value.toInt();
  }

  return int.tryParse(value.toString().trim()) ?? 0;
}

int _nonNegativeInt(dynamic value) {
  return _toInt(value).clamp(0, 2147483647);
}

int? _nullableInt(dynamic value) {
  if (value == null) {
    return null;
  }

  if (value is num) {
    return value.toInt();
  }

  final parsed = int.tryParse(value.toString().trim());

  return parsed;
}

String? _nullableString(dynamic value) {
  if (value == null) {
    return null;
  }

  final text = value.toString().trim();

  if (text.isEmpty) {
    return null;
  }

  return text;
}

String _formatEnum(String value) {
  final normalized = value.trim().toLowerCase().replaceAll('_', ' ');

  if (normalized.isEmpty) {
    return '';
  }

  return normalized
      .split(' ')
      .map((word) {
        if (word.isEmpty) {
          return word;
        }

        return word[0].toUpperCase() + word.substring(1);
      })
      .join(' ');
}

import 'crop_season_model.dart';

enum CropStageStatus {
  pending('PENDING', 'Pending'),
  active('ACTIVE', 'Active'),
  completed('COMPLETED', 'Completed'),
  skipped('SKIPPED', 'Skipped');

  const CropStageStatus(this.wireValue, this.label);

  final String wireValue;
  final String label;

  static CropStageStatus fromJson(dynamic value) {
    final wireValue = value?.toString().trim().toUpperCase() ?? '';

    for (final status in values) {
      if (status.wireValue == wireValue) {
        return status;
      }
    }

    throw const FormatException('Invalid crop stage status received.');
  }
}

enum CropActivityStatus {
  pending('PENDING', 'Pending'),
  inProgress('IN_PROGRESS', 'In progress'),
  completed('COMPLETED', 'Completed'),
  skipped('SKIPPED', 'Skipped');

  const CropActivityStatus(this.wireValue, this.label);

  final String wireValue;
  final String label;

  static CropActivityStatus fromJson(dynamic value) {
    final wireValue = value?.toString().trim().toUpperCase() ?? '';

    for (final status in values) {
      if (status.wireValue == wireValue) {
        return status;
      }
    }

    throw const FormatException('Invalid activity status received.');
  }
}

enum CropActivityPriority {
  low('LOW', 'Low'),
  medium('MEDIUM', 'Medium'),
  high('HIGH', 'High'),
  critical('CRITICAL', 'Critical');

  const CropActivityPriority(this.wireValue, this.label);

  final String wireValue;
  final String label;

  static CropActivityPriority fromJson(dynamic value) {
    final wireValue = value?.toString().trim().toUpperCase() ?? '';

    for (final priority in values) {
      if (priority.wireValue == wireValue) {
        return priority;
      }
    }

    throw const FormatException('Invalid activity priority received.');
  }
}

class CropPlanSummary {
  final String cropSeasonId;
  final String cropName;
  final String? cropVariety;
  final FarmingSeason season;
  final int estimatedDurationDays;
  final int stagesCreated;
  final int activitiesCreated;

  const CropPlanSummary({
    required this.cropSeasonId,
    required this.cropName,
    required this.cropVariety,
    required this.season,
    required this.estimatedDurationDays,
    required this.stagesCreated,
    required this.activitiesCreated,
  });

  factory CropPlanSummary.fromJson(Map<String, dynamic> json) {
    final cropSeasonId = json['crop_season_id']?.toString().trim() ?? '';
    final cropName = json['crop_name']?.toString().trim() ?? '';
    final duration = _integer(json['estimated_duration_days']);
    final stagesCreated = _integer(json['stages_created']);
    final activitiesCreated = _integer(json['activities_created']);

    if (cropSeasonId.isEmpty || cropName.isEmpty) {
      throw const FormatException('Invalid crop plan response received.');
    }

    if (duration == null ||
        stagesCreated == null ||
        activitiesCreated == null) {
      throw const FormatException('Invalid crop plan counts received.');
    }

    return CropPlanSummary(
      cropSeasonId: cropSeasonId,
      cropName: cropName,
      cropVariety: _nullableString(json['crop_variety']),
      season: FarmingSeason.fromJson(json['season']),
      estimatedDurationDays: duration,
      stagesCreated: stagesCreated,
      activitiesCreated: activitiesCreated,
    );
  }
}

class CropStageModel {
  final String id;
  final String cropSeasonId;
  final String name;
  final String? description;
  final int stageOrder;
  final int startDay;
  final int endDay;
  final CropStageStatus status;
  final DateTime? startedAt;
  final DateTime? completedAt;

  const CropStageModel({
    required this.id,
    required this.cropSeasonId,
    required this.name,
    required this.description,
    required this.stageOrder,
    required this.startDay,
    required this.endDay,
    required this.status,
    required this.startedAt,
    required this.completedAt,
  });

  factory CropStageModel.fromJson(Map<String, dynamic> json) {
    final id = json['id']?.toString().trim() ?? '';
    final cropSeasonId = json['crop_season_id']?.toString().trim() ?? '';
    final name = json['name']?.toString().trim() ?? '';
    final stageOrder = _integer(json['stage_order']);
    final startDay = _integer(json['start_day']);
    final endDay = _integer(json['end_day']);

    if (id.isEmpty || cropSeasonId.isEmpty || name.isEmpty) {
      throw const FormatException('Invalid crop stage response received.');
    }

    if (stageOrder == null || startDay == null || endDay == null) {
      throw const FormatException('Invalid crop stage timeline received.');
    }

    return CropStageModel(
      id: id,
      cropSeasonId: cropSeasonId,
      name: name,
      description: _nullableString(json['description']),
      stageOrder: stageOrder,
      startDay: startDay,
      endDay: endDay,
      status: CropStageStatus.fromJson(json['status']),
      startedAt: _optionalDate(json['started_at']),
      completedAt: _optionalDate(json['completed_at']),
    );
  }
}

class CropActivityModel {
  final String id;
  final String cropSeasonId;
  final String? stageId;
  final String activityType;
  final String title;
  final String? description;
  final DateTime scheduledDate;
  final DateTime? originalScheduledDate;
  final DateTime? completedDate;
  final CropActivityStatus status;
  final String? notes;
  final CropActivityPriority priority;
  final int? estimatedDurationMinutes;
  final String source;

  const CropActivityModel({
    required this.id,
    required this.cropSeasonId,
    required this.stageId,
    required this.activityType,
    required this.title,
    required this.description,
    required this.scheduledDate,
    required this.originalScheduledDate,
    required this.completedDate,
    required this.status,
    required this.notes,
    required this.priority,
    required this.estimatedDurationMinutes,
    required this.source,
  });

  factory CropActivityModel.fromJson(Map<String, dynamic> json) {
    final id = json['id']?.toString().trim() ?? '';
    final cropSeasonId = json['crop_season_id']?.toString().trim() ?? '';
    final title = json['title']?.toString().trim() ?? '';
    final activityType = json['activity_type']?.toString().trim() ?? '';
    final scheduledDate = _optionalDate(json['scheduled_date']);

    if (id.isEmpty || cropSeasonId.isEmpty || title.isEmpty) {
      throw const FormatException('Invalid activity response received.');
    }

    if (activityType.isEmpty || scheduledDate == null) {
      throw const FormatException('Invalid activity schedule received.');
    }

    return CropActivityModel(
      id: id,
      cropSeasonId: cropSeasonId,
      stageId: _nullableString(json['stage_id']),
      activityType: activityType,
      title: title,
      description: _nullableString(json['description']),
      scheduledDate: scheduledDate,
      originalScheduledDate: _optionalDate(json['original_scheduled_date']),
      completedDate: _optionalDate(json['completed_date']),
      status: CropActivityStatus.fromJson(json['status']),
      notes: _nullableString(json['notes']),
      priority: CropActivityPriority.fromJson(json['priority']),
      estimatedDurationMinutes: _integer(json['estimated_duration_minutes']),
      source: json['source']?.toString().trim() ?? '',
    );
  }
}

String? _nullableString(dynamic value) {
  if (value == null) {
    return null;
  }

  final text = value.toString().trim();

  return text.isEmpty ? null : text;
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

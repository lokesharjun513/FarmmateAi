import 'package:dio/dio.dart';

import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import 'models/crop_plan_models.dart';
import 'models/crop_recommendation_model.dart';
import 'models/crop_season_create_input.dart';
import 'models/crop_season_model.dart';

class CropRepository {
  final ApiClient _apiClient;

  CropRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<List<CropSeasonModel>> getCropSeasons(String farmId) async {
    final normalizedFarmId = farmId.trim();

    if (normalizedFarmId.isEmpty) {
      throw Exception('Select a farm to view its crops.');
    }

    try {
      final response = await _apiClient.dio.get(
        ApiConfig.cropSeasons,
        queryParameters: {'farm_id': normalizedFarmId},
      );

      return _parseCropSeasonList(response.data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to load crops. Please try again.',
          forbiddenMessage: 'You do not have permission to view these crops.',
          serverErrorMessage:
              'FarmMate could not load your crops right now. Please try again.',
          invalidMessage: 'Unable to load crops. Please try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to load crops. Please try again.');
    }
  }

  Future<CropRecommendationModel> getCropRecommendations(String farmId) async {
    final normalizedFarmId = farmId.trim();

    if (normalizedFarmId.isEmpty) {
      throw Exception('Select a farm to get crop recommendations.');
    }

    try {
      final response = await _apiClient.dio.post(
        ApiConfig.cropRecommendation,
        data: {'farm_id': normalizedFarmId},
        options: Options(receiveTimeout: ApiConfig.aiRequestTimeout),
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage:
            'Invalid crop recommendations received from server. Please try again.',
      );

      final recommendation = CropRecommendationModel.fromJson(data);

      if (recommendation.farmId != normalizedFarmId) {
        throw const FormatException(
          'The crop recommendations do not match the selected farm. Please try again.',
        );
      }

      return recommendation;
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage:
              'Unable to generate crop recommendations. Please try again.',
          forbiddenMessage:
              'You do not have permission to get recommendations for this farm.',
          serverErrorMessage:
              'FarmMate could not generate crop recommendations right now. Please try again.',
          invalidMessage:
              'FarmMate could not use this farm\'s details for recommendations. Check the farm details and try again.',
          rateLimitMessage:
              'Too many recommendation requests. Please wait a moment and try again.',
          unavailableMessage:
              'FarmMate AI is temporarily unavailable. Please try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception(
        'Unable to generate crop recommendations. Please try again.',
      );
    }
  }

  Future<CropSeasonModel> createCropSeason({
    required String farmId,
    required CropSeasonCreateInput input,
  }) async {
    final normalizedFarmId = farmId.trim();

    if (normalizedFarmId.isEmpty) {
      throw Exception('Select a farm before creating a crop.');
    }

    try {
      final response = await _apiClient.dio.post(
        ApiConfig.cropSeasons,
        queryParameters: {'farm_id': normalizedFarmId},
        data: input.toJson(),
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop response received from server.',
      );

      return CropSeasonModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to create crop. Please try again.',
          forbiddenMessage:
              'You do not have permission to add a crop to this farm.',
          serverErrorMessage:
              'FarmMate could not create your crop right now. Please try again.',
          invalidMessage: 'Check the crop details and try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to create crop. Please try again.');
    }
  }

  Future<CropSeasonModel> updateCropSeason({
    required String cropSeasonId,
    String? cropName,
    String? cropVariety,
    FarmingSeason? season,
    int? year,
    DateTime? sowingDate,
    DateTime? expectedHarvestDate,
    double? landArea,
    String? landUnit,
    String? notes,
  }) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to update.');
    }

    final payload = <String, dynamic>{};

    if (cropName != null) {
      payload['crop_name'] = cropName.trim();
    }

    if (cropVariety != null) {
      payload['crop_variety'] = cropVariety.trim();
    }

    if (season != null) {
      payload['season'] = season.wireValue;
    }

    if (year != null) {
      payload['year'] = year;
    }

    if (sowingDate != null) {
      payload['sowing_date'] = formatApiDate(sowingDate);
    }

    if (expectedHarvestDate != null) {
      payload['expected_harvest_date'] = formatApiDate(expectedHarvestDate);
    }

    if (landArea != null) {
      payload['land_area'] = landArea;
    }

    if (landUnit != null) {
      payload['land_unit'] = landUnit.trim();
    }

    if (notes != null) {
      payload['notes'] = notes.trim();
    }

    if (payload.isEmpty) {
      throw Exception('Provide at least one crop detail to update.');
    }

    try {
      final response = await _apiClient.dio.put(
        ApiConfig.cropSeason(normalizedCropSeasonId),
        data: payload,
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop response received from server.',
      );

      return CropSeasonModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to update crop. Please try again.',
          forbiddenMessage: 'You do not have permission to edit this crop.',
          serverErrorMessage:
              'FarmMate could not update your crop right now. Please try again.',
          invalidMessage: 'Check the crop details and try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to update crop. Please try again.');
    }
  }

  Future<CropSeasonModel> activateCropSeason(String cropSeasonId) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to start farming.');
    }

    try {
      final response = await _apiClient.dio.patch(
        ApiConfig.cropSeasonStart(normalizedCropSeasonId),
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop response received from server.',
      );

      return CropSeasonModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to start this crop. Please try again.',
          forbiddenMessage: 'You do not have permission to start this crop.',
          serverErrorMessage:
              'FarmMate could not start your crop right now. Please try again.',
          invalidMessage: 'This crop cannot be started yet.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to start this crop. Please try again.');
    }
  }

  Future<CropSeasonModel> harvestCropSeason(
    String cropSeasonId, {
    DateTime? harvestedDate,
    String? notes,
  }) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to harvest.');
    }

    final payload = <String, dynamic>{};

    if (harvestedDate != null) {
      payload['harvested_date'] = formatApiDate(harvestedDate);
    }

    final normalizedNotes = notes?.trim();

    if (normalizedNotes != null && normalizedNotes.isNotEmpty) {
      payload['notes'] = normalizedNotes;
    }

    try {
      final response = await _apiClient.dio.patch(
        ApiConfig.cropSeasonHarvest(normalizedCropSeasonId),
        data: payload.isEmpty ? null : payload,
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop response received from server.',
      );

      return CropSeasonModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to harvest this crop. Please try again.',
          forbiddenMessage: 'You do not have permission to harvest this crop.',
          serverErrorMessage:
              'FarmMate could not harvest your crop right now. Please try again.',
          invalidMessage: 'This crop cannot be harvested yet.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to harvest this crop. Please try again.');
    }
  }

  Future<CropSeasonModel> cancelCropSeason(
    String cropSeasonId, {
    String? reason,
  }) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to cancel.');
    }

    final normalizedReason = reason?.trim();
    final payload = <String, dynamic>{};

    if (normalizedReason != null && normalizedReason.isNotEmpty) {
      payload['reason'] = normalizedReason;
    }

    try {
      final response = await _apiClient.dio.patch(
        ApiConfig.cropSeasonCancel(normalizedCropSeasonId),
        data: payload.isEmpty ? null : payload,
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop response received from server.',
      );

      return CropSeasonModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to cancel this crop. Please try again.',
          forbiddenMessage: 'You do not have permission to cancel this crop.',
          serverErrorMessage:
              'FarmMate could not cancel your crop right now. Please try again.',
          invalidMessage: 'This crop cannot be cancelled.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to cancel this crop. Please try again.');
    }
  }

  Future<void> deleteCropSeason(String cropSeasonId) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to delete.');
    }

    try {
      await _apiClient.dio.delete(ApiConfig.cropSeason(normalizedCropSeasonId));
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to delete this crop. Please try again.',
          forbiddenMessage: 'You do not have permission to delete this crop.',
          serverErrorMessage:
              'FarmMate could not delete your crop right now. Please try again.',
          invalidMessage: 'This crop cannot be deleted.',
        ),
      );
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to delete this crop. Please try again.');
    }
  }

  Future<CropStageModel> completeCropStage(String stageId) async {
    return _mutateStage(
      path: ApiConfig.cropStageComplete(stageId),
      fallbackMessage: 'Unable to complete this stage. Please try again.',
      invalidMessage: 'This stage cannot be completed yet.',
    );
  }

  Future<CropStageModel> skipCropStage(String stageId) async {
    return _mutateStage(
      path: ApiConfig.cropStageSkip(stageId),
      fallbackMessage: 'Unable to skip this stage. Please try again.',
      invalidMessage: 'This stage cannot be skipped.',
    );
  }

  Future<CropStageModel> _mutateStage({
    required String path,
    required String fallbackMessage,
    required String invalidMessage,
  }) async {
    try {
      final response = await _apiClient.dio.patch(path);

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop stage response received from server.',
      );

      return CropStageModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: fallbackMessage,
          forbiddenMessage: 'You do not have permission to update this stage.',
          serverErrorMessage:
              'FarmMate could not update this stage right now. Please try again.',
          invalidMessage: invalidMessage,
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception(fallbackMessage);
    }
  }

  Future<CropActivityModel> startActivity(String activityId) async {
    return _mutateActivity(
      path: ApiConfig.activityStart(activityId),
      fallbackMessage: 'Unable to start this activity. Please try again.',
      invalidMessage: 'This activity cannot be started.',
    );
  }

  Future<CropActivityModel> completeActivity(String activityId) async {
    return _mutateActivity(
      path: ApiConfig.activityComplete(activityId),
      fallbackMessage: 'Unable to complete this activity. Please try again.',
      invalidMessage: 'This activity cannot be completed yet.',
    );
  }

  Future<CropActivityModel> skipActivity(String activityId) async {
    return _mutateActivity(
      path: ApiConfig.activitySkip(activityId),
      fallbackMessage: 'Unable to skip this activity. Please try again.',
      invalidMessage: 'This activity cannot be skipped.',
    );
  }

  Future<CropActivityModel> rescheduleActivity(
    String activityId,
    DateTime scheduledDate,
  ) async {
    final normalizedActivityId = activityId.trim();

    if (normalizedActivityId.isEmpty) {
      throw Exception('Select an activity to reschedule.');
    }

    try {
      final response = await _apiClient.dio.put(
        ApiConfig.activity(normalizedActivityId),
        data: {'scheduled_date': formatApiDate(scheduledDate)},
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid activity response received from server.',
      );

      return CropActivityModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to reschedule this activity.',
          forbiddenMessage:
              'You do not have permission to update this activity.',
          serverErrorMessage:
              'FarmMate could not reschedule this activity. Please try again.',
          invalidMessage: 'This activity cannot be rescheduled.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to reschedule this activity.');
    }
  }

  Future<void> deleteActivity(String activityId) async {
    final normalizedActivityId = activityId.trim();

    if (normalizedActivityId.isEmpty) {
      throw Exception('Select an activity to delete.');
    }

    try {
      await _apiClient.dio.delete(ApiConfig.activity(normalizedActivityId));
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to delete this activity. Please try again.',
          forbiddenMessage:
              'You do not have permission to delete this activity.',
          serverErrorMessage:
              'FarmMate could not delete this activity right now. Please try again.',
          invalidMessage: 'This activity cannot be deleted.',
        ),
      );
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to delete this activity. Please try again.');
    }
  }

  Future<CropActivityModel> _mutateActivity({
    required String path,
    required String fallbackMessage,
    required String invalidMessage,
  }) async {
    try {
      final response = await _apiClient.dio.patch(path);

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid activity response received from server.',
      );

      return CropActivityModel.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: fallbackMessage,
          forbiddenMessage:
              'You do not have permission to update this activity.',
          serverErrorMessage:
              'FarmMate could not update this activity right now. Please try again.',
          invalidMessage: invalidMessage,
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception(fallbackMessage);
    }
  }

  Future<CropPlanSummary> generateCropPlan({
    required String cropSeasonId,
    required String state,
    required String district,
    required String village,
    String? soilType,
  }) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season before generating a plan.');
    }

    final payload = <String, dynamic>{
      'state': state.trim(),
      'district': district.trim(),
      'village': village.trim(),
    };

    final normalizedSoilType = soilType?.trim();

    if (normalizedSoilType != null && normalizedSoilType.isNotEmpty) {
      payload['soil_type'] = normalizedSoilType;
    }

    try {
      final response = await _apiClient.dio.post(
        ApiConfig.cropPlanGenerate(normalizedCropSeasonId),
        data: payload,
        options: Options(receiveTimeout: ApiConfig.aiRequestTimeout),
      );

      final data = _unwrapObject(
        response.data,
        invalidMessage: 'Invalid crop plan response received from server.',
      );

      return CropPlanSummary.fromJson(data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to generate a crop plan. Please try again.',
          forbiddenMessage: 'You do not have permission to plan this crop.',
          serverErrorMessage:
              'FarmMate could not generate your plan right now. Please try again.',
          invalidMessage:
              'The crop plan request was not accepted. Please check the details.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to generate a crop plan. Please try again.');
    }
  }

  Future<List<CropStageModel>> getCropStages(String cropSeasonId) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to view its plan.');
    }

    try {
      final response = await _apiClient.dio.get(
        ApiConfig.cropStages,
        queryParameters: {'crop_season_id': normalizedCropSeasonId},
      );

      final rawList = _unwrapList(
        response.data,
        invalidMessage: 'Invalid crop stages received from server.',
      );

      return rawList
          .map((item) {
            if (item is! Map) {
              throw const FormatException(
                'Invalid crop stage received from server.',
              );
            }

            return CropStageModel.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to load the crop plan. Please try again.',
          forbiddenMessage: 'You do not have permission to view this plan.',
          serverErrorMessage:
              'FarmMate could not load the crop plan right now. Please try again.',
          invalidMessage: 'Unable to load the crop plan. Please try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to load the crop plan. Please try again.');
    }
  }

  Future<List<CropActivityModel>> getCropActivities(String cropSeasonId) async {
    final normalizedCropSeasonId = cropSeasonId.trim();

    if (normalizedCropSeasonId.isEmpty) {
      throw Exception('Select a crop season to view its plan.');
    }

    try {
      final response = await _apiClient.dio.get(
        ApiConfig.activities,
        queryParameters: {'crop_season_id': normalizedCropSeasonId},
      );

      final rawList = _unwrapList(
        response.data,
        invalidMessage: 'Invalid crop activities received from server.',
      );

      return rawList
          .map((item) {
            if (item is! Map) {
              throw const FormatException(
                'Invalid crop activity received from server.',
              );
            }

            return CropActivityModel.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to load the crop plan. Please try again.',
          forbiddenMessage: 'You do not have permission to view this plan.',
          serverErrorMessage:
              'FarmMate could not load the crop plan right now. Please try again.',
          invalidMessage: 'Unable to load the crop plan. Please try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to load the crop plan. Please try again.');
    }
  }

  Map<String, dynamic> _unwrapObject(
    dynamic responseData, {
    required String invalidMessage,
  }) {
    if (responseData is! Map) {
      throw FormatException(invalidMessage);
    }

    final data = Map<String, dynamic>.from(responseData);

    if (data['success'] == false) {
      throw Exception(
        _cleanMessage(data['message']) ??
            _detailMessage(data['detail']) ??
            invalidMessage,
      );
    }

    final payload = data['data'];

    if (payload is! Map) {
      throw FormatException(invalidMessage);
    }

    return Map<String, dynamic>.from(payload);
  }

  List<dynamic> _unwrapList(
    dynamic responseData, {
    required String invalidMessage,
  }) {
    if (responseData is! Map) {
      throw FormatException(invalidMessage);
    }

    final data = Map<String, dynamic>.from(responseData);

    if (data['success'] == false) {
      throw Exception(
        _cleanMessage(data['message']) ??
            _detailMessage(data['detail']) ??
            invalidMessage,
      );
    }

    final payload = data['data'];

    if (payload is! List) {
      throw FormatException(invalidMessage);
    }

    return payload;
  }

  List<CropSeasonModel> _parseCropSeasonList(dynamic responseData) {
    dynamic rawList = responseData;

    if (responseData is Map) {
      final data = Map<String, dynamic>.from(responseData);

      if (data['success'] == false) {
        throw Exception(
          _cleanMessage(data['message']) ??
              _detailMessage(data['detail']) ??
              'Unable to load crops. Please try again.',
        );
      }

      if (data['data'] is List) {
        rawList = data['data'];
      } else if (data.containsKey('success')) {
        throw const FormatException(
          'Crop data is missing from the server response.',
        );
      } else {
        throw const FormatException('Invalid crop list received from server.');
      }
    }

    if (rawList is! List) {
      throw const FormatException('Invalid crop list received from server.');
    }

    try {
      return rawList
          .map((item) {
            if (item is! Map) {
              throw const FormatException(
                'Invalid crop data received from server.',
              );
            }

            return CropSeasonModel.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false);
    } on FormatException {
      rethrow;
    } catch (_) {
      throw const FormatException('Invalid crop data received from server.');
    }
  }

  String _dioErrorMessage(
    DioException error, {
    required String fallbackMessage,
    required String forbiddenMessage,
    required String serverErrorMessage,
    required String invalidMessage,
    String? rateLimitMessage,
    String? unavailableMessage,
  }) {
    final statusCode = error.response?.statusCode;
    final responseData = error.response?.data;

    if (statusCode == 401) {
      return 'Your session has expired. Please log in again.';
    }

    if (statusCode == 403) {
      return forbiddenMessage;
    }

    if (statusCode == 429 && rateLimitMessage != null) {
      return rateLimitMessage;
    }

    if ((statusCode == 502 || statusCode == 503) &&
        unavailableMessage != null) {
      return unavailableMessage;
    }

    if (statusCode == 500) {
      return serverErrorMessage;
    }

    if (responseData is Map) {
      final data = Map<String, dynamic>.from(responseData);
      final message = _cleanMessage(data['message']);

      if (message != null) {
        return message;
      }

      final detail = _detailMessage(data['detail']);

      if (detail != null) {
        return detail;
      }
    }

    if (statusCode == 422) {
      return invalidMessage;
    }

    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError) {
      return 'Unable to reach FarmMate AI. Check your connection and try again.';
    }

    final errorMessage = _cleanMessage(error.error);

    if (errorMessage != null) {
      return errorMessage;
    }

    return fallbackMessage;
  }

  String? _detailMessage(dynamic detail) {
    if (detail is String) {
      return _cleanMessage(detail);
    }

    if (detail is List && detail.isNotEmpty) {
      final first = detail.first;

      if (first is Map) {
        final message = _cleanMessage(first['msg']);

        if (message != null) {
          return message;
        }
      }
    }

    return null;
  }

  String? _cleanMessage(dynamic value) {
    if (value == null) {
      return null;
    }

    final message = value.toString().trim();

    return message.isEmpty ? null : message;
  }
}

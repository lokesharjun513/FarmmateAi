import 'package:dio/dio.dart';

import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import 'models/farm_model.dart';

class FarmRepository {
  final ApiClient _apiClient;

  FarmRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<List<FarmModel>> getFarms() async {
    try {
      final response = await _apiClient.dio.get(ApiConfig.farms);

      return _parseFarmList(response.data);
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to load farms. Please try again.',
          forbiddenMessage: 'You do not have permission to view farms.',
          serverErrorMessage:
              'FarmMate could not load your farms right now. Please try again.',
          invalidMessage: 'Unable to load farms. Please try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to load farms. Please try again.');
    }
  }

  Future<FarmModel> createFarm(FarmCreateInput input) async {
    try {
      final response = await _apiClient.dio.post(
        ApiConfig.farms,
        data: input.toJson(),
      );

      final responseData = response.data;

      if (responseData is Map) {
        final data = Map<String, dynamic>.from(responseData);

        if (data['success'] == true && data['data'] is Map) {
          return FarmModel.fromJson(
            Map<String, dynamic>.from(data['data'] as Map),
          );
        }

        final message = _cleanMessage(data['message']);

        if (message != null) {
          throw Exception(message);
        }
      }

      throw Exception('Unable to create farm. Please try again.');
    } on DioException catch (error) {
      throw Exception(_dioErrorMessage(error));
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to create farm. Please try again.');
    }
  }

  Future<FarmModel> setPrimary(String farmId) async {
    final normalizedFarmId = farmId.trim();

    if (normalizedFarmId.isEmpty) {
      throw Exception('Select a farm to make primary.');
    }

    try {
      final response = await _apiClient.dio.patch(
        '${ApiConfig.farms}/$normalizedFarmId',
        data: const {'is_primary': true},
      );

      final responseData = response.data;

      if (responseData is Map) {
        final data = Map<String, dynamic>.from(responseData);

        if (data['success'] == true && data['data'] is Map) {
          return FarmModel.fromJson(
            Map<String, dynamic>.from(data['data'] as Map),
          );
        }

        final message = _cleanMessage(data['message']);

        if (message != null) {
          throw Exception(message);
        }
      }

      throw Exception('Unable to set primary farm. Please try again.');
    } on DioException catch (error) {
      throw Exception(
        _dioErrorMessage(
          error,
          fallbackMessage: 'Unable to set primary farm. Please try again.',
          forbiddenMessage: 'You do not have permission to change your farms.',
          serverErrorMessage:
              'FarmMate could not switch your primary farm right now. Please try again.',
          invalidMessage:
              'Unable to switch the primary farm. Please try again.',
        ),
      );
    } on FormatException catch (error) {
      throw Exception(error.message);
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception('Unable to set primary farm. Please try again.');
    }
  }

  List<FarmModel> _parseFarmList(dynamic responseData) {
    dynamic rawList = responseData;

    if (responseData is Map) {
      final data = Map<String, dynamic>.from(responseData);

      if (data['success'] == false) {
        throw Exception(
          _cleanMessage(data['message']) ??
              _detailMessage(data['detail']) ??
              'Unable to load farms. Please try again.',
        );
      }

      if (data['data'] is List) {
        rawList = data['data'];
      } else if (data.containsKey('success')) {
        throw const FormatException(
          'Farm data is missing from the server response.',
        );
      } else {
        throw const FormatException('Invalid farm list received from server.');
      }
    }

    if (rawList is! List) {
      throw const FormatException('Invalid farm list received from server.');
    }

    try {
      return rawList
          .map((item) {
            if (item is! Map) {
              throw const FormatException(
                'Invalid farm data received from server.',
              );
            }

            return FarmModel.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false);
    } on FormatException {
      rethrow;
    } catch (_) {
      throw const FormatException('Invalid farm data received from server.');
    }
  }

  String _dioErrorMessage(
    DioException error, {
    String fallbackMessage = 'Unable to create farm. Please try again.',
    String forbiddenMessage = 'You do not have permission to add a farm.',
    String serverErrorMessage =
        'FarmMate could not save your farm right now. Please try again.',
    String invalidMessage = 'Please check the farm details and try again.',
  }) {
    final statusCode = error.response?.statusCode;
    final responseData = error.response?.data;

    if (statusCode == 401) {
      return 'Your session has expired. Please log in again.';
    }

    if (statusCode == 403) {
      return forbiddenMessage;
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

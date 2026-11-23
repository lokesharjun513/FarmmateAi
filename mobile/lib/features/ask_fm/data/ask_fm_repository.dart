import 'package:dio/dio.dart';

import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';

class AskFmRepository {
  final ApiClient _apiClient;

  AskFmRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<String> sendMessage(String message, String farmId, {String? language}) async {
    final trimmedMessage = message.trim();

    if (trimmedMessage.isEmpty) {
      throw Exception('Please enter a question.');
    }

    try {
      final response = await _apiClient.dio.post(
        ApiConfig.askFm,
        data: {
          'message': trimmedMessage,
          'farm_id': farmId,
          'language': ?language,
        },
      );

      final responseData = response.data;

      if (responseData is Map) {
        final data = Map<String, dynamic>.from(responseData);

        if (data['success'] == true && data['data'] is Map) {
          final payload = Map<String, dynamic>.from(data['data'] as Map);
          final answer = payload['answer']?.toString().trim();

          if (answer != null && answer.isNotEmpty) {
            return answer;
          }
        }
      }

      throw Exception(
        'FarmMate AI returned an empty response. Please try again.',
      );
    } on DioException catch (error) {
      throw Exception(_dioErrorMessage(error));
    } catch (error) {
      if (error is Exception) {
        rethrow;
      }

      throw Exception(
        'FarmMate AI could not answer right now. Please try again.',
      );
    }
  }

  String _dioErrorMessage(DioException error) {
    final statusCode = error.response?.statusCode;

    switch (statusCode) {
      case 401:
        return 'Your session has expired. Please log in again.';

      case 403:
        return 'You do not have access to Ask FM.';

      case 404:
        return 'Your farmer profile could not be found. Please complete onboarding.';

      case 422:
        return 'Please enter a question between 1 and 2,000 characters.';

      case 429:
        return 'Too many questions right now. Please wait a moment and try again.';

      case 502:
      case 503:
        return 'FarmMate AI is temporarily unavailable. Please try again.';

      case 500:
        return 'FarmMate AI could not answer right now. Please try again.';
    }

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        return 'Unable to reach FarmMate AI. Please check your connection.';

      case DioExceptionType.badCertificate:
        return 'A secure connection could not be established.';

      case DioExceptionType.cancel:
        return 'The question was cancelled. Please try again.';

      case DioExceptionType.badResponse:
      case DioExceptionType.transformTimeout:
      case DioExceptionType.unknown:
        break;
    }

    return 'FarmMate AI could not answer right now. Please try again.';
  }
}

import 'package:dio/dio.dart';

import '../../../../core/network/api_client.dart';
import '../../data/models/weather_model.dart';

class WeatherRepository {
  final ApiClient _apiClient;

  WeatherRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<CurrentWeatherModel> getCurrentWeather({
    required double latitude,
    required double longitude,
    required String location,
  }) async {
    try {
      final response = await _apiClient.dio.get(
        '/weather/current',
        queryParameters: {
          'latitude': latitude,
          'longitude': longitude,
          'location': location,
        },
      );

      final responseData = response.data;

      if (responseData is! Map<String, dynamic>) {
        throw Exception('Invalid weather response.');
      }

      final data = responseData['data'];

      if (data is! Map<String, dynamic>) {
        throw Exception(
          responseData['message']?.toString() ?? 'Weather data is unavailable.',
        );
      }

      final weather = CurrentWeatherModel.fromJson(data);

      if (!weather.hasTemperature) {
        throw Exception('Current weather is unavailable right now.');
      }

      return weather;
    } on DioException catch (e) {
      final responseData = e.response?.data;

      if (responseData is Map<String, dynamic>) {
        final message = responseData['message']?.toString();

        if (message != null && message.isNotEmpty) {
          throw Exception(message);
        }
      }

      throw Exception(e.message ?? 'Unable to load current weather.');
    } catch (e) {
      if (e is Exception) {
        rethrow;
      }

      throw Exception('Unable to load current weather.');
    }
  }
}

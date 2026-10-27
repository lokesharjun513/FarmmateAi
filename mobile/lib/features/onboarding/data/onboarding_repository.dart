import 'package:dio/dio.dart';

import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';

class OnboardingRepository {
  final ApiClient _apiClient;

  OnboardingRepository({required this._apiClient});

  // ============================================================
  // CHECK FARMER PROFILE
  // ============================================================

  /// Checks whether the authenticated user has a farmer profile.
  ///
  /// Returns:
  /// true  -> farmer profile exists
  /// false -> farmer profile does not exist
  Future<bool> checkProfileExists() async {
    try {
      final response = await _apiClient.dio.get(ApiConfig.farmerProfile);

      return response.statusCode == 200;
    } on DioException catch (e) {
      // --------------------------------------------------------
      // 404 means the authenticated user has not created
      // a farmer profile yet.
      // --------------------------------------------------------

      if (e.response?.statusCode == 404) {
        return false;
      }

      throw Exception(e.error?.toString() ?? 'Unable to check farmer profile.');
    } catch (e) {
      throw Exception(e.toString().replaceFirst('Exception: ', ''));
    }
  }
}

// lib/features/farmer/data/farmer_repository.dart

import 'package:dio/dio.dart';

import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import 'models/farmer_profile_model.dart';

class FarmerRepository {
  final ApiClient _apiClient;

  FarmerRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  // ============================================================
  // GET FARMER PROFILE
  // ============================================================

  Future<FarmerProfileModel?> getProfile() async {
    try {
      final response = await _apiClient.dio.get(ApiConfig.farmerProfile);

      final data = response.data;

      if (data is Map<String, dynamic>) {
        if (data['success'] == true && data['data'] != null) {
          return FarmerProfileModel.fromJson(
            data['data'] as Map<String, dynamic>,
          );
        }

        final message = data['message']?.toString() ?? '';

        if (message == 'Farmer profile not found.') {
          return null;
        }

        throw Exception(
          message.isNotEmpty ? message : 'Unable to retrieve farmer profile.',
        );
      }

      throw Exception('Invalid profile response.');
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        return null;
      }

      throw Exception(
        _getDioErrorMessage(e, fallback: 'Unable to retrieve farmer profile.'),
      );
    }
  }

  // ============================================================
  // CREATE FARMER PROFILE
  // ============================================================

  Future<FarmerProfileModel> createProfile({
    required String preferredLanguage,
    required int experienceYears,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        ApiConfig.farmerProfile,
        data: {
          'preferred_language': preferredLanguage,
          'experience_years': experienceYears,
        },
      );

      final data = response.data;

      if (data is Map<String, dynamic> &&
          data['success'] == true &&
          data['data'] != null) {
        return FarmerProfileModel.fromJson(
          data['data'] as Map<String, dynamic>,
        );
      }

      final message = data is Map<String, dynamic>
          ? data['message']?.toString()
          : null;

      throw Exception(
        message?.isNotEmpty == true
            ? message!
            : 'Unable to create farmer profile.',
      );
    } on DioException catch (e) {
      throw Exception(
        _getDioErrorMessage(e, fallback: 'Unable to create farmer profile.'),
      );
    }
  }

  // ============================================================
  // UPDATE FARMER PROFILE
  // ============================================================

  Future<FarmerProfileModel> updateProfile({
    required String preferredLanguage,
    required int experienceYears,
  }) async {
    try {
      final response = await _apiClient.dio.patch(
        ApiConfig.farmerProfile,
        data: {
          'preferred_language': preferredLanguage,
          'experience_years': experienceYears,
        },
      );

      final data = response.data;

      if (data is Map<String, dynamic> &&
          data['success'] == true &&
          data['data'] != null) {
        return FarmerProfileModel.fromJson(
          data['data'] as Map<String, dynamic>,
        );
      }

      final message = data is Map<String, dynamic>
          ? data['message']?.toString()
          : null;

      throw Exception(
        message?.isNotEmpty == true
            ? message!
            : 'Unable to update farmer profile.',
      );
    } on DioException catch (e) {
      throw Exception(
        _getDioErrorMessage(e, fallback: 'Unable to update farmer profile.'),
      );
    }
  }

  // ============================================================
  // DIO ERROR MESSAGE
  // ============================================================

  String _getDioErrorMessage(DioException error, {required String fallback}) {
    final responseData = error.response?.data;

    if (responseData is Map<String, dynamic>) {
      final message = responseData['message'];

      if (message != null && message.toString().isNotEmpty) {
        return message.toString();
      }

      final detail = responseData['detail'];

      if (detail != null && detail.toString().isNotEmpty) {
        return detail.toString();
      }
    }

    if (error.message != null && error.message!.isNotEmpty) {
      return error.message!;
    }

    return fallback;
  }
}

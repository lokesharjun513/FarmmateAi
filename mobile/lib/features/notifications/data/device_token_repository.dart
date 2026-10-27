import 'package:dio/dio.dart';

import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';

class DeviceTokenRepository {
  final ApiClient _apiClient;

  DeviceTokenRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<void> registerDevice({required String fid, String? deviceName}) async {
    final cleanFid = fid.trim();

    if (cleanFid.isEmpty) {
      throw Exception('Firebase Installation ID cannot be empty.');
    }

    try {
      final response = await _apiClient.dio.post(
        ApiConfig.deviceTokens,
        data: {
          'fid': cleanFid,
          if (deviceName != null && deviceName.trim().isNotEmpty)
            'device_name': deviceName.trim(),
        },
      );

      _throwIfUnsuccessful(response.data, 'Unable to register this device.');
    } on DioException catch (error) {
      throw Exception(
        error.error?.toString() ??
            'Unable to register this device. Please try again.',
      );
    }
  }

  Future<void> deactivateDevice(String fid) async {
    final cleanFid = fid.trim();

    if (cleanFid.isEmpty) {
      return;
    }

    try {
      await _apiClient.dio.delete(ApiConfig.deviceToken(cleanFid));
    } on DioException catch (error) {
      throw Exception(
        error.error?.toString() ??
            'Unable to deactivate this device. Please try again.',
      );
    }
  }

  void _throwIfUnsuccessful(dynamic data, String fallbackMessage) {
    if (data is! Map<String, dynamic>) {
      return;
    }

    if (data['success'] == false) {
      final message = data['message'];

      throw Exception(
        message is String && message.trim().isNotEmpty
            ? message.trim()
            : fallbackMessage,
      );
    }
  }
}

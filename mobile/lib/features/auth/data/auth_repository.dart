import 'package:dio/dio.dart';
import '../../../core/config/api_config.dart';
import '../../../core/network/api_client.dart';
import 'models/auth_response.dart';
import 'models/user_model.dart';

class AuthRepository {
  final ApiClient _apiClient;

  AuthRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<UserModel> register({
    required String fullName,
    required String mobile,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        ApiConfig.register,
        data: {
          'full_name': fullName,
          'mobile': mobile,
          'email': email,
          'password': password,
        },
      );

      final authResponse = AuthResponse<UserModel>.fromJson(
        response.data,
        (json) => UserModel.fromJson(json as Map<String, dynamic>),
      );

      if (authResponse.success && authResponse.data != null) {
        return authResponse.data!;
      } else {
        throw authResponse.message.isNotEmpty
            ? authResponse.message
            : 'Registration failed.';
      }
    } on DioException catch (e) {
      throw e.error?.toString() ?? 'Registration failed. Please try again.';
    } catch (e) {
      throw e.toString();
    }
  }

  Future<LoginData> login({
    required String identifier,
    required String password,
  }) async {
    try {
      final response = await _apiClient.dio.post(
        ApiConfig.login,
        data: {'identifier': identifier, 'password': password},
      );

      final authResponse = AuthResponse<LoginData>.fromJson(
        response.data,
        (json) => LoginData.fromJson(json as Map<String, dynamic>),
      );

      if (authResponse.success && authResponse.data != null) {
        return authResponse.data!;
      } else {
        throw authResponse.message.isNotEmpty
            ? authResponse.message
            : 'Login failed.';
      }
    } on DioException catch (e) {
      throw e.error?.toString() ?? 'Login failed. Please try again.';
    } catch (e) {
      throw e.toString();
    }
  }

  Future<UserModel> getMe() async {
    try {
      final response = await _apiClient.dio.get(ApiConfig.me);

      final authResponse = AuthResponse<UserModel>.fromJson(
        response.data,
        (json) => UserModel.fromJson(json as Map<String, dynamic>),
      );

      if (authResponse.success && authResponse.data != null) {
        return authResponse.data!;
      } else {
        throw authResponse.message.isNotEmpty
            ? authResponse.message
            : 'Failed to retrieve user session.';
      }
    } on DioException catch (e) {
      throw e.error?.toString() ?? 'Session verification failed.';
    } catch (e) {
      throw e.toString();
    }
  }

  // ============================================================
  // PASSWORD RESET
  // ============================================================

  Future<Map<String, dynamic>> forgotPassword({required String email}) async {
    final response = await _apiClient.dio.post(
      ApiConfig.forgotPassword,
      data: {'email': email},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> verifyResetOtp({
    required String email,
    required String otp,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.verifyResetOtp,
      data: {'email': email, 'otp': otp},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> resetPassword({
    required String resetToken,
    required String newPassword,
  }) async {
    final response = await _apiClient.dio.post(
      ApiConfig.resetPassword,
      data: {'reset_token': resetToken, 'new_password': newPassword},
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> resendResetOtp({required String email}) async {
    final response = await _apiClient.dio.post(
      ApiConfig.resendResetOtp,
      data: {'email': email},
    );
    return response.data as Map<String, dynamic>;
  }
}

import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../storage/token_storage.dart';

class ApiClient {
  late final Dio dio;
  final TokenStorage _tokenStorage;

  ApiClient({TokenStorage? tokenStorage})
    : _tokenStorage = tokenStorage ?? TokenStorage() {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: ApiConfig.connectTimeout,
        sendTimeout: ApiConfig.sendTimeout,
        receiveTimeout: ApiConfig.receiveTimeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.getToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (DioException e, handler) {
          final errorMessage = _handleDioError(e);
          return handler.next(
            DioException(
              requestOptions: e.requestOptions,
              error: errorMessage,
              response: e.response,
              type: e.type,
            ),
          );
        },
      ),
    );
  }

  String _handleDioError(DioException error) {
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError) {
      return 'Unable to connect to FarmMate AI. Please check your internet connection.';
    }

    if (error.response != null) {
      final data = error.response?.data;
      if (data is Map<String, dynamic> && data.containsKey('message')) {
        return data['message'].toString();
      }
      switch (error.response?.statusCode) {
        case 400:
          return 'Bad request. Please check your inputs.';
        case 401:
          return 'Unauthorized. Please login again.';
        case 403:
          return 'Access forbidden.';
        case 404:
          return 'Requested resource not found.';
        case 422:
          return 'Validation error. Please check your information.';
        case 500:
          return 'Server error. Please try again later.';
        default:
          return 'Something went wrong. Please try again.';
      }
    }
    return 'An unexpected error occurred. Please try again.';
  }
}

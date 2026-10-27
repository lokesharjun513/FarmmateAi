// lib/features/dashboard/data/repositories/dashboard_repository.dart

import 'package:dio/dio.dart';

import '../../../../core/config/api_config.dart';
import '../../../../core/network/api_client.dart';
import '../models/dashboard_model.dart';

class DashboardRepository {
  final ApiClient _apiClient;

  DashboardRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  // ============================================================
  // GET DASHBOARD
  // ============================================================

  Future<DashboardModel> getDashboard() async {
    try {
      final response = await _apiClient.dio.get(ApiConfig.dashboard);

      return _parseDashboardResponse(response.data);
    } on DioException catch (e) {
      throw Exception(_handleDioException(e));
    } on FormatException catch (e) {
      throw Exception(e.message);
    } catch (e) {
      if (e is Exception) {
        rethrow;
      }

      throw Exception(e.toString());
    }
  }

  // ============================================================
  // PARSE DASHBOARD RESPONSE
  // ============================================================

  DashboardModel _parseDashboardResponse(dynamic responseData) {
    // ----------------------------------------------------------
    // RESPONSE MUST BE A MAP
    // ----------------------------------------------------------

    if (responseData == null) {
      throw const FormatException(
        'Dashboard server returned an empty response.',
      );
    }

    if (responseData is! Map) {
      throw const FormatException(
        'Invalid dashboard response received from server.',
      );
    }

    final data = Map<String, dynamic>.from(responseData);

    // ----------------------------------------------------------
    // SUCCESS RESPONSE
    //
    // Expected:
    //
    // {
    //   "success": true,
    //   "data": {
    //      ...
    //   }
    // }
    //
    // ----------------------------------------------------------

    if (data['success'] == true) {
      final dashboardData = data['data'];

      if (dashboardData is Map) {
        return DashboardModel.fromJson(
          Map<String, dynamic>.from(dashboardData),
        );
      }

      // --------------------------------------------------------
      // SOME BACKENDS MAY RETURN:
      //
      // {
      //   "success": true,
      //   "greeting": "...",
      //   "farmer": {...},
      //   ...
      // }
      // --------------------------------------------------------

      if (_looksLikeDashboardPayload(data)) {
        return DashboardModel.fromJson(data);
      }

      throw const FormatException(
        'Dashboard data is missing from the server response.',
      );
    }

    // ----------------------------------------------------------
    // SUCCESS FIELD NOT PRESENT
    //
    // Allow direct dashboard response if the backend returns:
    //
    // {
    //   "greeting": "...",
    //   "farmer": {...},
    //   "farm": {...}
    // }
    //
    // ----------------------------------------------------------

    if (!data.containsKey('success') && _looksLikeDashboardPayload(data)) {
      return DashboardModel.fromJson(data);
    }

    // ----------------------------------------------------------
    // API SUCCESS = FALSE
    // ----------------------------------------------------------

    throw Exception(_extractApiErrorMessage(data));
  }

  // ============================================================
  // DASHBOARD PAYLOAD DETECTION
  // ============================================================

  bool _looksLikeDashboardPayload(Map<String, dynamic> data) {
    return data.containsKey('greeting') ||
        data.containsKey('farmer') ||
        data.containsKey('farm') ||
        data.containsKey('active_crop') ||
        data.containsKey('weather') ||
        data.containsKey('advisor') ||
        data.containsKey('stats') ||
        data.containsKey('activities') ||
        data.containsKey('ask_fm');
  }

  // ============================================================
  // API ERROR MESSAGE
  // ============================================================

  String _extractApiErrorMessage(Map<String, dynamic> data) {
    // ----------------------------------------------------------
    // MESSAGE
    // ----------------------------------------------------------

    final message = _cleanString(data['message']);

    if (message != null) {
      return message;
    }

    // ----------------------------------------------------------
    // DETAIL
    //
    // FastAPI commonly returns:
    //
    // {
    //   "detail": "Something went wrong"
    // }
    //
    // ----------------------------------------------------------

    final detail = data['detail'];

    final detailMessage = _extractErrorValue(detail);

    if (detailMessage != null) {
      return detailMessage;
    }

    // ----------------------------------------------------------
    // ERRORS
    // ----------------------------------------------------------

    final errors = data['errors'];

    final errorsMessage = _extractErrors(errors);

    if (errorsMessage != null) {
      return errorsMessage;
    }

    // ----------------------------------------------------------
    // DEFAULT
    // ----------------------------------------------------------

    return 'Unable to load dashboard.';
  }

  // ============================================================
  // EXTRACT ERROR VALUE
  // ============================================================

  String? _extractErrorValue(dynamic value) {
    if (value == null) {
      return null;
    }

    // ----------------------------------------------------------
    // STRING
    // ----------------------------------------------------------

    if (value is String) {
      final message = value.trim();

      return message.isEmpty ? null : message;
    }

    // ----------------------------------------------------------
    // MAP
    // ----------------------------------------------------------

    if (value is Map) {
      final map = Map<String, dynamic>.from(value);

      final message = _cleanString(map['message']);

      if (message != null) {
        return message;
      }

      final detail = _cleanString(map['detail']);

      if (detail != null) {
        return detail;
      }

      final msg = _cleanString(map['msg']);

      if (msg != null) {
        return msg;
      }

      final errors = _extractErrors(map['errors']);

      if (errors != null) {
        return errors;
      }

      return null;
    }

    // ----------------------------------------------------------
    // LIST
    // ----------------------------------------------------------

    if (value is List) {
      final messages = value
          .map(_extractErrorValue)
          .whereType<String>()
          .where((message) => message.trim().isNotEmpty)
          .toList();

      if (messages.isEmpty) {
        return null;
      }

      return messages.join(', ');
    }

    // ----------------------------------------------------------
    // OTHER TYPES
    // ----------------------------------------------------------

    final text = value.toString().trim();

    return text.isEmpty ? null : text;
  }

  // ============================================================
  // EXTRACT ERRORS
  // ============================================================

  String? _extractErrors(dynamic errors) {
    if (errors == null) {
      return null;
    }

    // ----------------------------------------------------------
    // LIST
    // ----------------------------------------------------------

    if (errors is List) {
      final messages = <String>[];

      for (final error in errors) {
        final message = _extractErrorValue(error);

        if (message != null && message.trim().isNotEmpty) {
          messages.add(message.trim());
        }
      }

      if (messages.isEmpty) {
        return null;
      }

      return messages.join(', ');
    }

    // ----------------------------------------------------------
    // MAP
    // ----------------------------------------------------------

    if (errors is Map) {
      final messages = <String>[];

      errors.forEach((key, value) {
        final message = _extractErrorValue(value);

        if (message != null && message.trim().isNotEmpty) {
          messages.add('$key: $message');
        }
      });

      if (messages.isEmpty) {
        return null;
      }

      return messages.join(', ');
    }

    // ----------------------------------------------------------
    // STRING / OTHER
    // ----------------------------------------------------------

    return _extractErrorValue(errors);
  }

  // ============================================================
  // DIO ERROR HANDLING
  // ============================================================

  String _handleDioException(DioException e) {
    // ----------------------------------------------------------
    // SERVER RESPONSE
    // ----------------------------------------------------------

    final responseData = e.response?.data;

    if (responseData is Map) {
      final data = Map<String, dynamic>.from(responseData);

      final serverMessage = _extractApiErrorMessage(data);

      if (serverMessage != 'Unable to load dashboard.') {
        return serverMessage;
      }
    }

    // ----------------------------------------------------------
    // RESPONSE IS STRING
    // ----------------------------------------------------------

    if (responseData is String) {
      final message = responseData.trim();

      if (message.isNotEmpty) {
        return message;
      }
    }

    // ----------------------------------------------------------
    // HTTP STATUS
    // ----------------------------------------------------------

    final statusCode = e.response?.statusCode;

    switch (statusCode) {
      case 400:
        return 'Invalid dashboard request.';

      case 401:
        return 'Your session has expired. Please login again.';

      case 403:
        return 'You are not authorized to access the dashboard.';

      case 404:
        return 'Dashboard endpoint was not found.';

      case 408:
        return 'Dashboard request timed out.';

      case 409:
        return 'Dashboard data conflict. Please try again.';

      case 422:
        return 'Invalid dashboard data.';

      case 429:
        return 'Too many requests. Please try again later.';

      case 500:
        return 'Server error. Please try again later.';

      case 502:
        return 'Bad gateway. Please try again later.';

      case 503:
        return 'Dashboard service is temporarily unavailable.';

      case 504:
        return 'Dashboard server timed out.';
    }

    // ----------------------------------------------------------
    // DIO ERROR TYPE
    // ----------------------------------------------------------

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
        return 'Connection timed out.';

      case DioExceptionType.sendTimeout:
        return 'Request timed out.';

      case DioExceptionType.receiveTimeout:
        return 'Server response timed out.';

      case DioExceptionType.connectionError:
        return 'Unable to connect to the server.';

      case DioExceptionType.cancel:
        return 'Dashboard request was cancelled.';

      case DioExceptionType.badCertificate:
        return 'Secure connection failed.';

      case DioExceptionType.badResponse:
        return 'Invalid response from server.';

      case DioExceptionType.transformTimeout:
        return 'Request processing timed out.';

      case DioExceptionType.unknown:
        return _handleUnknownDioError(e);
    }
  }

  // ============================================================
  // UNKNOWN DIO ERROR
  // ============================================================

  String _handleUnknownDioError(DioException e) {
    final error = e.error;

    if (error != null) {
      final message = error.toString().trim();

      if (message.isNotEmpty && message != 'null') {
        return message;
      }
    }

    return 'Network error. Please try again.';
  }

  // ============================================================
  // CLEAN STRING
  // ============================================================

  String? _cleanString(dynamic value) {
    if (value == null) {
      return null;
    }

    final text = value.toString().trim();

    if (text.isEmpty) {
      return null;
    }

    return text;
  }
}

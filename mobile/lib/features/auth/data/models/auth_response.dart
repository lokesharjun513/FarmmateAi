class AuthResponse<T> {
  final bool success;
  final String message;
  final T? data;

  AuthResponse({required this.success, required this.message, this.data});

  factory AuthResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object? json) fromJsonT,
  ) {
    return AuthResponse<T>(
      success: json['success'] == true,
      message: json['message']?.toString() ?? '',
      data: json['data'] != null ? fromJsonT(json['data']) : null,
    );
  }
}

class LoginData {
  final String accessToken;
  final String tokenType;

  LoginData({required this.accessToken, required this.tokenType});

  factory LoginData.fromJson(Map<String, dynamic> json) {
    return LoginData(
      accessToken: json['access_token']?.toString() ?? '',
      tokenType: json['token_type']?.toString() ?? 'bearer',
    );
  }
}

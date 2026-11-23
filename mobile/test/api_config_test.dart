import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/core/config/api_config.dart';

void main() {
  group('ApiConfig.normalizeBaseUrl', () {
    test('appends /api/v1 to a bare host', () {
      expect(
        ApiConfig.normalizeBaseUrl('https://farmate-ai-api.onrender.com'),
        'https://farmate-ai-api.onrender.com/api/v1',
      );
    });

    test('strips trailing slash before appending the prefix', () {
      expect(
        ApiConfig.normalizeBaseUrl('https://farmate-ai-api.onrender.com/'),
        'https://farmate-ai-api.onrender.com/api/v1',
      );
    });

    test('leaves an already-prefixed URL unchanged', () {
      expect(
        ApiConfig.normalizeBaseUrl('https://farmate-ai-api.onrender.com/api/v1'),
        'https://farmate-ai-api.onrender.com/api/v1',
      );
    });

    test('strips trailing slash from an already-prefixed URL', () {
      expect(
        ApiConfig.normalizeBaseUrl('https://farmate-ai-api.onrender.com/api/v1/'),
        'https://farmate-ai-api.onrender.com/api/v1',
      );
    });

    test('normalizes the Android emulator default', () {
      expect(
        ApiConfig.normalizeBaseUrl('http://10.0.2.2:8000'),
        'http://10.0.2.2:8000/api/v1',
      );
    });

    test('normalizes the desktop/simulator default', () {
      expect(
        ApiConfig.normalizeBaseUrl('http://127.0.0.1:8000'),
        'http://127.0.0.1:8000/api/v1',
      );
    });

    test('handles whitespace around the URL', () {
      expect(
        ApiConfig.normalizeBaseUrl('  https://farmate-ai-api.onrender.com  '),
        'https://farmate-ai-api.onrender.com/api/v1',
      );
    });
  });

  group('ApiConfig route constants', () {
    test('auth routes remain relative to the versioned base', () {
      expect(ApiConfig.login, '/auth/login');
      expect(ApiConfig.register, '/auth/register');
      expect(ApiConfig.forgotPassword, '/auth/forgot-password');
    });

    test('key resource routes remain versioned-base relative', () {
      expect(ApiConfig.farms, '/farms');
      expect(ApiConfig.weatherCurrent, '/weather/current');
      expect(ApiConfig.dashboard, '/dashboard');
    });
  });

  group('Production URL composition', () {
    test('login resolves to /api/v1/auth/login with exactly one prefix', () {
      final base = ApiConfig.normalizeBaseUrl(
        'https://farmate-ai-api.onrender.com',
      );
      final loginUrl = '$base${ApiConfig.login}';

      expect(loginUrl, 'https://farmate-ai-api.onrender.com/api/v1/auth/login');
      expect(
        'api/v1'.allMatches(loginUrl).length,
        1,
        reason: 'The /api/v1 prefix must appear exactly once',
      );
    });
  });
}

import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/farm/data/farm_repository.dart';

class FakeTokenStorage extends TokenStorage {
  @override
  Future<String?> getToken() async => 'test-token';
}

class FakeHttpAdapter implements HttpClientAdapter {
  FakeHttpAdapter(this.handler);

  final ResponseBody Function(RequestOptions options) handler;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonResponse(dynamic body, {int statusCode = 200}) {
  return ResponseBody.fromString(
    jsonEncode(body),
    statusCode,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );
}

FarmRepository buildRepository(
  ResponseBody Function(RequestOptions options) handler, {
  void Function(RequestOptions options)? onRequest,
}) {
  final apiClient = ApiClient(tokenStorage: FakeTokenStorage());

  apiClient.dio.httpClientAdapter = FakeHttpAdapter((options) {
    onRequest?.call(options);
    return handler(options);
  });

  return FarmRepository(apiClient: apiClient);
}

Map<String, dynamic> farmJson({
  String id = 'farm-1',
  String name = 'North Field',
  bool isPrimary = true,
}) {
  return {
    'id': id,
    'farmer_id': 'farmer-1',
    'farm_name': name,
    'state': 'Andhra Pradesh',
    'district': 'Nellore',
    'mandal': 'Kavali',
    'village': 'Ramapuram',
    'latitude': null,
    'longitude': null,
    'land_area': 2.5,
    'land_unit': 'Acres',
    'soil_type': 'Clay',
    'water_source': 'Borewell',
    'water_availability': 'HIGH',
    'irrigation_method': 'Drip',
    'is_primary': isPrimary,
  };
}

Matcher throwsExceptionWith(String message) {
  return throwsA(
    isA<Exception>().having(
      (error) => error.toString(),
      'message',
      contains(message),
    ),
  );
}

void main() {
  test('getFarms parses the authenticated wrapped list response', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (options) => jsonResponse({
        'success': true,
        'message': 'Farms retrieved successfully.',
        'data': [
          farmJson(id: 'farm-2', name: 'South Field', isPrimary: false),
          farmJson(),
        ],
      }),
      onRequest: (options) {
        captured = options;
      },
    );

    final farms = await repository.getFarms();

    expect(captured!.path, '/farms');
    expect(captured!.headers['Authorization'], 'Bearer test-token');
    expect(farms, hasLength(2));
    expect(farms.first.farmName, 'South Field');
    expect(farms.last.isPrimary, isTrue);
  });

  test('getFarms accepts an empty list', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': <dynamic>[]}),
    );

    final farms = await repository.getFarms();

    expect(farms, isEmpty);
  });

  test('getFarms surfaces API success false messages', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': false,
        'message': 'Farmer profile is required.',
      }),
    );

    await expectLater(
      repository.getFarms(),
      throwsExceptionWith('Farmer profile is required.'),
    );
  });

  test('getFarms rejects malformed list data', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': 'not-a-list'}),
    );

    await expectLater(
      repository.getFarms(),
      throwsExceptionWith('Farm data is missing'),
    );
  });

  test('getFarms maps unauthorized responses', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'detail': 'Unauthorized'}, statusCode: 401),
    );

    await expectLater(
      repository.getFarms(),
      throwsExceptionWith('session has expired'),
    );
  });

  test('getFarms maps connection failures', () async {
    final repository = buildRepository((options) {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.connectionError,
      );
    });

    await expectLater(
      repository.getFarms(),
      throwsExceptionWith('Unable to reach FarmMate AI'),
    );
  });

  test(
    'setPrimary patches the selected farm and parses the response',
    () async {
      RequestOptions? captured;

      final repository = buildRepository(
        (_) => jsonResponse({
          'success': true,
          'message': 'Farm updated successfully.',
          'data': farmJson(id: 'farm-2', name: 'South Field', isPrimary: true),
        }),
        onRequest: (options) {
          captured = options;
        },
      );

      final farm = await repository.setPrimary('farm-2');

      expect(captured!.method, 'PATCH');
      expect(captured!.path, '/farms/farm-2');
      expect(captured!.headers['Authorization'], 'Bearer test-token');
      expect(captured!.data, {'is_primary': true});
      expect(farm.id, 'farm-2');
      expect(farm.isPrimary, isTrue);
    },
  );

  test('setPrimary maps server failures without reporting success', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'detail': 'Internal server error'}, statusCode: 500),
    );

    await expectLater(
      repository.setPrimary('farm-2'),
      throwsExceptionWith('could not switch your primary farm'),
    );
  });

  test('setPrimary rejects malformed farm responses', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': 'not-a-farm'}),
    );

    await expectLater(
      repository.setPrimary('farm-2'),
      throwsExceptionWith('Unable to set primary farm'),
    );
  });
}

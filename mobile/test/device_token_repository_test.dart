import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/notifications/data/device_token_repository.dart';

class FakeTokenStorage extends TokenStorage {
  @override
  Future<String?> getToken() async => 'test-token';
}

class FakeHttpAdapter implements HttpClientAdapter {
  FakeHttpAdapter(this.handler, {this.onRequest});

  final ResponseBody Function(RequestOptions options) handler;
  final void Function(RequestOptions options)? onRequest;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    onRequest?.call(options);
    return handler(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonResponse(Object body, {int statusCode = 200}) {
  return ResponseBody.fromString(
    jsonEncode(body),
    statusCode,
    headers: {
      Headers.contentTypeHeader: [Headers.jsonContentType],
    },
  );
}

DeviceTokenRepository buildRepository(
  ResponseBody Function(RequestOptions options) handler, {
  void Function(RequestOptions options)? onRequest,
}) {
  final apiClient = ApiClient(tokenStorage: FakeTokenStorage());
  apiClient.dio.httpClientAdapter = FakeHttpAdapter(
    handler,
    onRequest: onRequest,
  );

  return DeviceTokenRepository(apiClient: apiClient);
}

void main() {
  test('registerDevice posts the FID and device name', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'message': 'Device registration saved successfully.',
        'data': null,
      }),
      onRequest: (options) {
        captured = options;
      },
    );

    await repository.registerDevice(fid: ' fid-1 ', deviceName: ' Android ');

    expect(captured!.path, '/notifications/devices');
    expect(captured!.method, 'POST');
    expect(captured!.data, {'fid': 'fid-1', 'device_name': 'Android'});
    expect(captured!.headers['Authorization'], 'Bearer test-token');
  });

  test('registerDevice surfaces API success false messages', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': false, 'message': 'FID is invalid.'}),
    );

    expect(
      () => repository.registerDevice(fid: 'fid-1'),
      throwsA(
        predicate((error) => error.toString().contains('FID is invalid.')),
      ),
    );
  });

  test('deactivateDevice encodes the FID in the delete path', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({}, statusCode: 204),
      onRequest: (options) {
        captured = options;
      },
    );

    await repository.deactivateDevice(' fid/with space ');

    expect(captured!.method, 'DELETE');
    expect(captured!.path, '/notifications/devices/fid%2Fwith%20space');
  });
}

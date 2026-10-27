import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/config/api_config.dart';
import 'package:mobile/core/network/api_client.dart';
import 'package:mobile/core/storage/token_storage.dart';
import 'package:mobile/features/crops/data/crop_repository.dart';
import 'package:mobile/features/crops/data/models/crop_plan_models.dart';
import 'package:mobile/features/crops/data/models/crop_season_model.dart';

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

CropRepository buildRepository(
  ResponseBody Function(RequestOptions options) handler, {
  void Function(RequestOptions options)? onRequest,
}) {
  final apiClient = ApiClient(tokenStorage: FakeTokenStorage());

  apiClient.dio.httpClientAdapter = FakeHttpAdapter((options) {
    onRequest?.call(options);
    return handler(options);
  });

  return CropRepository(apiClient: apiClient);
}

Map<String, dynamic> cropJson({
  String id = 'crop-1',
  String farmId = 'farm-1',
  String cropName = 'Rice',
  String? cropVariety = 'BPT 5204',
  String season = 'KHARIF',
  int year = 2026,
  String sowingDate = '2026-06-12',
  String? expectedHarvestDate = '2026-10-20',
  String? harvestedDate,
  double landArea = 2.5,
  String status = 'ACTIVE',
  bool isActive = true,
  String? cancellationReason,
}) {
  return {
    'id': id,
    'farm_id': farmId,
    'crop_name': cropName,
    'crop_variety': cropVariety,
    'season': season,
    'year': year,
    'sowing_date': sowingDate,
    'expected_harvest_date': expectedHarvestDate,
    'harvested_date': harvestedDate,
    'land_area': landArea,
    'land_unit': 'Acres',
    'status': status,
    'is_active': isActive,
    'notes': null,
    'cancellation_reason': cancellationReason,
  };
}

Map<String, dynamic> stageJson({
  String id = 'stage-1',
  String status = 'COMPLETED',
}) {
  return {
    'id': id,
    'crop_season_id': 'crop-1',
    'name': 'Land preparation',
    'description': 'Prepare the field.',
    'stage_order': 1,
    'start_day': 1,
    'end_day': 10,
    'status': status,
    'started_at': '2026-06-12',
    'completed_at': '2026-06-20',
  };
}

Map<String, dynamic> activityJson({
  String id = 'activity-1',
  String status = 'COMPLETED',
  String scheduledDate = '2026-06-12',
}) {
  return {
    'id': id,
    'crop_season_id': 'crop-1',
    'stage_id': 'stage-1',
    'activity_type': 'LAND_PREPARATION',
    'title': 'Plough the field',
    'description': null,
    'scheduled_date': scheduledDate,
    'original_scheduled_date': null,
    'completed_date': null,
    'status': status,
    'notes': null,
    'priority': 'MEDIUM',
    'estimated_duration_minutes': null,
    'source': 'AI_PLANNED',
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
  test('getCropSeasons sends farm id and parses the wrapped list', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (options) => jsonResponse({
        'success': true,
        'message': 'Crop seasons retrieved successfully.',
        'data': [
          cropJson(),
          cropJson(
            id: 'crop-2',
            cropName: 'Cotton',
            cropVariety: null,
            season: 'RABI',
            status: 'PLANNED',
            isActive: false,
            expectedHarvestDate: null,
          ),
        ],
      }),
      onRequest: (options) {
        captured = options;
      },
    );

    final crops = await repository.getCropSeasons(' farm-1 ');

    expect(captured!.path, '/crop-seasons');
    expect(captured!.method, 'GET');
    expect(captured!.queryParameters['farm_id'], 'farm-1');
    expect(captured!.headers['Authorization'], 'Bearer test-token');
    expect(crops, hasLength(2));
    expect(crops.first.cropName, 'Rice');
    expect(crops.first.cropVariety, 'BPT 5204');
    expect(crops.first.season, FarmingSeason.kharif);
    expect(crops.first.status, CropSeasonStatus.active);
    expect(crops.first.sowingDate, DateTime(2026, 6, 12));
    expect(crops.first.expectedHarvestDate, DateTime(2026, 10, 20));
    expect(crops.first.isActive, isTrue);
    expect(crops.last.status, CropSeasonStatus.planned);
    expect(crops.last.expectedHarvestDate, isNull);
    expect(crops.last.isActive, isFalse);
  });

  test('getCropSeasons accepts an empty list', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': <dynamic>[]}),
    );

    final crops = await repository.getCropSeasons('farm-1');

    expect(crops, isEmpty);
  });

  test('getCropSeasons parses cancellation details when present', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': [
          cropJson(
            status: 'CANCELLED',
            isActive: false,
            harvestedDate: null,
            cancellationReason: 'Heavy rain damaged the nursery.',
          ),
        ],
      }),
    );

    final crops = await repository.getCropSeasons('farm-1');

    expect(crops.single.isCancelled, isTrue);
    expect(crops.single.cancellationReason, 'Heavy rain damaged the nursery.');
  });

  test('getCropSeasons requires a farm id', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': <dynamic>[]}),
    );

    await expectLater(
      repository.getCropSeasons('   '),
      throwsExceptionWith('Select a farm'),
    );
  });

  test('getCropSeasons surfaces API success false messages', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': false, 'message': 'Farm not found.'}),
    );

    await expectLater(
      repository.getCropSeasons('farm-1'),
      throwsExceptionWith('Farm not found.'),
    );
  });

  test('getCropSeasons rejects malformed list data', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': 'not-a-list'}),
    );

    await expectLater(
      repository.getCropSeasons('farm-1'),
      throwsExceptionWith('Crop data is missing'),
    );
  });

  test('getCropSeasons rejects malformed crop entries', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': [cropJson(id: '')],
      }),
    );

    await expectLater(
      repository.getCropSeasons('farm-1'),
      throwsExceptionWith('Invalid crop season response'),
    );
  });

  test('getCropSeasons rejects unknown statuses', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': [cropJson(status: 'PLANTED')],
      }),
    );

    await expectLater(
      repository.getCropSeasons('farm-1'),
      throwsExceptionWith('Invalid crop status'),
    );
  });

  test('getCropSeasons maps unauthorized responses', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'detail': 'Unauthorized'}, statusCode: 401),
    );

    await expectLater(
      repository.getCropSeasons('farm-1'),
      throwsExceptionWith('session has expired'),
    );
  });

  test('getCropSeasons maps connection failures', () async {
    final repository = buildRepository((options) {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.connectionError,
      );
    });

    await expectLater(
      repository.getCropSeasons('farm-1'),
      throwsExceptionWith('Unable to reach FarmMate AI'),
    );
  });

  test(
    'getCropRecommendations posts farm id and parses the response',
    () async {
      RequestOptions? captured;

      final repository = buildRepository(
        (_) => jsonResponse({
          'success': true,
          'data': {
            'farm_id': 'farm-1',
            'recommended_sowing_date': '2026-08-20',
            'recommended_crops': [
              {
                'crop_name': 'Rice',
                'confidence': 95,
                'reason':
                    'Suitable for the current season and water conditions.',
              },
              {
                'crop_name': 'Maize',
                'confidence': 80,
                'reason': 'Good alternative for the available conditions.',
              },
            ],
          },
        }),
        onRequest: (options) {
          captured = options;
        },
      );

      final recommendation = await repository.getCropRecommendations(
        ' farm-1 ',
      );

      final requestBody = captured!.data is String
          ? jsonDecode(captured!.data as String)
          : captured!.data;

      expect(captured!.path, '/crop-recommendation');
      expect(captured!.method, 'POST');
      expect(requestBody, {'farm_id': 'farm-1'});
      expect(captured!.headers['Authorization'], 'Bearer test-token');
      expect(captured!.receiveTimeout, ApiConfig.aiRequestTimeout);
      expect(recommendation.farmId, 'farm-1');
      expect(recommendation.recommendedSowingDate, DateTime(2026, 8, 20));
      expect(recommendation.recommendedCrops, hasLength(2));
      expect(recommendation.recommendedCrops.first.cropName, 'Rice');
      expect(recommendation.recommendedCrops.first.confidence, 95);
      expect(
        recommendation.recommendedCrops.first.reason,
        'Suitable for the current season and water conditions.',
      );
    },
  );

  test('getCropRecommendations keeps an invalid sowing date hidden', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': {
          'farm_id': 'farm-1',
          'recommended_sowing_date': '2026-02-30',
          'recommended_crops': [
            {'crop_name': 'Rice', 'confidence': 90, 'reason': 'Suitable crop.'},
          ],
        },
      }),
    );

    final recommendation = await repository.getCropRecommendations('farm-1');

    expect(recommendation.recommendedSowingDate, isNull);
  });

  test('getCropRecommendations requires a farm id', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': {
          'farm_id': 'farm-1',
          'recommended_crops': [
            {'crop_name': 'Rice', 'confidence': 90, 'reason': 'Suitable crop.'},
          ],
        },
      }),
    );

    await expectLater(
      repository.getCropRecommendations('   '),
      throwsExceptionWith('Select a farm'),
    );
  });

  test('getCropRecommendations rejects an empty recommendation list', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': {
          'farm_id': 'farm-1',
          'recommended_sowing_date': '2026-08-20',
          'recommended_crops': <dynamic>[],
        },
      }),
    );

    await expectLater(
      repository.getCropRecommendations('farm-1'),
      throwsExceptionWith('No crop recommendations'),
    );
  });

  test('getCropRecommendations rejects invalid confidence scores', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': {
          'farm_id': 'farm-1',
          'recommended_crops': [
            {
              'crop_name': 'Rice',
              'confidence': 101,
              'reason': 'Suitable crop.',
            },
          ],
        },
      }),
    );

    await expectLater(
      repository.getCropRecommendations('farm-1'),
      throwsExceptionWith('invalid confidence'),
    );
  });

  test('getCropRecommendations rejects a mismatched farm', () async {
    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': {
          'farm_id': 'farm-2',
          'recommended_crops': [
            {'crop_name': 'Rice', 'confidence': 90, 'reason': 'Suitable crop.'},
          ],
        },
      }),
    );

    await expectLater(
      repository.getCropRecommendations('farm-1'),
      throwsExceptionWith('do not match the selected farm'),
    );
  });

  test('getCropRecommendations maps rate limiting', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'detail': 'Rate limit exceeded'}, statusCode: 429),
    );

    await expectLater(
      repository.getCropRecommendations('farm-1'),
      throwsExceptionWith('Too many recommendation requests'),
    );
  });

  test('getCropRecommendations maps AI service failures', () async {
    final repository = buildRepository(
      (_) => jsonResponse({'detail': 'AI unavailable'}, statusCode: 503),
    );

    await expectLater(
      repository.getCropRecommendations('farm-1'),
      throwsExceptionWith('FarmMate AI is temporarily unavailable'),
    );
  });

  test('getCropRecommendations maps receive timeouts', () async {
    final repository = buildRepository((options) {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.receiveTimeout,
      );
    });

    await expectLater(
      repository.getCropRecommendations('farm-1'),
      throwsExceptionWith('Unable to reach FarmMate AI'),
    );
  });

  test('generateCropPlan uses the extended AI receive timeout', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': {
          'crop_season_id': 'crop-1',
          'crop_name': 'Rice',
          'crop_variety': 'BPT 5204',
          'season': 'KHARIF',
          'estimated_duration_days': 120,
          'stages_created': 2,
          'activities_created': 5,
        },
      }),
      onRequest: (options) {
        captured = options;
      },
    );

    final summary = await repository.generateCropPlan(
      cropSeasonId: ' crop-1 ',
      state: 'Andhra Pradesh',
      district: 'Nellore',
      village: 'Ramapuram',
      soilType: 'Clay',
    );

    expect(captured!.path, '/crop-planner/crop-1/generate');
    expect(captured!.method, 'POST');
    expect(captured!.receiveTimeout, ApiConfig.aiRequestTimeout);
    expect(captured!.connectTimeout, ApiConfig.connectTimeout);
    expect(summary.cropSeasonId, 'crop-1');
    expect(summary.cropName, 'Rice');
  });

  test('updateCropSeason PUTs only supplied fields', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': cropJson()}),
      onRequest: (options) {
        captured = options;
      },
    );

    await repository.updateCropSeason(
      cropSeasonId: ' crop-1 ',
      cropName: ' Paddy ',
      landArea: 1.5,
      landUnit: 'Acres',
      sowingDate: DateTime(2026, 7, 1),
    );

    expect(captured!.path, '/crop-seasons/crop-1');
    expect(captured!.method, 'PUT');
    expect(captured!.data, {
      'crop_name': 'Paddy',
      'sowing_date': '2026-07-01',
      'land_area': 1.5,
      'land_unit': 'Acres',
    });
  });

  test('activateCropSeason patches the start endpoint', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': cropJson()}),
      onRequest: (options) {
        captured = options;
      },
    );

    final crop = await repository.activateCropSeason(' crop-1 ');

    expect(captured!.path, '/crop-seasons/crop-1/start');
    expect(captured!.method, 'PATCH');
    expect(crop.isActiveSeason, isTrue);
  });

  test('harvestCropSeason sends the harvested date', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': cropJson(status: 'HARVESTED', isActive: false),
      }),
      onRequest: (options) {
        captured = options;
      },
    );

    final crop = await repository.harvestCropSeason(
      'crop-1',
      harvestedDate: DateTime(2026, 10, 2),
    );

    expect(captured!.path, '/crop-seasons/crop-1/complete');
    expect(captured!.method, 'PATCH');
    expect(captured!.data, {'harvested_date': '2026-10-02'});
    expect(crop.isHarvested, isTrue);
  });

  test('cancelCropSeason sends the reason and parses cancellation', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({
        'success': true,
        'data': cropJson(
          status: 'CANCELLED',
          isActive: false,
          cancellationReason: 'Heavy rain.',
        ),
      }),
      onRequest: (options) {
        captured = options;
      },
    );

    final crop = await repository.cancelCropSeason(
      'crop-1',
      reason: ' Heavy rain. ',
    );

    expect(captured!.path, '/crop-seasons/crop-1/cancel');
    expect(captured!.method, 'PATCH');
    expect(captured!.data, {'reason': 'Heavy rain.'});
    expect(crop.isCancelled, isTrue);
    expect(crop.cancellationReason, 'Heavy rain.');
  });

  test('deleteCropSeason calls the crop delete endpoint', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse(<String, dynamic>{}, statusCode: 204),
      onRequest: (options) {
        captured = options;
      },
    );

    await repository.deleteCropSeason(' crop-1 ');

    expect(captured!.path, '/crop-seasons/crop-1');
    expect(captured!.method, 'DELETE');
  });

  test('completeCropStage patches and parses the stage', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': stageJson()}),
      onRequest: (options) {
        captured = options;
      },
    );

    final stage = await repository.completeCropStage(' stage-1 ');

    expect(captured!.path, '/crop-stages/stage-1/complete');
    expect(captured!.method, 'PATCH');
    expect(stage.status, CropStageStatus.completed);
  });

  test('activity actions use their lifecycle endpoints', () async {
    final requests = <String>[];
    final repository = buildRepository((options) {
      requests.add('${options.method} ${options.path}');

      return jsonResponse({
        'success': true,
        'data': activityJson(status: 'IN_PROGRESS'),
      });
    });

    await repository.startActivity('activity-1');
    await repository.completeActivity('activity-1');
    await repository.skipActivity('activity-1');

    expect(requests, [
      'PATCH /activities/activity-1/start',
      'PATCH /activities/activity-1/complete',
      'PATCH /activities/activity-1/skip',
    ]);
  });

  test('rescheduleActivity PUTs the new date', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse({'success': true, 'data': activityJson()}),
      onRequest: (options) {
        captured = options;
      },
    );

    await repository.rescheduleActivity('activity-1', DateTime(2026, 7, 5));

    expect(captured!.path, '/activities/activity-1');
    expect(captured!.method, 'PUT');
    expect(captured!.data, {'scheduled_date': '2026-07-05'});
  });

  test('deleteActivity calls the activity delete endpoint', () async {
    RequestOptions? captured;

    final repository = buildRepository(
      (_) => jsonResponse(<String, dynamic>{}, statusCode: 204),
      onRequest: (options) {
        captured = options;
      },
    );

    await repository.deleteActivity(' activity-1 ');

    expect(captured!.path, '/activities/activity-1');
    expect(captured!.method, 'DELETE');
  });
}

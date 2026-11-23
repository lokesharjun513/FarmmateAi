import 'dart:async';

import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/weather/data/models/weather_model.dart';
import 'package:mobile/features/weather/data/models/weather_repository.dart';
import 'package:mobile/features/weather/location_service.dart';
import 'package:mobile/features/weather/providers/weather_provider.dart';

const _weather = CurrentWeatherModel(
  location: 'Nellore, Andhra Pradesh',
  latitude: 14.4426,
  longitude: 79.9865,
  temperature: 32.5,
  hasTemperature: true,
  feelsLike: 35.0,
  humidity: 70,
  windSpeed: 12.0,
  pressure: 1008.0,
  weatherCode: 0,
  weatherCondition: 'Clear Sky',
  rainProbability: 20,
);

const _location = LocationData(
  latitude: 14.4426,
  longitude: 79.9865,
  locationName: 'Nellore, Andhra Pradesh',
  village: 'Nellore',
);

class FakeLocationService extends LocationService {
  FakeLocationService(this._location);

  final LocationData? _location;

  int calls = 0;

  @override
  Future<LocationData?> getCurrentLocation() async {
    calls++;
    return _location;
  }
}

class FakeWeatherRepository extends WeatherRepository {
  FakeWeatherRepository(this._handler);

  final Future<CurrentWeatherModel> Function() _handler;

  int calls = 0;

  @override
  Future<CurrentWeatherModel> getCurrentWeather({
    required double latitude,
    required double longitude,
    required String location,
  }) {
    calls++;
    return _handler();
  }
}

void main() {
  group('WeatherProvider', () {
    test('loads weather successfully and exposes it', () async {
      final repository = FakeWeatherRepository(() async => _weather);
      final locationService = FakeLocationService(_location);

      final provider = WeatherProvider(
        weatherRepository: repository,
        locationService: locationService,
      );

      await provider.loadCurrentWeather();

      expect(provider.weather, _weather);
      expect(provider.hasWeather, isTrue);
      expect(provider.errorMessage, isNull);
      expect(provider.isLoading, isFalse);
      expect(locationService.calls, 1);
      expect(repository.calls, 1);
    });

    test('keeps last observation when a later fetch fails', () async {
      var fail = false;

      final repository = FakeWeatherRepository(() async {
        if (fail) {
          throw Exception(
            'Weather service is temporarily unavailable. Please try again later.',
          );
        }
        return _weather;
      });
      final locationService = FakeLocationService(_location);

      final provider = WeatherProvider(
        weatherRepository: repository,
        locationService: locationService,
      );

      await provider.loadCurrentWeather();
      expect(provider.weather, _weather);

      fail = true;
      await provider.loadCurrentWeather();

      // The last successful observation is retained for the UI
      // to render, and the backend message surfaces in state.
      expect(provider.weather, _weather);
      expect(provider.hasWeather, isTrue);
      expect(provider.isLoading, isFalse);
      expect(
        provider.errorMessage,
        'Weather service is temporarily unavailable. Please try again later.',
      );
    });

    test('surfaces the backend error message verbatim', () async {
      final repository = FakeWeatherRepository(
        () async => throw Exception('Weather service is temporarily unavailable.'),
      );
      final locationService = FakeLocationService(_location);

      final provider = WeatherProvider(
        weatherRepository: repository,
        locationService: locationService,
      );

      await provider.loadCurrentWeather();

      expect(provider.weather, isNull);
      expect(provider.errorMessage, 'Weather service is temporarily unavailable.');
    });

    test('reports missing location permission without fetching weather', () async {
      final repository = FakeWeatherRepository(() async => _weather);
      final locationService = FakeLocationService(null);

      final provider = WeatherProvider(
        weatherRepository: repository,
        locationService: locationService,
      );

      await provider.loadCurrentWeather();

      expect(provider.errorMessage, 'Location permission is required.');
      expect(provider.hasWeather, isFalse);
      expect(repository.calls, 0);
    });

    test('deduplicates concurrent loads', () async {
      final completer = Completer<CurrentWeatherModel>();
      final repository = FakeWeatherRepository(() => completer.future);
      final locationService = FakeLocationService(_location);

      final provider = WeatherProvider(
        weatherRepository: repository,
        locationService: locationService,
      );

      final first = provider.loadCurrentWeather();
      final second = provider.loadCurrentWeather();

      completer.complete(_weather);

      await Future.wait([first, second]);

      expect(repository.calls, 1);
      expect(provider.weather, _weather);
      expect(provider.isLoading, isFalse);
    });

    test('clearWeather resets observation and error', () async {
      final repository = FakeWeatherRepository(() async => _weather);
      final locationService = FakeLocationService(_location);

      final provider = WeatherProvider(
        weatherRepository: repository,
        locationService: locationService,
      );

      await provider.loadCurrentWeather();
      expect(provider.hasWeather, isTrue);

      provider.clearWeather();

      expect(provider.weather, isNull);
      expect(provider.errorMessage, isNull);
    });
  });
}

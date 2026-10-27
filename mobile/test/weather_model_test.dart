import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/weather/data/models/weather_model.dart';

void main() {
  test('missing temperature is marked unavailable instead of zero', () {
    final weather = CurrentWeatherModel.fromJson({
      'location': 'Kavali',
      'latitude': 14.9,
      'longitude': 79.9,
      'wind_speed': 8,
      'weather_code': 0,
      'weather_condition': 'Clear',
    });

    expect(weather.hasTemperature, isFalse);
    expect(weather.temperature, 0);
  });

  test('valid temperature is available', () {
    final weather = CurrentWeatherModel.fromJson({
      'location': 'Kavali',
      'latitude': 14.9,
      'longitude': 79.9,
      'temperature': 31.5,
      'wind_speed': 8,
      'weather_code': 0,
      'weather_condition': 'Clear',
    });

    expect(weather.hasTemperature, isTrue);
    expect(weather.temperature, 31.5);
  });
}

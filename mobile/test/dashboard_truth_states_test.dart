import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/dashboard/data/models/dashboard_model.dart';

void main() {
  group('WeatherDashboard availability', () {
    test('respects is_available false from the backend', () {
      final weather = WeatherDashboard.fromJson({
        'temperature': 31.5,
        'humidity': 62,
        'condition': 'Sunny',
        'rain_probability': 10,
        'is_available': false,
      });

      expect(weather.isAvailable, isFalse);
    });

    test('missing temperature is not treated as 0 degree weather', () {
      final weather = WeatherDashboard.fromJson({
        'humidity': 62,
        'condition': 'Sunny',
        'is_available': true,
      });

      expect(weather.isAvailable, isFalse);
      expect(weather.temperature, 0);
    });

    test('available weather keeps backend values', () {
      final weather = WeatherDashboard.fromJson({
        'temperature': 31.5,
        'humidity': 62,
        'condition': 'Sunny',
        'rain_probability': 10,
        'is_available': true,
      });

      expect(weather.isAvailable, isTrue);
      expect(weather.temperature, 31.5);
      expect(weather.condition, 'Sunny');
      expect(weather.rainProbability, 10);
    });
  });

  group('AdvisorDashboard availability', () {
    test('unavailable advice is not shown as a recommendation', () {
      final advisor = AdvisorDashboard.fromJson({
        'summary': 'FarmMate AI recommendations are temporarily unavailable.',
        'priority': 'LOW',
        'available': false,
      });

      expect(advisor.isAvailable, isFalse);
      expect(advisor.hasRecommendation, isFalse);
    });

    test('available advice is treated as a recommendation', () {
      final advisor = AdvisorDashboard.fromJson({
        'summary': 'Irrigate the field before noon.',
        'priority': 'HIGH',
        'available': true,
      });

      expect(advisor.isAvailable, isTrue);
      expect(advisor.hasRecommendation, isTrue);
      expect(advisor.isHighPriority, isTrue);
    });

    test('empty recommendation text is not treated as advice', () {
      final advisor = AdvisorDashboard.fromJson({
        'summary': 'No recommendation available.',
        'priority': 'LOW',
        'available': true,
      });

      expect(advisor.isAvailable, isTrue);
      expect(advisor.hasRecommendation, isFalse);
    });
  });
}

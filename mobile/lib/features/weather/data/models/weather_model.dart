class CurrentWeatherModel {
  final String location;
  final double latitude;
  final double longitude;

  final double temperature;
  final bool hasTemperature;
  final double? feelsLike;
  final int? humidity;
  final double windSpeed;
  final double? pressure;
  final double? visibility;
  final double? uvIndex;
  final double? precipitation;

  final int weatherCode;
  final String weatherCondition;
  final int? rainProbability;

  final DateTime? sunrise;
  final DateTime? sunset;

  const CurrentWeatherModel({
    required this.location,
    required this.latitude,
    required this.longitude,
    required this.temperature,
    required this.hasTemperature,
    this.feelsLike,
    this.humidity,
    required this.windSpeed,
    this.pressure,
    this.visibility,
    this.uvIndex,
    this.precipitation,
    required this.weatherCode,
    required this.weatherCondition,
    this.rainProbability,
    this.sunrise,
    this.sunset,
  });

  factory CurrentWeatherModel.fromJson(Map<String, dynamic> json) {
    final temperature = _toNullableDouble(json['temperature']);

    return CurrentWeatherModel(
      location: json['location']?.toString() ?? 'Unknown location',
      latitude: _toDouble(json['latitude']),
      longitude: _toDouble(json['longitude']),
      temperature: temperature ?? 0,
      hasTemperature: temperature != null,
      feelsLike: _toNullableDouble(json['feels_like']),
      humidity: _toNullableInt(json['humidity']),
      windSpeed: _toDouble(json['wind_speed']),
      pressure: _toNullableDouble(json['pressure']),
      visibility: _toNullableDouble(json['visibility']),
      uvIndex: _toNullableDouble(json['uv_index']),
      precipitation: _toNullableDouble(json['precipitation']),
      weatherCode: _toInt(json['weather_code']),
      weatherCondition: json['weather_condition']?.toString() ?? 'Unknown',
      rainProbability: _toNullableInt(json['rain_probability']),
      sunrise: _toDateTime(json['sunrise']),
      sunset: _toDateTime(json['sunset']),
    );
  }

  static double _toDouble(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  static double? _toNullableDouble(dynamic value) {
    if (value == null) {
      return null;
    }

    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value.toString());
  }

  static int _toInt(dynamic value) {
    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  static int? _toNullableInt(dynamic value) {
    if (value == null) {
      return null;
    }

    if (value is num) {
      return value.toInt();
    }

    return int.tryParse(value.toString());
  }

  static DateTime? _toDateTime(dynamic value) {
    if (value == null) {
      return null;
    }

    return DateTime.tryParse(value.toString());
  }
}

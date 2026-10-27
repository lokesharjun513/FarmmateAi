import 'package:flutter/foundation.dart';

import '../../weather/data/models/weather_model.dart';
import '../../weather/data/models/weather_repository.dart';
import '../location_service.dart';

class WeatherProvider extends ChangeNotifier {
  final WeatherRepository _weatherRepository;
  final LocationService _locationService;

  CurrentWeatherModel? _weather;

  bool _isLoading = false;
  String? _errorMessage;

  WeatherProvider({
    WeatherRepository? weatherRepository,
    LocationService? locationService,
  }) : _weatherRepository = weatherRepository ?? WeatherRepository(),
       _locationService = locationService ?? const LocationService();

  CurrentWeatherModel? get weather => _weather;

  bool get isLoading => _isLoading;

  String? get errorMessage => _errorMessage;

  bool get hasWeather => _weather != null;

  Future<void> loadCurrentWeather() async {
    if (_isLoading) {
      return;
    }

    _isLoading = true;
    _errorMessage = null;

    notifyListeners();

    try {
      // --------------------------------------------------------
      // 1. Get farmer's current location
      // --------------------------------------------------------

      final location = await _locationService.getCurrentLocation();

      if (location == null) {
        _errorMessage =
            'Location permission is required to show local weather.';

        _isLoading = false;
        notifyListeners();
        return;
      }

      // --------------------------------------------------------
      // 2. Request weather from backend
      // --------------------------------------------------------
      //
      // For now we don't have reverse geocoding in the mobile
      // application, so send a simple location name.
      //
      // Backend receives:
      //
      // latitude
      // longitude
      // location
      //
      // We can replace this with the actual village/city later.
      //

      final weather = await _weatherRepository.getCurrentWeather(
        latitude: location.latitude,
        longitude: location.longitude,
        location: location.locationName,
      );

      _weather = weather;
    } catch (e) {
      _errorMessage = e.toString().replaceFirst('Exception: ', '');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearWeather() {
    _weather = null;
    _errorMessage = null;
    notifyListeners();
  }
}

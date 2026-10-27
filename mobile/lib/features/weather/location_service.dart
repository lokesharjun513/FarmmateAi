import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';

/// ============================================================
/// LOCATION DATA
/// ============================================================

class LocationData {
  final double latitude;
  final double longitude;

  final String locationName;

  final String? state;
  final String? district;
  final String? mandal;
  final String? village;

  const LocationData({
    required this.latitude,
    required this.longitude,
    required this.locationName,
    this.state,
    this.district,
    this.mandal,
    this.village,
  });

  @override
  String toString() {
    return '''
LocationData(
  latitude: $latitude,
  longitude: $longitude,
  locationName: $locationName,
  state: $state,
  district: $district,
  mandal: $mandal,
  village: $village,
)
''';
  }
}

/// ============================================================
/// WEATHER LOCATION SERVICE
/// ============================================================

class LocationService {
  const LocationService();

  // ============================================================
  // GET CURRENT LOCATION
  // ============================================================

  Future<LocationData?> getCurrentLocation() async {
    // ----------------------------------------------------------
    // Check GPS service
    // ----------------------------------------------------------

    final serviceEnabled = await Geolocator.isLocationServiceEnabled();

    if (!serviceEnabled) {
      throw Exception('Please turn on GPS/location services and try again.');
    }

    // ----------------------------------------------------------
    // Check permission
    // ----------------------------------------------------------

    var permission = await Geolocator.checkPermission();

    // ----------------------------------------------------------
    // Request permission
    // ----------------------------------------------------------

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    // ----------------------------------------------------------
    // Permission denied
    // ----------------------------------------------------------

    if (permission == LocationPermission.denied) {
      throw Exception(
        'Location permission denied. Please allow location access.',
      );
    }

    // ----------------------------------------------------------
    // Permanently denied
    // ----------------------------------------------------------

    if (permission == LocationPermission.deniedForever) {
      throw Exception(
        'Location permission is permanently denied. Please enable it from device settings.',
      );
    }

    // ----------------------------------------------------------
    // Get GPS position
    // ----------------------------------------------------------

    final position = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );

    // ----------------------------------------------------------
    // Reverse geocode
    // ----------------------------------------------------------

    return await _reverseGeocode(
      latitude: position.latitude,
      longitude: position.longitude,
    );
  }

  // ============================================================
  // ADDRESS → LOCATION
  // ============================================================

  Future<LocationData?> getLocationFromAddress({
    required String state,
    required String district,
    required String mandal,
    required String village,
  }) async {
    final addressParts = <String>[
      village.trim(),
      mandal.trim(),
      district.trim(),
      state.trim(),
      'India',
    ].where((value) => value.isNotEmpty).toList();

    if (addressParts.isEmpty) {
      return null;
    }

    final address = addressParts.join(', ');

    try {
      final locations = await locationFromAddress(address);

      if (locations.isEmpty) {
        return null;
      }

      final location = locations.first;

      return LocationData(
        latitude: location.latitude,
        longitude: location.longitude,
        locationName: address,
        state: _clean(state),
        district: _clean(district),
        mandal: _clean(mandal),
        village: _clean(village),
      );
    } catch (e) {
      return null;
    }
  }

  // ============================================================
  // REVERSE GEOCODING
  // GPS → ADDRESS
  // ============================================================

  Future<LocationData> _reverseGeocode({
    required double latitude,
    required double longitude,
  }) async {
    String? state;
    String? district;
    String? mandal;
    String? village;

    String locationName = 'Current Location';

    try {
      final placemarks = await placemarkFromCoordinates(latitude, longitude);

      if (placemarks.isNotEmpty) {
        final place = placemarks.first;

        // ------------------------------------------------------
        // STATE
        // ------------------------------------------------------

        state = _clean(place.administrativeArea);

        // ------------------------------------------------------
        // DISTRICT
        // ------------------------------------------------------

        district = _clean(place.subAdministrativeArea);

        // ------------------------------------------------------
        // MANDAL / TALUK
        // ------------------------------------------------------

        mandal = _firstAvailable([
          place.subLocality,
          place.locality,
          place.subAdministrativeArea,
        ]);

        // ------------------------------------------------------
        // VILLAGE / LOCALITY
        // ------------------------------------------------------

        village = _firstAvailable([
          place.thoroughfare,
          place.subLocality,
          place.locality,
        ]);

        // ------------------------------------------------------
        // LOCATION NAME
        // ------------------------------------------------------

        //final placeName = _clean(place.name);

        final parts = <String?>[
          _clean(place.name),
          village,
          district,
          state,
        ].whereType<String>().toList();

        if (parts.isNotEmpty) {
          locationName = parts.join(', ');
        }
      }
    } catch (_) {
      // Keep GPS coordinates even if reverse
      // geocoding fails.
    }

    return LocationData(
      latitude: latitude,
      longitude: longitude,
      locationName: locationName,
      state: state,
      district: district,
      mandal: mandal,
      village: village,
    );
  }

  // ============================================================
  // CLEAN STRING
  // ============================================================

  String? _clean(String? value) {
    if (value == null) {
      return null;
    }

    final result = value.trim();

    if (result.isEmpty) {
      return null;
    }

    return result;
  }

  // ============================================================
  // FIRST AVAILABLE VALUE
  // ============================================================

  String? _firstAvailable(List<String?> values) {
    for (final value in values) {
      final cleaned = _clean(value);

      if (cleaned != null) {
        return cleaned;
      }
    }

    return null;
  }
}

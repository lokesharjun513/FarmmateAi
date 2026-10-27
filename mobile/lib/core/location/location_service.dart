import 'package:flutter/foundation.dart';
import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';

/// ============================================================
/// FARM LOCATION DATA
/// ============================================================
///
/// Location information used by FarmMate farm screens.
///
/// This model is intentionally separate from the weather
/// LocationData model.
class FarmLocationData {
  final double latitude;
  final double longitude;

  final String? state;
  final String? district;
  final String? mandal;
  final String? village;

  const FarmLocationData({
    required this.latitude,
    required this.longitude,
    this.state,
    this.district,
    this.mandal,
    this.village,
  });

  @override
  String toString() {
    return '''
FarmLocationData(
  latitude: $latitude,
  longitude: $longitude,
  state: $state,
  district: $district,
  mandal: $mandal,
  village: $village,
)
''';
  }
}

/// ============================================================
/// LOCATION SERVICE
/// ============================================================

class LocationService {
  const LocationService();

  // ============================================================
  // CURRENT GPS LOCATION
  // ============================================================

  Future<FarmLocationData?> getCurrentLocation() async {
    try {
      // --------------------------------------------------------
      // CHECK LOCATION SERVICE
      // --------------------------------------------------------

      final serviceEnabled = await Geolocator.isLocationServiceEnabled();

      if (!serviceEnabled) {
        throw Exception('Location service is disabled. Please turn on GPS.');
      }

      // --------------------------------------------------------
      // CHECK LOCATION PERMISSION
      // --------------------------------------------------------

      var permission = await Geolocator.checkPermission();

      // --------------------------------------------------------
      // REQUEST LOCATION PERMISSION
      // --------------------------------------------------------

      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }

      // --------------------------------------------------------
      // PERMISSION DENIED
      // --------------------------------------------------------

      if (permission == LocationPermission.denied) {
        throw Exception(
          'Location permission denied. Please allow location permission.',
        );
      }

      // --------------------------------------------------------
      // PERMISSION PERMANENTLY DENIED
      // --------------------------------------------------------

      if (permission == LocationPermission.deniedForever) {
        throw Exception(
          'Location permission permanently denied. '
          'Please enable it from device settings.',
        );
      }

      // --------------------------------------------------------
      // GET CURRENT GPS POSITION
      // --------------------------------------------------------

      final position = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      );

      final latitude = position.latitude;
      final longitude = position.longitude;

      debugPrint('Farmer latitude: $latitude');
      debugPrint('Farmer longitude: $longitude');

      // --------------------------------------------------------
      // REVERSE GEOCODING
      // GPS → ADDRESS
      // --------------------------------------------------------

      String? state;
      String? district;
      String? mandal;
      String? village;

      try {
        final placemarks = await placemarkFromCoordinates(latitude, longitude);

        if (placemarks.isNotEmpty) {
          final place = placemarks.first;

          // ----------------------------------------------------
          // STATE
          // ----------------------------------------------------

          state = _clean(place.administrativeArea);

          // ----------------------------------------------------
          // DISTRICT
          // ----------------------------------------------------

          district = _clean(place.subAdministrativeArea);

          // ----------------------------------------------------
          // MANDAL / TALUK
          // ----------------------------------------------------

          mandal = _clean(place.subLocality);

          // ----------------------------------------------------
          // VILLAGE / LOCALITY
          // ----------------------------------------------------

          village = _clean(place.locality);

          // ----------------------------------------------------
          // FALLBACK VALUES
          // ----------------------------------------------------
          //
          // Different geocoding providers may return
          // locality/subLocality differently.
          //
          // If village is missing, use subLocality.
          // If mandal is missing, use locality.
          // ----------------------------------------------------

          village ??= _clean(place.subLocality);

          mandal ??= _clean(place.locality);

          debugPrint('Reverse geocoding result:');
          debugPrint('State: $state');
          debugPrint('District: $district');
          debugPrint('Mandal: $mandal');
          debugPrint('Village: $village');
        }
      } catch (e) {
        // ------------------------------------------------------
        // GPS coordinates are still valid even when
        // reverse geocoding fails.
        // ------------------------------------------------------

        debugPrint('Reverse geocoding failed: $e');
      }

      // --------------------------------------------------------
      // RETURN FARM LOCATION
      // --------------------------------------------------------

      return FarmLocationData(
        latitude: latitude,
        longitude: longitude,
        state: state,
        district: district,
        mandal: mandal,
        village: village,
      );
    } catch (e) {
      debugPrint('Current location failed: $e');

      rethrow;
    }
  }

  // ============================================================
  // ADDRESS → LATITUDE / LONGITUDE
  // ============================================================

  Future<FarmLocationData?> getLocationFromAddress({
    required String state,
    required String district,
    required String mandal,
    required String village,
  }) async {
    // ----------------------------------------------------------
    // CLEAN INPUT
    // ----------------------------------------------------------

    final cleanState = state.trim();
    final cleanDistrict = district.trim();
    final cleanMandal = mandal.trim();
    final cleanVillage = village.trim();

    // ----------------------------------------------------------
    // VALIDATE ADDRESS
    // ----------------------------------------------------------

    if (cleanState.isEmpty ||
        cleanDistrict.isEmpty ||
        cleanMandal.isEmpty ||
        cleanVillage.isEmpty) {
      return null;
    }

    // ----------------------------------------------------------
    // COMPLETE ADDRESS
    // ----------------------------------------------------------

    final address = [
      cleanVillage,
      cleanMandal,
      cleanDistrict,
      cleanState,
      'India',
    ].join(', ');

    debugPrint('Resolving address: $address');

    try {
      // --------------------------------------------------------
      // TRY 1
      // Village + Mandal + District + State + India
      // --------------------------------------------------------

      List<Location> locations = [];

      try {
        locations = await locationFromAddress(address);
      } catch (e) {
        debugPrint('Full address geocoding failed: $e');
      }

      // --------------------------------------------------------
      // TRY 2
      // Village + Mandal + District + State
      // --------------------------------------------------------

      if (locations.isEmpty) {
        final address2 = [
          cleanVillage,
          cleanMandal,
          cleanDistrict,
          cleanState,
        ].join(', ');

        debugPrint('Trying simplified address: $address2');

        try {
          locations = await locationFromAddress(address2);
        } catch (e) {
          debugPrint('Simplified address geocoding failed: $e');
        }
      }

      // --------------------------------------------------------
      // TRY 3
      // Mandal + District + State + India
      // --------------------------------------------------------

      if (locations.isEmpty) {
        final address3 = [
          cleanMandal,
          cleanDistrict,
          cleanState,
          'India',
        ].join(', ');

        debugPrint('Trying mandal address: $address3');

        try {
          locations = await locationFromAddress(address3);
        } catch (e) {
          debugPrint('Mandal address geocoding failed: $e');
        }
      }

      // --------------------------------------------------------
      // NO RESULT
      // --------------------------------------------------------

      if (locations.isEmpty) {
        debugPrint('No coordinates found for address.');

        return null;
      }

      // --------------------------------------------------------
      // FIRST RESULT
      // --------------------------------------------------------

      final location = locations.first;

      final latitude = location.latitude;
      final longitude = location.longitude;

      debugPrint('Address resolved successfully.');
      debugPrint('Latitude: $latitude');
      debugPrint('Longitude: $longitude');

      // --------------------------------------------------------
      // RETURN LOCATION
      // --------------------------------------------------------

      return FarmLocationData(
        latitude: latitude,
        longitude: longitude,
        state: cleanState,
        district: cleanDistrict,
        mandal: cleanMandal,
        village: cleanVillage,
      );
    } catch (e) {
      debugPrint('Address geocoding failed: $e');

      return null;
    }
  }

  // ============================================================
  // STRING CLEANER
  // ============================================================

  String? _clean(String? value) {
    final result = value?.trim();

    return result?.isEmpty == true ? null : result;
  }
}

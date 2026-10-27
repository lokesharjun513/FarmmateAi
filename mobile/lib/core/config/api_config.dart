class ApiConfig {
  ApiConfig._();

  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://192.168.1.5:8000/api/v1',
  );

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration sendTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);

  // AI operations may legitimately run up to the backend's 60 second
  // AI_REQUEST_TIMEOUT. Allow a small network/serialization buffer.
  static const Duration aiRequestTimeout = Duration(seconds: 75);
  // Auth
  static const String register = '/auth/register';
  static const String login = '/auth/login';
  static const String me = '/auth/me';

  // Farmer
  static const String farmerProfile = '/farmer/profile';

  // Farm
  static const String farms = '/farms';

  // Crop seasons
  static const String cropSeasons = '/crop-seasons';
  static const String activeCropSeasons = '/crop-seasons/active';
  static const String activeCropSeasonsAcrossFarms = '/crop-seasons/active/all';
  static const String plannedCropSeasons = '/crop-seasons/planned';
  static const String harvestedCropSeasons = '/crop-seasons/harvested';
  static const String cancelledCropSeasons = '/crop-seasons/cancelled';
  static const String latestCropSeason = '/crop-seasons/latest';

  // Crop planning
  static const String cropRecommendation = '/crop-recommendation';
  static const String cropStages = '/crop-stages';
  static const String activities = '/activities';

  static String cropSeason(String cropSeasonId) {
    return '/crop-seasons/${cropSeasonId.trim()}';
  }

  static String cropSeasonStart(String cropSeasonId) {
    return '${cropSeason(cropSeasonId)}/start';
  }

  static String cropSeasonHarvest(String cropSeasonId) {
    return '${cropSeason(cropSeasonId)}/complete';
  }

  static String cropSeasonCancel(String cropSeasonId) {
    return '${cropSeason(cropSeasonId)}/cancel';
  }

  static String cropStageComplete(String stageId) {
    return '/crop-stages/${stageId.trim()}/complete';
  }

  static String cropStageSkip(String stageId) {
    return '/crop-stages/${stageId.trim()}/skip';
  }

  static String activityStart(String activityId) {
    return '/activities/${activityId.trim()}/start';
  }

  static String activityComplete(String activityId) {
    return '/activities/${activityId.trim()}/complete';
  }

  static String activitySkip(String activityId) {
    return '/activities/${activityId.trim()}/skip';
  }

  static String activity(String activityId) {
    return '/activities/${activityId.trim()}';
  }

  static String cropPlanGenerate(String cropSeasonId) {
    return '/crop-planner/${cropSeasonId.trim()}/generate';
  }

  // Onboarding
  static const String onboardingNext = '/onboarding/next';

  // Weather
  static const String weatherCurrent = '/weather/current';

  // Dashboard
  static const String dashboard = '/dashboard';

  // Ask FM
  static const String askFm = '/ask-fm';

  // Push notifications
  static const String deviceTokens = '/notifications/devices';

  static String deviceToken(String fid) {
    return '/notifications/devices/${Uri.encodeComponent(fid.trim())}';
  }
}

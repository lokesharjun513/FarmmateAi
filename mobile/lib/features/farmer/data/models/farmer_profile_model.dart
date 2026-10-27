// lib/features/farmer/data/models/farmer_profile_model.dart

class FarmerProfileModel {
  final String id;
  final String userId;
  final String preferredLanguage;
  final int experienceYears;
  final int profileCompletion;
  final bool onboardingCompleted;

  const FarmerProfileModel({
    required this.id,
    required this.userId,
    required this.preferredLanguage,
    required this.experienceYears,
    required this.profileCompletion,
    required this.onboardingCompleted,
  });

  factory FarmerProfileModel.fromJson(Map<String, dynamic> json) {
    return FarmerProfileModel(
      id: json['id']?.toString() ?? '',
      userId: json['user_id']?.toString() ?? '',
      preferredLanguage: json['preferred_language']?.toString() ?? '',
      experienceYears: (json['experience_years'] as num?)?.toInt() ?? 0,
      profileCompletion: (json['profile_completion'] as num?)?.toInt() ?? 0,
      onboardingCompleted: json['onboarding_completed'] == true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'preferred_language': preferredLanguage,
      'experience_years': experienceYears,
      'profile_completion': profileCompletion,
      'onboarding_completed': onboardingCompleted,
    };
  }
}

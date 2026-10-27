class UserModel {
  final String id;
  final String fullName;
  final String mobile;
  final String email;
  final bool isActive;

  UserModel({
    required this.id,
    required this.fullName,
    required this.mobile,
    required this.email,
    required this.isActive,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id']?.toString() ?? '',
      fullName: json['full_name']?.toString() ?? '',
      mobile: json['mobile']?.toString() ?? '',
      email: json['email']?.toString() ?? '',
      isActive: json['is_active'] == true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'full_name': fullName,
      'mobile': mobile,
      'email': email,
      'is_active': isActive,
    };
  }
}

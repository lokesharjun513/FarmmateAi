import 'package:flutter/material.dart';
import '../../../../../app/theme/app_colors.dart';

class ProfilePlaceholderScreen extends StatelessWidget {
  const ProfilePlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        title: const Text("My Profile"),
        backgroundColor: AppColors.surfaceLight,
        elevation: 0,
      ),
      body: const Center(
        child: Text(
          "Profile module coming soon",
          style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
        ),
      ),
    );
  }
}

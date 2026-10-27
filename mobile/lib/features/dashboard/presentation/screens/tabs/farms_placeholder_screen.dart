import 'package:flutter/material.dart';
import '../../../../../app/theme/app_colors.dart';

class FarmsPlaceholderScreen extends StatelessWidget {
  const FarmsPlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        title: const Text("My Farms"),
        backgroundColor: AppColors.surfaceLight,
        elevation: 0,
      ),
      body: const Center(
        child: Text(
          "Farms module coming soon",
          style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
        ),
      ),
    );
  }
}

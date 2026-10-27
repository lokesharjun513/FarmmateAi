import '../../../../../app/theme/app_colors.dart';
import 'package:flutter/material.dart';

class CropsPlaceholderScreen extends StatelessWidget {
  const CropsPlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        title: const Text("My Crops"),
        backgroundColor: AppColors.surfaceLight,
        elevation: 0,
      ),
      body: const Center(
        child: Text(
          "Crops module coming soon",
          style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
        ),
      ),
    );
  }
}

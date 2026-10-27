import 'package:flutter/material.dart';
import '../../../../../app/theme/app_colors.dart';

class AskFMPlaceholderScreen extends StatelessWidget {
  const AskFMPlaceholderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        title: const Text("Ask FM"),
        backgroundColor: AppColors.surfaceLight,
        elevation: 0,
      ),
      body: const Center(
        child: Text(
          "Ask FM module coming soon",
          style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
        ),
      ),
    );
  }
}

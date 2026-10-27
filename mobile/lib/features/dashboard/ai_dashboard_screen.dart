// lib/features/dashboard/ai_dashboard_screen.dart
import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';
import '../../shared/widgets/ai_greeting_card.dart';

class AIDashboardScreen extends StatelessWidget {
  const AIDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // AI Greeting & Priority Status
            const AIGreetingCard(
              farmerName: "Lokesh",
              message: "Your paddy is 17 days old and in healthy condition.",
              subtitle: "🌧 Rain expected this evening. Don't irrigate today.",
            ),
            const SizedBox(height: 20),

            // Today's Tasks Section
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "Today's AI Tasks",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                TextButton(onPressed: () {}, child: const Text("View All")),
              ],
            ),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primarySurface,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.task_alt, color: AppColors.primary),
                ),
                title: const Text("Check leaf sheath for early blast symptoms"),
                subtitle: const Text("Before 5:00 PM • Medium Priority"),
                trailing: Checkbox(value: false, onChanged: (v) {}),
              ),
            ),
            const SizedBox(height: 20),

            // Weather Intelligence Snippet
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.borderLight),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.cloud_queue_rounded,
                    size: 40,
                    color: AppColors.info,
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          "Kandukur • 32°C • Partly Cloudy",
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 4),
                        Text(
                          "High humidity (82%). Ideal conditions for fungal monitoring.",
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Ask FM Prompt Card
            GestureDetector(
              onTap: () {
                // Navigate to Ask FM chat interface
              },
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.aiBubbleBg,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.3),
                  ),
                ),
                child: Row(
                  children: const [
                    Icon(
                      Icons.chat_bubble_outline_rounded,
                      color: AppColors.primary,
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        "Have a question about your crop? Ask FM...",
                        style: TextStyle(
                          color: AppColors.primaryDark,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    Icon(
                      Icons.arrow_forward_ios_rounded,
                      size: 16,
                      color: AppColors.primary,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

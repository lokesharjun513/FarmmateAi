// lib/shared/widgets/ai_chat_bubble.dart
import 'package:flutter/material.dart';
import '../../app/theme/app_colors.dart';

class AIChatBubble extends StatelessWidget {
  final String message;
  final bool isAI;
  final String? timestamp;

  const AIChatBubble({
    super.key,
    required this.message,
    required this.isAI,
    this.timestamp,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
      child: Row(
        mainAxisAlignment: isAI
            ? MainAxisAlignment.start
            : MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (isAI) ...[
            Container(
              margin: const EdgeInsets.only(right: 8, bottom: 4),
              padding: const EdgeInsets.all(6),
              decoration: const BoxDecoration(
                color: AppColors.primarySurface,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.psychology,
                color: AppColors.primary,
                size: 18,
              ),
            ),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isAI ? AppColors.aiBubbleBg : AppColors.primary,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isAI ? 4 : 16),
                  bottomRight: Radius.circular(isAI ? 16 : 4),
                ),
                border: isAI ? Border.all(color: AppColors.borderLight) : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    message,
                    style: TextStyle(
                      color: isAI ? AppColors.textPrimary : Colors.white,
                      fontSize: 15,
                      height: 1.4,
                    ),
                  ),
                  if (timestamp != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      timestamp!,
                      style: TextStyle(
                        color: isAI ? AppColors.textHint : Colors.white70,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

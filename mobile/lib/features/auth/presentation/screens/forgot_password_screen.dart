import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../providers/auth_provider.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key, this.initialEmail = ''});

  final String initialEmail;

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _emailController =
      TextEditingController(text: widget.initialEmail);
  bool _isSubmitting = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _handleSendOtp() async {
    if (_isSubmitting) return;
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() {
      _isSubmitting = true;
    });

    FocusScope.of(context).unfocus();
    final authProvider = context.read<AuthProvider>();

    try {
      final result = await authProvider.forgotPassword(
        email: _emailController.text.trim(),
      );

      if (!mounted) return;

      if (result['data']?['status'] == 'cooldown') {
        _showCooldownDialog(result['data'] ?? result);
      } else {
        context.go(
          '/verify-otp',
          extra: {
            'email': _emailController.text.trim(),
            'resend_cooldown_until': result['data']?['resend_cooldown_until'],
          },
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Something went wrong. Please try again.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  void _showCooldownDialog(Map<String, dynamic> result) {
    final cooldownUntil = result['resend_cooldown_until'];
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Resend Cooldown'),
        content: Text(
          cooldownUntil != null
              ? 'A reset code has already been sent. You can resend another code after ${_formatCooldownTime(cooldownUntil)}.'
              : 'A reset code has already been sent. Please wait before requesting another.',
        ),
        actions: [
          TextButton(
            onPressed: () => context.pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  String _formatCooldownTime(String? isoString) {
    if (isoString == null) return 'a short time';
    try {
      final expiry = DateTime.parse(isoString);
      final difference = expiry.difference(DateTime.now()).inSeconds;
      if (difference <= 0) return 'now';
      final minutes = (difference / 60).ceil();
      return '$minutes minute${minutes > 1 ? 's' : ''}';
    } catch (_) {
      return 'a short time';
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final isLoading = _isSubmitting || authProvider.isLoading;
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: Stack(
        children: [
          // Bottom Waves (Anchored to bottom)
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: IgnorePointer(
              child: SizedBox(
                height: 120,
                child: CustomPaint(
                  painter: _BottomWavesPainter(),
                ),
              ),
            ),
          ),
          SafeArea(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // 1. Horizontal Header
                      Row(
                        children: [
                          // Circular Back Arrow
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: AppColors.surfaceLight,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: AppColors.primary.withValues(alpha: 0.06),
                                  blurRadius: 8,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: IconButton(
                              padding: EdgeInsets.zero,
                              icon: const Icon(
                                Icons.arrow_back_ios_new,
                                size: 16,
                                color: AppColors.textPrimary,
                              ),
                              onPressed: () => context.go('/login'),
                            ),
                          ),
                          const Spacer(),
                          // Center Brand Header
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 32,
                                height: 32,
                                decoration: BoxDecoration(
                                  color: AppColors.primarySurface,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Icon(
                                  Icons.eco_rounded,
                                  size: 18,
                                  color: AppColors.primary,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'FarmMate AI',
                                style: textTheme.titleSmall?.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: -0.2,
                                ),
                              ),
                            ],
                          ),
                          const Spacer(),
                          const SizedBox(width: 40), // Balance the back button
                        ],
                      ),

                          const SizedBox(height: 32),

                  // 2. Envelope Illustration
                  Center(
                    child: SizedBox(
                      width: 170,
                      height: 140,
                      child: CustomPaint(
                        painter: _EnvelopeIllustrationPainter(),
                      ),
                    ),
                  ),

                  const SizedBox(height: 40),

                  // 3. Main Heading
                  Text(
                    'Forgot Password?',
                    textAlign: TextAlign.center,
                    style: textTheme.headlineLarge?.copyWith(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.8,
                      fontSize: 26,
                    ),
                  ),

                  const SizedBox(height: 8),

                  // 4. Description
                  Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 320),
                      child: Text(
                        'No worries. Enter your registered email address and we’ll send you a verification code.',
                        textAlign: TextAlign.center,
                        style: textTheme.bodyMedium?.copyWith(
                          color: AppColors.textSecondary,
                          height: 1.45,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 36),

                  // 5 & 6. Email Input (No outer AuthCard, Pill-shaped)
                  AutofillGroup(
                    child: Form(
                      key: _formKey,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Container(
                            height: 54,
                            decoration: BoxDecoration(
                              color: const Color(0xFFF3F2EC), // Warm ivory fill
                              borderRadius: BorderRadius.circular(28),
                              border: Border.all(color: AppColors.borderLight),
                            ),
                            child: TextFormField(
                              controller: _emailController,
                              enabled: !isLoading,
                              keyboardType: TextInputType.emailAddress,
                              textInputAction: TextInputAction.send,
                              autofillHints: const [AutofillHints.email],
                              textCapitalization: TextCapitalization.none,
                              autocorrect: false,
                              enableSuggestions: false,
                              maxLength: 255,
                              onChanged: (_) => authProvider.clearError(),
                              style: const TextStyle(
                                color: AppColors.textPrimary,
                                fontSize: 15,
                              ),
                              decoration: const InputDecoration(
                                hintText: 'Email address',
                                hintStyle: TextStyle(
                                  color: AppColors.textHint,
                                  fontSize: 15,
                                ),
                                prefixIcon: Padding(
                                  padding: EdgeInsets.only(left: 16, right: 12),
                                  child: Icon(
                                    Icons.email_outlined,
                                    color: AppColors.textSecondary,
                                    size: 20,
                                  ),
                                ),
                                prefixIconConstraints: BoxConstraints(
                                  minWidth: 48,
                                  minHeight: 48,
                                ),
                                border: InputBorder.none,
                                enabledBorder: InputBorder.none,
                                focusedBorder: InputBorder.none,
                                errorBorder: InputBorder.none,
                                focusedErrorBorder: InputBorder.none,
                                counterText: '',
                                contentPadding: EdgeInsets.symmetric(
                                  horizontal: 16,
                                  vertical: 16,
                                ),
                              ),
                              validator: (value) {
                                final email = value?.trim() ?? '';
                                if (email.isEmpty) {
                                  return 'Please enter your email address';
                                }
                                final isEmail = RegExp(
                                  r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
                                ).hasMatch(email);
                                if (!isEmail) {
                                  return 'Enter a valid email address';
                                }
                                return null;
                              },
                              onFieldSubmitted: (_) {
                                if (!isLoading) _handleSendOtp();
                              },
                            ),
                          ),

                          const SizedBox(height: 24),

                          // 7. Primary Button
                          SizedBox(
                            height: 52,
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFF1E5D46),
                                    Color(0xFF174D3A),
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                borderRadius: BorderRadius.circular(26),
                                boxShadow: [
                                  BoxShadow(
                                    color: AppColors.primary.withValues(alpha: 0.25),
                                    blurRadius: 12,
                                    offset: const Offset(0, 6),
                                  ),
                                ],
                              ),
                              child: ElevatedButton(
                                onPressed: isLoading ? null : _handleSendOtp,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.transparent,
                                  shadowColor: Colors.transparent,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(26),
                                  ),
                                ),
                                child: AnimatedSwitcher(
                                  duration: const Duration(milliseconds: 180),
                                  child: isLoading
                                      ? Row(
                                          key: const ValueKey('loading'),
                                          mainAxisAlignment:
                                              MainAxisAlignment.center,
                                          children: const [
                                            SizedBox(
                                              width: 18,
                                              height: 18,
                                              child: CircularProgressIndicator(
                                                strokeWidth: 2,
                                                color: Colors.white,
                                              ),
                                            ),
                                            SizedBox(width: 10),
                                            Text(
                                              'Sending...',
                                              style: TextStyle(
                                                color: Colors.white,
                                                fontSize: 16,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ],
                                        )
                                      : Row(
                                          key: const ValueKey('label'),
                                          mainAxisAlignment:
                                              MainAxisAlignment.center,
                                          children: const [
                                            Text(
                                              'Send OTP',
                                              style: TextStyle(
                                                color: Colors.white,
                                                fontSize: 16,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                            SizedBox(width: 8),
                                            Icon(
                                              Icons.arrow_forward_rounded,
                                              color: Colors.white,
                                              size: 18,
                                            ),
                                          ],
                                        ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 28),

                  // 8. Footer ("Back to Sign In")
                  Center(
                    child: TextButton(
                      onPressed: isLoading ? null : () => context.go('/login'),
                      child: const Text(
                        'Back to Sign In',
                        style: TextStyle(
                          color: AppColors.primary,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),

                      const SizedBox(height: 48), // Padding above waves
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Custom Painters ────────────────────────────────────────────────────────

class _EnvelopeIllustrationPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);

    // Soft sage background blob / circle
    final bgPaint = Paint()
      ..color = const Color(0xFFE2EBE0)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, size.width * 0.45, bgPaint);

    // Envelope body paint
    final envelopePaint = Paint()
      ..color = const Color(0xFF86A882)
      ..style = PaintingStyle.fill;

    // Envelope base rect / path
    final path = Path();
    path.addRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: center, width: 56, height: 42),
        const Radius.circular(8),
      ),
    );
    canvas.drawPath(path, envelopePaint);

    // Envelope flap paint (lighter)
    final flapPaint = Paint()
      ..color = const Color(0xFF9CB898)
      ..style = PaintingStyle.fill;

    final flapPath = Path();
    flapPath.moveTo(center.dx - 28, center.dy - 21);
    flapPath.lineTo(center.dx, center.dy - 2);
    flapPath.lineTo(center.dx + 28, center.dy - 21);
    flapPath.close();
    canvas.drawPath(flapPath, flapPaint);

    // Padlock on lower right
    final lockCenter = Offset(center.dx + 16, center.dy + 14);

    // Padlock body
    final lockBodyPaint = Paint()
      ..color = const Color(0xFF174D3A)
      ..style = PaintingStyle.fill;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: lockCenter, width: 20, height: 16),
        const Radius.circular(4),
      ),
      lockBodyPaint,
    );

    // Padlock shackle
    final shacklePaint = Paint()
      ..color = const Color(0xFF174D3A)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    final shacklePath = Path();
    shacklePath.addArc(
      Rect.fromCenter(
        center: Offset(lockCenter.dx, lockCenter.dy - 7),
        width: 10,
        height: 10,
      ),
      3.14,
      3.14,
    );
    canvas.drawPath(shacklePath, shacklePaint);

    // Decorative green strokes
    final strokePaint = Paint()
      ..color = const Color(0xFF6D9B68)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    // Top-left sparkle/stroke
    canvas.drawLine(
      Offset(center.dx - 32, center.dy - 24),
      Offset(center.dx - 26, center.dy - 30),
      strokePaint,
    );
    // Top-right sparkle/stroke
    canvas.drawLine(
      Offset(center.dx + 30, center.dy - 20),
      Offset(center.dx + 36, center.dy - 26),
      strokePaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _BottomWavesPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // Wave 1 (Back, lighter)
    final paint1 = Paint()
      ..color = const Color(0xFFE8EDE4)
      ..style = PaintingStyle.fill;

    final path1 = Path();
    path1.moveTo(0, size.height * 0.4);
    path1.quadraticBezierTo(
      size.width * 0.25,
      size.height * 0.1,
      size.width * 0.55,
      size.height * 0.35,
    );
    path1.quadraticBezierTo(
      size.width * 0.8,
      size.height * 0.6,
      size.width,
      size.height * 0.3,
    );
    path1.lineTo(size.width, size.height);
    path1.lineTo(0, size.height);
    path1.close();
    canvas.drawPath(path1, paint1);

    // Wave 2 (Front, slightly darker sage)
    final paint2 = Paint()
      ..color = const Color(0xFFDCE5D7)
      ..style = PaintingStyle.fill;

    final path2 = Path();
    path2.moveTo(0, size.height * 0.6);
    path2.quadraticBezierTo(
      size.width * 0.35,
      size.height * 0.8,
      size.width * 0.7,
      size.height * 0.45,
    );
    path2.quadraticBezierTo(
      size.width * 0.88,
      size.height * 0.3,
      size.width,
      size.height * 0.5,
    );
    path2.lineTo(size.width, size.height);
    path2.lineTo(0, size.height);
    path2.close();
    canvas.drawPath(path2, paint2);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

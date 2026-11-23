import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../widgets/auth_widgets.dart';

/// Verify OTP screen for the password reset flow.
///
/// Matches the reference design: warm ivory background, shield illustration,
/// asterisk capsule, countdown timer, green verify button, change email link,
/// and bottom wave decoration.
class VerifyOtpsScreen extends StatefulWidget {
  const VerifyOtpsScreen({super.key, required this.initialEmail});

  final String initialEmail;

  @override
  State<VerifyOtpsScreen> createState() => _VerifyOtpsScreenState();
}

class _VerifyOtpsScreenState extends State<VerifyOtpsScreen> {
  final _formKey = GlobalKey<FormState>();
  final _otpController = TextEditingController();
  final _otpFocusNode = FocusNode();

  bool _isVerifying = false;
  bool _isResending = false;
  Timer? _cooldownTimer;
  int _cooldownSeconds = 0;
  String? _inlineError;

  @override
  void initState() {
    super.initState();
    _otpController.addListener(_onCodeChanged);
    // Auto-request focus after frame renders
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _otpFocusNode.requestFocus();
      // Initialize cooldown from the server deadline passed via navigation,
      // so the countdown survives navigating back to this screen.
      final extra = GoRouterState.of(context).extra;
      if (extra is Map && extra['resend_cooldown_until'] != null) {
        _applyBackendCooldown(extra['resend_cooldown_until']);
      }
    });
  }

  @override
  void dispose() {
    _otpController.removeListener(_onCodeChanged);
    _otpController.dispose();
    _otpFocusNode.dispose();
    _cooldownTimer?.cancel();
    super.dispose();
  }

  // ─── Derived / state helpers ──────────────────────────────────────────────

  bool get _hasSixDigits => _otpController.text.length == 6;

  String get _maskedEmail {
    final email = widget.initialEmail;
    if (email.isEmpty || !email.contains('@')) return email;
    final parts = email.split('@');
    final name = parts[0];
    final domain = parts[1];
    return '${name[0]}${'*' * math.min(6, name.length - 1)}@$domain';
  }

  void _onCodeChanged() {
    if (!mounted) return;
    setState(() {
      if (_otpController.text.isNotEmpty) {
        _inlineError = null;
      }
    });
  }

  // ─── Actions ───────────────────────────────────────────────────────────────

  Future<void> _handleVerifyOtp() async {
    if (_isVerifying || !_hasSixDigits) return;

    setState(() {
      _isVerifying = true;
      _inlineError = null;
    });

    final authProvider = context.read<AuthProvider>();

    try {
      final result = await authProvider.verifyResetOtp(
        email: widget.initialEmail,
        otp: _otpController.text,
      );

      if (!mounted) return;

      if (result['data'] != null &&
          result['data']['reset_authorization'] != null) {
        // Success — navigate with the reset authorization and expiry.
        context.go('/set-new-password', extra: {
          'reset_token': result['data']['reset_authorization'],
          'expires_at': result['data']['expires_at'],
          'email': widget.initialEmail,
        });
      } else {
        // Incorrect / expired / max-attempts — show inline error, keep the OTP.
        final msg = _friendlyVerifyError(result);
        setState(() => _inlineError = msg ?? 'Invalid OTP. Please try again.');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _inlineError = 'Something went wrong. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _isVerifying = false);
    }
  }

  String? _friendlyVerifyError(Map<String, dynamic> result) {
    final detail = result['detail']?.toString();
    final message = result['message']?.toString();
    final msg = detail ?? message;
    if (msg != null && msg.isNotEmpty) return msg;
    return null;
  }

  Future<void> _handleResendOtp() async {
    if (_isResending || _cooldownSeconds > 0) return;

    setState(() {
      _isResending = true;
      _inlineError = null;
    });

    final authProvider = context.read<AuthProvider>();

    try {
      final result = await authProvider.resendResetOtp(
        email: widget.initialEmail,
      );

      if (!mounted) return;

      final status = result['data']?['status'] ?? result['status'];
      if (status == 'cooldown') {
        final raw = result['data']?['resend_cooldown_until'];
        _applyBackendCooldown(raw);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please wait before requesting another code.'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      } else {
        // Success — restart cooldown and clear the previous OTP.
        _otpController.clear();
        _inlineError = null;
        _startCooldown(seconds: 60);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Code resent successfully.'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        setState(() => _inlineError = 'Something went wrong. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _isResending = false);
    }
  }

  void _applyBackendCooldown(Object? isoUntil) {
    var seconds = 60;
    if (isoUntil is String) {
      try {
        final until = DateTime.tryParse(isoUntil);
        if (until != null) {
          final remaining = until.difference(DateTime.now()).inSeconds;
          if (remaining > 0) seconds = remaining.clamp(1, 300);
        }
      } catch (_) {
        // fall through to the default
      }
    }
    _startCooldown(seconds: seconds);
  }

  void _startCooldown({int seconds = 45}) {
    _cooldownTimer?.cancel();
    setState(() => _cooldownSeconds = seconds);
    _cooldownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_cooldownSeconds <= 1) {
        timer.cancel();
        setState(() => _cooldownSeconds = 0);
      } else {
        setState(() => _cooldownSeconds--);
      }
    });
  }

  // ─── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: Stack(
        children: [
          // Bottom wave decoration
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: IgnorePointer(
              child: SizedBox(
                height: 120,
                child: CustomPaint(painter: _BottomWavesPainter()),
              ),
            ),
          ),
          SafeArea(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Header: back arrow + brand
                      Row(
                        children: [
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
                              onPressed: () => context.go(
                                '/forgot-password',
                                extra: {'email': widget.initialEmail},
                              ),
                            ),
                          ),
                          const Spacer(),
                          // Center brand
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
                          const SizedBox(width: 40), // balance the back button
                        ],
                      ),

                      const SizedBox(height: 36),

                      // Shield illustration
                      Center(
                        child: SizedBox(
                          width: 100,
                          height: 110,
                          child: CustomPaint(
                            painter: _ShieldIllustrationPainter(),
                          ),
                        ),
                      ),

                      const SizedBox(height: 28),

                      // Heading
                      Center(
                        child: Text(
                          'Verify OTP',
                          style: textTheme.headlineLarge?.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.8,
                            fontSize: 26,
                          ),
                        ),
                      ),

                      const SizedBox(height: 12),

                      // Email description
                      Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 300),
                          child: Text(
                            "We've sent a 6-digit code to",
                            textAlign: TextAlign.center,
                            style: textTheme.bodyMedium?.copyWith(
                              color: AppColors.textSecondary,
                              height: 1.45,
                              fontSize: 14,
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 4),

                      // Masked email
                      Center(
                        child: Semantics(
                          label: 'email $_maskedEmail',
                          child: Text(
                            _maskedEmail,
                            style: textTheme.bodyMedium?.copyWith(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.w700,
                              fontSize: 14,
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 32),

                      // OTP Input
                      AutofillGroup(
                        child: Form(
                          key: _formKey,
                          child: _buildOtpInput(),
                        ),
                      ),

                      // Inline error
                      if (_inlineError != null) ...[
                        const SizedBox(height: 12),
                        AuthErrorBanner(message: _inlineError!),
                      ],

                      const SizedBox(height: 20),

                      // Verify Code button
                      _buildVerifyButton(),

                      const SizedBox(height: 16),

                      // Resend section
                      _buildResendSection(),

                      const SizedBox(height: 16),

                      // Change Email link
                      Center(
                        child: TextButton(
                          onPressed: (_isVerifying || _isResending)
                              ? null
                              : () => context.go(
                                    '/forgot-password',
                                    extra: {'email': widget.initialEmail},
                                  ),
                          child: Text(
                            'Change Email',
                            style: TextStyle(
                              color: (_isVerifying || _isResending)
                                  ? AppColors.textHint
                                  : AppColors.primary,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 48),
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

  Widget _buildOtpInput() {
    final code = _otpController.text;
    final focused = _otpFocusNode.hasFocus;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () => _otpFocusNode.requestFocus(),
      child: SizedBox(
        height: 60,
        child: Stack(
          alignment: Alignment.center,
          children: [
            // Hidden real TextField: captures typing, paste, and OTP autofill.
            // Its own text is invisible; the boxes below render the digits.
            TextField(
              controller: _otpController,
              focusNode: _otpFocusNode,
              enabled: !_isVerifying && !_isResending,
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.done,
              autofillHints: const [AutofillHints.oneTimeCode],
              autocorrect: false,
              enableSuggestions: false,
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(6),
              ],
              cursorColor: Colors.transparent,
              style:
                  const TextStyle(fontSize: 1, color: Colors.transparent),
              decoration: const InputDecoration(
                border: InputBorder.none,
                counterText: '',
              ),
              onChanged: (_) => setState(() {}),
              onSubmitted: (_) => _handleVerifyOtp(),
            ),
            // Six box visuals driven by the single controller.
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: List.generate(6, (index) {
                final isActiveBox = focused &&
                    (code.isEmpty ? index == 0 : index == code.length);
                return Expanded(
                  child: Container(
                    height: 60,
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: AppColors.surfaceLight,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: isActiveBox
                            ? AppColors.primary
                            : (index < code.length
                                ? AppColors.primary
                                : AppColors.borderLight),
                        width: isActiveBox ? 2.5 : 1,
                      ),
                    ),
                    child: Text(
                      index < code.length ? code[index] : '',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVerifyButton() {
    return SizedBox(
      height: 52,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1E5D46), Color(0xFF174D3A)],
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
          onPressed:
              (_hasSixDigits && !_isVerifying) ? _handleVerifyOtp : null,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.transparent,
            shadowColor: Colors.transparent,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(26),
            ),
          ),
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 180),
            child: _isVerifying
                ? Row(
                    key: const ValueKey('verifying'),
                    mainAxisAlignment: MainAxisAlignment.center,
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
                        'Verifying...',
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
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: const [
                      Text(
                        'Verify Code',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      SizedBox(width: 8),
                      Icon(Icons.arrow_forward_rounded,
                          color: Colors.white, size: 18),
                    ],
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildResendSection() {
    final cooldownActive = _cooldownSeconds > 0;
    final waiting = _isResending;

    return Center(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (cooldownActive) ...[
            Icon(
              Icons.access_time_rounded,
              size: 16,
              color: AppColors.textSecondary,
            ),
            const SizedBox(width: 6),
          ],
          TextButton(
            onPressed:
                (cooldownActive || waiting) ? null : _handleResendOtp,
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: Text(
                cooldownActive
                    ? 'Resend code in 00:${_cooldownSeconds.toString().padLeft(2, '0')}'
                    : waiting
                        ? 'Resending...'
                        : 'Resend OTP',
                key: ValueKey(cooldownActive
                    ? 'countdown'
                    : waiting
                        ? 'resending'
                        : 'resend'),
                style: TextStyle(
                  color: (cooldownActive || waiting)
                      ? AppColors.textHint
                      : AppColors.primary,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Custom Painters ──────────────────────────────────────────────────────────

class _ShieldIllustrationPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.5);

    // Soft sage circle background
    final bgPaint = Paint()
      ..color = const Color(0xFFE2EBE0)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, size.width * 0.5, bgPaint);

    // Shield path
    final shieldWidth = size.width * 0.52;
    final shieldHeight = size.height * 0.58;
    final shieldTop = center.dy - shieldHeight * 0.55;

    final shieldPath = Path();
    shieldPath.moveTo(center.dx - shieldWidth / 2, shieldTop);
    shieldPath.lineTo(center.dx + shieldWidth / 2, shieldTop);
    shieldPath.lineTo(center.dx + shieldWidth / 2, shieldTop + shieldHeight * 0.55);
    shieldPath.quadraticBezierTo(
      center.dx + shieldWidth / 2,
      shieldTop + shieldHeight * 0.85,
      center.dx,
      shieldTop + shieldHeight,
    );
    shieldPath.quadraticBezierTo(
      center.dx - shieldWidth / 2,
      shieldTop + shieldHeight * 0.85,
      center.dx - shieldWidth / 2,
      shieldTop + shieldHeight * 0.55,
    );
    shieldPath.close();

    final shieldFillPaint = Paint()
      ..color = const Color(0xFF174D3A)
      ..style = PaintingStyle.fill;
    canvas.drawPath(shieldPath, shieldFillPaint);

    final shieldStrokePaint = Paint()
      ..color = const Color(0xFF2E6B4F)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    canvas.drawPath(shieldPath, shieldStrokePaint);

    // Checkmark
    final checkPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final checkPath = Path();
    checkPath.moveTo(center.dx - shieldWidth * 0.22, center.dy - shieldHeight * 0.05);
    checkPath.lineTo(center.dx - shieldWidth * 0.04, center.dy + shieldHeight * 0.13);
    checkPath.lineTo(center.dx + shieldWidth * 0.24, center.dy - shieldHeight * 0.12);
    canvas.drawPath(checkPath, checkPaint);

    // Asterisk capsule
    final capsuleLeft = center.dx - 26;
    final capsuleTop = size.height * 0.76;
    final capsulePaint = Paint()
      ..color = const Color(0xFFF0F4ED)
      ..style = PaintingStyle.fill;

    final capsuleRRect = RRect.fromRectAndRadius(
      Rect.fromLTWH(capsuleLeft, capsuleTop, 52, 22),
      const Radius.circular(11),
    );
    canvas.drawRRect(capsuleRRect, capsulePaint);

    // Four asterisks inside capsule
    final starPaint = Paint()
      ..color = const Color(0xFF86A882)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..strokeCap = StrokeCap.round;

    const starPositions = [-14.0, -2.0, 10.0, 22.0];
    for (final starX in starPositions) {
      final starCenterX = capsuleLeft + 26 + starX;
      final starCenterY = capsuleTop + 11;
      canvas.drawLine(
        Offset(starCenterX - 3, starCenterY),
        Offset(starCenterX + 3, starCenterY),
        starPaint,
      );
      canvas.drawLine(
        Offset(starCenterX, starCenterY - 3),
        Offset(starCenterX, starCenterY + 3),
        starPaint,
      );
    }

    // Green accent strokes (decorative)
    final accentPaint = Paint()
      ..color = const Color(0xFF6D9B68)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    // Top-left stroke
    canvas.drawLine(
      Offset(center.dx - 38, center.dy - 40),
      Offset(center.dx - 30, center.dy - 48),
      accentPaint,
    );
    // Top-right stroke
    canvas.drawLine(
      Offset(center.dx + 36, center.dy - 38),
      Offset(center.dx + 44, center.dy - 46),
      accentPaint,
    );
    // Bottom-left stroke
    canvas.drawLine(
      Offset(center.dx - 36, center.dy + 30),
      Offset(center.dx - 28, center.dy + 38),
      accentPaint,
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

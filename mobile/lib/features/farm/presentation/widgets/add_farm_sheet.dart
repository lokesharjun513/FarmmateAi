import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../data/models/farm_model.dart';
import '../../providers/farm_provider.dart';
import 'add_farm_form.dart';

Future<FarmModel?> showAddFarmSheet(
  BuildContext context, {
  required FarmProvider provider,
  ValueChanged<FarmModel>? onCreated,
}) {
  return showModalBottomSheet<FarmModel>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    enableDrag: false,
    backgroundColor: Colors.transparent,
    barrierColor: AppColors.primaryDark.withValues(alpha: 0.42),
    builder: (_) {
      return ChangeNotifierProvider<FarmProvider>.value(
        value: provider,
        child: _AddFarmSheet(onCreated: onCreated),
      );
    },
  );
}

class _AddFarmSheet extends StatefulWidget {
  const _AddFarmSheet({this.onCreated});

  final ValueChanged<FarmModel>? onCreated;

  @override
  State<_AddFarmSheet> createState() => _AddFarmSheetState();
}

class _AddFarmSheetState extends State<_AddFarmSheet> {
  bool _isSubmitting = false;

  void _handleSubmittingChanged(bool isSubmitting) {
    if (!mounted || _isSubmitting == isSubmitting) {
      return;
    }

    setState(() {
      _isSubmitting = isSubmitting;
    });
  }

  Future<void> _close() async {
    if (_isSubmitting) {
      return;
    }

    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final provider = context.watch<FarmProvider>();
    final isPrimary = provider.nextFarmIsPrimary ?? false;
    final availableHeight =
        mediaQuery.size.height -
        mediaQuery.viewInsets.bottom -
        mediaQuery.padding.top;
    final sheetHeight = (availableHeight * 0.92).clamp(0.0, 900.0);

    return PopScope(
      canPop: !_isSubmitting,
      child: Padding(
        padding: EdgeInsets.only(bottom: mediaQuery.viewInsets.bottom),
        child: Container(
          key: const Key('add_farm_sheet'),
          height: sheetHeight,
          decoration: const BoxDecoration(
            color: AppColors.backgroundLight,
            borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
          ),
          child: SafeArea(
            top: false,
            child: Column(
              children: [
                const SizedBox(height: 10),
                Container(
                  width: 42,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.borderStrong,
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 14, 12, 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Add farm',
                              style: TextStyle(
                                color: AppColors.primaryDark,
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -0.4,
                              ),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              isPrimary
                                  ? 'Set up your first farm.'
                                  : 'Add another farm to your profile.',
                              style: const TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 12,
                                height: 1.35,
                              ),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        key: const Key('add_farm_sheet_close_button'),
                        onPressed: _isSubmitting ? null : _close,
                        tooltip: 'Close',
                        icon: const Icon(
                          Icons.close_rounded,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: AddFarmForm(
                      createFarm: provider.createFarm,
                      isPrimary: isPrimary,
                      successActionLabel: 'View my farms',
                      onCreated: widget.onCreated,
                      onSubmittingChanged: _handleSubmittingChanged,
                      onContinue: (farm) {
                        Navigator.of(context).pop(farm);
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../weather/location_service.dart';
import '../../data/farm_repository.dart';
import '../widgets/add_farm_form.dart';

class AddFarmScreen extends StatelessWidget {
  const AddFarmScreen({super.key, this.repository, this.initialLocation});

  final FarmRepository? repository;
  final LocationData? initialLocation;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.backgroundLight,
        elevation: 0,
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(
            Icons.arrow_back_rounded,
            color: AppColors.primaryDark,
          ),
        ),
        title: const Text('Add farm'),
      ),
      body: SafeArea(
        top: false,
        child: LayoutBuilder(
          builder: (context, constraints) {
            final horizontalPadding = constraints.maxWidth < 380 ? 20.0 : 24.0;

            return Padding(
              padding: EdgeInsets.fromLTRB(
                horizontalPadding,
                8,
                horizontalPadding,
                0,
              ),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 560),
                  child: AddFarmForm(
                    repository: repository,
                    initialLocation: initialLocation,
                    successActionLabel: 'Go to dashboard',
                    onContinue: (_) {
                      Navigator.of(context).pop(true);
                    },
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

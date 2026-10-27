import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../ask_fm/ask_fm_screen.dart';
import '../../../auth/providers/auth_provider.dart';
import '../../../crops/presentation/screens/crops_tab.dart';
import '../../../crops/providers/crop_provider.dart';
import '../../../farm/data/models/farm_model.dart';
import '../../../farm/presentation/screens/farm_tab.dart';
import '../../../farm/providers/farm_provider.dart';

import '../../data/repositories/dashboard_repository.dart';
import '../../providers/dashboard_provider.dart';
import 'home_tab.dart';

class MainShellScreen extends StatelessWidget {
  const MainShellScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<DashboardProvider>(
          create: (_) {
            final provider = DashboardProvider(
              repository: DashboardRepository(),
            );

            provider.loadDashboard();

            return provider;
          },
        ),
        ChangeNotifierProvider<FarmProvider>(
          create: (_) {
            final provider = FarmProvider();

            provider.loadFarms();

            return provider;
          },
        ),
        ChangeNotifierProvider<CropProvider>(
          create: (_) {
            final provider = CropProvider();

            provider.loadCrops();

            return provider;
          },
        ),
      ],
      child: const _MainShellContent(),
    );
  }
}

// ============================================================
// MAIN SHELL CONTENT
// ============================================================

class _MainShellContent extends StatefulWidget {
  const _MainShellContent();

  @override
  State<_MainShellContent> createState() => _MainShellContentState();
}

class _MainShellContentState extends State<_MainShellContent> {
  int _currentIndex = 0;

  late final List<Widget> _screens = [
    HomeTab(
      onOpenProfile: () => _selectTab(4),
      onOpenFarms: () => _selectTab(1),
      onFarmCreated: _refreshFarmList,
    ),
    FarmTab(
      onFarmCreated: _handleFarmCreated,
      onPrimaryChanged: _handleFarmCreated,
    ),
    const _AskFmTab(),
    const CropsTab(),
    const _ProfileTab(),
  ];

  void _selectTab(int index) {
    if (_currentIndex == index) {
      return;
    }

    setState(() {
      _currentIndex = index;
    });
  }

  void _refreshFarmList() {
    context.read<FarmProvider>().refreshFarms();
    context.read<CropProvider>().refreshCrops();
  }

  void _handleFarmCreated(FarmModel farm) {
    context.read<DashboardProvider>().refreshDashboard();
    context.read<CropProvider>().refreshCrops();
  }

  static const List<_NavigationItem> _navigationItems = [
    _NavigationItem(
      icon: Icons.home_outlined,
      activeIcon: Icons.home_rounded,
      label: 'Home',
    ),
    _NavigationItem(
      icon: Icons.agriculture_outlined,
      activeIcon: Icons.agriculture_rounded,
      label: 'Farm',
    ),
    _NavigationItem(
      icon: Icons.auto_awesome_outlined,
      activeIcon: Icons.auto_awesome_rounded,
      label: 'Ask',
    ),
    _NavigationItem(
      icon: Icons.grass_outlined,
      activeIcon: Icons.grass_rounded,
      label: 'Crops',
    ),
    _NavigationItem(
      icon: Icons.person_outline_rounded,
      activeIcon: Icons.person_rounded,
      label: 'Profile',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(
        bottom: false,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: IndexedStack(index: _currentIndex, children: _screens),
          ),
        ),
      ),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  // ==========================================================
  // BOTTOM NAVIGATION
  // ==========================================================

  Widget _buildBottomNavigationBar() {
    return SafeArea(
      top: false,
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.surfaceLight,
          border: const Border(
            top: BorderSide(color: AppColors.borderLight, width: 0.8),
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.primaryDark.withValues(alpha: 0.08),
              blurRadius: 20,
              offset: const Offset(0, -6),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(10, 8, 10, 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: List.generate(_navigationItems.length, (index) {
              final item = _navigationItems[index];

              return Expanded(
                child: _buildNavigationItem(
                  item: item,
                  selected: _currentIndex == index,
                  onTap: () {
                    _selectTab(index);
                  },
                ),
              );
            }),
          ),
        ),
      ),
    );
  }

  Widget _buildNavigationItem({
    required _NavigationItem item,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOutCubic,
          margin: const EdgeInsets.symmetric(horizontal: 3),
          padding: const EdgeInsets.symmetric(vertical: 7, horizontal: 4),
          decoration: BoxDecoration(
            color: selected
                ? AppColors.primary.withValues(alpha: 0.10)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 180),
                transitionBuilder: (Widget child, Animation<double> animation) {
                  return ScaleTransition(
                    scale: animation,
                    child: FadeTransition(opacity: animation, child: child),
                  );
                },
                child: Icon(
                  selected ? item.activeIcon : item.icon,
                  key: ValueKey(selected),
                  size: 23,
                  color: selected ? AppColors.primary : AppColors.textSecondary,
                ),
              ),

              const SizedBox(height: 4),

              AnimatedDefaultTextStyle(
                duration: const Duration(milliseconds: 180),
                style: TextStyle(
                  color: selected ? AppColors.primary : AppColors.textSecondary,
                  fontSize: 11,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                ),
                child: Text(item.label),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ============================================================
// NAVIGATION MODEL
// ============================================================

class _NavigationItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;

  const _NavigationItem({
    required this.icon,
    required this.activeIcon,
    required this.label,
  });
}

// ============================================================
// ASK FM TAB
// ============================================================

class _AskFmTab extends StatelessWidget {
  const _AskFmTab();

  @override
  Widget build(BuildContext context) {
    return const AskFMScreen(embedded: true);
  }
}

// ============================================================
// PROFILE TAB
// ============================================================

class _ProfileTab extends StatelessWidget {
  const _ProfileTab();

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final user = authProvider.user;

    final name = user?.fullName.trim() ?? '';
    final displayName = name.isNotEmpty ? name : 'Farmer';

    final mobile = user?.mobile.trim() ?? '';
    final displayMobile = mobile.isNotEmpty ? mobile : 'Mobile number';

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              const Text(
                'Profile',
                style: TextStyle(
                  color: AppColors.primaryDark,
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.6,
                ),
              ),

              const SizedBox(height: 30),

              _buildProfileHeader(name: displayName, mobile: displayMobile),

              const SizedBox(height: 32),

              _buildMenuCard(context),

              const SizedBox(height: 24),

              _buildLogoutButton(context),

              const SizedBox(height: 20),

              const Center(
                child: Text(
                  'FarmMate AI',
                  style: TextStyle(
                    color: AppColors.textHint,
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.4,
                  ),
                ),
              ),
            ]),
          ),
        ),
      ],
    );
  }

  Widget _buildProfileHeader({required String name, required String mobile}) {
    return Column(
      children: [
        Container(
          width: 104,
          height: 104,
          decoration: BoxDecoration(
            color: AppColors.primarySurface,
            shape: BoxShape.circle,
            border: Border.all(
              color: AppColors.primary.withValues(alpha: 0.18),
              width: 2,
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryDark.withValues(alpha: 0.10),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Center(
            child: Container(
              width: 78,
              height: 78,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.10),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.agriculture_rounded,
                color: AppColors.primary,
                size: 42,
              ),
            ),
          ),
        ),

        const SizedBox(height: 18),

        Text(
          name,
          textAlign: TextAlign.center,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 21,
            fontWeight: FontWeight.w800,
          ),
        ),

        const SizedBox(height: 6),

        Text(
          mobile,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildMenuCard(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppColors.borderLight),
        boxShadow: [
          BoxShadow(
            color: AppColors.primaryDark.withValues(alpha: 0.05),
            blurRadius: 18,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: Column(
        children: [
          _buildMenuItem(
            icon: Icons.edit_outlined,
            title: 'Edit Profile',
            subtitle: 'Update your personal information',
            onTap: () {
              context.push('/edit-profile');
            },
          ),

          _buildDivider(),

          _buildMenuItem(
            icon: Icons.dark_mode_outlined,
            title: 'Theme',
            subtitle: 'Appearance and display preferences',
            onTap: () {},
          ),

          _buildDivider(),

          _buildMenuItem(
            icon: Icons.settings_outlined,
            title: 'Settings',
            subtitle: 'Manage your app preferences',
            onTap: () {},
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 15),
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Icon(icon, color: AppColors.primary, size: 22),
              ),

              const SizedBox(width: 14),

              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                      ),
                    ),

                    const SizedBox(height: 3),

                    Text(
                      subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 8),

              const Icon(
                Icons.chevron_right_rounded,
                color: AppColors.textHint,
                size: 23,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDivider() {
    return const Padding(
      padding: EdgeInsets.only(left: 78),
      child: Divider(height: 1, thickness: 0.7, color: AppColors.borderLight),
    );
  }

  // ==========================================================
  // LOGOUT
  // ==========================================================

  Future<void> _handleLogout(BuildContext context) async {
    final shouldLogout = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          backgroundColor: AppColors.surfaceLight,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
          ),
          title: const Text(
            'Logout?',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w800,
            ),
          ),
          content: const Text(
            'Are you sure you want to logout from FarmMate AI?',
            style: TextStyle(color: AppColors.textSecondary, height: 1.4),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(dialogContext, false);
              },
              child: const Text(
                'Cancel',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),

            ElevatedButton(
              onPressed: () {
                Navigator.pop(dialogContext, true);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.error,
                foregroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Logout'),
            ),
          ],
        );
      },
    );

    if (shouldLogout != true || !context.mounted) {
      return;
    }

    await context.read<AuthProvider>().logout();
  }

  Widget _buildLogoutButton(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _handleLogout(context),
        borderRadius: BorderRadius.circular(18),
        child: Container(
          width: double.infinity,
          height: 56,
          decoration: BoxDecoration(
            color: AppColors.error.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.error.withValues(alpha: 0.14)),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.logout_rounded, color: AppColors.error, size: 21),

              SizedBox(width: 9),

              Text(
                'Logout',
                style: TextStyle(
                  color: AppColors.error,
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

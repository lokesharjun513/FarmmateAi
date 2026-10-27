import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';
import '../../shared/widgets/ai_chat_bubble.dart';
import '../farm/data/farm_repository.dart';
import '../farm/data/models/farm_model.dart';
import 'data/ask_fm_repository.dart';

class AskFMScreen extends StatefulWidget {
  const AskFMScreen({
    super.key,
    this.embedded = false,
    this.repository,
    this.farmRepository,
  });

  final bool embedded;
  final AskFmRepository? repository;
  final FarmRepository? farmRepository;

  @override
  State<AskFMScreen> createState() => _AskFMScreenState();
}

class _AskFMScreenState extends State<AskFMScreen> {
  late final AskFmRepository _repository;
  late final FarmRepository _farmRepository;

  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_AskFmMessage> _messages = [];

  List<FarmModel> _farms = [];
  FarmModel? _selectedFarm;
  String _selectedLanguage = 'English';
  bool _isLoadingFarms = true;
  bool _isSending = false;
  String? _errorMessage;
  String? _failedMessage;

  @override
  void initState() {
    super.initState();

    _repository = widget.repository ?? AskFmRepository();
    _farmRepository = widget.farmRepository ?? FarmRepository();
    _loadFarms();
  }

  Future<void> _loadFarms() async {
    try {
      final farms = await _farmRepository.getFarms();
      if (!mounted) return;
      setState(() {
        _farms = farms;
        _isLoadingFarms = false;
        if (farms.isNotEmpty) _selectedFarm = farms.first;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoadingFarms = false);
    }
  }

  void _retry() {
    if (_failedMessage == null) return;
    _sendMessage(retryText: _failedMessage);
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage({String? retryText}) async {
    if (_isSending || _selectedFarm == null) {
      return;
    }

    final message = (retryText ?? _controller.text).trim();

    if (message.isEmpty) {
      return;
    }

    setState(() {
      _isSending = true;
      _errorMessage = null;

      if (retryText == null) {
        _messages.add(_AskFmMessage(text: message, isUser: true));
        _failedMessage = null;
        _controller.clear();
      }
    });

    _scrollToBottom();

    try {
      final answer = await _repository.sendMessage(
        message,
        _selectedFarm!.id,
        language: _selectedLanguage,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _messages.add(_AskFmMessage(text: answer, isUser: false));
        _isSending = false;
        _failedMessage = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isSending = false;
        _errorMessage = _friendlyError(error);
        _failedMessage = message;
      });
    }

    _scrollToBottom();
  }

  void _onFarmChanged(FarmModel newFarm) {
    if (_selectedFarm?.id == newFarm.id) return;

    if (_messages.isEmpty) {
      setState(() => _selectedFarm = newFarm);
      return;
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Switch Farm'),
        content: Text('Would you like to continue your conversation or start a new conversation for ${newFarm.farmName}?'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              setState(() => _selectedFarm = newFarm);
            },
            child: const Text('Continue Conversation'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              setState(() {
                _selectedFarm = newFarm;
                _messages.clear();
              });
            },
            child: const Text('Start New Conversation'),
          ),
        ],
      ),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_scrollController.hasClients) {
        return;
      }

      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  String _friendlyError(Object error) {
    const fallback =
        'FarmMate AI could not answer right now. Please try again.';

    final message = error.toString().replaceFirst('Exception: ', '').trim();

    if (message.isEmpty) {
      return fallback;
    }

    final lower = message.toLowerCase();

    if (lower.contains('dioexception') ||
        lower.contains('socketexception') ||
        lower.contains('httpexception') ||
        lower.contains('formatexception') ||
        lower.contains('stacktrace') ||
        lower.contains('<html')) {
      return fallback;
    }

    return message;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.embedded) {
      return _buildBody(context);
    }

    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.surfaceLight,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
        title: const Row(
          children: [
            Icon(Icons.auto_awesome_rounded, color: AppColors.primary),
            SizedBox(width: 8),
            Text(
              'Ask FarmMate',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(top: false, child: _buildBody(context)),
    );
  }

  Widget _buildBody(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: Column(
          children: [
            if (widget.embedded) _buildEmbeddedHeader(),
            if (!_isLoadingFarms && _farms.isNotEmpty) _buildFarmSelector(),
            Expanded(
              child: _messages.isEmpty && !_isSending
                  ? _buildEmptyState()
                  : _buildMessageList(),
            ),
            if (_errorMessage != null) _buildErrorBanner(),
            _buildComposer(),
          ],
        ),
      ),
    );
  }

  Widget _buildFarmSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: AppColors.surfaceLight,
      child: Row(
        children: [
          const Icon(Icons.grass_rounded, color: AppColors.primary, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _selectedFarm?.farmName ?? 'Select a farm',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          PopupMenuButton<FarmModel>(
            onSelected: _onFarmChanged,
            itemBuilder: (context) => _farms
                .map((f) => PopupMenuItem(value: f, child: Text(f.farmName)))
                .toList(),
            icon: const Icon(Icons.arrow_drop_down_rounded),
          ),
          PopupMenuButton<String>(
            onSelected: (lang) => setState(() => _selectedLanguage = lang),
            itemBuilder: (context) => ['English', 'Hindi', 'Telugu']
                .map((l) => PopupMenuItem(value: l, child: Text(l)))
                .toList(),
            child: Text(_selectedLanguage, style: const TextStyle(fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }

  Widget _buildEmbeddedHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 14),
      decoration: const BoxDecoration(
        color: AppColors.surfaceLight,
        border: Border(
          bottom: BorderSide(color: AppColors.borderLight, width: 0.8),
        ),
      ),
      child: const Row(
        children: [
          Icon(Icons.auto_awesome_rounded, color: AppColors.primary, size: 24),
          SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Ask FarmMate',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'AI guidance for your farm',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 76,
              height: 76,
              decoration: BoxDecoration(
                color: AppColors.primarySurface,
                shape: BoxShape.circle,
                border: Border.all(
                  color: AppColors.primary.withValues(alpha: 0.12),
                ),
              ),
              child: const Icon(
                Icons.auto_awesome_rounded,
                color: AppColors.primary,
                size: 34,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Ask about your farm',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 19,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Get help with pests, weather, irrigation, crop care, and farm tasks.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageList() {
    final itemCount = _messages.length + (_isSending ? 1 : 0);

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(vertical: 14),
      itemCount: itemCount,
      itemBuilder: (context, index) {
        if (_isSending && index == _messages.length) {
          return const AIChatBubble(
            message: 'FarmMate AI is thinking…',
            isAI: true,
          );
        }

        final message = _messages[index];

        return AIChatBubble(message: message.text, isAI: !message.isUser);
      },
    );
  }

  Widget _buildErrorBanner() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.16)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline_rounded, color: AppColors.error),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              _errorMessage ?? 'FarmMate AI could not answer right now.',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 12,
                height: 1.35,
              ),
            ),
          ),
          TextButton(
            key: const Key('ask_fm_retry_button'),
            onPressed: _isSending ? null : _retry,
            style: TextButton.styleFrom(
              foregroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(horizontal: 10),
            ),
            child: const Text(
              'Try again',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildComposer() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
      decoration: const BoxDecoration(
        color: AppColors.surfaceLight,
        border: Border(
          top: BorderSide(color: AppColors.borderLight, width: 0.8),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                key: const Key('ask_fm_input'),
                controller: _controller,
                enabled: !_isSending,
                minLines: 1,
                maxLines: 4,
                maxLength: 2000,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) {
                  if (!_isSending) {
                    _sendMessage();
                  }
                },
                decoration: InputDecoration(
                  hintText: 'Ask about pests, weather, or crop health…',
                  counterText: '',
                  filled: true,
                  fillColor: AppColors.backgroundLight,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              key: const Key('ask_fm_send_button'),
              onPressed: _isSending
                  ? null
                  : () {
                      _sendMessage();
                    },
              icon: _isSending
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send_rounded),
            ),
          ],
        ),
      ),
    );
  }
}

class _AskFmMessage {
  final String text;
  final bool isUser;

  const _AskFmMessage({required this.text, required this.isUser});
}

import 'package:flutter/material.dart';

class LanguageSelectorBadge extends StatelessWidget {
  final bool isUzbek;
  final ValueChanged<bool> onSelectLang;

  const LanguageSelectorBadge({
    super.key,
    required this.isUzbek,
    required this.onSelectLang,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 32,
      padding: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFCBD5E1), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // UZ Button
          GestureDetector(
            onTap: () => onSelectLang(true),
            behavior: HitTestBehavior.opaque,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: isUzbek ? const Color(0xFF0284C7) : Colors.transparent,
                borderRadius: BorderRadius.circular(16),
                boxShadow: isUzbek
                    ? [
                        BoxShadow(
                          color: const Color(0xFF0284C7).withValues(alpha: 0.25),
                          blurRadius: 4,
                          offset: const Offset(0, 1),
                        ),
                      ]
                    : null,
              ),
              child: Text(
                'UZ',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: isUzbek ? Colors.white : const Color(0xFF64748B),
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),

          const SizedBox(width: 2),

          // RU Button
          GestureDetector(
            onTap: () => onSelectLang(false),
            behavior: HitTestBehavior.opaque,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: !isUzbek ? const Color(0xFF0284C7) : Colors.transparent,
                borderRadius: BorderRadius.circular(16),
                boxShadow: !isUzbek
                    ? [
                        BoxShadow(
                          color: const Color(0xFF0284C7).withValues(alpha: 0.25),
                          blurRadius: 4,
                          offset: const Offset(0, 1),
                        ),
                      ]
                    : null,
              ),
              child: Text(
                'RU',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  color: !isUzbek ? Colors.white : const Color(0xFF64748B),
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_router.dart';
import 'services/llm_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // 初始化 LLM 大脑
  final llm = LlmService();
  await llm.initialize();
  
  runApp(
    ProviderScope(
      overrides: [
        llmServiceProvider.overrideWithValue(llm),
      ],
      child: const ArisMobileApp(),
    ),
  );
}

final llmServiceProvider = Provider<LlmService>((ref) {
  throw UnimplementedError('Must override in main');
});

class ArisMobileApp extends ConsumerWidget {
  const ArisMobileApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'Aris',
      debugShowCheckedModeBanner: false,
      theme: _buildDarkTheme(),
      initialRoute: AppRouter.home,
      onGenerateRoute: AppRouter.generateRoute,
    );
  }

  ThemeData _buildDarkTheme() {
    final textTheme = GoogleFonts.interTextTheme();

    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF000000),
      colorScheme: const ColorScheme.dark(
        primary: Color(0xFF0071E3),       // Apple Blue
        secondary: Color(0xFF00D4AA),     // Aris Teal
        surface: Color(0xFF000000),
        error: Color(0xFFFF453A),
        onPrimary: Color(0xFFFFFFFF),
        onSecondary: Color(0xFFFFFFFF),
        onSurface: Color(0xFFF5F5F7),
      ),
      textTheme: textTheme.copyWith(
        displayLarge: textTheme.displayLarge?.copyWith(
          fontFamily: 'Inter',
          fontWeight: FontWeight.w600,
          color: const Color(0xFFF5F5F7),
          letterSpacing: -0.3,
        ),
        bodyLarge: textTheme.bodyLarge?.copyWith(
          fontFamily: 'Inter',
          fontWeight: FontWeight.w400,
          color: const Color(0xFFF5F5F7),
          letterSpacing: -0.2,
        ),
        bodyMedium: textTheme.bodyMedium?.copyWith(
          fontFamily: 'Inter',
          fontWeight: FontWeight.w400,
          color: const Color(0xFFF5F5F7),
        ),
        labelSmall: textTheme.labelSmall?.copyWith(
          fontFamily: 'Inter',
          fontWeight: FontWeight.w500,
          color: const Color(0xFF8A8F98),
          letterSpacing: 0.8,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Color(0xFF000000),
        selectedItemColor: Color(0xFF0071E3),
        unselectedItemColor: Color(0x99555577),
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      dividerTheme: const DividerThemeData(
        color: Color(0x0FFFFFFF),
        thickness: 0.5,
      ),
      cardTheme: CardThemeData(
        color: const Color(0x0AFFFFFF),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: Color(0x0FFFFFFF), width: 0.5),
        ),
      ),
    );
  }
}

/**
 * Telegram WebApp theme parameter types and contract
 * See: https://core.telegram.org/bots/webapps#theming
 */

export type TelegramThemeParams = {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
  header_bg_color?: string;
  section_bg_color?: string;
  section_header_text_color?: string;
  subtitle_text_color?: string;
  destructive_text_color?: string;
};

export type TelegramColorScheme = 'light' | 'dark';

export interface TelegramWebApp {
  themeParams: TelegramThemeParams;
  colorScheme: TelegramColorScheme;
  backgroundColor: string;
  textColor: string;
  expand(): void;
  ready(): void;
  onEvent(type: string, callback: () => void): void;
  offEvent(type: string, callback: () => void): void;
  isVersionAtLeast(version: string): boolean;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp;
    };
  }
}

export interface ThemeChangeEvent {
  themeParams: TelegramThemeParams;
  colorScheme: TelegramColorScheme;
}
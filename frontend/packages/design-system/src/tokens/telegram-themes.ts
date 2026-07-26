/**
 * Telegram light theme defaults (fallback for test builds)
 * Based on Telegram WebApp specification
 */

export const TELEGRAM_LIGHT_THEME: TelegramThemeParams = {
  bg_color: '#ffffff',
  text_color: '#000000',
  hint_color: '#707579',
  link_color: '#3390ec',
  button_color: '#3390ec',
  button_text_color: '#ffffff',
  secondary_bg_color: '#f4f4f5',
  header_bg_color: '#ffffff',
  section_bg_color: '#ffffff',
  section_header_text_color: '#616d76',
  subtitle_text_color: '#707579',
  destructive_text_color: '#e53935'
};

/**
 * Telegram dark theme defaults (fallback for test builds)
 */

export const TELEGRAM_DARK_THEME: TelegramThemeParams = {
  bg_color: '#1c1c1d',
  text_color: '#ffffff',
  hint_color: '#aaaaaa',
  link_color: '#64b5ef',
  button_color: '#2ea5ff',
  button_text_color: '#ffffff',
  secondary_bg_color: '#2c2c2e',
  header_bg_color: '#1c1c1d',
  section_bg_color: '#2c2c2e',
  section_header_text_color: '#aaaaaa',
  subtitle_text_color: '#aaaaaa',
  destructive_text_color: '#ff6b6b'
};

/**
 * Fallback theme used when Telegram WebApp API is unavailable
 * (deterministic browser fallback for test builds)
 */

export const FALLBACK_THEME = TELEGRAM_LIGHT_THEME;
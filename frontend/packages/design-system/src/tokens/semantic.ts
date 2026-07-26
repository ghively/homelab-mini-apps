/**
 * Design system semantic tokens derived from Telegram theme parameters
 * These tokens are consumed by web components and user applications
 */

import type { TelegramThemeParams, TelegramColorScheme } from '../types/telegram.js';

export interface SemanticTokens {
  colors: {
    background: {
      primary: string;
      secondary: string;
      header: string;
      section: string;
    };
    text: {
      primary: string;
      secondary: string;
      hint: string;
      link: string;
      destructive: string;
    };
    button: {
      background: string;
      text: string;
    };
    sectionHeader: string;
  };
  colorScheme: TelegramColorScheme;
}

function normalizeColor(color: string | undefined, fallback: string): string {
  return color || fallback;
}

export function deriveSemanticTokens(
  themeParams: TelegramThemeParams,
  colorScheme: TelegramColorScheme
): SemanticTokens {
  return {
    colors: {
      background: {
        primary: normalizeColor(themeParams.bg_color, '#ffffff'),
        secondary: normalizeColor(themeParams.secondary_bg_color, '#f4f4f5'),
        header: normalizeColor(themeParams.header_bg_color, '#ffffff'),
        section: normalizeColor(themeParams.section_bg_color, '#ffffff')
      },
      text: {
        primary: normalizeColor(themeParams.text_color, '#000000'),
        secondary: normalizeColor(themeParams.subtitle_text_color, '#707579'),
        hint: normalizeColor(themeParams.hint_color, '#707579'),
        link: normalizeColor(themeParams.link_color, '#3390ec'),
        destructive: normalizeColor(themeParams.destructive_text_color, '#e53935')
      },
      button: {
        background: normalizeColor(themeParams.button_color, '#3390ec'),
        text: normalizeColor(themeParams.button_text_color, '#ffffff')
      },
      sectionHeader: normalizeColor(themeParams.section_header_text_color, '#616d76')
    },
    colorScheme
  };
}
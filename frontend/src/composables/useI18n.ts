import { createI18n } from 'vue-i18n'
import { ref, watch } from 'vue'
import messages from '../locales'
import type { Locale } from '../locales'

const STORAGE_KEY = 'dzeck-locale'

const getBrowserLocale = (): Locale => {
  const browserLang = navigator.language || navigator.languages?.[0]
  if (browserLang?.startsWith('zh')) {
    return 'zh'
  }
  if (browserLang?.startsWith('en')) {
    return 'en'
  }
  return 'id'
}

const getStoredLocale = (): Locale => {
  const storedLocale = localStorage.getItem(STORAGE_KEY)
  if (storedLocale === 'en' || storedLocale === 'zh' || storedLocale === 'id') {
    return storedLocale as Locale
  }
  const oldKey = localStorage.getItem('manus-locale')
  if (oldKey === 'en' || oldKey === 'zh') {
    return oldKey as Locale
  }
  return getBrowserLocale()
}

export const i18n = createI18n({
  legacy: false,
  locale: getStoredLocale(),
  fallbackLocale: 'id',
  messages,
  silentTranslationWarn: true,
  silentFallbackWarn: true,
  missingWarn: false,
  fallbackWarn: false,
  warnHtmlMessage: false
})

// Create a composable to use in components
export function useLocale() {
  const currentLocale = ref(getStoredLocale())

  // Switch language
  const setLocale = (locale: Locale) => {
    i18n.global.locale.value = locale
    currentLocale.value = locale
    localStorage.setItem(STORAGE_KEY, locale)
    document.querySelector('html')?.setAttribute('lang', locale)
  }

  // Watch language change
  watch(currentLocale, (val) => {
    setLocale(val)
  })

  return {
    currentLocale,
    setLocale
  }
}

export default i18n 
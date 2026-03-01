import en from './en'
import zh from './zh'
import id from './id'

export default {
  en,
  zh,
  id
}

export type Locale = 'en' | 'zh' | 'id'

export const availableLocales: { label: string; value: Locale }[] = [
  { label: 'Bahasa Indonesia', value: 'id' },
  { label: 'English', value: 'en' },
  { label: '中文 (Mandarin)', value: 'zh' }
]

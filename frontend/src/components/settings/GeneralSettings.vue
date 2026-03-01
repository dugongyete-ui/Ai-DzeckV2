<template>
  <div class="flex flex-col gap-0 w-full">
    <div class="pb-[32px] border-b border-[var(--border-light)] w-full">
      <div class="text-[13px] font-medium text-[var(--text-tertiary)] mb-1 w-full">{{ t('General') }}</div>
      <div class="mb-[24px] last:mb-[0] w-full">
        <div class="text-sm font-medium text-[var(--text-primary)] mb-[12px]">{{ t('Language') }}</div>
        <Select v-model="selectedLanguage" @update:modelValue="onLanguageChange">
          <SelectTrigger class="w-[208px] h-[36px]">
            <SelectValue :placeholder="t('Select language')" />
          </SelectTrigger>
          <SelectContent :side-offset="5">
            <SelectItem
              v-for="option in languageOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>

    <div class="py-[32px] border-b border-[var(--border-light)] w-full">
      <div class="text-[13px] font-medium text-[var(--text-tertiary)] mb-1 w-full">{{ t('AI Model') }}</div>
      <div class="mb-[24px] w-full">
        <div class="text-sm font-medium text-[var(--text-primary)] mb-[6px]">{{ t('Active Model') }}</div>
        <div class="text-xs text-[var(--text-tertiary)] mb-[12px]">{{ t('Model configured on the server. Change in .env to switch.') }}</div>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-2 px-3 h-[36px] rounded-[10px] bg-[var(--fill-tsp-gray-main)] border border-[var(--border-main)] text-sm text-[var(--text-primary)] min-w-[208px]">
            <Cpu :size="14" class="text-[var(--icon-tertiary)] flex-shrink-0" />
            <span class="truncate">{{ serverModel || t('Loading...') }}</span>
          </div>
          <div v-if="serverApiBase" class="text-xs text-[var(--text-tertiary)] truncate max-w-[200px]">{{ serverApiBase }}</div>
        </div>
      </div>
    </div>

    <div class="pt-[32px] w-full">
      <div class="text-[13px] font-medium text-[var(--text-tertiary)] mb-1 w-full">{{ t('Notifications') }}</div>
      <div class="mb-[24px] w-full">
        <div class="text-sm font-medium text-[var(--text-primary)] mb-[6px]">{{ t('Browser Notifications') }}</div>
        <div class="text-xs text-[var(--text-tertiary)] mb-[12px]">{{ t('Get notified when an AI task completes (only when tab is not focused).') }}</div>
        <div v-if="!notifSupported" class="text-xs text-[var(--text-tertiary)] italic">
          {{ t('Browser notifications are not supported in this browser.') }}
        </div>
        <div v-else class="flex items-center gap-3">
          <button
            v-if="notifPermission !== 'granted'"
            @click="requestNotifPermission"
            :disabled="notifPermission === 'denied'"
            class="flex items-center gap-1.5 px-3 h-[36px] rounded-[10px] text-sm font-medium border border-[var(--border-main)] hover:bg-[var(--fill-tsp-gray-main)] transition-colors text-[var(--text-secondary)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Bell :size="14" />
            {{ notifPermission === 'denied' ? t('Blocked by browser') : t('Enable Notifications') }}
          </button>
          <div v-else class="flex items-center gap-2">
            <div class="flex items-center gap-2">
              <div
                @click="toggleNotifications"
                class="relative inline-flex h-5 w-9 cursor-pointer rounded-full transition-colors"
                :class="notifEnabled ? 'bg-[var(--Button-primary-black)]' : 'bg-[var(--fill-tsp-gray-dark)]'"
              >
                <span
                  class="inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform mt-0.5"
                  :class="notifEnabled ? 'translate-x-4' : 'translate-x-0.5'"
                ></span>
              </div>
              <span class="text-sm text-[var(--text-primary)]">{{ notifEnabled ? t('Enabled') : t('Disabled') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Cpu, Bell } from 'lucide-vue-next'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { SelectOption } from '@/types/select'
import { useLocale } from '@/composables/useI18n'
import type { Locale } from '@/locales'
import { useNotification } from '@/composables/useNotification'
import { getAppSettings } from '@/api/agent'

const { t } = useI18n()
const { currentLocale, setLocale } = useLocale()
const {
  isSupported: notifSupported,
  permission: notifPermission,
  isEnabled: notifEnabled,
  requestPermission,
  disableNotifications,
} = useNotification()

const selectedLanguage = ref<Locale>(currentLocale.value)
const serverModel = ref<string>('')
const serverApiBase = ref<string>('')

const languageOptions: SelectOption[] = [
  { value: 'id', label: t('Indonesian') },
  { value: 'en', label: t('English') },
  { value: 'zh', label: t('Simplified Chinese') },
]

const onLanguageChange = (value: any) => {
  if (value && typeof value === 'string') {
    const locale = value as Locale
    setLocale(locale)
  }
}

const requestNotifPermission = async () => {
  await requestPermission()
}

const toggleNotifications = () => {
  if (notifEnabled.value) {
    disableNotifications()
  } else {
    notifEnabled.value = true
    localStorage.setItem('notifications_enabled', 'true')
  }
}

onMounted(async () => {
  try {
    const settings = await getAppSettings()
    serverModel.value = settings.model_name
    serverApiBase.value = settings.api_base
  } catch {
    serverModel.value = t('Unknown')
  }
})
</script>

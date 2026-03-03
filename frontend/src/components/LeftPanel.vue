<template>
  <div :class="isLeftPanelShow ?
    'h-full flex flex-col' :
    'h-full flex flex-col fixed top-0 start-0 bottom-0 z-[1]'" :style="isLeftPanelShow ?
      'width: 300px; transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);' :
      'width: 24px; transition: width 0.36s cubic-bezier(0.4, 0, 0.2, 1);'">
    <div
      :class="isLeftPanelShow ?
        'flex flex-col overflow-hidden bg-[var(--background-nav)] h-full opacity-100 translate-x-0' :
        'flex flex-col overflow-hidden bg-[var(--background-nav)] fixed top-1 start-1 bottom-1 z-[1] border-1 dark:border-[1px] border-[var(--border-main)] dark:border-[var(--border-light)] rounded-xl shadow-[0px_8px_32px_0px_rgba(0,0,0,0.16),0px_0px_0px_1px_rgba(0,0,0,0.06)] opacity-0 pointer-events-none -translate-x-10'"
      :style="(isLeftPanelShow ? 'width: 300px;' : 'width: 0px;') + ' transition: opacity 0.2s, transform 0.2s, width 0.2s;'">
      <div class="flex">
        <div class="flex items-center px-3 py-3 flex-row h-[52px] gap-1 justify-end w-full">
          <div class="flex justify-between w-full px-1 pt-2">
            <div class="relative flex">
              <div
                class="flex h-7 w-7 items-center justify-center cursor-pointer hover:bg-[var(--fill-tsp-gray-main)] rounded-md"
                @click="toggleLeftPanel">
                <PanelLeft class="h-5 w-5 text-[var(--icon-secondary)]" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="px-3 mb-1 flex justify-center flex-shrink-0">
        <button @click="handleNewTaskClick"
          class="flex min-w-[36px] w-full items-center justify-center gap-1.5 rounded-lg h-[32px] bg-[var(--Button-primary-white)] hover:bg-white/20 dark:hover:bg-black/60 cursor-pointer shadow-[0px_0.5px_3px_0px_var(--shadow-S)]">
          <Plus class="h-4 w-4 text-[var(--icon-primary)]" />
          <span class="text-sm font-medium text-[var(--text-primary)] whitespace-nowrap truncate">
            {{ t('New Task') }}
          </span>
          <div class="flex items-center gap-0.5">
            <span
              class="flex text-[var(--text-tertiary)] justify-center items-center min-w-5 h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)]">
              <Command :size="14" />
            </span>
            <span
              class="flex justify-center items-center w-5 h-5 px-1 rounded-[4px] bg-[var(--fill-tsp-white-light)] border border-[var(--border-light)] text-sm font-normal text-[var(--text-tertiary)] ">
              K
            </span>
          </div>
        </button>
      </div>
      <div v-if="sessions.length > 0" class="flex flex-col flex-1 min-h-0 overflow-auto pt-2 pb-5 overflow-x-hidden">
        <SessionItem v-for="session in sessions" :key="session.session_id" :session="session"
          @deleted="handleSessionDeleted" />
      </div>
      <div v-else class="flex flex-1 flex-col items-center justify-center gap-4">
        <div class="flex flex-col items-center gap-2 text-[var(--text-tertiary)]">
          <MessageSquareDashed :size="38" />
          <span class="text-sm font-medium">{{ t('Create a task to get started') }}</span></div>
      </div>

      <div v-if="sessions.length > 0" class="px-3 pb-3 flex-shrink-0">
        <button @click="showClearConfirm = true"
          class="flex w-full items-center justify-center gap-1.5 rounded-lg h-[32px] border border-[var(--border-main)] hover:bg-red-50 dark:hover:bg-red-950/30 hover:border-red-300 dark:hover:border-red-800 cursor-pointer transition-colors">
          <Trash2 class="h-4 w-4 text-[var(--text-tertiary)] hover:text-red-500" />
          <span class="text-sm font-medium text-[var(--text-tertiary)]">{{ t('Clear All History') }}</span>
        </button>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="showClearConfirm"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      @click.self="showClearConfirm = false">
      <div class="bg-[var(--background-main)] border border-[var(--border-main)] rounded-xl shadow-xl p-6 max-w-sm w-full mx-4">
        <div class="flex items-center gap-3 mb-3">
          <div class="flex items-center justify-center w-10 h-10 rounded-full bg-red-100 dark:bg-red-950/50 flex-shrink-0">
            <Trash2 class="h-5 w-5 text-red-500" />
          </div>
          <h3 class="text-base font-semibold text-[var(--text-primary)]">{{ t('Clear All History') }}</h3>
        </div>
        <p class="text-sm text-[var(--text-secondary)] mb-5">
          {{ t('This will permanently delete all chat sessions. This action cannot be undone.') }}
        </p>
        <div class="flex gap-2 justify-end">
          <button @click="showClearConfirm = false"
            class="px-4 py-2 text-sm font-medium rounded-lg border border-[var(--border-main)] text-[var(--text-primary)] hover:bg-[var(--fill-tsp-gray-main)] transition-colors">
            {{ t('Cancel') }}
          </button>
          <button @click="handleClearAllHistory" :disabled="isClearing"
            class="px-4 py-2 text-sm font-medium rounded-lg bg-red-500 hover:bg-red-600 text-white transition-colors disabled:opacity-60 flex items-center gap-1.5">
            <span v-if="isClearing" class="animate-spin">
              <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
            </span>
            <Trash2 v-else class="h-4 w-4" />
            {{ t('Delete All') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { PanelLeft, Plus, Command, MessageSquareDashed, Trash2 } from 'lucide-vue-next';
import SessionItem from './SessionItem.vue';
import { useLeftPanel } from '../composables/useLeftPanel';
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsSSE, getSessions, deleteAllSessions } from '../api/agent';
import { ListSessionItem } from '../types/response';
import { useI18n } from 'vue-i18n';

const { t } = useI18n()
const { isLeftPanelShow, toggleLeftPanel } = useLeftPanel()
const route = useRoute()
const router = useRouter()

const sessions = ref<ListSessionItem[]>([])
const cancelGetSessionsSSE = ref<(() => void) | null>(null)
const showClearConfirm = ref(false)
const isClearing = ref(false)

// Function to fetch sessions data
const updateSessions = async () => {
  try {
    const response = await getSessions()
    sessions.value = response.sessions
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  }
}

// Function to fetch sessions data
const fetchSessions = async () => {
  try {
    if (cancelGetSessionsSSE.value) {
      cancelGetSessionsSSE.value()
      cancelGetSessionsSSE.value = null
    }
    cancelGetSessionsSSE.value = await getSessionsSSE({
      onOpen: () => {
      },
      onMessage: (event) => {
        sessions.value = event.data.sessions
      },
      onError: (error) => {
        console.error('Failed to fetch sessions:', error)
      },
      onClose: () => {
      }
    })
  } catch (error) {
    console.error('Failed to fetch sessions:', error)
  }
}

const handleNewTaskClick = () => {
  router.push('/')
}

const handleSessionDeleted = (sessionId: string) => {
  sessions.value = sessions.value.filter(session => session.session_id !== sessionId);
}

const handleClearAllHistory = async () => {
  isClearing.value = true
  try {
    await deleteAllSessions()
    sessions.value = []
    showClearConfirm.value = false
    router.push('/')
  } catch (error) {
    console.error('Failed to clear all sessions:', error)
  } finally {
    isClearing.value = false
  }
}

// Handle keyboard shortcuts
const handleKeydown = (event: KeyboardEvent) => {
  // Check for Command + K (Mac) or Ctrl + K (Windows/Linux)
  if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
    event.preventDefault()
    handleNewTaskClick()
  }
}

onMounted(async () => {
  // Initial fetch of sessions
  fetchSessions()

  // Add keyboard event listener
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  if (cancelGetSessionsSSE.value) {
    cancelGetSessionsSSE.value()
    cancelGetSessionsSSE.value = null
  }

  // Remove keyboard event listener
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => route.path, async () => {
  await updateSessions()
})
</script>

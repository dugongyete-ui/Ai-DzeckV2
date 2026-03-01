import { ref, onMounted } from 'vue';

const isSupported = ref(false);
const permission = ref<NotificationPermission>('default');
const isEnabled = ref(false);

const NOTIFICATION_STORAGE_KEY = 'notifications_enabled';

export function useNotification() {
  const checkSupport = () => {
    isSupported.value = 'Notification' in window;
    if (isSupported.value) {
      permission.value = Notification.permission;
      const stored = localStorage.getItem(NOTIFICATION_STORAGE_KEY);
      isEnabled.value = stored === 'true' && Notification.permission === 'granted';
    }
  };

  const requestPermission = async (): Promise<boolean> => {
    if (!isSupported.value) return false;
    
    try {
      const result = await Notification.requestPermission();
      permission.value = result;
      if (result === 'granted') {
        isEnabled.value = true;
        localStorage.setItem(NOTIFICATION_STORAGE_KEY, 'true');
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  const disableNotifications = () => {
    isEnabled.value = false;
    localStorage.setItem(NOTIFICATION_STORAGE_KEY, 'false');
  };

  const notify = (title: string, options?: NotificationOptions) => {
    if (!isSupported.value || !isEnabled.value || Notification.permission !== 'granted') {
      return null;
    }
    
    if (document.hasFocus()) return null;
    
    try {
      const notification = new Notification(title, {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        ...options,
      });
      
      notification.onclick = () => {
        window.focus();
        notification.close();
      };
      
      return notification;
    } catch {
      return null;
    }
  };

  const notifyTaskComplete = (taskTitle?: string) => {
    return notify('Task Completed', {
      body: taskTitle ? `"${taskTitle}" has finished.` : 'Your AI task has completed.',
      tag: 'task-complete',
    });
  };

  const notifyTaskError = (taskTitle?: string) => {
    return notify('Task Error', {
      body: taskTitle ? `"${taskTitle}" encountered an error.` : 'Your AI task encountered an error.',
      tag: 'task-error',
    });
  };

  onMounted(() => {
    checkSupport();
  });

  return {
    isSupported,
    permission,
    isEnabled,
    requestPermission,
    disableNotifications,
    notify,
    notifyTaskComplete,
    notifyTaskError,
  };
}

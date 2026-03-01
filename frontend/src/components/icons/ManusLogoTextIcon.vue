<template>
    <span
      :style="{ fontSize: (Number(height) * 0.55) + 'px', lineHeight: height + 'px', fontWeight: 700, letterSpacing: '0.02em', color: 'var(--logo-color)', fontFamily: 'ui-sans-serif, system-ui, sans-serif', display: 'inline-flex', alignItems: 'center' }"
    >Dzeck</span>
</template>
<script setup lang="ts">
defineProps({
  width: {
    type: [String, Number],
    default: 88
  },
  height: {
    type: [String, Number],
    default: 38
  }
})
</script>

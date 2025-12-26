<script setup lang="ts">
const props = defineProps<{
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    isDanger?: boolean;
}>();

const emit = defineEmits(['confirm', 'cancel']);
</script>

<template>
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100]" @click.self="$emit('cancel')">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-scale-in">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
        <h2 class="text-lg font-bold text-slate-800 dark:text-white">{{ title }}</h2>
      </div>

      <!-- Body -->
      <div class="px-6 py-6">
        <p class="text-slate-600 dark:text-slate-300">{{ message }}</p>
      </div>

      <!-- Actions -->
      <div class="px-6 py-4 bg-slate-50 dark:bg-slate-900 flex gap-3 justify-end">
        <button 
            @click="$emit('cancel')" 
            class="px-5 py-2.5 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-600 font-medium transition-colors"
        >
            {{ cancelText || '取消' }}
        </button>
        <button 
            @click="$emit('confirm')" 
            class="px-5 py-2.5 rounded-lg font-medium transition-colors"
            :class="isDanger ? 'bg-red-600 hover:bg-red-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'"
        >
            {{ confirmText || '确定' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes scaleIn {
  0% { transform: scale(0.9); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.animate-scale-in {
  animation: scaleIn 0.2s ease-out;
}
</style>

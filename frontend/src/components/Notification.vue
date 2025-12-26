<script setup lang="ts">
import { onMounted } from 'vue';

const props = defineProps<{
  message: string;
  type?: 'success' | 'error' | 'info';
}>();

const emit = defineEmits(['close']);

onMounted(() => {
  setTimeout(() => {
    emit('close');
  }, 3000);
});
</script>

<template>
  <div 
    class="fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white font-medium z-[9999] animate-fade-in-down flex items-center gap-2"
    :class="{
      'bg-green-500': type === 'success',
      'bg-red-500': type === 'error',
      'bg-blue-500': type === 'info' || !type
    }"
  >
    <span>{{ message }}</span>
    <button @click="$emit('close')" class="ml-2 opacity-80 hover:opacity-100 font-bold">&times;</button>
  </div>
</template>

<style scoped>
.animate-fade-in-down {
  animation: fadeInDown 0.3s ease-out;
}
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

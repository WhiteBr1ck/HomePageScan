<script setup lang="ts">
import { ref, computed } from 'vue';
import { login } from '../api';

const username = ref('admin');
const password = ref('');
const error = ref('');
const emit = defineEmits(['close', 'success']);

const props = defineProps<{
    accentColor?: string;
}>();

// Simple i18n
const lang = ref(localStorage.getItem('lang') || 'zh');
const t = computed(() => lang.value === 'zh' ? {
    title: '管理员登录',
    username: '用户名',
    password: '密码',
    cancel: '取消',
    login: '登录',
    failed: '登录失败：请检查用户名/密码',
} : {
    title: 'Admin Login',
    username: 'Username',
    password: 'Password',
    cancel: 'Cancel',
    login: 'Login',
    failed: 'Login Failed: Check username/password',
});

const handleLogin = async () => {
    try {
        const res = await login({ username: username.value, password: password.value });
        localStorage.setItem('token', res.access_token);
        emit('success');
        emit('close');
    } catch (e: any) {
        error.value = t.value.failed;
    }
};
</script>

<template>
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="bg-white dark:bg-slate-800 rounded-xl p-8 shadow-2xl w-full max-w-sm animate-fade-in-up">
      <h2 class="text-2xl font-bold mb-6 text-slate-800 dark:text-white text-center">{{ t.title }}</h2>
      
      <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{{ t.username }}</label>
            <input 
                v-model="username" 
                type="text" 
                class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="admin"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">{{ t.password }}</label>
            <input 
                v-model="password" 
                type="password" 
                class="w-full px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                @keyup.enter="handleLogin" 
            />
          </div>
      </div>

      <p v-if="error" class="text-red-500 text-sm mt-4 text-center bg-red-50 dark:bg-red-900/20 p-2 rounded">{{ error }}</p>
      
      <div class="mt-8 flex justify-end gap-3">
        <button 
            @click="$emit('close')" 
            class="px-4 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
        >
            {{ t.cancel }}
        </button>
        <button 
            @click="handleLogin"
            class="px-6 py-2 rounded-lg text-white font-medium shadow-lg transition transform hover:-translate-y-0.5"
            :style="{ backgroundColor: props.accentColor || '#3b82f6' }"
        >
            {{ t.login }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

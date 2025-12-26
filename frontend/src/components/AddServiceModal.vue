<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{ lang: 'zh' | 'en'; accentColor?: string }>();
const emit = defineEmits(['close', 'save']);

const t = computed(() => props.lang === 'zh' ? {
    title: '手动添加服务',
    name: '服务名称',
    namePlaceholder: '例如：NAS 管理面板',
    lanUrl: '局域网地址',
    lanPlaceholder: 'http://192.168.1.100:8080',
    wanUrl: '公网地址（可选）',
    wanPlaceholder: 'https://nas.example.com',
    cancel: '取消',
    add: '添加',
} : {
    title: 'Add Service Manually',
    name: 'Service Name',
    namePlaceholder: 'e.g., NAS Dashboard',
    lanUrl: 'LAN URL',
    lanPlaceholder: 'http://192.168.1.100:8080',
    wanUrl: 'WAN URL (Optional)',
    wanPlaceholder: 'https://nas.example.com',
    cancel: 'Cancel',
    add: 'Add',
});

const form = ref({
    custom_name: '',
    lan_url: '',
    wan_url: '',
});

const handleSave = () => {
    if (!form.value.custom_name || !form.value.lan_url) {
        alert(props.lang === 'zh' ? '请填写名称和局域网地址' : 'Please fill name and LAN URL');
        return;
    }
    
    // Extract port from URL
    let port = 80;
    try {
        const url = new URL(form.value.lan_url);
        port = url.port ? parseInt(url.port) : (url.protocol === 'https:' ? 443 : 80);
    } catch {}
    
    emit('save', { ...form.value, port });
};
</script>

<template>
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
      
      <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
        <h2 class="text-lg font-bold text-slate-800 dark:text-white">{{ t.title }}</h2>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
      </div>

      <div class="p-6 space-y-4">
        <div>
            <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-1">{{ t.name }}</label>
            <input v-model="form.custom_name" type="text" :placeholder="t.namePlaceholder" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>
        
        <div>
            <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-1">{{ t.lanUrl }}</label>
            <input v-model="form.lan_url" type="text" :placeholder="t.lanPlaceholder" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>
        
        <div>
            <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-1">{{ t.wanUrl }}</label>
            <input v-model="form.wan_url" type="text" :placeholder="t.wanPlaceholder" class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>
      </div>

      <div class="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3">
        <button @click="$emit('close')" class="px-4 py-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition">{{ t.cancel }}</button>
        <button @click="handleSave" class="px-6 py-2 text-white font-medium rounded-lg shadow-md transition" :style="{ backgroundColor: props.accentColor || '#3b82f6' }">{{ t.add }}</button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { updateService, uploadIcon, type Service } from '../api';

const props = defineProps<{ service: Service | null; accentColor?: string }>();
const emit = defineEmits(['close', 'update']);

// i18n
const lang = ref(localStorage.getItem('lang') || 'zh');
const t = computed(() => lang.value === 'zh' ? {
    editService: '编辑服务',
    general: '基本信息',
    network: '网络',
    displayName: '显示名称',
    iconUrl: '图标地址（可选）',
    uploadHint: '上传图片或粘贴URL',
    visible: '在列表中显示',
    lanUrl: '局域网地址',
    lanHint: '家庭/办公室内网访问地址',
    wanUrl: '公网地址',
    wanHint: '远程/外网访问地址',
    cancel: '取消',
    save: '保存更改',
    upload: '上传',
    noIcon: '无图标',
} : {
    editService: 'Edit Service',
    general: 'General',
    network: 'Network',
    displayName: 'Display Name',
    iconUrl: 'Icon URL (Optional)',
    uploadHint: 'Upload an image or paste a URL.',
    visible: 'Visible in list',
    lanUrl: 'LAN URL (Local Network)',
    lanHint: 'Used when accessing from home/office.',
    wanUrl: 'WAN URL (Public/Internet)',
    wanHint: 'Used when accessing remotely.',
    cancel: 'Cancel',
    save: 'Save Changes',
    upload: 'Upload',
    noIcon: 'No Icon',
});

const form = ref<Partial<Service>>({});
const activeTab = ref<'general' | 'network'>('general');
const isUploading = ref(false);

watch(() => props.service, (newVal) => {
    if (newVal) {
        form.value = { ...newVal };
    }
}, { immediate: true });

const displayIcon = computed(() => {
    const url = form.value.icon_url || props.service?.icon_url;
    if (url?.startsWith('http') || url?.startsWith('/')) return url;
    if (url) return url;
    return '';
});

const handleFileUpload = async (event: Event) => {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    
    isUploading.value = true;
    try {
        const url = await uploadIcon(file);
        form.value.icon_url = url;
    } catch (e) {
        alert("Upload Failed");
    } finally {
        isUploading.value = false;
    }
};

const save = async () => {
    if (!props.service) return;
    try {
        await updateService(props.service.id, form.value);
        emit('update');
        emit('close');
    } catch (e) {
        alert("Update failed.");
    }
};
</script>

<template>
  <div v-if="service" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-fade-in-up">
      
      <!-- Header -->
      <div class="bg-slate-50 dark:bg-slate-900 px-6 py-4 flex justify-between items-center border-b border-slate-200 dark:border-slate-700">
        <h2 class="text-lg font-bold text-slate-800 dark:text-slate-100">{{ t.editService }}</h2>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-2xl leading-none">&times;</button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-slate-200 dark:border-slate-700">
          <button 
            @click="activeTab = 'general'"
            class="flex-1 py-3 text-sm font-medium transition-colors"
            :class="activeTab === 'general' ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50 dark:bg-slate-800' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'"
          >
            {{ t.general }}
          </button>
          <button 
            @click="activeTab = 'network'"
            class="flex-1 py-3 text-sm font-medium transition-colors"
            :class="activeTab === 'network' ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50 dark:bg-slate-800' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'"
          >
            {{ t.network }}
          </button>
      </div>

      <!-- Body -->
      <div class="p-6 h-80 overflow-y-auto">
          
          <!-- General Tab -->
          <div v-if="activeTab === 'general'" class="space-y-4">
              <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-1">{{ t.displayName }}</label>
                  <input v-model="form.custom_name" type="text" class="input-base" :placeholder="service.title" />
              </div>
              
              <div class="flex items-start gap-4">
                  <div class="w-20 h-20 bg-slate-100 dark:bg-slate-900 rounded-lg flex items-center justify-center border border-dashed border-slate-300 dark:border-slate-600 overflow-hidden relative group">
                      <img v-if="displayIcon" :src="displayIcon" class="w-full h-full object-contain" />
                      <span v-else class="text-xs text-slate-400">{{ t.noIcon }}</span>
                      
                      <!-- Overlay Upload -->
                      <label class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                          <span class="text-white text-xs font-bold">{{ isUploading ? '...' : t.upload }}</span>
                          <input type="file" class="hidden" accept="image/*" @change="handleFileUpload"/>
                      </label>
                  </div>
                  <div class="flex-1">
                      <label class="block text-xs font-bold text-slate-500 uppercase mb-1">{{ t.iconUrl }}</label>
                      <input v-model="form.icon_url" type="text" class="input-base text-sm" placeholder="/static/icons/..." />
                      <p class="text-xs text-slate-400 mt-1">{{ t.uploadHint }}</p>
                  </div>
              </div>

              <div>
                  <label class="flex items-center gap-2 cursor-pointer">
                      <input v-model="form.is_visible" type="checkbox" class="w-4 h-4 rounded text-blue-600 focus:ring-blue-500" />
                      <span class="text-sm text-slate-700 dark:text-slate-300">{{ t.visible }}</span>
                  </label>
              </div>
          </div>

          <!-- Network Tab -->
          <div v-if="activeTab === 'network'" class="space-y-4">
              <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-1">{{ t.lanUrl }}</label>
                  <input v-model="form.lan_url" type="text" class="input-base" placeholder="http://192.168.1.x:port" />
                  <p class="text-xs text-slate-400 mt-1">{{ t.lanHint }}</p>
              </div>
              <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-1">{{ t.wanUrl }}</label>
                  <input v-model="form.wan_url" type="text" class="input-base" placeholder="https://myapp.example.com" />
                  <p class="text-xs text-slate-400 mt-1">{{ t.wanHint }}</p>
              </div>
          </div>
      </div>

      <!-- Footer -->
      <div class="bg-slate-50 dark:bg-slate-900 px-6 py-4 flex justify-end gap-3 border-t border-slate-200 dark:border-slate-700">
        <button @click="$emit('close')" class="px-4 py-2 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition">{{ t.cancel }}</button>
        <button @click="save" class="px-6 py-2 text-white font-medium rounded-lg shadow-md transition" :style="{ backgroundColor: props.accentColor || '#3b82f6' }">{{ t.save }}</button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.input-base {
    @apply w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 transition-shadow;
}
.animate-fade-in-up {
  animation: fadeInUp 0.3s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

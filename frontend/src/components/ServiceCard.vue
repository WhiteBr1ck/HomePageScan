<script setup lang="ts">
import { computed } from 'vue';
import type { Service } from '../api';

const props = defineProps<{
  service: Service;
  isAdmin: boolean;
  viewMode: 'grid' | 'list';
  isDeleteMode?: boolean;
  accentColor?: string;
}>();

const emit = defineEmits(['edit', 'delete']);

const handleDelete = (e: Event) => {
    e.stopPropagation();
    emit('delete');
};

const displayIcon = computed(() => {
    if (props.service.icon_url) {
        if (props.service.icon_url.startsWith('http') || props.service.icon_url.startsWith('/')) return props.service.icon_url;
        return props.service.icon_url;
    }
    return ''; 
});

const defaultUrl = computed(() => props.service.lan_url || props.service.url);
const wanUrl = computed(() => props.service.wan_url);

const openLink = (url: string | undefined) => {
    if(url) window.open(url, '_blank');
};

const displayUrl = computed(() => {
    const url = defaultUrl.value || '';
    try {
        const u = new URL(url);
        return u.host;
    } catch {
        return url;
    }
});

const displayWanUrl = computed(() => {
    if (!wanUrl.value) return '';
    try {
        const u = new URL(wanUrl.value);
        return u.host;
    } catch {
        return wanUrl.value;
    }
});

// Detect if service uses HTTPS (check both LAN and WAN URLs)
const isHttps = computed(() => {
    const lanUrl = props.service.lan_url || props.service.url || '';
    const wanUrl = props.service.wan_url || '';
    return lanUrl.startsWith('https://') || wanUrl.startsWith('https://');
});
</script>

<template>
  <!-- Grid View -->
  <div 
    v-if="viewMode === 'grid'"
    class="group bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl hover:border-blue-400 dark:hover:border-blue-500 transition-all duration-300 relative p-5 flex flex-col"
    style="min-height: 260px;"
  >
    <!-- Delete Badge (Top Right Corner) -->
    <button 
      v-if="isAdmin && isDeleteMode"
      @click.stop="handleDelete"
      class="absolute -top-2 -right-2 w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center z-50 shadow-lg hover:bg-red-600 hover:scale-110 transition-all"
      title="删除"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
    </button>

    <!-- Edit Button -->
    <button 
      v-if="isAdmin && !isDeleteMode"
      @click.stop="emit('edit')"
      class="absolute top-3 right-3 p-2 rounded-full bg-slate-100 dark:bg-slate-700 opacity-0 group-hover:opacity-100 transition-all hover:bg-blue-100 dark:hover:bg-blue-600 text-slate-400 hover:text-blue-600 dark:hover:text-white z-10"
      title="编辑"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
    </button>

    <!-- Icon -->
    <div class="w-14 h-14 mx-auto mb-3 bg-slate-100 dark:bg-slate-900 rounded-xl flex items-center justify-center overflow-hidden flex-shrink-0">
        <img v-if="displayIcon" :src="displayIcon" alt="Icon" class="w-full h-full object-contain" @error="($event.target as HTMLImageElement).style.display='none'" />
        <div v-else class="text-slate-300 dark:text-slate-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
        </div>
    </div>

    <!-- Title -->
    <h3 class="font-bold text-slate-800 dark:text-slate-100 text-center text-sm leading-tight line-clamp-2 mb-2">
        {{ service.custom_name || service.title || 'Unknown' }}
    </h3>
    
    <!-- LAN URL -->
    <p class="text-xs text-slate-500 text-center truncate mb-1" :title="defaultUrl">
        <span class="text-blue-500">LAN:</span> {{ displayUrl }}
    </p>
    
    <!-- WAN URL (if exists) -->
    <p v-if="wanUrl" class="text-xs text-slate-500 text-center truncate mb-2" :title="wanUrl">
        <span class="text-green-500">WAN:</span> {{ displayWanUrl }}
    </p>
    
    <!-- Meta: Port & Protocol -->
    <div class="flex items-center justify-center gap-2 mb-3">
         <span class="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded">{{ service.port }}</span>
         <span v-if="!isHttps" class="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded text-xs font-medium">HTTP</span>
         <span v-else class="px-1.5 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded text-xs font-medium flex items-center gap-0.5">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            HTTPS
         </span>
    </div>

    <!-- Spacer -->
    <div class="flex-1"></div>

    <!-- Action Buttons -->
    <div class="flex gap-2 mt-auto">
         <button 
            @click.stop="openLink(defaultUrl)"
            class="flex-1 px-3 py-2 text-xs font-bold text-white rounded-lg shadow-sm transition-colors text-center"
            :style="{ backgroundColor: accentColor || '#3b82f6' }"
         >
            LAN
         </button>
         <button 
            v-if="wanUrl"
            @click.stop="openLink(wanUrl)"
            class="flex-1 px-3 py-2 text-xs font-bold text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm transition-colors text-center"
         >
            WAN
         </button>
    </div>
  </div>

  <!-- List View -->
  <div 
    v-else
    class="group bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-lg hover:border-blue-400 transition-all duration-200 p-4 flex items-center gap-4 relative"
  >
    <!-- Delete Badge (Top Right Corner) -->
    <button 
      v-if="isAdmin && isDeleteMode"
      @click.stop="handleDelete"
      class="absolute -top-2 -right-2 w-7 h-7 bg-red-500 text-white rounded-full flex items-center justify-center z-50 shadow-lg hover:bg-red-600 hover:scale-110 transition-all"
      title="删除"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
    </button>

    <!-- Icon -->
    <div class="w-12 h-12 flex-shrink-0 bg-slate-100 dark:bg-slate-900 rounded-xl flex items-center justify-center overflow-hidden">
        <img v-if="displayIcon" :src="displayIcon" alt="Icon" class="w-full h-full object-contain" @error="($event.target as HTMLImageElement).style.display='none'" />
        <span v-else class="text-slate-300 text-xs font-bold">WEB</span>
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0">
        <h3 class="font-bold text-slate-800 dark:text-slate-100 text-base truncate">
            {{ service.custom_name || service.title || 'Unknown' }}
        </h3>
        <div class="flex items-center gap-3 mt-1 text-xs text-slate-400">
            <span><span class="text-blue-500">LAN:</span> {{ displayUrl }}</span>
            <span v-if="wanUrl"><span class="text-green-500">WAN:</span> {{ displayWanUrl }}</span>
        </div>
        <div class="flex items-center gap-2 mt-1">
             <span class="text-xs font-mono text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-600 px-1.5 py-0.5 rounded">{{ service.port }}</span>
             <span v-if="isHttps" class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-400">HTTPS</span>
             <span v-else class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-600 text-slate-500 dark:text-slate-400">HTTP</span>
        </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2 flex-shrink-0">
         <button 
            @click.stop="openLink(defaultUrl)"
            class="px-4 py-2 text-xs font-bold text-white rounded-lg shadow-sm transition-colors"
            :style="{ backgroundColor: accentColor || '#3b82f6' }"
         >
            LAN
         </button>
         <button 
            v-if="wanUrl"
            @click.stop="openLink(wanUrl)"
            class="px-4 py-2 text-xs font-bold text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm transition-colors"
         >
            WAN
         </button>
         <button 
            v-if="isAdmin && !isDeleteMode"
            @click.stop="emit('edit')"
            class="p-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
         >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
         </button>
    </div>
  </div>
</template>

<style scoped>
@keyframes bounceIn {
  0% { transform: scale(0); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
</style>

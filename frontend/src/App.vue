<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { getServices, triggerScan, getProfiles, createProfile, deleteProfile, reorderServices, deleteService, getAppSettings, type Service, type Profile, type AppSettings } from './api';
import ServiceCard from './components/ServiceCard.vue';
import LoginModal from './components/LoginModal.vue';
import EditModal from './components/EditModal.vue';
import SettingsModal from './components/SettingsModal.vue';
import AddServiceModal from './components/AddServiceModal.vue';
import Notification from './components/Notification.vue';
import ConfirmModal from './components/ConfirmModal.vue';
import api from './api';
import draggable from 'vuedraggable';

// --- i18n ---
const lang = ref<'zh' | 'en'>(localStorage.getItem('lang') as 'zh' | 'en' || 'zh');
const t = computed(() => lang.value === 'zh' ? {
    login: '登录',
    scan: '扫描',
    scanning: '扫描中...',
    newProfile: '新建配置',
    noServices: '暂无服务',
    scanHint: '点击"扫描"按钮检测服务',
    profileName: '配置名称',
    switchedTo: '已切换到',
    profileCreated: '配置已创建',
    profileDeleted: '配置已删除',
    scanStarted: '扫描已启动',
    scanFailed: '扫描失败',
    scanComplete: '扫描完成',
    cannotDeleteDefault: '无法删除默认配置',
    confirmDelete: '确定删除配置',
    andAllServices: '及其所有服务吗？',
    gridView: '网格视图',
    listView: '列表视图',
    addService: '添加服务',
    sortBy: '排序方式',
    sortName: '按名称',
    sortPort: '按端口',
    sortCustom: '自定义',
    deleteProfile: '删除当前配置',
    settings: '设置',
    serviceAdded: '服务已添加',
    totalServices: '个服务',
    dragHint: '拖拽卡片可自定义排序',
    scanLogs: '扫描日志',
    hideLogs: '隐藏日志',
    showLogs: '显示日志',
    toggleEdit: '编辑模式',
    confirmDeleteService: '确定要删除该服务吗？',
    deleted: '已删除',
    deleteAll: '全部删除',
    confirmDeleteAll: '确定要删除所有服务吗？',
    saveChanges: '保存更改',
    reset: '重置默认',
    cancel: '取消',
    confirm: '确定',
    edit: '编辑',
} : {
    login: 'Login',
    scan: 'SCAN',
    scanning: 'SCANNING...',
    newProfile: 'New Profile',
    noServices: 'No services discovered',
    scanHint: 'Hit SCAN to detect services.',
    profileName: 'Profile Name',
    switchedTo: 'Switched to',
    profileCreated: 'Profile Created',
    profileDeleted: 'Profile Deleted',
    scanStarted: 'Scan started for',
    scanFailed: 'Scan failed',
    scanComplete: 'Scan Complete',
    cannotDeleteDefault: 'Cannot delete default profile',
    confirmDelete: 'Delete profile',
    andAllServices: 'and all its services?',
    gridView: 'Grid View',
    listView: 'List View',
    addService: 'Add Service',
    sortBy: 'Sort by',
    sortName: 'Name',
    sortPort: 'Port',
    sortCustom: 'Custom',
    deleteProfile: 'Delete Profile',
    settings: 'Settings',
    serviceAdded: 'Service Added',
    totalServices: 'services',
    dragHint: 'Drag cards to reorder',
    scanLogs: 'Scan Logs',
    hideLogs: 'Hide Logs',
    showLogs: 'Show Logs',
    toggleEdit: 'Edit Mode',
    confirmDeleteService: 'Are you sure you want to delete this service?',
    deleted: 'Deleted',
    deleteAll: 'Delete All',
    confirmDeleteAll: 'Are you sure you want to delete all services?',
    saveChanges: 'Save Changes',
    reset: 'Reset to Default',
    cancel: 'Cancel',
    confirm: 'Confirm',
    edit: 'Edit',
});

const handleLangChange = (newLang: 'zh' | 'en') => {
    lang.value = newLang;
    localStorage.setItem('lang', newLang);
};

// --- State ---
const services = ref<Service[]>([]);
const currentProfile = ref<Profile>();
const appSettings = ref<AppSettings>(); // Global site branding
const profiles = ref<Profile[]>([]);
const currentProfileId = ref<number>(1);

const isLoggedIn = ref(!!localStorage.getItem('token'));
const showLogin = ref(false);
const showSettings = ref(false);
// Theme & View settings
const themeMode = ref<'light' | 'dark' | 'auto'>(appSettings.value?.theme_mode || 'auto');
const viewMode = ref<'grid' | 'list'>(appSettings.value?.view_mode || 'grid');
const gridSize = ref<'small' | 'medium' | 'large'>(appSettings.value?.grid_size || 'medium');
const accentColor = ref<string>(appSettings.value?.accent_color || '#3b82f6');
const showColorPicker = ref(false);
const presetColors = [
    { name: 'Blue', value: '#3b82f6' },
    { name: 'Purple', value: '#8b5cf6' },
    { name: 'Pink', value: '#ec4899' },
    { name: 'Red', value: '#ef4444' },
    { name: 'Orange', value: '#f97316' },
    { name: 'Yellow', value: '#eab308' },
    { name: 'Green', value: '#10b981' },
    { name: 'Teal', value: '#14b8a6' },
    { name: 'Cyan', value: '#06b6d4' },
    { name: 'Indigo', value: '#6366f1' },
    { name: 'Rose', value: '#f43f5e' },
    { name: 'Emerald', value: '#059669' },
];
const showAddService = ref(false);
const showProfileMenu = ref(false);

const editingService = ref<Service | null>(null);
const targetIP = ref('127.0.0.1');

const isScanning = ref(false);
const notification = ref<{message: string, type: 'success' | 'error' | 'info'} | null>(null);
const isEditMode = ref(false); // Edit Mode (drag, delete)
const showDeleteConfirm = ref(false);
const pendingDeleteService = ref<Service | null>(null);
const showDeleteAllConfirm = ref(false);
const showConfirm = ref(false);
const confirmMessage = ref('');
const confirmCallback = ref<(() => void) | null>(null);

// Scan progress
const scanProgress = ref(0);
const scanLogs = ref<string[]>([]);
const showLogs = ref(true);

// Draggable local state (to fix computed property mutation issue)
const dragServices = ref<Service[]>([]);

let refreshInterval: number;
let scanEventSource: EventSource | null = null;

const sortedServices = computed(() => {
    // Services are always sorted by sort_order from the backend
    return [...services.value].sort((a, b) => (b.sort_order || 0) - (a.sort_order || 0));
});

// Watch services to update draggable list (only when not actively editing)
watch(services, (newVal) => {
    console.log('🔄 Services changed, isEditMode:', isEditMode.value, 'newVal length:', newVal.length);
    // Only sync if not in edit mode to prevent resetting during drag
    if (!isEditMode.value) {
        dragServices.value = [...newVal];
        console.log('✅ Updated dragServices');
    } else {
        console.log('⚠️ Skipped dragServices update (in edit mode)');
    }
}, { immediate: true });

// Grid classes based on size
const gridClasses = computed(() => {
    if (viewMode.value === 'list') return 'grid-cols-1';
    const sizeMap = {
        small: 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6',
        medium: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
        large: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3'
    };
    return sizeMap[gridSize.value];
});

// Theme application
const applyTheme = () => {
    const html = document.documentElement;
    if (themeMode.value === 'dark') {
        html.classList.add('dark');
    } else if (themeMode.value === 'light') {
        html.classList.remove('dark');
    } else { // auto
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
    }
};

// Save theme and view preferences
const saveThemePreferences = async () => {
    // Always save to localStorage as backup
    localStorage.setItem('theme_mode', themeMode.value);
    localStorage.setItem('view_mode', viewMode.value);
    localStorage.setItem('grid_size', gridSize.value);
    localStorage.setItem('accent_color', accentColor.value);
    
    const token = localStorage.getItem('token');
    if (!token) {
        console.log('Not logged in, saved to localStorage only');
        return;
    }
    try {
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                theme_mode: themeMode.value,
                view_mode: viewMode.value,
                grid_size: gridSize.value,
                accent_color: accentColor.value
            })
        });
        if (response.ok) {
            console.log('✅ Theme preferences saved to server');
        }
    } catch (e) {
        console.error('Failed to save preferences:', e);
    }
};

const saveViewPreferences = () => {
    saveThemePreferences();
};

// Watch theme mode changes
watch(themeMode, () => {
    applyTheme();
    saveThemePreferences();
});

// Watch view mode and grid size changes
watch([viewMode, gridSize], () => {
    saveThemePreferences();
});

// Helper function to convert hex to RGB
const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
};

// Helper to generate color shades from base color
const generateColorShades = (baseColor: string) => {
    const rgb = hexToRgb(baseColor);
    if (!rgb) return;
    
    const shades = {
        50: `${Math.min(255, rgb.r + 200)} ${Math.min(255, rgb.g + 200)} ${Math.min(255, rgb.b + 200)}`,
        100: `${Math.min(255, rgb.r + 160)} ${Math.min(255, rgb.g + 160)} ${Math.min(255, rgb.b + 160)}`,
        200: `${Math.min(255, rgb.r + 120)} ${Math.min(255, rgb.g + 120)} ${Math.min(255, rgb.b + 120)}`,
        300: `${Math.min(255, rgb.r + 80)} ${Math.min(255, rgb.g + 80)} ${Math.min(255, rgb.b + 80)}`,
        400: `${Math.min(255, rgb.r + 40)} ${Math.min(255, rgb.g + 40)} ${Math.min(255, rgb.b + 40)}`,
        500: `${rgb.r} ${rgb.g} ${rgb.b}`,
        600: `${Math.max(0, rgb.r - 20)} ${Math.max(0, rgb.g - 20)} ${Math.max(0, rgb.b - 20)}`,
        700: `${Math.max(0, rgb.r - 40)} ${Math.max(0, rgb.g - 40)} ${Math.max(0, rgb.b - 40)}`,
        800: `${Math.max(0, rgb.r - 60)} ${Math.max(0, rgb.g - 60)} ${Math.max(0, rgb.b - 60)}`,
        900: `${Math.max(0, rgb.r - 80)} ${Math.max(0, rgb.g - 80)} ${Math.max(0, rgb.b - 80)}`,
    };
    
    Object.entries(shades).forEach(([shade, value]) => {
        document.documentElement.style.setProperty(`--color-primary-${shade}`, value);
    });
};

// Watch accent color changes  
watch(accentColor, () => {
    generateColorShades(accentColor.value);
    saveThemePreferences();
});

// Listen to system theme changes when in auto mode
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
mediaQuery.addEventListener('change', () => {
    if (themeMode.value === 'auto') {
        applyTheme();
    }
});

const handleQuickDelete = async (service: Service) => {
    console.log('🗑️ handleQuickDelete called, isEditMode:', isEditMode.value, 'service:', service.id);
    if (!isEditMode.value) {
        // In normal mode, use the standard delete confirm
        console.log('📝 Normal mode - showing confirm dialog');
        pendingDeleteService.value = service;
        showDeleteConfirm.value = true;
    } else {
        // In edit mode, delete immediately without confirm
        console.log('✂️ Edit mode - deleting service directly');
        const beforeLength = dragServices.value.length;
        try {
            console.log('📤 Calling API to delete service', service.id);
            await deleteService(service.id);
            console.log('✅ Delete successful');
            // Remove from dragServices
            dragServices.value = dragServices.value.filter(s => s.id !== service.id);
            console.log(`Removed from dragServices: ${beforeLength} -> ${dragServices.value.length}`);
            showToast(t.value.deleted, 'success');
        } catch (e) {
            console.error('❌ Delete failed:', e);
            showToast('Delete failed', 'error');
        }
    }
};

// Native HTML5 drag and drop handlers
let draggedService: Service | null = null;

const dragStart = (e: DragEvent, service: Service) => {
    console.log('🎯 Drag started:', service.id);
    draggedService = service;
    if (e.dataTransfer) {
        e.dataTransfer.effectAllowed = 'move';
    }
};

const drop = (e: DragEvent, targetService: Service) => {
    e.preventDefault();
    if (!draggedService || draggedService.id === targetService.id) return;
    
    console.log('📍 Drop:', draggedService.id, 'onto', targetService.id);
    
    // Reorder dragServices
    const draggedIndex = dragServices.value.findIndex(s => s.id === draggedService!.id);
    const targetIndex = dragServices.value.findIndex(s => s.id === targetService.id);
    
    if (draggedIndex !== -1 && targetIndex !== -1) {
        const newServices = [...dragServices.value];
        const [removed] = newServices.splice(draggedIndex, 1);
        newServices.splice(targetIndex, 0, removed);
        dragServices.value = newServices;
        console.log('✅ Reordered:', dragServices.value.map(s => s.id));
    }
    
    draggedService = null;
};

const onDragEnd = async () => {
    console.log('🎯 Drag ended, new order:', dragServices.value.map(s => s.id));
    // Don't save automatically - let user click "Save Changes" button
    // This prevents state sync issues with the draggable component
};

const confirmDelete = async () => {
    if (!pendingDeleteService.value) return;
    console.log('🗑️ confirmDelete called for service:', pendingDeleteService.value.id);
    try {
        console.log('📤 Calling API delete');
        await deleteService(pendingDeleteService.value.id);
        console.log('✅ Delete successful, fetching services');
        showToast(t.value.deleted, 'success');
        await fetchServices();
        console.log('✅ Services refreshed');
    } catch (e) {
        console.error('❌ Delete failed:', e);
        showToast('Delete failed', 'error');
    } finally {
        showDeleteConfirm.value = false;
        pendingDeleteService.value = null;
    }
};

const cancelDelete = () => {
    showDeleteConfirm.value = false;
    pendingDeleteService.value = null;
};

const handleDeleteAll = () => {
    showDeleteAllConfirm.value = true;
};

const confirmDeleteAll = async () => {
    showDeleteAllConfirm.value = false;
    try {
        // Delete all services in current profile
        const deletePromises = sortedServices.value.map(s => deleteService(s.id));
        await Promise.all(deletePromises);
        showToast(lang.value === 'zh' ? '全部服务已删除' : 'All services deleted', 'success');
        await fetchServices();
    } catch (e) {
        showToast('Failed to delete all', 'error');
    }
};

const saveOrder = async () => {
    console.log('💾 saveOrder called, dragServices:', dragServices.value.map(s => s.id));
    const orderedIds = dragServices.value.map(s => s.id);
    try {
        console.log('📤 Saving order:', orderedIds);
        await reorderServices(orderedIds);
        console.log('✅ Order saved, fetching services');
        await fetchServices();
        console.log('✅ Services fetched, exiting edit mode');
        // The order is already saved on drag, so just exit edit mode
        isEditMode.value = false;
        showToast(t.value.saveChanges, 'success');
    } catch (e) {
        console.error('❌ Save order failed:', e);
        showToast(lang.value === 'zh' ? '保存失败' : 'Save failed', 'error');
    }
};

// Sort helpers for edit mode
const sortByName = () => {
    dragServices.value = [...dragServices.value].sort((a, b) => 
        (a.custom_name || a.title || '').localeCompare(b.custom_name || b.title || '')
    );
};

const sortByPort = () => {
    dragServices.value = [...dragServices.value].sort((a, b) => a.port - b.port);
};

const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    notification.value = { message, type };
};

const loadData = async () => {
    try {
        // Fetch app settings (site branding)
        appSettings.value = await getAppSettings();
        
        // Apply saved settings from server or localStorage fallback
        if (appSettings.value?.theme_mode) {
            themeMode.value = appSettings.value.theme_mode;
        } else {
            const saved = localStorage.getItem('theme_mode');
            if (saved) themeMode.value = saved as 'light' | 'dark' | 'auto';
        }
        if (appSettings.value?.view_mode) {
            viewMode.value = appSettings.value.view_mode;
        } else {
            const saved = localStorage.getItem('view_mode');
            if (saved) viewMode.value = saved as 'grid' | 'list';
        }
        if (appSettings.value?.grid_size) {
            gridSize.value = appSettings.value.grid_size;
        } else {
            const saved = localStorage.getItem('grid_size');
            if (saved) gridSize.value = saved as 'small' | 'medium' | 'large';
        }
        if (appSettings.value?.accent_color) {
            accentColor.value = appSettings.value.accent_color;
        } else {
            const saved = localStorage.getItem('accent_color');
            if (saved) accentColor.value = saved;
        }
        applyTheme();
        generateColorShades(accentColor.value);
        
        // Fetch profiles
        const profs = await getProfiles();
        profiles.value = profs;
        if (profs.length > 0) {
            // If currentProfileId is not valid, or no currentProfile is set, default to the first profile
            if (!profs.find(p => p.id === currentProfileId.value) || !currentProfile.value) {
                currentProfileId.value = profs[0].id;
                currentProfile.value = profs[0];
            } else {
                // Ensure currentProfile ref is updated if currentProfileId is valid
                currentProfile.value = profs.find(p => p.id === currentProfileId.value);
            }
            if(currentProfile.value?.scan_target) targetIP.value = currentProfile.value.scan_target;
        } else {
            currentProfile.value = undefined; // No profiles
            currentProfileId.value = 0;
        }
        await fetchServices();
    } catch(e) {
        console.error('Load data failed:', e);
    }
};

// Settings modal ref and confirmation handlers
const settingsModalRef = ref<any>(null);

const confirmSaveSettings = () => {
    confirmMessage.value = lang.value === 'zh' ? '确定要保存站点设置吗？' : 'Save site settings?';
    confirmCallback.value = () => {
        settingsModalRef.value?.doSaveSiteSettings();
    };
    showConfirm.value = true;
};

const confirmResetSettings = () => {
    confirmMessage.value = lang.value === 'zh' ? '确定要重置站点设置为默认值吗？' : 'Reset site settings to default?';
    confirmCallback.value = () => {
        settingsModalRef.value?.doResetSiteSettings();
    };
    showConfirm.value = true;
};

const fetchServices = async () => {
  try {
      if(currentProfileId.value) {
          services.value = await getServices(currentProfileId.value);
      } else {
          services.value = []; // No profile selected
      }
  } catch(e) { /* Silent */ }
};

const handleProfileChange = async (id: number) => {
    showProfileMenu.value = false;
    currentProfileId.value = id;
    if(currentProfile.value?.scan_target) targetIP.value = currentProfile.value.scan_target;
    await fetchServices();
    showToast(`${t.value.switchedTo} ${currentProfile.value?.name}`, 'info');
};

const handleCreateProfile = async () => {
    showProfileMenu.value = false;
    const name = prompt(t.value.profileName + ":");
    if(name) {
        try {
            await createProfile({ name });
            showToast(t.value.profileCreated, "success");
            await loadData();
        } catch(e) {
            showToast("Failed to create profile", "error");
        }
    }
}

const handleDeleteProfile = async () => {
    showProfileMenu.value = false;
    if(!currentProfile.value || currentProfile.value.name === "Default") {
        showToast(t.value.cannotDeleteDefault, "error");
        return;
    }
    if(confirm(`${t.value.confirmDelete} "${currentProfile.value.name}" ${t.value.andAllServices}`)) {
        try {
            await deleteProfile(currentProfileId.value);
            showToast(t.value.profileDeleted, "success");
            currentProfileId.value = 1;
            await loadData();
        } catch(e) {
            showToast("Delete failed", "error");
        }
    }
}

const handleScan = async () => {
  if (!isLoggedIn.value) {
    showLogin.value = true;
    return;
  }
  
  if (isScanning.value) return;
  
  isScanning.value = true;
  scanProgress.value = 0;
  scanLogs.value = [];
  showLogs.value = true;

  try {
    if (scanEventSource) scanEventSource.close();
    scanEventSource = new EventSource('/api/scan/stream');
    
    scanEventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        scanProgress.value = data.progress;
        
        // Append new logs
        if (data.logs && data.logs.length > 0) {
             // Simple diff: replace if significantly different, or just use latest
             scanLogs.value = data.logs;
        }

        if (data.completed) {
            isScanning.value = false;
            scanEventSource?.close();
            fetchServices();
            showToast(t.value.scanComplete, "success");
        }
    };
    
    scanEventSource.onerror = () => {
        scanEventSource?.close();
        isScanning.value = false;
    };

    await triggerScan(targetIP.value, currentProfileId.value);
    
  } catch (e) {
    isScanning.value = false;
    scanEventSource?.close();
    showToast(t.value.scanFailed, "error");
  }
};

const handleAddService = async (data: any) => {
    showAddService.value = false;
    try {
        let ip = '0.0.0.0';
        let port = data.port || 80;
        try {
            const url = new URL(data.lan_url);
            ip = url.hostname;
            port = url.port ? parseInt(url.port) : (url.protocol === 'https:' ? 443 : 80);
        } catch {}
        
        await api.post('/services/manual', {
            profile_id: currentProfileId.value,
            custom_name: data.custom_name,
            lan_url: data.lan_url,
            wan_url: data.wan_url || null,
            port: port,
            ip: ip,
            protocol: data.lan_url.startsWith('https') ? 'https' : 'http',
            url: data.lan_url,
            title: data.custom_name,
        });
        showToast(t.value.serviceAdded, "success");
        await fetchServices();
    } catch (e) {
        showToast("Failed to add service", "error");
    }
};

const logout = () => {
    showSettings.value = false;
    localStorage.removeItem('token');
    isLoggedIn.value = false;
};

const handleLogout = logout;

const onLoginSuccess = () => {
    isLoggedIn.value = true;
    loadData();
};

onMounted(() => {
    loadData();
    refreshInterval = setInterval(() => {
        if(!isScanning.value) fetchServices();
    }, 5000) as any;
    updatePageBranding(); // Initial update
});

onUnmounted(() => {
    clearInterval(refreshInterval);
    if(scanEventSource) scanEventSource.close();
});

// Watch for app settings changes and update page branding
watch(appSettings, () => {
    updatePageBranding();
}, { deep: true });

// Function to update page title and favicon
const updatePageBranding = () => {
    if (!appSettings.value) return;
    
    // Update document title
    document.title = appSettings.value.site_title || 'HomePageScan';
    
    // Update favicon
    let link: HTMLLinkElement | null = document.querySelector("link[rel~='icon']");
    if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
    }
    
    if (appSettings.value.site_icon_url) {
        link.href = appSettings.value.site_icon_url.startsWith('http') 
            ? appSettings.value.site_icon_url 
            : appSettings.value.site_icon_url;
    } else {
        // Default favicon
        link.href = '/favicon.svg';
    }
};
</script>

<template>
  <div class="min-h-screen bg-slate-100 dark:bg-slate-900 font-sans text-slate-900 dark:text-slate-100 pb-20 transition-colors duration-300">
    <Notification v-if="notification" :message="notification.message" :type="notification.type" @close="notification = null" />

    <!-- Navbar -->
    <header class="bg-white dark:bg-slate-800 shadow-sm sticky top-0 z-40 border-b border-slate-200 dark:border-slate-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        
        <!-- Left: Logo & Profile -->
        <div class="flex items-center gap-3">
            <div v-if="appSettings?.site_icon_url" class="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center">
                <img :src="appSettings.site_icon_url.startsWith('http') ? appSettings.site_icon_url : appSettings.site_icon_url" alt="Logo" class="w-full h-full object-cover" />
            </div>
            <div v-else class="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center">
                <img src="/favicon.svg" alt="Logo" class="w-full h-full object-cover" />
            </div>
            <span class="font-bold text-lg text-slate-800 dark:text-white hidden sm:block">{{ appSettings?.site_title || 'HomePageScan' }}</span>
            
            <div class="relative" v-if="isLoggedIn">
                <button 
                    @click="showProfileMenu = !showProfileMenu"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                    <span>{{ currentProfile?.name || 'Default' }}</span>
                    <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                </button>
                
                <!-- Backdrop to close menu -->
                <div v-if="showProfileMenu" class="fixed inset-0 z-40" @click="showProfileMenu = false"></div>
                <div v-if="showProfileMenu" class="absolute left-0 mt-2 w-52 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 py-2 z-50">
                    <button 
                        v-for="p in profiles" 
                        :key="p.id"
                        @click="handleProfileChange(p.id)"
                        class="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
                        :class="p.id === currentProfileId ? 'text-blue-600 font-bold bg-blue-50 dark:bg-blue-900/20' : 'text-slate-700 dark:text-slate-300'"
                    >
                        <span class="w-2 h-2 rounded-full" :class="p.id === currentProfileId ? 'bg-blue-500' : 'bg-transparent'"></span>
                        {{ p.name }}
                    </button>
                    <div class="border-t border-slate-200 dark:border-slate-700 my-1"></div>
                    <button @click="handleCreateProfile" class="w-full text-left px-4 py-2.5 text-sm text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                        {{ t.newProfile }}
                    </button>
                    <button @click="handleDeleteProfile" class="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2">
                         <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        {{ t.deleteProfile }}
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Right: Controls -->
        <div class="flex items-center gap-2">
             <!-- Scan Bar -->
             <div class="flex items-center bg-slate-100 dark:bg-slate-700 rounded-lg overflow-hidden" v-if="isLoggedIn">
                <input v-model="targetIP" class="bg-transparent border-none outline-none text-sm w-40 px-3 py-2 text-slate-700 dark:text-slate-200" placeholder="192.168.1.1" />
                <button @click="handleScan" :disabled="isScanning" class="text-white px-4 py-2 text-sm font-medium transition-all flex items-center gap-1.5 disabled:opacity-50" :style="{ backgroundColor: accentColor }">
                    <svg v-if="isScanning" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span>{{ isScanning ? t.scanning : t.scan }}</span>
                </button>
            </div>

             <!-- Theme Toggle -->
             <div class="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-700 rounded-lg">
                <button @click="themeMode = 'light'" class="p-1.5 rounded transition-colors" :class="themeMode === 'light' ? 'bg-white text-yellow-500 shadow' : 'text-slate-400'" title="Light"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg></button>
                <button @click="themeMode = 'dark'" class="p-1.5 rounded transition-colors" :class="themeMode === 'dark' ? 'bg-white text-purple-500 shadow' : 'text-slate-400'" title="Dark"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg></button>
                <button @click="themeMode = 'auto'" class="p-1.5 rounded transition-colors" :class="themeMode === 'auto' ? 'bg-white text-blue-500 shadow' : 'text-slate-400'" title="Auto"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg></button>
             </div>
             <!-- Color Picker -->
             <div class="relative">
                <button @click="showColorPicker = !showColorPicker" class="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 transition"><div class="w-5 h-5 rounded" :style="{ backgroundColor: accentColor }"></div></button>
                <!-- Backdrop to close picker -->
                <div v-if="showColorPicker" class="fixed inset-0 z-40" @click="showColorPicker = false"></div>
                <div v-if="showColorPicker" class="absolute top-full right-0 mt-2 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 p-4 z-50 w-48"><div class="text-xs font-medium text-slate-600 dark:text-slate-400 mb-3">{{ lang === 'zh' ? '强调色' : 'Accent Color' }}</div><div class="grid grid-cols-3 gap-3"><button v-for="color in presetColors" :key="color.value" @click="accentColor = color.value; showColorPicker = false" class="w-8 h-8 rounded-lg border-2 hover:scale-110 transition" :class="accentColor === color.value ? 'border-slate-400 ring-2' : 'border-transparent'" :style="{ backgroundColor: color.value }" :title="color.name"></button></div></div>
             </div>

            <!-- Settings -->
            <button v-if="isLoggedIn" @click="showSettings = true" class="p-2 text-slate-400 hover:text-blue-600 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors" :title="t.settings">
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            </button>

            <button v-if="!isLoggedIn" @click="showLogin = true" class="text-sm font-semibold text-white px-4 py-2 rounded-lg transition-colors" :style="{ backgroundColor: accentColor }">{{ t.login }}</button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        <!-- Scan Progress -->
        <div v-if="isScanning" class="mb-6 bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700 animate-fade-in-down">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-3">
                    <span class="relative flex h-3 w-3">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                    </span>
                    <h3 class="font-bold text-slate-800 dark:text-white">{{ t.scanning }}</h3>
                </div>
                <div class="text-xs font-mono text-slate-500">{{ scanProgress }}%</div>
            </div>
            <div class="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden mb-3">
                <div class="h-full bg-blue-500 transition-all duration-300 ease-out" :style="{ width: scanProgress + '%' }"></div>
            </div>
            <button @click="showLogs = !showLogs" class="text-xs text-blue-500 hover:text-blue-600 mb-2">
                {{ showLogs ? t.hideLogs : t.showLogs }}
            </button>
             <div v-if="showLogs" class="bg-black/90 rounded-lg p-3 font-mono text-xs text-green-400 h-32 overflow-y-auto custom-scrollbar">
                <div v-for="(log, i) in scanLogs" :key="i" class="whitespace-nowrap">> {{ log }}</div>
            </div>
        </div>

        <!-- Toolbar (only for logged in users) -->
        <div v-if="isLoggedIn && sortedServices.length > 0" class="mb-6 flex flex-wrap items-center justify-between gap-4 bg-white dark:bg-slate-800 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
            <div class="flex items-center justify-between gap-4">
                <div class="flex items-center gap-4">
                    <!-- Profile Selector -->
                    <div v-if="isLoggedIn && profiles.length > 1" class="relative">
                        <button @click="showProfileMenu = !showProfileMenu" class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors text-sm font-medium text-slate-700 dark:text-slate-300">
                            <span>{{ currentProfile?.name }}</span>
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                        </button>
                        
                        <div v-if="showProfileMenu" class="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 py-1 z-50">
                            <button v-for="profile in profiles" :key="profile.id" @click="handleProfileChange(profile.id); showProfileMenu = false" class="w-full px-4 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center justify-between" :class="profile.id === currentProfileId ? 'text-blue-600 font-medium' : 'text-slate-700 dark:text-slate-300'">
                                <span>{{ profile.name }}</span>
                                <svg v-if="profile.id === currentProfileId" class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" /></svg>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Edit Mode Toolbar -->
                <div v-if="isLoggedIn && services.length > 0" class="flex items-center gap-2">
                    <!-- Edit Mode Toggle Button with Icon -->
                    <button 
                        v-if="!isEditMode"
                        @click="isEditMode = true"
                        class="p-2 rounded-lg transition-colors border flex items-center gap-2 bg-white dark:bg-slate-700 text-slate-500 border-slate-200 dark:border-slate-600 hover:text-blue-500"
                        :title="t.toggleEdit"
                    >
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                        <span class="text-sm font-medium hidden sm:inline">{{ lang === 'zh' ? '编辑' : 'Edit' }}</span>
                    </button>
                    
                    <template v-if="isEditMode">
                        <!-- Sort helpers in edit mode with better styling -->
                        <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-700 rounded-lg p-1">
                            <span class="text-sm text-slate-500 pl-2 font-medium">{{ t.sortBy }}:</span>
                            <button @click="sortByName" class="px-3 py-1.5 text-sm font-medium rounded-md transition-all text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-600 hover:shadow">
                                {{ t.sortName }}
                            </button>
                            <button @click="sortByPort" class="px-3 py-1.5 text-sm font-medium rounded-md transition-all text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-600 hover:shadow">
                                {{ t.sortPort }}
                            </button>
                        </div>
                        
                        <div class="h-6 w-px bg-slate-300 dark:bg-slate-600"></div>
                        
                        <!-- View Mode -->
                        <div class="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-700 rounded-lg">
                           <button @click="viewMode = 'grid'" class="p-1.5 rounded transition" :class="viewMode === 'grid' ? 'bg-white shadow' : 'text-slate-400'" :style="viewMode === 'grid' ? { color: accentColor } : {}" title="Grid"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg></button>
                           <button @click="viewMode = 'list'" class="p-1.5 rounded transition" :class="viewMode === 'list' ? 'bg-white shadow' : 'text-slate-400'" :style="viewMode === 'list' ? { color: accentColor } : {}" title="List"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg></button>
                        </div>
                        <!-- Grid Size -->
                        <div v-if="viewMode === 'grid'" class="flex gap-1 p-1 bg-slate-100 dark:bg-slate-700 rounded-lg">
                           <button @click="gridSize = 'small'" class="px-2 py-1.5 text-xs font-medium rounded" :class="gridSize === 'small' ? 'bg-white shadow' : 'text-slate-400'" :style="gridSize === 'small' ? { color: accentColor } : {}">S</button>
                           <button @click="gridSize = 'medium'" class="px-2 py-1.5 text-xs font-medium rounded" :class="gridSize === 'medium' ? 'bg-white shadow' : 'text-slate-400'" :style="gridSize === 'medium' ? { color: accentColor } : {}">M</button>
                           <button @click="gridSize = 'large'" class="px-2 py-1.5 text-xs font-medium rounded" :class="gridSize === 'large' ? 'bg-white shadow' : 'text-slate-400'" :style="gridSize === 'large' ? { color: accentColor } : {}">L</button>
                        </div>
                        
                        <div class="h-6 w-px bg-slate-300 dark:bg-slate-600"></div>
                        
                        <button 
                            @click="handleDeleteAll"
                            class="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 border border-red-200 dark:border-red-800 text-sm font-medium hover:bg-red-100 transition-colors flex items-center gap-1.5"
                        >
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                            {{ t.deleteAll }}
                        </button>
                        <button 
                            @click="saveOrder"
                            class="px-3 py-2 rounded-lg text-white text-sm font-medium transition-colors flex items-center gap-1.5"
                            :style="{ backgroundColor: accentColor }"
                        >
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                            {{ t.saveChanges }}
                        </button>
                    </template>
                </div>
                
                <button v-if="isLoggedIn" @click="showAddService = true" class="flex items-center gap-1.5 px-4 py-2 text-white text-sm font-medium rounded-lg transition-colors" :style="{ backgroundColor: accentColor }">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                    {{ t.addService }}
                </button>
            </div>
        </div>

        <p v-if="isLoggedIn && services.length > 0 && isEditMode" class="text-xs text-slate-400 mb-4 text-center">💡 {{ t.dragHint }}</p>

        <div v-if="sortedServices.length === 0" class="flex flex-col items-center justify-center py-24 text-slate-400">
             <div class="w-20 h-20 bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            </div>
            <p class="text-xl font-medium text-slate-600 dark:text-slate-400">{{ t.noServices }}</p>
            <p class="text-sm mt-2 opacity-75" v-if="isLoggedIn">{{ t.scanHint }}</p>
             <button v-if="isLoggedIn" @click="showAddService = true" class="mt-6 flex items-center gap-2 px-5 py-2.5 text-white font-medium rounded-lg transition-colors" :style="{ backgroundColor: accentColor }">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
                {{ t.addService }}
            </button>
        </div>

        <!-- Cards Draggable (edit mode) -->
        <TransitionGroup
            v-if="isEditMode && dragServices.length > 0"
            name="list"
            tag="div"
            class="grid gap-4 mb-6"
            :class="gridClasses"
        >
            <ServiceCard 
                v-for="service in dragServices" 
                :key="service.id" 
                :service="service" 
                :is-admin="isLoggedIn" 
                :view-mode="viewMode" 
                :is-delete-mode="isEditMode"
                :accent-color="accentColor"
                @edit="editingService = service" 
                @delete="handleQuickDelete(service)" 
                draggable="true"
                @dragstart="(e) => dragStart(e, service)"
                @dragover.prevent
                @drop="(e) => drop(e, service)"
            />
        </TransitionGroup>

        <!-- Cards Non-Draggable (normal view) -->
        <div 
            v-else-if="services.length > 0"
            class="grid gap-4 mb-6"
            :class="gridClasses"
        >
            <ServiceCard v-for="service in services" :key="service.id" :service="service" :is-admin="isLoggedIn" :view-mode="viewMode" :is-delete-mode="false" :accent-color="accentColor" @edit="editingService = service" @delete="handleQuickDelete(service)" />
        </div>
    </main>
    
    <transition name="fade"><LoginModal v-if="showLogin" :accent-color="accentColor" @close="showLogin = false" @success="onLoginSuccess" /></transition>
    <transition name="fade"><EditModal v-if="editingService" :service="editingService" :accent-color="accentColor" @close="editingService = null" @update="fetchServices" /></transition>
    <transition name="fade">    <SettingsModal 
        v-if="showSettings"
        ref="settingsModalRef"
        :current-lang="lang" 
        :current-profile="currentProfile"
        :all-profiles="profiles"
        :app-settings="appSettings"
        :accent-color="accentColor"
        @close="showSettings = false" 
        @lang-change="handleLangChange" 
        @logout="handleLogout"
        @profile-updated="loadData"
        @show-toast="(msg, type) => showToast(msg, type)"
        @confirm-save="confirmSaveSettings"
        @confirm-reset="confirmResetSettings"
    /></transition>
    <transition name="fade"><AddServiceModal v-if="showAddService" :lang="lang" :accent-color="accentColor" @close="showAddService = false" @save="handleAddService" /></transition>
    <transition name="fade">
        <ConfirmModal 
            v-if="showDeleteConfirm && pendingDeleteService"
            :title="lang === 'zh' ? '确认删除' : 'Confirm Delete'"
            :message="(lang === 'zh' ? '确定要删除服务 ' : 'Delete service ') + (pendingDeleteService.custom_name || pendingDeleteService.title) + '?'"
            :confirm-text="lang === 'zh' ? '删除' : 'Delete'"
            :cancel-text="lang === 'zh' ? '取消' : 'Cancel'"
            :is-danger="true"
            @confirm="confirmDelete"
            @cancel="cancelDelete"
        />
    </transition>
    <transition name="fade">
        <ConfirmModal 
            v-if="showDeleteAllConfirm"
            :title="lang === 'zh' ? '确认删除全部' : 'Confirm Delete All'"
            :message="t.confirmDeleteAll"
            :confirm-text="t.deleteAll"
            :cancel-text="lang === 'zh' ? '取消' : 'Cancel'"
            :is-danger="true"
            @confirm="confirmDeleteAll"
            @cancel="showDeleteAllConfirm = false"
        />
    </transition>

    <!-- Universal Confirm Modal -->
    <transition name="fade">
        <div v-if="showConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white dark:bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
                <p class="text-lg text-slate-800 dark:text-white mb-6">{{ confirmMessage }}</p>
                <div class="flex gap-3">
                    <button @click="showConfirm = false" class="flex-1 min-w-[100px] px-6 py-2.5 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 rounded-lg transition-colors whitespace-nowrap">
                        {{ t.cancel }}
                    </button>
                    <button @click="confirmCallback?.(); showConfirm = false" class="flex-1 min-w-[100px] px-6 py-2.5 text-white rounded-lg transition-colors whitespace-nowrap" :style="{ backgroundColor: accentColor }">
                        {{ t.confirm }}
                    </button>
                </div>
            </div>
        </div>
    </transition>
  </div>
</template>

<style>
/* CSS Variables for dynamic accent color */
:root {
  --color-primary-50: 239 246 255;
  --color-primary-100: 219 234 254;
  --color-primary-200: 191 219 254;
  --color-primary-300: 147 197 253;
  --color-primary-400: 96 165 250;
  --color-primary-500: 59 130 246;
  --color-primary-600: 37 99 235;
  --color-primary-700: 29 78 216;
  --color-primary-800: 30 64 175;
  --color-primary-900: 30 58 138;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.animate-fade-in-down { animation: fadeInDown 0.3s ease-out; }
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #000; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
</style>

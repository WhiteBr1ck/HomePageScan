<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import api, { type Profile, type AppSettings, setGuestDefaultProfile, uploadIcon, updateAppSettings } from '../api';

const props = defineProps<{ 
    currentLang: 'zh' | 'en';
    currentUser?: string;
    currentProfile?: Profile;
    allProfiles?: Profile[];
    appSettings?: AppSettings;
    accentColor?: string;
}>();
const emit = defineEmits(['close', 'langChange', 'logout', 'profileUpdated', 'showToast', 'confirmSave', 'confirmReset']);

const t = computed(() => props.currentLang === 'zh' ? {
    title: '设置',
    language: '语言',
    chinese: '中文',
    english: 'English',
    account: '账户',
    username: '用户名',
    changePassword: '修改密码',
    currentPassword: '当前密码',
    newPassword: '新密码',
    confirmPassword: '确认新密码',
    save: '保存',
    cancel: '取消',
    logout: '退出登录',
    passwordChanged: '密码修改成功',
    passwordError: '密码修改失败',
    passwordMismatch: '两次密码不一致',
    wrongPassword: '当前密码错误',
    // Site tab
    site: '站点',
    siteTitle: '站点标题',
    siteIcon: '站点图标',
    uploadIcon: '上传图标',
    guestDefault: '访客默认配置',
    guestDefaultHint: '未登录用户将只能看到此配置',
    setAsGuest: '设为默认',
    updated: '更新成功',
} : {
    title: 'Settings',
    language: 'Language',
    chinese: '中文',
    english: 'English',
    account: 'Account',
    username: 'Username',
    changePassword: 'Change Password',
    currentPassword: 'Current Password',
    newPassword: 'New Password',
    confirmPassword: 'Confirm New Password',
    save: 'Save',
    cancel: 'Cancel',
    logout: 'Logout',
    passwordChanged: 'Password changed successfully',
    passwordError: 'Failed to change password',
    password: 'Password',
    wrongPassword: 'Current password is incorrect',
    // Site tab
    site: 'Site',
    siteTitle: 'Site Title',
    siteIcon: 'Site Icon',
    uploadIcon: 'Upload Icon',
    guestDefault: 'Guest Default Profile',
    guestDefaultHint: 'Unauthenticated users will only see this profile',
    setAsGuest: 'Set as Default',
    updated: 'Updated successfully',
});

const activeTab = ref<'general' | 'account' | 'site'>('general');
const selectedLang = ref(props.currentLang);

// Password form
const currentPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const passwordMessage = ref('');
const passwordError = ref(false);
const isChangingPassword = ref(false);

// Site settings - initialize from appSettings
const siteTitle = ref('');
const siteIcon = ref('');

// Watch for appSettings changes
watch(() => props.appSettings, (newSettings) => {
    if (newSettings) {
        siteTitle.value = newSettings.site_title || '';
        siteIcon.value = newSettings.site_icon_url || '';
    }
}, { immediate: true });

const isUploadingIcon = ref(false);

const handleIconUpload = async (event: Event) => {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    
    isUploadingIcon.value = true;
    try {
        const url = await uploadIcon(file);
        siteIcon.value = url;
    } catch (e) {
        alert('Upload failed');
    } finally {
        isUploadingIcon.value = false;
    }
};

const saveSiteSettings = async () => {
    // Emit confirm event instead of directly saving
    emit('confirmSave');
};

const doSaveSiteSettings = async () => {
    try {
        await updateAppSettings({
            site_title: siteTitle.value,
            site_icon_url: siteIcon.value || undefined
        });
        emit('profileUpdated');
        emit('showToast', t.value.updated, 'success');
    } catch (e) {
        console.error('Failed to update settings:', e);
        emit('showToast', 'Failed to update', 'error');
    }
};

const resetSiteSettings = async () => {
    // Emit confirm event instead of directly resetting
    emit('confirmReset');
};

const doResetSiteSettings = async () => {
    try {
        await updateAppSettings({
            site_title: 'HomePageScan',
            site_icon_url: ''  // Use empty string instead of undefined
        });
        siteTitle.value = 'HomePageScan';
        siteIcon.value = '';
        emit('profileUpdated');
        emit('showToast', t.value.reset || 'Reset to default', 'success');
    } catch (e) {
        console.error('Failed to reset settings:', e);
        emit('showToast', 'Failed to reset', 'error');
    }
};

// Expose methods for parent to call after confirmation
defineExpose({ doSaveSiteSettings, doResetSiteSettings });

const handleSetGuestDefault = async (profileId: number) => {
    try {
        await setGuestDefaultProfile(profileId);
        emit('profileUpdated');
        alert(t.value.updated);
    } catch (e) {
        alert('Failed to set guest default');
    }
};

const handleLangChange = () => {
    emit('langChange', selectedLang.value);
};

const handlePasswordChange = async () => {
    passwordMessage.value = '';
    passwordError.value = false;
    
    if (newPassword.value !== confirmPassword.value) {
        passwordMessage.value = t.value.passwordMismatch;
        passwordError.value = true;
        return;
    }
    
    if (!currentPassword.value || !newPassword.value) {
        return;
    }
    
    isChangingPassword.value = true;
    try {
        await api.post('/users/password', {
            current_password: currentPassword.value,
            new_password: newPassword.value
        });
        passwordMessage.value = t.value.passwordChanged;
        passwordError.value = false;
        currentPassword.value = '';
        newPassword.value = '';
        confirmPassword.value = '';
    } catch (e: any) {
        passwordMessage.value = e.response?.data?.detail || t.value.passwordError;
        passwordError.value = true;
    } finally {
        isChangingPassword.value = false;
    }
};
</script>

<template>
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
        <h2 class="text-lg font-bold text-slate-800 dark:text-white">{{ t.title }}</h2>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-slate-200 dark:border-slate-700">
        <button 
            @click="activeTab = 'general'"
            class="flex-1 py-3 text-sm font-medium transition-colors"
            :class="activeTab === 'general' ? 'border-b-2' : 'text-slate-500'"
            :style="activeTab === 'general' ? { color: props.accentColor || '#3b82f6', borderColor: props.accentColor || '#3b82f6' } : {}"
        >
            {{ t.language }}
        </button>
        <button 
            @click="activeTab = 'account'"
            class="flex-1 py-3 text-sm font-medium transition-colors"
            :class="activeTab === 'account' ? 'border-b-2' : 'text-slate-500'"
            :style="activeTab === 'account' ? { color: props.accentColor || '#3b82f6', borderColor: props.accentColor || '#3b82f6' } : {}"
        >
            {{ t.account }}
        </button>
        <button 
            @click="activeTab = 'site'"
            class="flex-1 py-3 text-sm font-medium transition-colors"
            :class="activeTab === 'site' ? 'border-b-2' : 'text-slate-500'"
            :style="activeTab === 'site' ? { color: props.accentColor || '#3b82f6', borderColor: props.accentColor || '#3b82f6' } : {}"
        >
            {{ t.site }}
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-6">
        
        <!-- General Tab -->
        <div v-if="activeTab === 'general'" class="space-y-6">
            <!-- Language -->
            <div>
                <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-3">{{ t.language }}</label>
                <div class="flex gap-2">
                    <button 
                        @click="selectedLang = 'zh'; handleLangChange()"
                        class="flex-1 py-3 rounded-xl text-sm font-medium transition-all"
                        :class="selectedLang === 'zh' ? 'text-white shadow-lg' : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200'"
                        :style="selectedLang === 'zh' ? { backgroundColor: props.accentColor || '#3b82f6' } : {}"
                    >
                        {{ t.chinese }}
                    </button>
                    <button 
                        @click="selectedLang = 'en'; handleLangChange()"
                        class="flex-1 py-3 rounded-xl text-sm font-medium transition-all"
                        :class="selectedLang === 'en' ? 'text-white shadow-lg' : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200'"
                        :style="selectedLang === 'en' ? { backgroundColor: props.accentColor || '#3b82f6' } : {}"
                    >
                        {{ t.english }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Account Tab -->
        <div v-if="activeTab === 'account'" class="space-y-5">
            <div>
                <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-2">{{ t.username }}</label>
                <input type="text" :value="currentUser || 'admin'" disabled class="w-full px-4 py-2.5 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400 cursor-not-allowed" />
            </div>
            
            <div class="border-t border-slate-200 dark:border-slate-700 pt-5">
                <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-3">{{ t.changePassword }}</label>
                <div class="space-y-3">
                    <input 
                        v-model="currentPassword"
                        type="password" 
                        :placeholder="t.currentPassword" 
                        class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" 
                    />
                    <input 
                        v-model="newPassword"
                        type="password" 
                        :placeholder="t.newPassword" 
                        class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" 
                    />
                    <input 
                        v-model="confirmPassword"
                        type="password" 
                        :placeholder="t.confirmPassword" 
                        class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" 
                    />
                </div>
                
                <p v-if="passwordMessage" class="text-sm mt-3 p-2 rounded" :class="passwordError ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'">
                    {{ passwordMessage }}
                </p>
                
                <button 
                    @click="handlePasswordChange"
                    :disabled="isChangingPassword"
                    class="mt-4 w-full py-2.5 rounded-lg text-white font-medium transition-colors disabled:opacity-50"
                    :style="{ backgroundColor: props.accentColor || '#3b82f6' }"
                >
                    {{ isChangingPassword ? '...' : t.save }}
                </button>
            </div>

            <div class="pt-4 border-t border-slate-200 dark:border-slate-700">
                <button @click="$emit('logout'); $emit('close')" class="w-full py-2.5 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 font-medium hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors">
                    {{ t.logout }}
                </button>
            </div>
        </div>

        <!-- Site Tab -->
        <div v-if="activeTab === 'site'" class="space-y-5">
            <div>
                <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-2">{{ t.siteTitle }}</label>
                <input 
                    v-model="siteTitle"
                    type="text" 
                    placeholder="HomePageScan" 
                    class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none" 
                />
            </div>

            <div>
                <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-2">{{ t.siteIcon }}</label>
                <div class="flex gap-3 items-center">
                    <div class="w-16 h-16 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600 flex items-center justify-center overflow-hidden">
                        <img v-if="siteIcon" :src="siteIcon" class="w-full h-full object-cover" />
                        <span v-else class="text-xs text-slate-400">{{ t.uploadIcon }}</span>
                    </div>
                    <label class="px-4 py-2 rounded-lg text-white text-sm font-medium cursor-pointer transition-colors" :style="{ backgroundColor: props.accentColor || '#3b82f6' }">
                        {{ isUploadingIcon ? '...' : t.uploadIcon }}
                        <input type="file" class="hidden" accept="image/*" @change="handleIconUpload" />
                    </label>
                </div>
                <input 
                    v-model="siteIcon"
                    type="text" 
                    placeholder="/static/icons/..." 
                    class="w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none mt-3" 
                />
            </div>

            <div class="flex gap-2">
                <button 
                    @click="resetSiteSettings" 
                    class="px-4 py-2.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-300 font-medium transition-colors"
                >
                    重置默认
                </button>
                <button 
                    @click="saveSiteSettings"
                    class="flex-1 py-2.5 rounded-lg text-white font-medium transition-colors"
                    :style="{ backgroundColor: props.accentColor || '#3b82f6' }"
                >
                    {{ t.save }}
                </button>
            </div>

            <div class="border-t border-slate-200 dark:border-slate-700 pt-5">
                <label class="block text-sm font-bold text-slate-600 dark:text-slate-300 mb-2">{{ t.guestDefault }}</label>
                <p class="text-xs text-slate-500 mb-3">{{ t.guestDefaultHint }}</p>
                <div class="space-y-2">
                    <div v-for="profile in allProfiles" :key="profile.id" class="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                        <span class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ profile.name }}</span>
                        <button 
                            v-if="!profile.is_guest_default"
                            @click="handleSetGuestDefault(profile.id)"
                            class="px-3 py-1 text-xs rounded-md bg-slate-100 dark:bg-slate-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                            {{ t.setAsGuest }}
                        </button>
                        <span v-else class="text-xs px-3 py-1 rounded-md bg-green-50 text-green-600 font-medium">✓ {{ lang === 'zh' ? '默认' : 'Default' }}</span>
                    </div>
                </div>
            </div>
        </div>
      </div>

    </div>
  </div>
</template>

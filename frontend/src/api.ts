import axios from 'axios';

// Use relative URL in production (Nginx proxy), absolute in development
const API_BASE = import.meta.env.DEV ? 'http://localhost:8000/api' : '/api';

const api = axios.create({
    baseURL: API_BASE,
});

// Interceptor for JWT
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export interface UserLogin {
    username: string;
    password: string;
}

export interface Profile {
    id: number;
    name: string;
    scan_target?: string;
    is_guest_default?: boolean;
}

export interface AppSettings {
    id: number;
    site_title: string;
    site_icon_url?: string;
    default_sort_by: string;
    view_mode?: 'grid' | 'list';
    grid_size?: 'small' | 'medium' | 'large';
    theme_mode?: 'light' | 'dark' | 'auto';
    accent_color?: string;
}

export interface Service {
    id: number;
    profile_id?: number;
    ip: string;
    port: number;
    protocol: string;
    url: string; // Detected URL
    lan_url?: string; // Manual LAN Override
    wan_url?: string; // Manual WAN Override
    title: string;
    custom_name?: string;
    icon_url?: string;
    is_visible: boolean;
    is_manual_lock: boolean;
    last_scanned: string;
    sort_order?: number;
}

// --- Auth ---
export const login = async (creds: UserLogin) => {
    const { data } = await api.post('/login', creds);
    return data;
};

// --- Profiles ---
export const getProfiles = async (): Promise<Profile[]> => {
    const { data } = await api.get('/profiles');
    return data;
};

export const createProfile = async (profile: Partial<Profile>) => {
    const { data } = await api.post('/profiles', profile);
    return data;
};

export const updateProfile = async (id: number, profile: Partial<Profile>) => {
    const { data } = await api.put(`/profiles/${id}`, profile);
    return data;
};

export const deleteProfile = async (id: number) => {
    await api.delete(`/profiles/${id}`);
};

export const setGuestDefaultProfile = async (id: number) => {
    const { data } = await api.post(`/profiles/${id}/set-guest-default`);
    return data;
};

// --- App Settings ---
export const getAppSettings = async (): Promise<AppSettings> => {
    const { data } = await api.get('/settings');
    return data;
};

export const updateAppSettings = async (settings: Partial<AppSettings>): Promise<AppSettings> => {
    const { data } = await api.put('/settings', settings);
    return data;
};

// --- Services ---
export const getServices = async (profileId: number = 1): Promise<Service[]> => {
    const { data } = await api.get('/services', { params: { profile_id: profileId } });
    return data;
};

export const updateService = async (id: number, updates: Partial<Service>) => {
    const { data } = await api.post(`/services/${id}`, updates);
    return data;
};

export const deleteService = async (serviceId: number): Promise<void> => {
    await api.delete(`/services/${serviceId}`);
};

export const reorderServices = async (orderedIds: number[]): Promise<void> => {
    // Backend expects: { "ordered_ids": [1, 2, 3] }
    await api.post('/reorder-services', { ordered_ids: orderedIds });
};

export const triggerScan = async (targetIP: string, profileId: number): Promise<void> => {
    await api.post('/scan', { target_ip: targetIP, profile_id: profileId });
};

// --- Upload ---
export const uploadIcon = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return data.url; // Relative URL /static/icons/...
};

export default api;

import { apiClientMethods } from './apiClient';

export interface WorkItemLimits {
  max_epics: number;
  max_features_per_epic: number;
  max_user_stories_per_feature: number;
  max_tasks_per_user_story: number;
  max_test_cases_per_user_story: number;
}

export interface WorkItemLimitsResponse {
  limits: WorkItemLimits;
  has_custom_settings: boolean;
  settings_detail: Record<string, {
    value: string;
    is_user_default: boolean;
    scope?: string;
  }>;
}

export interface VisualSettings {
  glow_intensity: number;
}

export interface SettingsRequest {
  settings: {
    work_item_limits?: WorkItemLimits;
    visual_settings?: VisualSettings;
  };
  scope: 'session' | 'user_default';
  session_id?: string;
}

export interface WorkItemLimitsRequest {
  max_epics: number;
  max_features_per_epic: number;
  max_user_stories_per_feature: number;
  max_tasks_per_user_story: number;
  max_test_cases_per_user_story: number;
  scope: 'session' | 'user_default';
  session_id?: string;
  is_user_default?: boolean;
}

export interface VisualSettingsRequest {
  glow_intensity: number;
  scope: 'session' | 'user_default';
  session_id?: string;
}

export interface SessionDeleteRequest {
  session_id: string;
}

export const settingsApi = {
  // Get all settings for a user/session
  getSettings: async (userId: string, sessionId?: string) => {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await apiClientMethods.get(`/settings/${userId}`, { params });
    return response;
  },

  // Save all settings
  saveSettings: async (userId: string, request: SettingsRequest) => {
    const response = await apiClientMethods.post(`/settings/${userId}`, request);
    return response;
  },

  // Get work item limits
  getWorkItemLimits: async (userId: string, sessionId?: string) => {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await apiClientMethods.get(`/settings/${userId}/work-item-limits`, { params });
    return response;
  },

  // Save work item limits
  saveWorkItemLimits: async (userId: string, request: WorkItemLimitsRequest) => {
    const response = await apiClientMethods.post(`/settings/${userId}/work-item-limits`, request);
    return response;
  },

  // Get visual settings
  getVisualSettings: async (userId: string, sessionId?: string) => {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await apiClientMethods.get(`/settings/${userId}/visual-settings`, { params });
    return response;
  },

  // Save visual settings
  saveVisualSettings: async (userId: string, request: VisualSettingsRequest) => {
    const response = await apiClientMethods.post(`/settings/${userId}/visual-settings`, request);
    return response;
  },

  // Delete session settings
  deleteSessionSettings: async (userId: string, request: SessionDeleteRequest) => {
    const response = await apiClientMethods.delete(`/settings/${userId}/session`, { data: request });
    return response;
  },

  // Get setting history
  getSettingHistory: async (userId: string, settingType?: string) => {
    const params = settingType ? { setting_type: settingType } : {};
    const response = await apiClientMethods.get(`/settings/${userId}/history`, { params });
    return response;
  }
}; 
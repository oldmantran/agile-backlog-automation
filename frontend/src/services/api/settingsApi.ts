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
  getSettings: async (sessionId?: string) => {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await apiClientMethods.get('/settings', { params });
    return response;
  },

  // Save all settings
  saveSettings: async (request: SettingsRequest) => {
    const response = await apiClientMethods.post('/settings', request);
    return response;
  },

  // Get work item limits
  getWorkItemLimits: async (sessionId?: string) => {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await apiClientMethods.get('/settings/work-item-limits', { params });
    return response;
  },

  // Save work item limits
  saveWorkItemLimits: async (request: WorkItemLimitsRequest) => {
    const response = await apiClientMethods.post('/settings/work-item-limits', request);
    return response;
  },

  // Get visual settings
  getVisualSettings: async (sessionId?: string) => {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await apiClientMethods.get('/settings/visual-settings', { params });
    return response;
  },

  // Save visual settings
  saveVisualSettings: async (request: VisualSettingsRequest) => {
    const response = await apiClientMethods.post('/settings/visual-settings', request);
    return response;
  },

  // Delete session settings
  deleteSessionSettings: async (request: SessionDeleteRequest) => {
    const response = await apiClientMethods.delete('/settings/session', { data: request });
    return response;
  },

  // Get setting history
  getSettingHistory: async (settingType?: string) => {
    const params = settingType ? { setting_type: settingType } : {};
    const response = await apiClientMethods.get('/settings/history', { params });
    return response;
  }
}; 
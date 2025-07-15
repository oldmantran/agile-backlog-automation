import axios from 'axios';
import { Project, GenerationStatus } from '../../types/project';
import { ApiResponse } from '../../types/api';
import { BacklogJob } from '../../types/backlogJob';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const backlogApi = {
  // Backlog Generation
  generateBacklog: async (projectId: string): Promise<{ jobId: string }> => {
    const response = await api.post<ApiResponse<{ jobId: string }>>(`/backlog/generate/${projectId}`);
    return response.data.data;
  },

  getGenerationStatus: async (jobId: string): Promise<GenerationStatus> => {
    const response = await api.get<ApiResponse<GenerationStatus>>(`/backlog/status/${jobId}`);
    return response.data.data;
  },
  
  // Template Management
  getTemplates: async (domain?: string): Promise<any[]> => {
    const params = domain ? { domain } : {};
    const response = await api.get<ApiResponse<any[]>>('/backlog/templates', { params });
    return response.data.data;
  },
  
  // Preview Generation
  previewBacklog: async (projectData: Partial<Project>): Promise<any> => {
    const response = await api.post<ApiResponse<any>>('/backlog/preview', projectData);
    return response.data.data;
  },

  // Backlog Export
  exportBacklog: async (projectId: string, format: 'json' | 'yaml' | 'csv' = 'json'): Promise<Blob> => {
    const response = await api.get(`/backlog/export/${projectId}`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  // Fetch backlog jobs by user
  getBacklogJobs: async (user_email: string): Promise<BacklogJob[]> => {
    const response = await api.get(`/backlog/jobs`, { params: { user_email } });
    return response.data;
  },
};

export default backlogApi;

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
  timeout: 300000, // 5 minute timeout (increased from 60 seconds)
  // Force direct connection to bypass React proxy
  withCredentials: false,
});

export const backlogApi = {
  // Backlog Generation
  generateBacklog: async (projectId: string): Promise<GenerationStatus> => {
    console.log(`📞 Calling generateBacklog API for project: ${projectId}`);
    console.log(`🌐 API URL: ${API_BASE_URL}/backlog/generate/${projectId}`);
    
    try {
      console.log('🚀 Making POST request...');
      const startTime = new Date();
      
      const response = await api.post<GenerationStatus>(`/backlog/generate/${projectId}`);
      
      const endTime = new Date();
      console.log(`✅ Request completed in ${(endTime.getTime() - startTime.getTime()) / 1000} seconds`);
      
      return response.data;
    } catch (error) {
      console.error('❌ generateBacklog error:', error);
      throw error;
    }
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
  getBacklogJobs: async (
    user_email: string, 
    exclude_test_generated: boolean = true,
    exclude_failed: boolean = true,
    exclude_deleted: boolean = true
  ): Promise<BacklogJob[]> => {
    const response = await api.get(`/backlog/jobs`, { 
      params: { 
        user_email, 
        exclude_test_generated, 
        exclude_failed, 
        exclude_deleted 
      } 
    });
    return response.data;
  },

  // Delete a backlog job (soft delete)
  deleteBacklogJob: async (jobId: number): Promise<{ status: string; message: string }> => {
    const response = await api.delete(`/backlog/jobs/${jobId}`);
    return response.data;
  },
};

export default backlogApi;

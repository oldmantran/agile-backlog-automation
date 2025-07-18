import { apiClientMethods } from './apiClient';
import { Project, GenerationStatus } from '../../types/project';
import { ApiResponse } from '../../types/api';
import { BacklogJob } from '../../types/backlogJob';

export const backlogApi = {
  // Backlog Generation
  generateBacklog: async (projectId: string): Promise<GenerationStatus> => {
    console.log(`📞 Calling generateBacklog API for project: ${projectId}`);
    console.log(`🌐 API URL: ${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/backlog/generate/${projectId}`);
    try {
      console.log('🚀 Making POST request...');
      const response = await apiClientMethods.post<GenerationStatus>(`/backlog/generate/${projectId}`);
      console.log('📥 Response received:', response);
      return response; // The response is already unwrapped by the interceptor
    } catch (error) {
      console.error('❌ generateBacklog error:', error);
      throw error;
    }
  },

  getGenerationStatus: async (jobId: string): Promise<GenerationStatus> => {
    const response = await apiClientMethods.get<GenerationStatus>(`/backlog/status/${jobId}`);
    return response;
  },
  
  // Template Management
  getTemplates: async (domain?: string): Promise<any[]> => {
    const params = domain ? { domain } : {};
    const response = await apiClientMethods.get<any[]>('/backlog/templates', { params });
    return response;
  },
  
  // Preview Generation
  previewBacklog: async (projectData: Partial<Project>): Promise<any> => {
    const response = await apiClientMethods.post<any>('/backlog/preview', projectData);
    return response;
  },

  // Backlog Export
  exportBacklog: async (projectId: string, format: 'json' | 'yaml' | 'csv' = 'json'): Promise<Blob> => {
    const response = await apiClientMethods.get<Blob>(`/backlog/export/${projectId}`, {
      params: { format },
      responseType: 'blob',
    });
    return response;
  },

  // Fetch backlog jobs by user
  getBacklogJobs: async (
    user_email: string, 
    exclude_test_generated: boolean = true,
    exclude_failed: boolean = true,
    exclude_deleted: boolean = true
  ): Promise<BacklogJob[]> => {
    const response = await apiClientMethods.get<BacklogJob[]>(`/backlog/jobs`, { 
      params: { 
        user_email, 
        exclude_test_generated, 
        exclude_failed, 
        exclude_deleted 
      } 
    });
    return response;
  },

  // Delete a backlog job (soft delete)
  deleteBacklogJob: async (jobId: number): Promise<{ status: string; message: string }> => {
    const response = await apiClientMethods.delete<{ status: string; message: string }>(`/backlog/jobs/${jobId}`);
    return response;
  },
};

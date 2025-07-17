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
  timeout: 60000, // 60 second timeout
  // Force direct connection to bypass React proxy
  withCredentials: false,
});

export const backlogApi = {
  // Backlog Generation
  generateBacklog: async (projectId: string): Promise<{ jobId: string }> => {
    console.log('📞 Calling generateBacklog API for project:', projectId);
    console.log('🌐 API URL:', `${API_BASE_URL}/backlog/generate/${projectId}`);
    
    try {
      console.log('🚀 Making POST request...');
      console.log('⏰ Request start time:', new Date().toISOString());
      
      // Add a timeout promise to catch hanging requests
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
          console.error('⏰ Request timeout after 60 seconds');
          reject(new Error('Request timeout - request hung for 60 seconds'));
        }, 60000);
      });
      
      const requestPromise = api.post<ApiResponse<{ jobId: string }>>(`/backlog/generate/${projectId}`);
      
      // Race between the request and timeout
      const response = await Promise.race([requestPromise, timeoutPromise]) as any;
      
      console.log('⏰ Request completed at:', new Date().toISOString());
      console.log('📥 Raw API response:', response);
      console.log('📥 Response status:', response.status);
      console.log('📥 Response headers:', response.headers);
      console.log('📥 Response data:', response.data);
      console.log('📥 Response data.data:', response.data.data);
      
      // The backend returns { success: true, data: { jobId: "..." } }
      // So we need to return response.data.data, not response.data.data.data
      return response.data.data;
    } catch (error: any) {
      console.error('❌ generateBacklog API error:', error);
      console.error('⏰ Error occurred at:', new Date().toISOString());
      
      if (error.code === 'ECONNABORTED') {
        console.error('❌ Request timed out after 60 seconds');
        throw new Error('Request timed out - the backend may be processing. Please try again.');
      }
      
      if (error.response) {
        console.error('❌ Server responded with error:', error.response.status, error.response.data);
        throw new Error(`Server error: ${error.response.status} - ${error.response.data?.detail || error.response.data}`);
      }
      
      if (error.request) {
        console.error('❌ No response received from server');
        throw new Error('No response from server - please check if the backend is running.');
      }
      
      console.error('❌ Network error:', error.message);
      throw new Error(`Network error: ${error.message}`);
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

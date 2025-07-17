import { Project } from '../../types/project';
import { apiClientMethods, ApiError, NetworkError } from './apiClient';

export const projectApi = {
  createProject: async (projectData: any): Promise<any> => {
    try {
      const response = await apiClientMethods.post<{ projectId: string; status: string }>('/projects', projectData);
      return response; // Return the full response, not just response.data
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(`Failed to create project: ${error.message}`);
      } else if (error instanceof NetworkError) {
        throw new Error('Network error: Unable to connect to server');
      }
      throw new Error('Failed to create project');
    }
  },

  getProject: async (projectId: string): Promise<Project> => {
    try {
      const response = await apiClientMethods.get<Project>(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          throw new Error(`Project not found: ${projectId}`);
        }
        throw new Error(`Failed to fetch project: ${error.message}`);
      } else if (error instanceof NetworkError) {
        throw new Error('Network error: Unable to connect to server');
      }
      throw new Error('Failed to fetch project');
    }
  },

  updateProject: async (projectId: string, updates: Partial<Project>): Promise<Project> => {
    try {
      const response = await apiClientMethods.put<Project>(`/projects/${projectId}`, updates);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          throw new Error(`Project not found: ${projectId}`);
        }
        throw new Error(`Failed to update project: ${error.message}`);
      } else if (error instanceof NetworkError) {
        throw new Error('Network error: Unable to connect to server');
      }
      throw new Error('Failed to update project');
    }
  },

  deleteProject: async (projectId: string): Promise<boolean> => {
    try {
      const response = await apiClientMethods.delete<{ success: boolean }>(`/projects/${projectId}`);
      return response.data.success;
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 404) {
          throw new Error(`Project not found: ${projectId}`);
        }
        throw new Error(`Failed to delete project: ${error.message}`);
      } else if (error instanceof NetworkError) {
        throw new Error('Network error: Unable to connect to server');
      }
      throw new Error('Failed to delete project');
    }
  },

  listProjects: async (page = 1, limit = 10): Promise<{ projects: Project[], total: number }> => {
    try {
      const response = await apiClientMethods.get<{ projects: Project[], pagination: { total: number } }>('/projects', {
        params: { page, limit },
      });
      
      // Handle the nested response structure from the backend
      if (response && response.data && response.data.projects) {
        return {
          projects: response.data.projects,
          total: response.data.pagination?.total || response.data.projects.length
        };
      } else {
        console.warn('Unexpected API response structure:', response);
        return { projects: [], total: 0 };
      }
    } catch (error) {
      if (error instanceof ApiError) {
        throw new Error(`Failed to list projects: ${error.message}`);
      } else if (error instanceof NetworkError) {
        throw new Error('Network error: Unable to connect to server');
      }
      throw new Error('Failed to list projects');
    }
  },
};

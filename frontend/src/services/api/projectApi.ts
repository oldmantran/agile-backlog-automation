import axios from 'axios';
import { Project } from '../../types/project';
import { ApiResponse } from '../../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const projectApi = {
  createProject: async (projectData: Partial<Project>): Promise<Project> => {
    const response = await api.post<ApiResponse<Project>>('/projects', projectData);
    return response.data.data;
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await api.get<ApiResponse<Project>>(`/projects/${projectId}`);
    return response.data.data;
  },

  updateProject: async (projectId: string, updates: Partial<Project>): Promise<Project> => {
    const response = await api.put<ApiResponse<Project>>(`/projects/${projectId}`, updates);
    return response.data.data;
  },

  deleteProject: async (projectId: string): Promise<boolean> => {
    const response = await api.delete<ApiResponse<{ success: boolean }>>(`/projects/${projectId}`);
    return response.data.success;
  },

  listProjects: async (page = 1, limit = 10): Promise<{ projects: Project[], total: number }> => {
    const response = await api.get<ApiResponse<{ projects: Project[], total: number }>>('/projects', {
      params: { page, limit },
    });
    return response.data.data;
  },
};

export default projectApi;

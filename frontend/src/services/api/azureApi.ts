import axios from 'axios';
import { AzureCredentials, ValidationResult, AzureProject, AreaPath, Iteration } from '../../types/azure';
import { ApiResponse } from '../../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const azureApi = {
  validateConnection: async (credentials: AzureCredentials): Promise<ValidationResult> => {
    const response = await api.post<ApiResponse<ValidationResult>>('/azure/validate', credentials);
    return response.data.data;
  },
  
  getProjects: async (credentials: AzureCredentials): Promise<AzureProject[]> => {
    const response = await api.post<ApiResponse<AzureProject[]>>('/azure/projects', credentials);
    return response.data.data;
  },
  
  getAreaPaths: async (credentials: AzureCredentials, projectName: string): Promise<AreaPath[]> => {
    const response = await api.post<ApiResponse<AreaPath[]>>('/azure/area-paths', {
      ...credentials,
      projectName,
    });
    return response.data.data;
  },
  
  getIterations: async (credentials: AzureCredentials, projectName: string): Promise<Iteration[]> => {
    const response = await api.post<ApiResponse<Iteration[]>>('/azure/iterations', {
      ...credentials,
      projectName,
    });
    return response.data.data;
  },
};

export default azureApi;

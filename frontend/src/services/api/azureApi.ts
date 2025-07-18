import { apiClientMethods } from './apiClient';
import { AzureCredentials, ValidationResult, AzureProject, AreaPath, Iteration } from '../../types/azure';

export const azureApi = {
  validateConnection: async (credentials: AzureCredentials): Promise<ValidationResult> => {
    const response = await apiClientMethods.post<ValidationResult>('/azure/validate', credentials);
    return response;
  },
  
  getProjects: async (credentials: AzureCredentials): Promise<AzureProject[]> => {
    const response = await apiClientMethods.post<AzureProject[]>('/azure/projects', credentials);
    return response;
  },
  
  getAreaPaths: async (credentials: AzureCredentials, projectName: string): Promise<AreaPath[]> => {
    const response = await apiClientMethods.post<AreaPath[]>('/azure/area-paths', {
      ...credentials,
      projectName,
    });
    return response;
  },
  
  getIterations: async (credentials: AzureCredentials, projectName: string): Promise<Iteration[]> => {
    const response = await apiClientMethods.post<Iteration[]>('/azure/iterations', {
      ...credentials,
      projectName,
    });
    return response;
  },
};

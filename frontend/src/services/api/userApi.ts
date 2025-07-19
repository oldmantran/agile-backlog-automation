import { apiClientMethods } from './apiClient';

export interface CurrentUser {
  user_id: string;
  email: string;
  display_name: string;
}

export const userApi = {
  // Get current user information
  getCurrentUser: async (): Promise<CurrentUser> => {
    const response = await apiClientMethods.get('/user/current') as any;
    return response.data;
  }
}; 
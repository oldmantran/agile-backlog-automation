import { apiClientMethods } from './apiClient';

export interface CurrentUser {
  user_id: string;
  email: string;
  display_name: string;
}

export const userApi = {
  // Get current user information
  getCurrentUser: async (): Promise<CurrentUser> => {
    try {
      console.log('Fetching current user from /api/user/current');
      const response = await apiClientMethods.get('/user/current');
      console.log('getCurrentUser response:', response);
      return response as CurrentUser;
    } catch (error) {
      console.error('getCurrentUser error:', error);
      throw error;
    }
  }
}; 
export const routes = {
  home: '/',
  dashboard: '/dashboard',
  newProject: '/project/new',
  projectDetails: (id: string) => `/project/${id}`,
  projectSettings: (id: string) => `/project/${id}/settings`,
  userSettings: '/settings',
};

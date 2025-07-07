import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Project } from '../types/project';

export const useProject = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const createProject = async (projectData: Partial<Project>): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call for now
      console.log('Creating project:', projectData);
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Normally we'd call an API here
      // const response = await api.post('/api/projects', projectData);
      // const newProject = response.data;
      
      const mockProjectId = `proj-${Date.now()}`;
      
      setIsLoading(false);
      navigate(`/project/${mockProjectId}`);
    } catch (err) {
      setIsLoading(false);
      setError(err instanceof Error ? err.message : 'Failed to create project');
      throw err;
    }
  };
  
  const getProject = async (projectId: string): Promise<Project | null> => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call
      console.log('Fetching project:', projectId);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Mock project data
      const mockProject: Project = {
        id: projectId,
        basics: {
          name: 'Sample Project',
          description: 'This is a sample project',
          domain: 'software',
          teamSize: 5,
          timeline: '3 months'
        },
        vision: {
          visionStatement: 'To create an innovative software solution',
          businessObjectives: ['Increase efficiency', 'Reduce costs'],
          successMetrics: ['User adoption', 'Cost savings'],
          targetAudience: 'Enterprise users'
        },
        azureConfig: {
          organizationUrl: 'https://dev.azure.com/sample',
          personalAccessToken: '******',
          project: 'SampleProject',
          areaPath: 'SampleProject\\Area',
          iterationPath: 'SampleProject\\Iteration'
        },
        status: 'completed',
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      setIsLoading(false);
      return mockProject;
    } catch (err) {
      setIsLoading(false);
      setError(err instanceof Error ? err.message : 'Failed to fetch project');
      return null;
    }
  };

  return {
    createProject,
    getProject,
    isLoading,
    error,
  };
};

export default useProject;

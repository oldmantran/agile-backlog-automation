import { apiClientMethods } from './apiClient';
import { GenerationStatus } from '../../types/project';

export interface JobInfo {
  jobId: string;
  projectId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  currentAgent: string;
  currentAction: string;
  startTime: string;
  endTime?: string;
  error?: string;
}

export const jobsApi = {
  // Get all active and recent jobs
  getAllJobs: async (): Promise<JobInfo[]> => {
    const response = await apiClientMethods.get<JobInfo[]>('/jobs');
    return response;
  },

  // Get specific job status
  getJobStatus: async (jobId: string): Promise<GenerationStatus> => {
    const response = await apiClientMethods.get<GenerationStatus>(`/backlog/status/${jobId}`);
    return response;
  },

  // Poll for job updates (helper function)
  pollJobStatus: async (jobId: string, onUpdate: (status: GenerationStatus) => void, intervalMs = 2000): Promise<void> => {
    const poll = async () => {
      try {
        const status = await jobsApi.getJobStatus(jobId);
        onUpdate(status);
        
        // Continue polling if still running
        if (status.status === 'running' || status.status === 'queued') {
          setTimeout(poll, intervalMs);
        }
      } catch (error) {
        console.error('Error polling job status:', error);
      }
    };
    
    poll();
  },
};

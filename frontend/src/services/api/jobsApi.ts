import axios from 'axios';
import { GenerationStatus } from '../../types/project';
import { ApiResponse } from '../../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
    const response = await api.get<ApiResponse<JobInfo[]>>('/jobs');
    return response.data.data;
  },

  // Get specific job status
  getJobStatus: async (jobId: string): Promise<GenerationStatus> => {
    const response = await api.get<ApiResponse<GenerationStatus>>(`/backlog/status/${jobId}`);
    return response.data.data;
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

export default jobsApi;

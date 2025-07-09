export interface ProjectBasics {
  name: string;
  description: string;
  domain: string;
}

export interface ProductVision {
  visionStatement: string;
  businessObjectives: string[];
  successMetrics: string[];
  targetAudience: string;
}

export interface AzureConfig {
  organizationUrl: string;
  personalAccessToken: string;
  project: string;
  areaPath: string;
  iterationPath: string;
}

export interface Project {
  id: string;
  basics: ProjectBasics;
  vision: ProductVision;
  azureConfig: AzureConfig;
  status: 'draft' | 'generating' | 'completed' | 'error';
  createdAt: Date;
  updatedAt: Date;
}

export interface GenerationStatus {
  jobId: string;
  projectId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  currentAgent: string;
  currentAction: string;
  estimatedTimeRemaining: number;
  logs: string[];
  completedAt?: Date;
  error?: string;
}

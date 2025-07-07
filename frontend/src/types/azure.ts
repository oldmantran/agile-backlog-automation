export interface AzureCredentials {
  organizationUrl: string;
  personalAccessToken: string;
}

export interface AzureProject {
  id: string;
  name: string;
  url: string;
}

export interface AreaPath {
  path: string;
  name: string;
}

export interface Iteration {
  path: string;
  name: string;
  startDate?: Date;
  endDate?: Date;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  projects?: AzureProject[];
}

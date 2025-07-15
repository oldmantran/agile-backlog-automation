export interface BacklogJob {
  id: number;
  user_email: string;
  project_name: string;
  epics_generated: number;
  features_generated: number;
  user_stories_generated: number;
  tasks_generated: number;
  test_cases_generated: number;
  execution_time_seconds?: number;
  created_at: string;
  raw_summary?: string;
}

import React, { useState } from 'react';
import {
  Box,
  VStack,
  Heading,
  useToast,
  Container,
  Text,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import SimplifiedProjectForm from '../../components/forms/SimplifiedProjectForm';
import { Project } from '../../types/project';
import { projectApi } from '../../services/api/projectApi';
import { backlogApi } from '../../services/api/backlogApi';

const SimpleProjectWizard: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();

  const handleSubmit = async (projectData: Partial<Project>) => {
    try {
      setIsSubmitting(true);
      
      toast({
        title: 'Creating Project',
        description: 'Setting up your project and generating backlog...',
        status: 'info',
        duration: 3000,
      });

      // Create the project
      const projectResponse = await projectApi.createProject(projectData);
      
      if (projectResponse.projectId) {
        const { projectId } = projectResponse;
        
        toast({
          title: 'Project Created',
          description: 'Starting backlog generation...',
          status: 'success',
          duration: 3000,
        });

        // Start backlog generation
        const backlogResponse = await backlogApi.generateBacklog(projectId);
        
        if (backlogResponse.jobId) {
          // Store job info in localStorage for dashboard
          const jobInfo = {
            jobId: backlogResponse.jobId,
            projectId: projectId,
            status: 'queued',
            progress: 0,
            startTime: new Date().toISOString(),
          };
          
          const existingJobs = JSON.parse(localStorage.getItem('activeJobs') || '[]');
          existingJobs.push(jobInfo);
          localStorage.setItem('activeJobs', JSON.stringify(existingJobs));
          
          toast({
            title: 'Backlog Generation Started',
            description: `Your backlog is being generated. Job ID: ${backlogResponse.jobId}. Check the dashboard for progress.`,
            status: 'success',
            duration: 5000,
          });
          
          // Redirect to dashboard with job ID
          window.location.href = `/dashboard?job=${backlogResponse.jobId}`;
        } else {
          throw new Error('Failed to start backlog generation');
        }
      } else {
        throw new Error('Failed to create project');
      }
    } catch (error) {
      console.error('Project creation error:', error);
      
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create project',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container maxWidth="900px" py={8}>
      <VStack spacing={8} align="stretch">
        <Box textAlign="center">
          <Heading size="xl" mb={4}>
            Agile Backlog Automation
          </Heading>
          <Text fontSize="lg" color="gray.600">
            Transform your product vision into a comprehensive backlog with AI-powered automation
          </Text>
        </Box>

        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">Simplified Setup</Text>
            <Text>
              Only 4 fields required: Vision Statement, Azure DevOps Project, Area Path, and Iteration Path. 
              Everything else is automatically extracted by AI or set to sensible defaults.
            </Text>
          </Box>
        </Alert>

        <SimplifiedProjectForm 
          onSubmit={handleSubmit}
          isSubmitting={isSubmitting}
        />
      </VStack>
    </Container>
  );
};

export default SimpleProjectWizard;

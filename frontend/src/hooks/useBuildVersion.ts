import { useState, useEffect } from 'react';

export interface BuildVersionInfo {
  build_version: string;
  timestamp: string;
}

export const useBuildVersion = () => {
  const [buildVersion, setBuildVersion] = useState<string>('2025.08.04.001');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBuildVersion = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/build-version');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: BuildVersionInfo = await response.json();
        setBuildVersion(data.build_version);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch build version:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch build version');
        // Keep the fallback version on error
      } finally {
        setLoading(false);
      }
    };

    fetchBuildVersion();
  }, []);

  return { buildVersion, loading, error };
};
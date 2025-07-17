import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { FiMonitor, FiPause, FiPlay, FiTrash2, FiDownload } from 'react-icons/fi';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  module: string;
}

interface ServerLogsProps {
  className?: string;
}

const ServerLogs: React.FC<ServerLogsProps> = ({ className = '' }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [maxLines, setMaxLines] = useState(100);
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (!isPaused) {
      scrollToBottom();
    }
  }, [logs, isPaused]);

  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // Connect to backend server on port 80
      const wsUrl = `${protocol}//localhost:8000/ws/logs`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setIsConnected(true);
        console.log('WebSocket connected to server logs');
      };
      
      wsRef.current.onmessage = (event) => {
        if (!isPaused) {
          try {
            const logEntry: LogEntry = JSON.parse(event.data);
            setLogs(prev => {
              const newLogs = [...prev, logEntry];
              // Keep only the last maxLines entries
              return newLogs.slice(-maxLines);
            });
          } catch (error) {
            console.error('Error parsing log message:', error);
          }
        }
      };
      
      wsRef.current.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected from server logs');
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setIsConnected(false);
    }
  };

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const togglePause = () => {
    setIsPaused(!isPaused);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const downloadLogs = () => {
    const logText = logs.map(log => 
      `[${new Date(log.timestamp).toLocaleString()}] ${log.level} (${log.module}): ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `server-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-400';
      case 'WARNING': return 'text-yellow-400';
      case 'INFO': return 'text-blue-400';
      case 'DEBUG': return 'text-gray-400';
      default: return 'text-foreground';
    }
  };

  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'bg-red-500/20 text-red-400 border-red-400/50';
      case 'WARNING': return 'bg-yellow-500/20 text-yellow-400 border-yellow-400/50';
      case 'INFO': return 'bg-blue-500/20 text-blue-400 border-blue-400/50';
      case 'DEBUG': return 'bg-gray-500/20 text-gray-400 border-gray-400/50';
      default: return 'bg-primary/20 text-primary border-primary/50';
    }
  };

  return (
    <Card className={`tron-card bg-card/50 backdrop-blur-sm border border-primary/30 ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FiMonitor className="w-5 h-5 text-primary glow-cyan" />
            <CardTitle className="text-foreground glow-cyan">Server Logs</CardTitle>
            <Badge className={isConnected ? 'bg-green-500/20 text-green-400 border-green-400/50' : 'bg-red-500/20 text-red-400 border-red-400/50'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
            {logs.length > 0 && (
              <Badge variant="outline" className="bg-primary/20 text-primary border-primary/50">
                {logs.length} entries
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={togglePause}
              className="text-primary border-primary/50 hover:bg-primary/10"
            >
              {isPaused ? <FiPlay className="w-4 h-4" /> : <FiPause className="w-4 h-4" />}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
              className="text-yellow-400 border-yellow-400/50 hover:bg-yellow-400/10"
            >
              <FiTrash2 className="w-4 h-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={downloadLogs}
              disabled={logs.length === 0}
              className="text-green-400 border-green-400/50 hover:bg-green-400/10"
            >
              <FiDownload className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="bg-black/30 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
          {logs.length === 0 ? (
            <div className="text-muted-foreground text-center py-8">
              {isConnected ? 'Waiting for server logs...' : 'Connecting to server logs...'}
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div key={index} className="flex items-start space-x-2 text-xs">
                  <span className="text-gray-400 whitespace-nowrap">
                    [{new Date(log.timestamp).toLocaleTimeString()}]
                  </span>
                  <Badge 
                    variant="outline" 
                    className={`${getLevelBadgeColor(log.level)} text-xs px-1 py-0 h-4`}
                  >
                    {log.level}
                  </Badge>
                  <span className="text-gray-400 whitespace-nowrap">
                    ({log.module})
                  </span>
                  <span className={`${getLevelColor(log.level)} break-all`}>
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
        
        {isPaused && (
          <div className="mt-2 text-xs text-yellow-400 text-center">
            ⏸️ Logs paused - click play to resume
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ServerLogs;

/**
 * WebSocket hook for real-time job updates in CineCraft.
 * Provides automatic reconnection and message handling.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: 'connection' | 'progress' | 'stage_complete' | 'status_change' | 'completion' | 'error' | 'status' | 'pong';
  job_id?: number;
  status?: string;
  progress?: number;
  stage?: string;
  stages_completed?: string[];
  old_status?: string;
  new_status?: string;
  result?: any;
  error?: string;
  error_message?: string;
  timestamp?: string;
  message?: string;
}

export interface UseWebSocketOptions {
  jobId: number;
  token: string;
  onProgress?: (progress: number, stage: string) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
  onStatusChange?: (oldStatus: string, newStatus: string) => void;
  onStageComplete?: (stage: string, progress: number) => void;
  onMessage?: (message: WebSocketMessage) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  isReconnecting: boolean;
  reconnectAttempts: number;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: string) => void;
  requestStatus: () => void;
  disconnect: () => void;
  reconnect: () => void;
}

/**
 * Custom hook for WebSocket connection to job updates.
 *
 * @param options - Configuration options
 * @returns WebSocket state and control functions
 *
 * @example
 * ```tsx
 * const { isConnected, lastMessage } = useWebSocket({
 *   jobId: 123,
 *   token: 'your-jwt-token',
 *   onProgress: (progress, stage) => {
 *     console.log(`${stage}: ${progress}%`);
 *   },
 *   onComplete: (result) => {
 *     console.log('Job complete!', result);
 *   },
 *   onError: (error) => {
 *     console.error('Job failed:', error);
 *   }
 * });
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    jobId,
    token,
    onProgress,
    onComplete,
    onError,
    onStatusChange,
    onStageComplete,
    onMessage,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  // Build WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_WS_URL || window.location.host;
    return `${protocol}//${host}/api/v1/ws/jobs/${jobId}?token=${encodeURIComponent(token)}`;
  }, [jobId, token]);

  // Send heartbeat ping
  const sendHeartbeat = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping');
    }
  }, []);

  // Start heartbeat interval
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    heartbeatIntervalRef.current = setInterval(sendHeartbeat, heartbeatInterval);
  }, [sendHeartbeat, heartbeatInterval]);

  // Stop heartbeat interval
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setLastMessage(message);

        // Call custom message handler
        if (onMessage) {
          onMessage(message);
        }

        // Handle specific message types
        switch (message.type) {
          case 'connection':
            console.log('WebSocket connected:', message);
            break;

          case 'progress':
            if (onProgress && message.progress !== undefined && message.stage) {
              onProgress(message.progress, message.stage);
            }
            break;

          case 'stage_complete':
            if (onStageComplete && message.stage && message.progress !== undefined) {
              onStageComplete(message.stage, message.progress);
            }
            break;

          case 'status_change':
            if (onStatusChange && message.old_status && message.new_status) {
              onStatusChange(message.old_status, message.new_status);
            }
            break;

          case 'completion':
            if (onComplete && message.result) {
              onComplete(message.result);
            }
            stopHeartbeat();
            break;

          case 'error':
            const errorMsg = message.error || message.error_message || 'Unknown error';
            if (onError) {
              onError(errorMsg);
            }
            console.error('WebSocket error message:', errorMsg);
            stopHeartbeat();
            break;

          case 'status':
            console.log('Job status:', message);
            break;

          case 'pong':
            // Heartbeat response
            break;

          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    },
    [onMessage, onProgress, onStageComplete, onStatusChange, onComplete, onError, stopHeartbeat]
  );

  // Reconnect logic
  const reconnect = useCallback(() => {
    if (!autoReconnect || !shouldReconnectRef.current) {
      return;
    }

    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      setIsReconnecting(false);
      return;
    }

    setIsReconnecting(true);

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`Attempting to reconnect (${reconnectAttempts + 1}/${maxReconnectAttempts})...`);
      setReconnectAttempts((prev) => prev + 1);
      connect();
    }, reconnectInterval);
  }, [autoReconnect, reconnectAttempts, maxReconnectAttempts, reconnectInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }

      const url = getWebSocketUrl();
      console.log('Connecting to WebSocket:', url);

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsReconnecting(false);
        setReconnectAttempts(0);
        startHeartbeat();
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        stopHeartbeat();

        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && shouldReconnectRef.current) {
          reconnect();
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnected(false);
      reconnect();
    }
  }, [getWebSocketUrl, handleMessage, startHeartbeat, stopHeartbeat, reconnect]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    stopHeartbeat();

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsReconnecting(false);
  }, [stopHeartbeat]);

  // Send message to server
  const sendMessage = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  // Request current status
  const requestStatus = useCallback(() => {
    sendMessage('status');
  }, [sendMessage]);

  // Manual reconnect
  const manualReconnect = useCallback(() => {
    shouldReconnectRef.current = true;
    setReconnectAttempts(0);
    connect();
  }, [connect]);

  // Connect on mount
  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [jobId, token]); // Reconnect if jobId or token changes

  return {
    isConnected,
    isReconnecting,
    reconnectAttempts,
    lastMessage,
    sendMessage,
    requestStatus,
    disconnect,
    reconnect: manualReconnect,
  };
}

/**
 * Hook for monitoring multiple jobs simultaneously.
 *
 * @param jobIds - Array of job IDs to monitor
 * @param token - JWT access token
 * @returns Map of job IDs to their WebSocket states
 *
 * @example
 * ```tsx
 * const jobStates = useMultipleWebSockets([123, 124, 125], token);
 * jobStates[123]?.isConnected // true/false
 * ```
 */
export function useMultipleWebSockets(
  jobIds: number[],
  token: string,
  options?: Partial<Omit<UseWebSocketOptions, 'jobId' | 'token'>>
): Record<number, UseWebSocketReturn> {
  const [connections, setConnections] = useState<Record<number, UseWebSocketReturn>>({});

  useEffect(() => {
    const newConnections: Record<number, UseWebSocketReturn> = {};

    jobIds.forEach((jobId) => {
      // This will be managed by individual useWebSocket hooks
      // In practice, you'd need to render multiple useWebSocket hooks
      // This is a simplified example
    });

    setConnections(newConnections);
  }, [jobIds, token]);

  return connections;
}

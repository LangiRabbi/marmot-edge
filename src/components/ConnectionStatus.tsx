/**
 * WebSocket connection status indicator component.
 * Shows real-time connection state with visual feedback.
 */

import React from 'react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Alert, AlertDescription } from './ui/alert';
import {
  Wifi,
  WifiOff,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity
} from 'lucide-react';
import { type ConnectionState } from '../services/websocketService';

interface ConnectionStatusProps {
  connectionState: ConnectionState;
  isConnected: boolean;
  error?: string | null;
  totalMessages?: number;
  messagesPerSecond?: number;
  onReconnect?: () => void;
  className?: string;
  showDetails?: boolean;
}

/**
 * Connection status indicator with visual feedback
 */
export function ConnectionStatus({
  connectionState,
  isConnected,
  error,
  totalMessages = 0,
  messagesPerSecond = 0,
  onReconnect,
  className = '',
  showDetails = false
}: ConnectionStatusProps) {
  // Get status configuration
  const statusConfig = getStatusConfig(connectionState, isConnected, error);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              <Badge
                variant={statusConfig.variant}
                className={`flex items-center gap-1.5 ${statusConfig.className}`}
              >
                <statusConfig.icon className="h-3 w-3" />
                <span className="text-xs font-medium">{statusConfig.label}</span>
              </Badge>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-medium">{statusConfig.title}</p>
              <p className="text-sm text-muted-foreground">{statusConfig.description}</p>
              {showDetails && isConnected && (
                <div className="text-xs text-muted-foreground border-t pt-1 mt-1">
                  <p>Messages: {totalMessages}</p>
                  <p>Rate: {messagesPerSecond.toFixed(1)}/s</p>
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {/* Reconnect button for error states */}
      {(connectionState === 'error' || connectionState === 'disconnected') && onReconnect && (
        <Button
          variant="outline"
          size="sm"
          onClick={onReconnect}
          className="h-6 px-2 text-xs"
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Reconnect
        </Button>
      )}

      {/* Error alert */}
      {error && (
        <Alert className="mt-2 max-w-md">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-sm">
            <strong>Connection Error:</strong> {error}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

/**
 * Compact connection status for header/navbar
 */
export function CompactConnectionStatus({
  connectionState,
  isConnected,
  error,
  onReconnect,
  className = ''
}: Pick<ConnectionStatusProps, 'connectionState' | 'isConnected' | 'error' | 'onReconnect' | 'className'>) {
  const statusConfig = getStatusConfig(connectionState, isConnected, error);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`flex items-center gap-1 cursor-help ${className}`}>
            <statusConfig.icon
              className={`h-4 w-4 ${statusConfig.iconColor}`}
            />
            {(connectionState === 'error' || connectionState === 'disconnected') && onReconnect && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onReconnect}
                className="h-6 w-6 p-0"
              >
                <RotateCcw className="h-3 w-3" />
              </Button>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="space-y-1">
            <p className="font-medium">{statusConfig.title}</p>
            <p className="text-sm text-muted-foreground">{statusConfig.description}</p>
            {error && (
              <p className="text-sm text-red-500 border-t pt-1 mt-1">
                Error: {error}
              </p>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Animated connection indicator for active states
 */
export function AnimatedConnectionIndicator({
  connectionState,
  messagesPerSecond = 0,
  className = ''
}: Pick<ConnectionStatusProps, 'connectionState' | 'messagesPerSecond' | 'className'>) {
  const isActive = connectionState === 'connected' && messagesPerSecond > 0;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative">
        <Activity
          className={`h-4 w-4 transition-colors ${
            isActive ? 'text-green-500' : 'text-gray-400'
          }`}
        />
        {isActive && (
          <div className="absolute -top-1 -right-1">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        )}
      </div>
      <span className="text-xs text-muted-foreground">
        {messagesPerSecond > 0 ? `${messagesPerSecond.toFixed(1)}/s` : 'Idle'}
      </span>
    </div>
  );
}

// Helper function to get status configuration
function getStatusConfig(connectionState: ConnectionState, isConnected: boolean, error?: string | null) {
  switch (connectionState) {
    case 'connected':
      return {
        icon: CheckCircle,
        iconColor: 'text-green-500',
        label: 'Connected',
        title: 'WebSocket Connected',
        description: 'Real-time updates active',
        variant: 'default' as const,
        className: 'bg-green-100 text-green-800 border-green-200'
      };

    case 'connecting':
      return {
        icon: Clock,
        iconColor: 'text-yellow-500',
        label: 'Connecting',
        title: 'Connecting to WebSocket',
        description: 'Establishing connection...',
        variant: 'secondary' as const,
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
      };

    case 'reconnecting':
      return {
        icon: RotateCcw,
        iconColor: 'text-blue-500',
        label: 'Reconnecting',
        title: 'Reconnecting to WebSocket',
        description: 'Attempting to restore connection...',
        variant: 'secondary' as const,
        className: 'bg-blue-100 text-blue-800 border-blue-200 animate-pulse'
      };

    case 'error':
      return {
        icon: AlertTriangle,
        iconColor: 'text-red-500',
        label: 'Error',
        title: 'Connection Error',
        description: error || 'Failed to connect to WebSocket',
        variant: 'destructive' as const,
        className: 'bg-red-100 text-red-800 border-red-200'
      };

    case 'disconnected':
    default:
      return {
        icon: WifiOff,
        iconColor: 'text-gray-500',
        label: 'Disconnected',
        title: 'WebSocket Disconnected',
        description: 'No real-time updates',
        variant: 'outline' as const,
        className: 'bg-gray-100 text-gray-800 border-gray-200'
      };
  }
}

export default ConnectionStatus;
import { getConfig } from '@/config/environment';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class Logger {
  private config = getConfig();
  
  private shouldLog(level: LogLevel): boolean {
    if (!this.config.logging.enabled) return false;
    
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    const configLevel = this.config.logging.level as LogLevel;
    const configLevelIndex = levels.indexOf(configLevel);
    const messageLevelIndex = levels.indexOf(level);
    
    return messageLevelIndex >= configLevelIndex;
  }
  
  private formatMessage(level: LogLevel, message: string, data?: unknown): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level.toUpperCase()}] ${message}`;
  }
  
  debug(message: string, data?: unknown): void {
    if (this.shouldLog('debug')) {
      console.log(this.formatMessage('debug', message), data || '');
    }
  }
  
  info(message: string, data?: unknown): void {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('info', message), data || '');
    }
  }
  
  warn(message: string, data?: unknown): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('warn', message), data || '');
    }
  }
  
  error(message: string, error?: Error | unknown): void {
    if (this.shouldLog('error')) {
      console.error(this.formatMessage('error', message), error || '');
      
      // In production, send to error reporting service
      if (this.config.app.environment === 'production' && error instanceof Error) {
        // TODO: Integrate with error reporting service (e.g., Sentry)
        // Example: Sentry.captureException(error);
      }
    }
  }
  
  // Group related logs
  group(label: string): void {
    if (this.config.logging.enabled) {
      console.group(label);
    }
  }
  
  groupEnd(): void {
    if (this.config.logging.enabled) {
      console.groupEnd();
    }
  }
  
  // Performance logging
  time(label: string): void {
    if (this.config.logging.enabled) {
      console.time(label);
    }
  }
  
  timeEnd(label: string): void {
    if (this.config.logging.enabled) {
      console.timeEnd(label);
    }
  }
}

// Export singleton instance
export const logger = new Logger();
import { useEffect, useCallback } from 'react';
import socketService from '../services/socket.service';

interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { onConnect, onDisconnect, onError } = options;

  useEffect(() => {
    const socket = socketService.getSocket();

    if (!socket) return;

    // 연결 이벤트 리스너
    if (onConnect) {
      socket.on('connect', onConnect);
    }

    if (onDisconnect) {
      socket.on('disconnect', onDisconnect);
    }

    if (onError) {
      socket.on('connect_error', onError);
    }

    // 클린업
    return () => {
      if (onConnect) socket.off('connect', onConnect);
      if (onDisconnect) socket.off('disconnect', onDisconnect);
      if (onError) socket.off('connect_error', onError);
    };
  }, [onConnect, onDisconnect, onError]);

  const on = useCallback((event: string, callback: (...args: any[]) => void) => {
    socketService.on(event, callback);
  }, []);

  const off = useCallback((event: string, callback?: (...args: any[]) => void) => {
    socketService.off(event, callback);
  }, []);

  const emit = useCallback((event: string, ...args: any[]) => {
    const socket = socketService.getSocket();
    if (socket?.connected) {
      socket.emit(event, ...args);
    }
  }, []);

  return {
    on,
    off,
    emit,
    socket: socketService.getSocket(),
  };
};

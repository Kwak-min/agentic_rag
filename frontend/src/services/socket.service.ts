import { io, Socket } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

class SocketService {
  private socket: Socket | null = null;

  /**
   * 소켓 연결
   */
  connect(token: string): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(SOCKET_URL, {
      auth: {
        token: `Bearer ${token}`,
      },
      transports: ['websocket', 'polling'],
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket 연결 성공');
    });

    this.socket.on('disconnect', () => {
      console.log('❌ WebSocket 연결 해제');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket 연결 오류:', error);
    });

    return this.socket;
  }

  /**
   * 소켓 연결 해제
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * 소켓 인스턴스 가져오기
   */
  getSocket(): Socket | null {
    return this.socket;
  }

  /**
   * 채팅 메시지 전송
   */
  sendChatMessage(message: string): void {
    if (this.socket?.connected) {
      this.socket.emit('chat_message', { message });
    } else {
      console.error('WebSocket이 연결되지 않았습니다');
    }
  }

  /**
   * 수위 데이터 구독
   */
  subscribeToWaterData(location?: string): void {
    if (this.socket?.connected) {
      this.socket.emit('water_subscribe', { location });
    }
  }

  /**
   * 수위 데이터 구독 해제
   */
  unsubscribeFromWaterData(): void {
    if (this.socket?.connected) {
      this.socket.emit('water_unsubscribe');
    }
  }

  /**
   * 이벤트 리스너 등록
   */
  on(event: string, callback: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  /**
   * 이벤트 리스너 제거
   */
  off(event: string, callback?: (...args: any[]) => void): void {
    if (this.socket) {
      if (callback) {
        this.socket.off(event, callback);
      } else {
        this.socket.off(event);
      }
    }
  }
}

export default new SocketService();

import { useAuthStore } from "@/store/authStore";

const WS_BASE_URL = (import.meta as any).env?.VITE_WS_URL || "ws://localhost:8000/notifications/ws";

class WebSocketService {
    private socket: WebSocket | null = null;
    private listeners: ((data: any) => void)[] = [];

    connect() {
        const token = useAuthStore.getState().token;
        if (!token || this.socket) return;

        this.socket = new WebSocket(`${WS_BASE_URL}?token=${token}`);

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.listeners.forEach((listener) => listener(data));
        };

        this.socket.onclose = () => {
            this.socket = null;
            // Attempt reconnect after 5s
            setTimeout(() => this.connect(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            this.socket?.close();
        };
    }

    subscribe(callback: (data: any) => void) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter((l) => l !== callback);
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

export const wsService = new WebSocketService();

class WebSocketService {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.listeners = new Map();
    }
    
    connect(token) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            return;
        }
        
        const wsUrl = `ws://${window.location.host}/api/v1/ws?token=${token}`;
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            
            // Отправляем подписки
            this.socket.send(JSON.stringify({
                type: 'subscribe',
                events: ['task_assigned', 'order_status_changed', 'low_stock']
            }));
        };
        
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect(token);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleMessage(data) {
        const { type } = data;
        
        // Вызываем зарегистрированные обработчики
        if (this.listeners.has(type)) {
            this.listeners.get(type).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${type} handler:`, error);
                }
            });
        }
        
        // Общие обработчики
        switch (type) {
            case 'task_assigned':
                this.showNotification(data);
                this.refreshTasks();
                break;
                
            case 'low_stock':
                this.showAlert(data);
                this.refreshInventory();
                break;
                
            case 'order_status_changed':
                this.updateOrderStatus(data);
                break;
        }
    }
    
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    showNotification(data) {
        // Используем Toast уведомления
        if (window.toast) {
            window.toast({
                title: 'Новая задача',
                message: data.message,
                type: 'info',
                duration: 5000
            });
        } else {
            // Fallback
            alert(`Уведомление: ${data.message}`);
        }
    }
    
    attemptReconnect(token) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            console.log(`Reconnecting in ${delay}ms...`);
            setTimeout(() => this.connect(token), delay);
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

// Использование
const wsService = new WebSocketService();

// В компоненте React/Vue
export function useWebSocket(token) {
    useEffect(() => {
        wsService.connect(token);
        
        // Подписываемся на события
        wsService.on('task_assigned', (data) => {
            console.log('Task assigned:', data);
            // Обновляем состояние
        });
        
        wsService.on('order_status_changed', (data) => {
            console.log('Order status changed:', data);
            // Обновляем UI
        });
        
        return () => {
            wsService.disconnect();
        };
    }, [token]);
}
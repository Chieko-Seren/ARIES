# 前端 API 文档

本文档详细说明 ARIES 系统的前端 API 接口。

## 目录

1. [API 客户端](#api-客户端)
2. [状态管理](#状态管理)
3. [工具函数](#工具函数)
4. [组件接口](#组件接口)
5. [类型定义](#类型定义)

## API 客户端

### 创建客户端实例

```typescript
import { createApiClient } from '@/api/client';

const api = createApiClient({
    baseURL: process.env.VUE_APP_API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});
```

### 请求拦截器

```typescript
api.interceptors.request.use(
    (config) => {
        // 添加认证令牌
        const token = store.getters['auth/token'];
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);
```

### 响应拦截器

```typescript
api.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    // 处理未认证
                    store.dispatch('auth/logout');
                    router.push('/login');
                    break;
                case 403:
                    // 处理无权限
                    router.push('/403');
                    break;
                case 429:
                    // 处理限流
                    showRateLimitError();
                    break;
            }
        }
        return Promise.reject(error);
    }
);
```

## 状态管理

### 认证状态

```typescript
// store/modules/auth.ts
export interface AuthState {
    token: string | null;
    user: User | null;
    permissions: string[];
}

export const auth = {
    namespaced: true,
    state: (): AuthState => ({
        token: null,
        user: null,
        permissions: []
    }),
    mutations: {
        SET_TOKEN(state, token: string) {
            state.token = token;
        },
        SET_USER(state, user: User) {
            state.user = user;
        },
        SET_PERMISSIONS(state, permissions: string[]) {
            state.permissions = permissions;
        }
    },
    actions: {
        async login({ commit }, credentials: LoginCredentials) {
            const { data } = await api.post('/auth/login', credentials);
            commit('SET_TOKEN', data.access_token);
            commit('SET_USER', data.user);
            return data;
        },
        async logout({ commit }) {
            await api.post('/auth/logout');
            commit('SET_TOKEN', null);
            commit('SET_USER', null);
            commit('SET_PERMISSIONS', []);
        }
    }
};
```

### 网络分析状态

```typescript
// store/modules/network.ts
export interface NetworkState {
    trafficStats: TrafficStats | null;
    alerts: Alert[];
    loading: boolean;
    error: string | null;
}

export const network = {
    namespaced: true,
    state: (): NetworkState => ({
        trafficStats: null,
        alerts: [],
        loading: false,
        error: null
    }),
    mutations: {
        SET_TRAFFIC_STATS(state, stats: TrafficStats) {
            state.trafficStats = stats;
        },
        SET_ALERTS(state, alerts: Alert[]) {
            state.alerts = alerts;
        },
        SET_LOADING(state, loading: boolean) {
            state.loading = loading;
        },
        SET_ERROR(state, error: string | null) {
            state.error = error;
        }
    },
    actions: {
        async fetchTrafficStats({ commit }, params: TrafficStatsParams) {
            commit('SET_LOADING', true);
            try {
                const { data } = await api.get('/network/traffic/stats', { params });
                commit('SET_TRAFFIC_STATS', data);
            } catch (error) {
                commit('SET_ERROR', error.message);
            } finally {
                commit('SET_LOADING', false);
            }
        }
    }
};
```

## 工具函数

### 请求工具

```typescript
// utils/request.ts
export const request = async <T>(
    url: string,
    options: RequestOptions = {}
): Promise<T> => {
    const {
        method = 'GET',
        data,
        params,
        headers = {},
        timeout = 10000
    } = options;

    try {
        const response = await api.request({
            url,
            method,
            data,
            params,
            headers,
            timeout
        });
        return response.data;
    } catch (error) {
        handleRequestError(error);
        throw error;
    }
};
```

### WebSocket 工具

```typescript
// utils/websocket.ts
export class WebSocketClient {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private readonly maxReconnectAttempts = 5;

    constructor(
        private url: string,
        private options: WebSocketOptions = {}
    ) {}

    connect() {
        this.ws = new WebSocket(this.url);
        this.setupEventHandlers();
    }

    private setupEventHandlers() {
        if (!this.ws) return;

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this.options.onOpen?.();
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.options.onMessage?.(data);
        };

        this.ws.onclose = () => {
            this.handleReconnect();
        };

        this.ws.onerror = (error) => {
            this.options.onError?.(error);
        };
    }

    private handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 1000 * Math.pow(2, this.reconnectAttempts));
        }
    }

    send(data: any) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    close() {
        this.ws?.close();
    }
}
```

## 组件接口

### 网络流量图表组件

```typescript
// components/NetworkTrafficChart.vue
export interface NetworkTrafficChartProps {
    data: TrafficData[];
    height?: number;
    showLegend?: boolean;
    refreshInterval?: number;
}

export interface NetworkTrafficChartEvents {
    (event: 'update', data: TrafficData[]): void;
    (event: 'error', error: Error): void;
}
```

### 告警列表组件

```typescript
// components/AlertList.vue
export interface AlertListProps {
    alerts: Alert[];
    loading?: boolean;
    pagination?: PaginationOptions;
    filterOptions?: AlertFilterOptions;
}

export interface AlertListEvents {
    (event: 'update', alerts: Alert[]): void;
    (event: 'filter', options: AlertFilterOptions): void;
    (event: 'page-change', page: number): void;
}
```

## 类型定义

### 通用类型

```typescript
// types/common.ts
export interface Pagination {
    page: number;
    per_page: number;
    total: number;
}

export interface ApiResponse<T> {
    code: number;
    message: string;
    data: T;
}

export interface ErrorResponse {
    code: number;
    message: string;
    errors?: Array<{
        field: string;
        message: string;
    }>;
}
```

### 网络分析类型

```typescript
// types/network.ts
export interface TrafficStats {
    total_bytes: number;
    total_packets: number;
    protocols: {
        tcp: number;
        udp: number;
        icmp: number;
    };
    timeline: Array<{
        timestamp: string;
        bytes: number;
        packets: number;
    }>;
}

export interface Alert {
    id: number;
    type: string;
    severity: 'low' | 'medium' | 'high';
    source_ip: string;
    destination_ip: string;
    description: string;
    created_at: string;
    status: 'active' | 'resolved';
}

export interface TrafficData {
    timestamp: string;
    bytes: number;
    packets: number;
    protocol: string;
    source_ip: string;
    destination_ip: string;
    source_port: number;
    destination_port: number;
}
```

### 用户类型

```typescript
// types/user.ts
export interface User {
    id: number;
    username: string;
    email: string;
    role: string;
    created_at: string;
    last_login: string;
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export interface AuthTokens {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}
```

## 使用示例

### 获取网络流量统计

```typescript
import { useStore } from 'vuex';
import { computed, onMounted } from 'vue';

export default {
    setup() {
        const store = useStore();
        const trafficStats = computed(() => store.state.network.trafficStats);
        const loading = computed(() => store.state.network.loading);

        onMounted(async () => {
            await store.dispatch('network/fetchTrafficStats', {
                start_time: '2024-01-01T00:00:00Z',
                end_time: '2024-01-02T00:00:00Z',
                interval: '1h'
            });
        });

        return {
            trafficStats,
            loading
        };
    }
};
```

### 实时流量监控

```typescript
import { ref, onMounted, onUnmounted } from 'vue';
import { WebSocketClient } from '@/utils/websocket';

export default {
    setup() {
        const trafficData = ref([]);
        const ws = new WebSocketClient('ws://host:port/ws/network/traffic', {
            onMessage: (data) => {
                trafficData.value.push(data);
                if (trafficData.value.length > 100) {
                    trafficData.value.shift();
                }
            },
            onError: (error) => {
                console.error('WebSocket error:', error);
            }
        });

        onMounted(() => {
            ws.connect();
            ws.send({
                action: 'subscribe',
                channel: 'traffic',
                params: {
                    interval: '1s',
                    filter: {
                        protocols: ['tcp', 'udp'],
                        ports: [80, 443]
                    }
                }
            });
        });

        onUnmounted(() => {
            ws.close();
        });

        return {
            trafficData
        };
    }
};
``` 
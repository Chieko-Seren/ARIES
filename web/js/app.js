// 导入依赖
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import ModelManager from './components/ModelManager.js';
import ModelSettings from './components/ModelSettings.js';

// Vue 应用程序
const { createApp, ref, onMounted, watch } = Vue;

// 初始化模型管理器
ModelManager.init();

// 常量定义
const OPENAI_API_URL = 'https://api.moleapi.com/v1/chat/completions';
const OPENAI_API_KEY = 'sk-lZSmH5ZCX4boiBkaZNkwXkiBKSQ0C7YhHw20D8y3fjr29pUc';  // 请设置您的 API 密钥

// 状态管理
const currentView = ref('dashboard');
const servers = ref([]);
const recentLogs = ref([]);
const plugins = ref([]);
const searchResults = ref([]);
const ciscoPrompt = ref('');
const generatedConfig = ref('');
const searchQuery = ref('');
const showAddServerModal = ref(false);
const showTerminal = ref(false);
const terminalOutput = ref([]);
const terminalInput = ref('');
const selectedServer = ref(null);
const isConnecting = ref(false);
const sshClient = ref(null);
const vectorData = ref([]);
const serverStats = ref({});
const vectorSpaceChart = ref(null);
const vectorStatsChart = ref(null);
const cpuChart = ref(null);
const memoryChart = ref(null);
const showModelSettings = ref(false);

const app = createApp({
    components: {
        'model-settings': ModelSettings
    },
    
    setup() {
        // 初始化
        onMounted(async () => {
            // 等待 DOM 完全加载
            await new Promise(resolve => setTimeout(resolve, 0));
            
            try {
                loadServersFromCookies();
                loadPlugins();
                loadRecentLogs();
                await initCharts();
                await initVectorSpace();
                startServerMonitoring();
            } catch (error) {
                console.error('初始化失败:', error);
                addLog('初始化失败: ' + error.message);
            }
        });

        // 服务器管理
        const loadServersFromCookies = () => {
            const savedServers = Cookies.get('servers');
            if (savedServers) {
                servers.value = JSON.parse(savedServers);
            }
        };

        const saveServersToCookies = () => {
            Cookies.set('servers', JSON.stringify(servers.value), { expires: 365 });
        };

        const addServer = (server) => {
            servers.value.push({
                ...server,
                id: Date.now(),
                status: 'offline'
            });
            saveServersToCookies();
            addLog(`添加服务器: ${server.name}`);
        };

        // SSH 连接管理
        const connectServer = async (server) => {
            console.log('连接服务器前状态:', {
                showTerminal: showTerminal.value,
                selectedServer: selectedServer.value
            });

            try {
                isConnecting.value = true;
                selectedServer.value = server;
                showTerminal.value = true;
                addLog(`正在连接到服务器 ${server.name} (${server.ip})...`);

                // 创建 WebSocket SSH 连接
                const ws = new WebSocket(`ws://${window.location.hostname}:8080/ssh`);
                
                ws.onopen = () => {
                    // 发送连接信息
                    ws.send(JSON.stringify({
                        type: 'connect',
                        host: server.ip,
                        port: server.port || 22,
                        username: server.username,
                        password: server.password,
                        privateKey: server.privateKey
                    }));
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    switch (data.type) {
                        case 'connected':
                            terminalOutput.value.push(`已连接到 ${server.name} (${server.ip})`);
                            terminalOutput.value.push('欢迎使用 ARIES Web 终端');
                            terminalOutput.value.push('输入 "help" 获取可用命令列表');
                            server.status = 'online';
                            saveServersToCookies();
                            break;
                        case 'output':
                            terminalOutput.value.push(data.content);
                            break;
                        case 'error':
                            throw new Error(data.message);
                    }
                };

                ws.onerror = (error) => {
                    throw new Error('WebSocket 连接错误: ' + error.message);
                };

                ws.onclose = () => {
                    server.status = 'offline';
                    saveServersToCookies();
                    if (showTerminal.value) {
                        terminalOutput.value.push('连接已关闭');
                    }
                };

                // 保存 WebSocket 连接
                sshClient.value = ws;
            } catch (error) {
                console.error('连接服务器失败:', error);
                addLog('连接服务器失败: ' + error.message);
                server.status = 'offline';
                saveServersToCookies();
                showTerminal.value = false;
                selectedServer.value = null;
            } finally {
                isConnecting.value = false;
                console.log('连接服务器后状态:', {
                    showTerminal: showTerminal.value,
                    selectedServer: selectedServer.value
                });
            }
        };

        const closeTerminal = () => {
            console.log('关闭终端前状态:', {
                showTerminal: showTerminal.value,
                selectedServer: selectedServer.value
            });

            if (sshClient.value) {
                sshClient.value.close();
                sshClient.value = null;
            }
            
            // 确保按正确的顺序重置状态
            terminalOutput.value = [];
            terminalInput.value = '';
            selectedServer.value = null;
            isConnecting.value = false;
            showTerminal.value = false;

            console.log('关闭终端后状态:', {
                showTerminal: showTerminal.value,
                selectedServer: selectedServer.value
            });
        };

        // 终端操作
        const handleTerminalInput = async (event) => {
            if (event.key === 'Enter') {
                const command = terminalInput.value.trim();
                if (!command) return;

                terminalOutput.value.push(`$ ${command}`);
                terminalInput.value = '';

                try {
                    if (command === 'help') {
                        showHelp();
                    } else if (command === 'clear') {
                        terminalOutput.value = [];
                    } else if (command === 'exit') {
                        closeTerminal();
                    } else if (command.startsWith('llm ')) {
                        await handleLLMCommand(command.substring(4));
                    } else {
                        await executeSSHCommand(command);
                    }
                } catch (error) {
                    terminalOutput.value.push(`错误: ${error.message}`);
                }
            }
        };

        const executeSSHCommand = async (command) => {
            if (!sshClient.value) {
                throw new Error('未连接到服务器');
            }

            return new Promise((resolve, reject) => {
                try {
                    sshClient.value.send(JSON.stringify({
                        type: 'command',
                        command: command
                    }));
                    resolve();
                } catch (error) {
                    reject(error);
                }
            });
        };

        const handleLLMCommand = async (prompt) => {
            try {
                const systemMessage = '你是一个专业的网络工程师，精通服务器管理和网络配置。请根据用户的自然语言描述，生成相应的命令并解释其作用。';
                
                terminalOutput.value.push('正在使用 ' + ModelManager.getCurrentModelConfig().name + ' 处理请求...');
                
                const response = await ModelManager.callModelAPI(
                    `当前服务器信息：${JSON.stringify(selectedServer.value)}\n用户请求：${prompt}`,
                    systemMessage
                );
                
                terminalOutput.value.push('LLM 分析:');
                terminalOutput.value.push(response);
                
            } catch (error) {
                console.error('LLM处理失败:', error);
                terminalOutput.value.push(`错误: ${error.message}`);
                
                if (error.message.includes('API密钥')) {
                    showModelSettings.value = true;
                }
            }
        };

        // 图表初始化
        const initCharts = async () => {
            // 等待 DOM 元素加载
            await new Promise(resolve => {
                const checkElement = () => {
                    const cpuCtx = document.getElementById('cpuChart');
                    const memoryCtx = document.getElementById('memoryChart');
                    if (cpuCtx && memoryCtx) {
                        resolve();
                    } else {
                        setTimeout(checkElement, 100);
                    }
                };
                checkElement();
            });

            // CPU 使用率图表
            const cpuCtx = document.getElementById('cpuChart').getContext('2d');
            cpuChart.value = new Chart(cpuCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU 使用率',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            // 内存使用率图表
            const memoryCtx = document.getElementById('memoryChart').getContext('2d');
            memoryChart.value = new Chart(memoryCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '内存使用率',
                        data: [],
                        borderColor: 'rgb(153, 102, 255)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        };

        // 向量空间可视化
        const initVectorSpace = async () => {
            // 等待 DOM 元素加载
            await new Promise(resolve => {
                const checkElement = () => {
                    const canvas = document.getElementById('vectorSpace');
                    if (canvas) {
                        resolve();
                    } else {
                        setTimeout(checkElement, 100);
                    }
                };
                checkElement();
            });

            try {
                const canvas = document.getElementById('vectorSpace');
                const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
                
                // 使用导入的 OrbitControls，而不是 THREE.OrbitControls
                const controls = new OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;

                // 设置场景
                scene.background = new THREE.Color(0x1a1a1a);
                camera.position.z = 5;

                // 添加坐标轴
                const axesHelper = new THREE.AxesHelper(5);
                scene.add(axesHelper);

                // 创建向量点
                const createVectorPoints = (vectors) => {
                    const geometry = new THREE.BufferGeometry();
                    const positions = [];
                    const colors = [];

                    vectors.forEach(vector => {
                        positions.push(vector.x, vector.y, vector.z);
                        colors.push(vector.color.r, vector.color.g, vector.color.b);
                    });

                    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
                    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

                    const material = new THREE.PointsMaterial({
                        size: 0.1,
                        vertexColors: true
                    });

                    return new THREE.Points(geometry, material);
                };

                // 动画循环
                const animate = () => {
                    requestAnimationFrame(animate);
                    controls.update();
                    renderer.render(scene, camera);
                };

                // 更新向量数据
                const updateVectorSpace = (vectors) => {
                    scene.remove(scene.getObjectByName('vectorPoints'));
                    const points = createVectorPoints(vectors);
                    points.name = 'vectorPoints';
                    scene.add(points);
                };

                // 初始向量数据
                const generateRandomVectors = (count) => {
                    const vectors = [];
                    for (let i = 0; i < count; i++) {
                        vectors.push({
                            x: Math.random() * 10 - 5,
                            y: Math.random() * 10 - 5,
                            z: Math.random() * 10 - 5,
                            color: {
                                r: Math.random(),
                                g: Math.random(),
                                b: Math.random()
                            }
                        });
                    }
                    return vectors;
                };

                // 初始化向量数据
                vectorData.value = generateRandomVectors(100);
                updateVectorSpace(vectorData.value);

                // 启动动画
                animate();

                // 响应式调整
                window.addEventListener('resize', () => {
                    const width = canvas.clientWidth;
                    const height = canvas.clientHeight;
                    camera.aspect = width / height;
                    camera.updateProjectionMatrix();
                    renderer.setSize(width, height);
                });

                // 保存图表实例
                vectorSpaceChart.value = {
                    scene,
                    camera,
                    renderer,
                    controls,
                    points: scene.getObjectByName('vectorPoints')
                };

            } catch (error) {
                console.error('初始化向量空间失败:', error);
                addLog('初始化向量空间失败: ' + error.message);
            }
        };

        // 服务器监控
        const startServerMonitoring = () => {
            setInterval(async () => {
                for (const server of servers.value) {
                    if (server.status === 'online') {
                        try {
                            const stats = await fetchServerStats(server);
                            updateServerCharts(server, stats);
                        } catch (error) {
                            console.error(`获取服务器 ${server.name} 状态失败:`, error);
                        }
                    }
                }
            }, 5000);
        };

        const fetchServerStats = async (server) => {
            if (!sshClient.value) return null;

            const cpuCommand = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'";
            const memoryCommand = "free | grep Mem | awk '{print $3/$2 * 100.0}'";

            const [cpuOutput, memoryOutput] = await Promise.all([
                executeSSHCommand(cpuCommand),
                executeSSHCommand(memoryCommand)
            ]);

            return {
                cpu: parseFloat(cpuOutput.trim()),
                memory: parseFloat(memoryOutput.trim())
            };
        };

        const updateServerCharts = (server, stats) => {
            const timestamp = new Date().toLocaleTimeString();
            
            // 更新 CPU 图表
            cpuChart.value.data.labels.push(timestamp);
            cpuChart.value.data.datasets[0].data.push(stats.cpu);
            if (cpuChart.value.data.labels.length > 20) {
                cpuChart.value.data.labels.shift();
                cpuChart.value.data.datasets[0].data.shift();
            }
            cpuChart.value.update();

            // 更新内存图表
            memoryChart.value.data.labels.push(timestamp);
            memoryChart.value.data.datasets[0].data.push(stats.memory);
            if (memoryChart.value.data.labels.length > 20) {
                memoryChart.value.data.labels.shift();
                memoryChart.value.data.datasets[0].data.shift();
            }
            memoryChart.value.update();
        };

        // 插件管理
        const loadPlugins = async () => {
            try {
                // 这里应该从后端 API 获取插件列表
                // 示例数据
                plugins.value = [
                    {
                        id: 1,
                        name: '网络监控',
                        description: '实时监控网络状态和性能',
                        enabled: true
                    },
                    {
                        id: 2,
                        name: '配置备份',
                        description: '自动备份网络设备配置',
                        enabled: false
                    },
                    {
                        id: 3,
                        name: '安全审计',
                        description: '执行网络安全审计和漏洞扫描',
                        enabled: false
                    }
                ];
            } catch (error) {
                console.error('加载插件列表失败:', error);
                addLog('加载插件列表失败: ' + error.message);
            }
        };

        const togglePlugin = async (plugin) => {
            try {
                // 这里应该实现实际的插件启用/禁用逻辑
                plugin.enabled = !plugin.enabled;
                addLog(`${plugin.name} 插件已${plugin.enabled ? '启用' : '禁用'}`);
            } catch (error) {
                console.error('切换插件状态失败:', error);
                addLog('切换插件状态失败: ' + error.message);
            }
        };

        // 知识库管理
        const searchVectors = async () => {
            try {
                if (!searchQuery.value.trim()) {
                    throw new Error('请输入搜索关键词');
                }
                
                const systemMessage = '你是一个专业的搜索助手，请根据用户的搜索请求，生成相关的搜索关键词和过滤条件。';
                
                // 使用当前模型生成搜索优化
                const searchOptimization = await ModelManager.callModelAPI(
                    searchQuery.value,
                    systemMessage
                );
                
                // 执行向量搜索
                const response = await fetch('/api/vector/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: searchQuery.value,
                        optimization: searchOptimization
                    })
                });
                
                if (!response.ok) {
                    throw new Error('搜索请求失败');
                }
                
                const data = await response.json();
                searchResults.value = data.results;
                
            } catch (error) {
                console.error('搜索失败:', error);
                searchResults.value = [{
                    title: '错误',
                    content: error.message,
                    similarity: 0
                }];
                
                if (error.message.includes('API密钥')) {
                    showModelSettings.value = true;
                }
            }
        };

        // 日志管理
        const addLog = (message) => {
            const log = {
                id: Date.now(),
                message,
                timestamp: new Date().toLocaleString()
            };
            recentLogs.value.unshift(log);
            if (recentLogs.value.length > 10) {
                recentLogs.value.pop();
            }
        };

        const loadRecentLogs = async () => {
            try {
                // 这里应该从后端 API 获取最近日志
                // 示例数据
                recentLogs.value = [
                    {
                        id: 1,
                        message: '系统启动完成',
                        timestamp: new Date().toLocaleString()
                    }
                ];
            } catch (error) {
                console.error('加载最近日志失败:', error);
            }
        };

        // 工具函数
        const openTerminal = () => {
            if (!selectedServer.value) {
                addLog('请先选择一个服务器');
                return;
            }
            showTerminal.value = true;
        };

        const openNetworkConfig = () => {
            currentView.value = 'network';
        };

        // 网络配置生成
        const generateCiscoConfig = async () => {
            try {
                if (!ciscoPrompt.value.trim()) {
                    throw new Error('请输入配置描述');
                }
                
                const systemMessage = '你是一个专业的网络工程师，精通Cisco设备配置。请根据用户的自然语言描述，生成相应的Cisco配置命令。';
                
                generatedConfig.value = '正在使用 ' + ModelManager.getCurrentModelConfig().name + ' 生成配置...';
                
                const response = await ModelManager.callModelAPI(ciscoPrompt.value, systemMessage);
                
                generatedConfig.value = response;
                
            } catch (error) {
                console.error('生成配置失败:', error);
                generatedConfig.value = `错误: ${error.message}`;
                
                if (error.message.includes('API密钥')) {
                    showModelSettings.value = true;
                }
            }
        };

        // 调试函数
        const debugState = () => {
            console.log('当前状态:', {
                showTerminal: showTerminal.value,
                selectedServer: selectedServer.value,
                isConnecting: isConnecting.value
            });
        };

        // 添加模型设置相关方法
        const toggleModelSettings = () => {
            showModelSettings.value = !showModelSettings.value;
        };

        return {
            // 状态
            currentView,
            servers,
            recentLogs,
            plugins,
            searchResults,
            ciscoPrompt,
            generatedConfig,
            searchQuery,
            showAddServerModal,
            showTerminal,
            terminalOutput,
            terminalInput,
            selectedServer,
            isConnecting,
            vectorSpaceChart,
            vectorStatsChart,
            cpuChart,
            memoryChart,
            sshClient,
            vectorData,
            serverStats,
            showModelSettings,

            // 方法
            connectServer,
            handleTerminalInput,
            generateCiscoConfig,
            togglePlugin,
            searchVectors,
            openTerminal,
            openNetworkConfig,
            closeTerminal,
            handleLLMCommand,
            debugState,
            toggleModelSettings
        };
    }
});

// 等待 DOM 加载完成后挂载应用
document.addEventListener('DOMContentLoaded', () => {
    const vm = app.mount('#app');
    // 将应用实例添加到 window 对象，方便调试
    window.appInstance = vm;
    console.log('Vue 应用已挂载，初始状态:', {
        showTerminal: vm.showTerminal,
        selectedServer: vm.selectedServer
    });
}); 
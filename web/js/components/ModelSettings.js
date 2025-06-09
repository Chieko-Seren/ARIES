// 模型设置组件
const ModelSettings = {
    template: `
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-6">模型设置</h2>
            
            <!-- 模型选择 -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">选择模型</label>
                <select v-model="selectedModel" 
                        @change="handleModelChange"
                        class="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500">
                    <option v-for="model in availableModels" 
                            :key="model.type" 
                            :value="model.type">
                        {{ model.name }} ({{ model.provider }})
                    </option>
                </select>
            </div>
            
            <!-- API密钥设置 -->
            <div class="space-y-4">
                <!-- OpenAI API密钥 -->
                <div v-if="showOpenAIKey">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        OpenAI API密钥
                    </label>
                    <div class="flex space-x-2">
                        <input type="password" 
                               v-model="apiKeys.openai"
                               @change="saveAPIKey('openai')"
                               class="flex-1 p-2 border rounded focus:ring-2 focus:ring-blue-500"
                               placeholder="输入OpenAI API密钥">
                        <button @click="toggleAPIKeyVisibility('openai')"
                                class="px-3 py-2 bg-gray-100 rounded hover:bg-gray-200">
                            {{ showKeys.openai ? '隐藏' : '显示' }}
                        </button>
                    </div>
                </div>
                
                <!-- Claude API密钥 -->
                <div v-if="showClaudeKey">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Claude API密钥
                    </label>
                    <div class="flex space-x-2">
                        <input type="password" 
                               v-model="apiKeys.claude"
                               @change="saveAPIKey('claude')"
                               class="flex-1 p-2 border rounded focus:ring-2 focus:ring-blue-500"
                               placeholder="输入Claude API密钥">
                        <button @click="toggleAPIKeyVisibility('claude')"
                                class="px-3 py-2 bg-gray-100 rounded hover:bg-gray-200">
                            {{ showKeys.claude ? '隐藏' : '显示' }}
                        </button>
                    </div>
                </div>
                
                <!-- Gemini API密钥 -->
                <div v-if="showGeminiKey">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Gemini API密钥
                    </label>
                    <div class="flex space-x-2">
                        <input type="password" 
                               v-model="apiKeys.gemini"
                               @change="saveAPIKey('gemini')"
                               class="flex-1 p-2 border rounded focus:ring-2 focus:ring-blue-500"
                               placeholder="输入Gemini API密钥">
                        <button @click="toggleAPIKeyVisibility('gemini')"
                                class="px-3 py-2 bg-gray-100 rounded hover:bg-gray-200">
                            {{ showKeys.gemini ? '隐藏' : '显示' }}
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- 模型参数设置 -->
            <div class="mt-6 space-y-4">
                <h3 class="text-lg font-medium text-gray-700">模型参数</h3>
                
                <!-- 温度设置 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        温度 (Temperature)
                        <span class="text-gray-500">({{ modelConfig.temperature }})</span>
                    </label>
                    <input type="range" 
                           v-model="modelConfig.temperature"
                           min="0" 
                           max="1" 
                           step="0.1"
                           @change="saveModelConfig"
                           class="w-full">
                </div>
                
                <!-- 最大token数 -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        最大Token数
                    </label>
                    <input type="number" 
                           v-model="modelConfig.maxTokens"
                           @change="saveModelConfig"
                           class="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500"
                           :min="100"
                           :max="modelConfig.contextLength">
                </div>
            </div>
            
            <!-- 状态提示 -->
            <div v-if="statusMessage" 
                 :class="['mt-4 p-3 rounded', 
                         statusType === 'success' ? 'bg-green-100 text-green-700' : 
                         statusType === 'error' ? 'bg-red-100 text-red-700' : 
                         'bg-blue-100 text-blue-700']">
                {{ statusMessage }}
            </div>
        </div>
    `,

    setup() {
        const { ref, computed, onMounted } = Vue;
        
        // 状态变量
        const selectedModel = ref(ModelManager.currentModel);
        const apiKeys = ref({
            openai: '',
            claude: '',
            gemini: ''
        });
        const showKeys = ref({
            openai: false,
            claude: false,
            gemini: false
        });
        const modelConfig = ref({...ModelManager.getCurrentModelConfig()});
        const statusMessage = ref('');
        const statusType = ref('info');
        
        // 计算属性
        const availableModels = computed(() => ModelManager.getAvailableModels());
        const showOpenAIKey = computed(() => 
            ['gpt4', 'gpt35'].includes(selectedModel.value));
        const showClaudeKey = computed(() => 
            selectedModel.value === ModelManager.ModelType.CLAUDE);
        const showGeminiKey = computed(() => 
            selectedModel.value === ModelManager.ModelType.GEMINI);
        
        // 方法
        const handleModelChange = () => {
            ModelManager.switchModel(selectedModel.value);
            modelConfig.value = {...ModelManager.getCurrentModelConfig()};
            showStatus('已切换到模型: ' + modelConfig.value.name, 'success');
        };
        
        const saveAPIKey = (provider) => {
            const key = apiKeys.value[provider];
            if (key) {
                localStorage.setItem(`${provider}_api_key`, key);
                showStatus(`${provider} API密钥已保存`, 'success');
            }
        };
        
        const toggleAPIKeyVisibility = (provider) => {
            showKeys.value[provider] = !showKeys.value[provider];
        };
        
        const saveModelConfig = () => {
            try {
                ModelManager.modelConfigs[selectedModel.value] = {
                    ...ModelManager.modelConfigs[selectedModel.value],
                    ...modelConfig.value
                };
                localStorage.setItem('model_config', JSON.stringify(ModelManager.modelConfigs));
                showStatus('模型配置已保存', 'success');
            } catch (error) {
                showStatus('保存配置失败: ' + error.message, 'error');
            }
        };
        
        const showStatus = (message, type = 'info') => {
            statusMessage.value = message;
            statusType.value = type;
            setTimeout(() => {
                statusMessage.value = '';
            }, 3000);
        };
        
        // 初始化
        onMounted(() => {
            // 加载保存的API密钥
            apiKeys.value.openai = localStorage.getItem('openai_api_key') || '';
            apiKeys.value.claude = localStorage.getItem('claude_api_key') || '';
            apiKeys.value.gemini = localStorage.getItem('gemini_api_key') || '';
            
            // 加载保存的模型配置
            const savedConfig = localStorage.getItem('model_config');
            if (savedConfig) {
                try {
                    const configs = JSON.parse(savedConfig);
                    ModelManager.modelConfigs = {...ModelManager.modelConfigs, ...configs};
                    modelConfig.value = {...ModelManager.getCurrentModelConfig()};
                } catch (error) {
                    console.error('加载模型配置失败:', error);
                }
            }
        });
        
        return {
            selectedModel,
            availableModels,
            apiKeys,
            showKeys,
            modelConfig,
            statusMessage,
            statusType,
            showOpenAIKey,
            showClaudeKey,
            showGeminiKey,
            handleModelChange,
            saveAPIKey,
            toggleAPIKeyVisibility,
            saveModelConfig
        };
    }
};

export default ModelSettings; 
// 模型管理组件
const ModelManager = {
    // 模型类型定义
    ModelType: {
        RWKV4: 'rwkv4',
        RWKV5: 'rwkv5',
        RWKV6: 'rwkv6',
        RWKV7: 'rwkv7',
        GPT4: 'gpt4',
        GPT35: 'gpt35',
        CLAUDE: 'claude',
        GEMINI: 'gemini'
    },

    // 模型配置
    modelConfigs: {
        [ModelType.RWKV4]: {
            name: 'RWKV-4',
            provider: 'rwkv',
            apiEndpoint: '/api/llm/rwkv',
            contextLength: 2048,
            maxTokens: 1000,
            temperature: 0.7
        },
        [ModelType.RWKV5]: {
            name: 'RWKV-5',
            provider: 'rwkv',
            apiEndpoint: '/api/llm/rwkv',
            contextLength: 4096,
            maxTokens: 2000,
            temperature: 0.7
        },
        [ModelType.RWKV6]: {
            name: 'RWKV-6',
            provider: 'rwkv',
            apiEndpoint: '/api/llm/rwkv',
            contextLength: 8192,
            maxTokens: 4000,
            temperature: 0.7
        },
        [ModelType.RWKV7]: {
            name: 'RWKV-7',
            provider: 'rwkv',
            apiEndpoint: '/api/llm/rwkv',
            contextLength: 16384,
            maxTokens: 8000,
            temperature: 0.7
        },
        [ModelType.GPT4]: {
            name: 'GPT-4',
            provider: 'openai',
            apiEndpoint: 'https://api.openai.com/v1/chat/completions',
            contextLength: 8192,
            maxTokens: 4000,
            temperature: 0.7
        },
        [ModelType.GPT35]: {
            name: 'GPT-3.5',
            provider: 'openai',
            apiEndpoint: 'https://api.openai.com/v1/chat/completions',
            contextLength: 4096,
            maxTokens: 2000,
            temperature: 0.7
        },
        [ModelType.CLAUDE]: {
            name: 'Claude',
            provider: 'anthropic',
            apiEndpoint: 'https://api.anthropic.com/v1/messages',
            contextLength: 100000,
            maxTokens: 4000,
            temperature: 0.7
        },
        [ModelType.GEMINI]: {
            name: 'Gemini',
            provider: 'google',
            apiEndpoint: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
            contextLength: 32768,
            maxTokens: 4000,
            temperature: 0.7
        }
    },

    // 当前选中的模型
    currentModel: null,

    // 初始化模型管理器
    init() {
        // 从本地存储加载上次选择的模型
        const savedModel = localStorage.getItem('selectedModel');
        if (savedModel && this.modelConfigs[savedModel]) {
            this.currentModel = savedModel;
        } else {
            // 默认使用RWKV-7
            this.currentModel = this.ModelType.RWKV7;
        }
    },

    // 切换模型
    switchModel(modelType) {
        if (this.modelConfigs[modelType]) {
            this.currentModel = modelType;
            localStorage.setItem('selectedModel', modelType);
            return true;
        }
        return false;
    },

    // 获取当前模型配置
    getCurrentModelConfig() {
        return this.modelConfigs[this.currentModel];
    },

    // 获取所有可用模型
    getAvailableModels() {
        return Object.entries(this.modelConfigs).map(([type, config]) => ({
            type,
            name: config.name,
            provider: config.provider
        }));
    },

    // 调用模型API
    async callModelAPI(prompt, systemMessage = '') {
        const config = this.getCurrentModelConfig();
        
        try {
            let response;
            switch (config.provider) {
                case 'rwkv':
                    response = await this._callRWKVAPI(prompt, systemMessage, config);
                    break;
                case 'openai':
                    response = await this._callOpenAIAPI(prompt, systemMessage, config);
                    break;
                case 'anthropic':
                    response = await this._callClaudeAPI(prompt, systemMessage, config);
                    break;
                case 'google':
                    response = await this._callGeminiAPI(prompt, systemMessage, config);
                    break;
                default:
                    throw new Error(`不支持的模型提供商: ${config.provider}`);
            }
            return response;
        } catch (error) {
            console.error('调用模型API失败:', error);
            throw error;
        }
    },

    // 调用RWKV API
    async _callRWKVAPI(prompt, systemMessage, config) {
        const response = await fetch(config.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: this.currentModel,
                prompt: prompt,
                system_message: systemMessage,
                max_tokens: config.maxTokens,
                temperature: config.temperature
            })
        });

        if (!response.ok) {
            throw new Error(`RWKV API错误: ${response.statusText}`);
        }

        const data = await response.json();
        return data.response;
    },

    // 调用OpenAI API
    async _callOpenAIAPI(prompt, systemMessage, config) {
        const response = await fetch(config.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('openai_api_key')}`
            },
            body: JSON.stringify({
                model: this.currentModel === this.ModelType.GPT4 ? 'gpt-4' : 'gpt-3.5-turbo',
                messages: [
                    {
                        role: 'system',
                        content: systemMessage
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                max_tokens: config.maxTokens,
                temperature: config.temperature
            })
        });

        if (!response.ok) {
            throw new Error(`OpenAI API错误: ${response.statusText}`);
        }

        const data = await response.json();
        return data.choices[0].message.content;
    },

    // 调用Claude API
    async _callClaudeAPI(prompt, systemMessage, config) {
        const response = await fetch(config.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': localStorage.getItem('claude_api_key'),
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: 'claude-3-opus-20240229',
                messages: [
                    {
                        role: 'system',
                        content: systemMessage
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                max_tokens: config.maxTokens,
                temperature: config.temperature
            })
        });

        if (!response.ok) {
            throw new Error(`Claude API错误: ${response.statusText}`);
        }

        const data = await response.json();
        return data.content[0].text;
    },

    // 调用Gemini API
    async _callGeminiAPI(prompt, systemMessage, config) {
        const response = await fetch(`${config.apiEndpoint}?key=${localStorage.getItem('gemini_api_key')}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                contents: [
                    {
                        role: 'user',
                        parts: [
                            {
                                text: `${systemMessage}\n\n${prompt}`
                            }
                        ]
                    }
                ],
                generationConfig: {
                    maxOutputTokens: config.maxTokens,
                    temperature: config.temperature
                }
            })
        });

        if (!response.ok) {
            throw new Error(`Gemini API错误: ${response.statusText}`);
        }

        const data = await response.json();
        return data.candidates[0].content.parts[0].text;
    }
};

export default ModelManager; 
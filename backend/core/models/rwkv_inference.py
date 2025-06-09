import os
from typing import Optional, List, Dict, Any
import torch
from rwkv.model import RWKV
from rwkv.utils import PIPELINE

class RWKVInference:
    def __init__(self, model_path: str, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        """
        初始化RWKV推理类
        
        Args:
            model_path: RWKV模型路径
            device: 运行设备，默认使用GPU（如果可用）或CPU
        """
        self.device = device
        self.model_path = model_path
        self.model = None
        self.pipeline = None
        self._load_model()
    
    def _load_model(self):
        """加载RWKV模型"""
        try:
            self.model = RWKV(model=self.model_path, strategy=f"{self.device} fp16")
            self.pipeline = PIPELINE(self.model)
            print(f"RWKV模型加载成功，使用设备: {self.device}")
        except Exception as e:
            raise Exception(f"RWKV模型加载失败: {str(e)}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 0.7,
        stop_tokens: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用RWKV模型生成文本
        
        Args:
            prompt: 输入提示
            max_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            top_p: 核采样参数
            stop_tokens: 停止生成的token列表
            **kwargs: 其他参数
            
        Returns:
            包含生成结果的字典
        """
        try:
            # 将输入转换为token
            tokens = self.pipeline.encode(prompt)
            
            # 生成文本
            output_tokens = []
            for _ in range(max_tokens):
                token = self.pipeline.sample_logits(
                    logits=self.model.forward(tokens),
                    temperature=temperature,
                    top_p=top_p,
                )
                tokens += [token]
                output_tokens.append(token)
                
                # 检查是否需要停止生成
                if stop_tokens and self.pipeline.decode([token]) in stop_tokens:
                    break
            
            # 解码生成的token
            generated_text = self.pipeline.decode(output_tokens)
            
            return {
                "text": generated_text,
                "tokens": len(output_tokens),
                "finish_reason": "stop" if stop_tokens else "length"
            }
            
        except Exception as e:
            raise Exception(f"RWKV生成失败: {str(e)}")
    
    def get_embeddings(self, text: str) -> torch.Tensor:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本的嵌入向量
        """
        try:
            tokens = self.pipeline.encode(text)
            with torch.no_grad():
                embeddings = self.model.forward(tokens, return_state=True)[1]
            return embeddings
        except Exception as e:
            raise Exception(f"获取嵌入向量失败: {str(e)}")
    
    def __del__(self):
        """清理资源"""
        if self.model is not None:
            del self.model
        if self.pipeline is not None:
            del self.pipeline
        torch.cuda.empty_cache() 
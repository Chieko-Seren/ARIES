#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - Intel 设备优化模块
针对 Intel CPU 的 SIMD 优化实现
"""

import numpy as np
import platform
import logging
from typing import Optional, List, Dict, Any
import os
import ctypes
from ctypes import c_int, c_float, c_double, POINTER, c_void_p
import warnings

logger = logging.getLogger(__name__)

class IntelOptimizer:
    """Intel 设备优化器类"""
    
    def __init__(self):
        """初始化 Intel 优化器"""
        self.is_intel = self._check_intel_cpu()
        self.simd_level = self._detect_simd_level()
        self._load_simd_library()
        
        if self.is_intel:
            logger.info(f"检测到 Intel CPU，SIMD 级别: {self.simd_level}")
        else:
            logger.warning("未检测到 Intel CPU，将使用标准实现")
    
    def _check_intel_cpu(self) -> bool:
        """检查是否为 Intel CPU
        
        Returns:
            是否为 Intel CPU
        """
        try:
            cpu_info = platform.processor().lower()
            return 'intel' in cpu_info or 'core' in cpu_info
        except Exception as e:
            logger.error(f"CPU 检测失败: {str(e)}")
            return False
    
    def _detect_simd_level(self) -> str:
        """检测 SIMD 指令集级别
        
        Returns:
            SIMD 指令集级别
        """
        if not self.is_intel:
            return "none"
            
        try:
            # 使用 CPUID 指令检测 SIMD 支持
            # 这里使用 ctypes 调用 CPUID
            class CPUID:
                def __init__(self):
                    self.libc = ctypes.CDLL('libc.so.6')
                    self.cpuid = self.libc.__get_cpuid
                    self.cpuid.argtypes = [c_int, POINTER(c_int), POINTER(c_int),
                                         POINTER(c_int), POINTER(c_int)]
                
                def get_cpuid(self, leaf: int) -> tuple:
                    eax = c_int(0)
                    ebx = c_int(0)
                    ecx = c_int(0)
                    edx = c_int(0)
                    self.cpuid(leaf, ctypes.byref(eax), ctypes.byref(ebx),
                             ctypes.byref(ecx), ctypes.byref(edx))
                    return (eax.value, ebx.value, ecx.value, edx.value)
            
            cpuid = CPUID()
            _, _, ecx, edx = cpuid.get_cpuid(1)
            
            # 检查各种 SIMD 指令集支持
            if edx & (1 << 25):  # SSE
                if edx & (1 << 26):  # SSE2
                    if ecx & (1 << 0):  # SSE3
                        if ecx & (1 << 9):  # SSSE3
                            if ecx & (1 << 19):  # SSE4.1
                                if ecx & (1 << 20):  # SSE4.2
                                    if ecx & (1 << 28):  # AVX
                                        if ecx & (1 << 12):  # FMA
                                            if ecx & (1 << 5):  # AVX2
                                                return "avx2"
                                            return "avx"
                                        return "sse4.2"
                                    return "sse4.1"
                                return "ssse3"
                            return "sse3"
                        return "sse2"
                    return "sse"
            return "none"
            
        except Exception as e:
            logger.error(f"SIMD 检测失败: {str(e)}")
            return "none"
    
    def _load_simd_library(self):
        """加载 SIMD 优化库"""
        if not self.is_intel:
            return
            
        try:
            # 根据检测到的 SIMD 级别加载对应的优化库
            lib_path = os.path.join(os.path.dirname(__file__), 
                                  f"simd_libs/libsimd_{self.simd_level}.so")
            
            if os.path.exists(lib_path):
                self.simd_lib = ctypes.CDLL(lib_path)
                self._setup_simd_functions()
                logger.info(f"已加载 SIMD 优化库: {lib_path}")
            else:
                logger.warning(f"未找到 SIMD 优化库: {lib_path}")
                self.simd_lib = None
                
        except Exception as e:
            logger.error(f"加载 SIMD 库失败: {str(e)}")
            self.simd_lib = None
    
    def _setup_simd_functions(self):
        """设置 SIMD 函数接口"""
        if not hasattr(self, 'simd_lib') or self.simd_lib is None:
            return
            
        try:
            # 设置向量运算函数
            self.simd_lib.vector_add.argtypes = [
                POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int
            ]
            self.simd_lib.vector_mul.argtypes = [
                POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int
            ]
            self.simd_lib.vector_dot.argtypes = [
                POINTER(c_float), POINTER(c_float), c_int
            ]
            self.simd_lib.vector_dot.restype = c_float
            
            # 设置矩阵运算函数
            self.simd_lib.matrix_mul.argtypes = [
                POINTER(c_float), POINTER(c_float), POINTER(c_float),
                c_int, c_int, c_int
            ]
            
            # 设置统计函数
            self.simd_lib.vector_mean.argtypes = [
                POINTER(c_float), c_int
            ]
            self.simd_lib.vector_mean.restype = c_float
            
            self.simd_lib.vector_std.argtypes = [
                POINTER(c_float), c_int
            ]
            self.simd_lib.vector_std.restype = c_float
            
        except Exception as e:
            logger.error(f"设置 SIMD 函数接口失败: {str(e)}")
            self.simd_lib = None
    
    def optimize_vector_operations(self, data: np.ndarray) -> np.ndarray:
        """优化向量运算
        
        Args:
            data: 输入数据数组
            
        Returns:
            优化后的数据数组
        """
        if not self.is_intel or not hasattr(self, 'simd_lib') or self.simd_lib is None:
            return data
            
        try:
            # 确保数据是连续的内存布局
            if not data.flags['C_CONTIGUOUS']:
                data = np.ascontiguousarray(data)
            
            # 根据数据类型选择优化方法
            if data.dtype == np.float32:
                return self._optimize_float32_vector(data)
            elif data.dtype == np.float64:
                return self._optimize_float64_vector(data)
            else:
                return data
                
        except Exception as e:
            logger.error(f"向量运算优化失败: {str(e)}")
            return data
    
    def _optimize_float32_vector(self, data: np.ndarray) -> np.ndarray:
        """优化 float32 向量运算
        
        Args:
            data: float32 类型的数据数组
            
        Returns:
            优化后的数据数组
        """
        try:
            # 获取数据指针
            data_ptr = data.ctypes.data_as(POINTER(c_float))
            size = data.size
            
            # 创建输出数组
            result = np.empty_like(data)
            result_ptr = result.ctypes.data_as(POINTER(c_float))
            
            # 根据 SIMD 级别选择优化方法
            if self.simd_level == "avx2":
                # 使用 AVX2 优化
                self.simd_lib.vector_avx2_optimize(data_ptr, result_ptr, size)
            elif self.simd_level == "avx":
                # 使用 AVX 优化
                self.simd_lib.vector_avx_optimize(data_ptr, result_ptr, size)
            else:
                # 使用 SSE 优化
                self.simd_lib.vector_sse_optimize(data_ptr, result_ptr, size)
            
            return result
            
        except Exception as e:
            logger.error(f"float32 向量优化失败: {str(e)}")
            return data
    
    def _optimize_float64_vector(self, data: np.ndarray) -> np.ndarray:
        """优化 float64 向量运算
        
        Args:
            data: float64 类型的数据数组
            
        Returns:
            优化后的数据数组
        """
        try:
            # 获取数据指针
            data_ptr = data.ctypes.data_as(POINTER(c_double))
            size = data.size
            
            # 创建输出数组
            result = np.empty_like(data)
            result_ptr = result.ctypes.data_as(POINTER(c_double))
            
            # 根据 SIMD 级别选择优化方法
            if self.simd_level == "avx2":
                # 使用 AVX2 优化
                self.simd_lib.vector_avx2_optimize_double(data_ptr, result_ptr, size)
            elif self.simd_level == "avx":
                # 使用 AVX 优化
                self.simd_lib.vector_avx_optimize_double(data_ptr, result_ptr, size)
            else:
                # 使用 SSE 优化
                self.simd_lib.vector_sse_optimize_double(data_ptr, result_ptr, size)
            
            return result
            
        except Exception as e:
            logger.error(f"float64 向量优化失败: {str(e)}")
            return data
    
    def optimize_matrix_operations(self, matrix: np.ndarray) -> np.ndarray:
        """优化矩阵运算
        
        Args:
            matrix: 输入矩阵
            
        Returns:
            优化后的矩阵
        """
        if not self.is_intel or not hasattr(self, 'simd_lib') or self.simd_lib is None:
            return matrix
            
        try:
            # 确保数据是连续的内存布局
            if not matrix.flags['C_CONTIGUOUS']:
                matrix = np.ascontiguousarray(matrix)
            
            # 根据数据类型选择优化方法
            if matrix.dtype == np.float32:
                return self._optimize_float32_matrix(matrix)
            elif matrix.dtype == np.float64:
                return self._optimize_float64_matrix(matrix)
            else:
                return matrix
                
        except Exception as e:
            logger.error(f"矩阵运算优化失败: {str(e)}")
            return matrix
    
    def _optimize_float32_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """优化 float32 矩阵运算
        
        Args:
            matrix: float32 类型的矩阵
            
        Returns:
            优化后的矩阵
        """
        try:
            # 获取矩阵信息
            rows, cols = matrix.shape
            matrix_ptr = matrix.ctypes.data_as(POINTER(c_float))
            
            # 创建输出矩阵
            result = np.empty_like(matrix)
            result_ptr = result.ctypes.data_as(POINTER(c_float))
            
            # 根据 SIMD 级别选择优化方法
            if self.simd_level == "avx2":
                # 使用 AVX2 优化
                self.simd_lib.matrix_avx2_optimize(matrix_ptr, result_ptr, rows, cols)
            elif self.simd_level == "avx":
                # 使用 AVX 优化
                self.simd_lib.matrix_avx_optimize(matrix_ptr, result_ptr, rows, cols)
            else:
                # 使用 SSE 优化
                self.simd_lib.matrix_sse_optimize(matrix_ptr, result_ptr, rows, cols)
            
            return result
            
        except Exception as e:
            logger.error(f"float32 矩阵优化失败: {str(e)}")
            return matrix
    
    def _optimize_float64_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """优化 float64 矩阵运算
        
        Args:
            matrix: float64 类型的矩阵
            
        Returns:
            优化后的矩阵
        """
        try:
            # 获取矩阵信息
            rows, cols = matrix.shape
            matrix_ptr = matrix.ctypes.data_as(POINTER(c_double))
            
            # 创建输出矩阵
            result = np.empty_like(matrix)
            result_ptr = result.ctypes.data_as(POINTER(c_double))
            
            # 根据 SIMD 级别选择优化方法
            if self.simd_level == "avx2":
                # 使用 AVX2 优化
                self.simd_lib.matrix_avx2_optimize_double(matrix_ptr, result_ptr, rows, cols)
            elif self.simd_level == "avx":
                # 使用 AVX 优化
                self.simd_lib.matrix_avx_optimize_double(matrix_ptr, result_ptr, rows, cols)
            else:
                # 使用 SSE 优化
                self.simd_lib.matrix_sse_optimize_double(matrix_ptr, result_ptr, rows, cols)
            
            return result
            
        except Exception as e:
            logger.error(f"float64 矩阵优化失败: {str(e)}")
            return matrix
    
    def get_optimization_info(self) -> Dict[str, Any]:
        """获取优化信息
        
        Returns:
            优化信息字典
        """
        return {
            "is_intel": self.is_intel,
            "simd_level": self.simd_level,
            "simd_lib_loaded": hasattr(self, 'simd_lib') and self.simd_lib is not None,
            "cpu_info": platform.processor(),
            "platform": platform.platform()
        } 
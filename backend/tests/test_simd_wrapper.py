import pytest
import numpy as np
import os
import time
from backend.core.optimization.simd_wrapper import SIMDWrapper

@pytest.fixture
def simd_wrapper():
    """创建 SIMD 包装器实例"""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lib_path = os.path.join(current_dir, "core", "optimization", "simd_libs", "libsimd_avx2.so")
    return SIMDWrapper(lib_path)

def test_vector_optimization(simd_wrapper):
    """测试向量优化"""
    # 测试 float32 向量
    data = np.random.rand(1000).astype(np.float32)
    result = simd_wrapper.optimize_vector(data)
    
    assert result.dtype == np.float32
    assert result.shape == data.shape
    assert np.allclose(result, data + data)  # 验证自加操作
    
    # 测试 float64 向量
    data = np.random.rand(1000).astype(np.float64)
    result = simd_wrapper.optimize_vector(data)
    
    assert result.dtype == np.float64
    assert result.shape == data.shape
    assert np.allclose(result, data * data)  # 验证自乘操作
    
    # 测试非连续数组
    data = np.random.rand(1000).astype(np.float32)[::2]
    result = simd_wrapper.optimize_vector(data)
    
    assert result.dtype == np.float32
    assert result.shape == data.shape
    assert np.allclose(result, data + data)

def test_matrix_optimization(simd_wrapper):
    """测试矩阵优化"""
    # 测试 float32 矩阵
    data = np.random.rand(100, 100).astype(np.float32)
    result = simd_wrapper.optimize_matrix(data)
    
    assert result.dtype == np.float32
    assert result.shape == data.shape
    
    # 测试 float64 矩阵
    data = np.random.rand(100, 100).astype(np.float64)
    result = simd_wrapper.optimize_matrix(data)
    
    assert result.dtype == np.float64
    assert result.shape == data.shape
    
    # 测试非连续数组
    data = np.random.rand(100, 100).astype(np.float32)[::2, ::2]
    result = simd_wrapper.optimize_matrix(data)
    
    assert result.dtype == np.float32
    assert result.shape == data.shape

def test_vector_dot(simd_wrapper):
    """测试向量点积"""
    a = np.random.rand(1000).astype(np.float32)
    b = np.random.rand(1000).astype(np.float32)
    
    result = simd_wrapper.vector_dot(a, b)
    expected = np.dot(a, b)
    
    assert np.isclose(result, expected)
    
    # 测试非连续数组
    a = np.random.rand(1000).astype(np.float32)[::2]
    b = np.random.rand(1000).astype(np.float32)[::2]
    
    result = simd_wrapper.vector_dot(a, b)
    expected = np.dot(a, b)
    
    assert np.isclose(result, expected)

def test_vector_mean(simd_wrapper):
    """测试向量均值"""
    data = np.random.rand(1000).astype(np.float32)
    
    result = simd_wrapper.vector_mean(data)
    expected = np.mean(data)
    
    assert np.isclose(result, expected)
    
    # 测试非连续数组
    data = np.random.rand(1000).astype(np.float32)[::2]
    
    result = simd_wrapper.vector_mean(data)
    expected = np.mean(data)
    
    assert np.isclose(result, expected)

def test_vector_std(simd_wrapper):
    """测试向量标准差"""
    data = np.random.rand(1000).astype(np.float32)
    
    result = simd_wrapper.vector_std(data)
    expected = np.std(data)
    
    assert np.isclose(result, expected, rtol=1e-5)
    
    # 测试非连续数组
    data = np.random.rand(1000).astype(np.float32)[::2]
    
    result = simd_wrapper.vector_std(data)
    expected = np.std(data)
    
    assert np.isclose(result, expected, rtol=1e-5)

def test_performance(simd_wrapper):
    """测试性能提升"""
    # 测试向量运算性能
    size = 1000000
    data = np.random.rand(size).astype(np.float32)
    
    # 标准 numpy 运算
    start_time = time.time()
    result_numpy = data + data
    numpy_time = time.time() - start_time
    
    # SIMD 优化运算
    start_time = time.time()
    result_simd = simd_wrapper.optimize_vector(data)
    simd_time = time.time() - start_time
    
    assert np.allclose(result_numpy, result_simd)
    assert simd_time < numpy_time  # SIMD 应该更快
    
    # 测试矩阵运算性能
    size = 1000
    data = np.random.rand(size, size).astype(np.float32)
    
    # 标准 numpy 运算
    start_time = time.time()
    result_numpy = np.dot(data, data)
    numpy_time = time.time() - start_time
    
    # SIMD 优化运算
    start_time = time.time()
    result_simd = simd_wrapper.optimize_matrix(data)
    simd_time = time.time() - start_time
    
    assert simd_time < numpy_time  # SIMD 应该更快

def test_error_handling(simd_wrapper):
    """测试错误处理"""
    # 测试无效输入类型
    with pytest.raises(TypeError):
        simd_wrapper.optimize_vector([1, 2, 3])
    
    # 测试无效维度
    with pytest.raises(ValueError):
        simd_wrapper.optimize_vector(np.random.rand(10, 10))
    
    # 测试无效数据类型
    with pytest.raises(ValueError):
        simd_wrapper.optimize_vector(np.random.rand(10).astype(np.int32))
    
    # 测试向量点积维度不匹配
    a = np.random.rand(10).astype(np.float32)
    b = np.random.rand(20).astype(np.float32)
    with pytest.raises(ValueError):
        simd_wrapper.vector_dot(a, b)
    
    # 测试无效库路径
    with pytest.raises(Exception):
        SIMDWrapper("invalid_path.so")

def test_memory_management(simd_wrapper):
    """测试内存管理"""
    # 测试大数组处理
    size = 10000000
    data = np.random.rand(size).astype(np.float32)
    
    # 确保不会发生内存泄漏
    for _ in range(10):
        result = simd_wrapper.optimize_vector(data)
        del result
    
    # 测试资源清理
    wrapper = SIMDWrapper()
    del wrapper  # 应该正确清理资源 
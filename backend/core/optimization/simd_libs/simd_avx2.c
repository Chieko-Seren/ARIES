#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// AVX2 优化的向量加法
void vector_avx2_optimize(float* input, float* output, int size) {
    int i;
    __m256 vec;
    
    // 使用 AVX2 指令处理 8 个浮点数
    for (i = 0; i < size - 7; i += 8) {
        vec = _mm256_loadu_ps(&input[i]);
        vec = _mm256_add_ps(vec, vec);  // 示例：向量自加
        _mm256_storeu_ps(&output[i], vec);
    }
    
    // 处理剩余元素
    for (; i < size; i++) {
        output[i] = input[i] + input[i];
    }
}

// AVX2 优化的向量乘法
void vector_avx2_optimize_double(double* input, double* output, int size) {
    int i;
    __m256d vec;
    
    // 使用 AVX2 指令处理 4 个双精度浮点数
    for (i = 0; i < size - 3; i += 4) {
        vec = _mm256_loadu_pd(&input[i]);
        vec = _mm256_mul_pd(vec, vec);  // 示例：向量自乘
        _mm256_storeu_pd(&output[i], vec);
    }
    
    // 处理剩余元素
    for (; i < size; i++) {
        output[i] = input[i] * input[i];
    }
}

// AVX2 优化的矩阵乘法
void matrix_avx2_optimize(float* input, float* output, int rows, int cols) {
    int i, j, k;
    __m256 vec_a, vec_b, vec_c;
    
    // 使用 AVX2 指令优化矩阵运算
    for (i = 0; i < rows; i++) {
        for (j = 0; j < cols - 7; j += 8) {
            vec_c = _mm256_setzero_ps();
            for (k = 0; k < cols; k++) {
                vec_a = _mm256_set1_ps(input[i * cols + k]);
                vec_b = _mm256_loadu_ps(&input[k * cols + j]);
                vec_c = _mm256_add_ps(vec_c, _mm256_mul_ps(vec_a, vec_b));
            }
            _mm256_storeu_ps(&output[i * cols + j], vec_c);
        }
        
        // 处理剩余列
        for (; j < cols; j++) {
            float sum = 0.0f;
            for (k = 0; k < cols; k++) {
                sum += input[i * cols + k] * input[k * cols + j];
            }
            output[i * cols + j] = sum;
        }
    }
}

// AVX2 优化的矩阵乘法（双精度）
void matrix_avx2_optimize_double(double* input, double* output, int rows, int cols) {
    int i, j, k;
    __m256d vec_a, vec_b, vec_c;
    
    // 使用 AVX2 指令优化矩阵运算
    for (i = 0; i < rows; i++) {
        for (j = 0; j < cols - 3; j += 4) {
            vec_c = _mm256_setzero_pd();
            for (k = 0; k < cols; k++) {
                vec_a = _mm256_set1_pd(input[i * cols + k]);
                vec_b = _mm256_loadu_pd(&input[k * cols + j]);
                vec_c = _mm256_add_pd(vec_c, _mm256_mul_pd(vec_a, vec_b));
            }
            _mm256_storeu_pd(&output[i * cols + j], vec_c);
        }
        
        // 处理剩余列
        for (; j < cols; j++) {
            double sum = 0.0;
            for (k = 0; k < cols; k++) {
                sum += input[i * cols + k] * input[k * cols + j];
            }
            output[i * cols + j] = sum;
        }
    }
}

// AVX2 优化的向量点积
float vector_dot_avx2(float* a, float* b, int size) {
    int i;
    __m256 vec_a, vec_b, vec_c;
    __m256 sum = _mm256_setzero_ps();
    
    // 使用 AVX2 指令计算点积
    for (i = 0; i < size - 7; i += 8) {
        vec_a = _mm256_loadu_ps(&a[i]);
        vec_b = _mm256_loadu_ps(&b[i]);
        vec_c = _mm256_mul_ps(vec_a, vec_b);
        sum = _mm256_add_ps(sum, vec_c);
    }
    
    // 水平相加
    float result = 0.0f;
    float temp[8];
    _mm256_storeu_ps(temp, sum);
    for (i = 0; i < 8; i++) {
        result += temp[i];
    }
    
    // 处理剩余元素
    for (; i < size; i++) {
        result += a[i] * b[i];
    }
    
    return result;
}

// AVX2 优化的向量均值
float vector_mean_avx2(float* input, int size) {
    int i;
    __m256 vec, sum = _mm256_setzero_ps();
    
    // 使用 AVX2 指令计算和
    for (i = 0; i < size - 7; i += 8) {
        vec = _mm256_loadu_ps(&input[i]);
        sum = _mm256_add_ps(sum, vec);
    }
    
    // 水平相加
    float result = 0.0f;
    float temp[8];
    _mm256_storeu_ps(temp, sum);
    for (i = 0; i < 8; i++) {
        result += temp[i];
    }
    
    // 处理剩余元素
    for (; i < size; i++) {
        result += input[i];
    }
    
    return result / size;
}

// AVX2 优化的向量标准差
float vector_std_avx2(float* input, int size) {
    float mean = vector_mean_avx2(input, size);
    int i;
    __m256 vec, diff, sum = _mm256_setzero_ps();
    __m256 mean_vec = _mm256_set1_ps(mean);
    
    // 使用 AVX2 指令计算方差
    for (i = 0; i < size - 7; i += 8) {
        vec = _mm256_loadu_ps(&input[i]);
        diff = _mm256_sub_ps(vec, mean_vec);
        sum = _mm256_add_ps(sum, _mm256_mul_ps(diff, diff));
    }
    
    // 水平相加
    float result = 0.0f;
    float temp[8];
    _mm256_storeu_ps(temp, sum);
    for (i = 0; i < 8; i++) {
        result += temp[i];
    }
    
    // 处理剩余元素
    for (; i < size; i++) {
        float diff = input[i] - mean;
        result += diff * diff;
    }
    
    return sqrtf(result / size);
} 
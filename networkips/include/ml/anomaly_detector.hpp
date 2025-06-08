#pragma once

#include <torch/torch.h>
#include <memory>
#include <string>
#include <vector>
#include "feature/feature_extractor.hpp"

namespace nips {
namespace ml {

enum class ModelType {
    DEEP_LEARNING,
    TRADITIONAL_ML
};

struct DetectionResult {
    float anomaly_score;
    float confidence;
    std::string threat_type;
    std::vector<std::string> indicators;
    bool is_anomaly;
};

class AnomalyDetector {
public:
    AnomalyDetector(ModelType type = ModelType::DEEP_LEARNING);
    ~AnomalyDetector();

    // 加载预训练模型
    bool loadModel(const std::string& model_path);
    
    // 保存模型
    bool saveModel(const std::string& model_path);
    
    // 检测异常
    DetectionResult detect(const feature::FlowFeatures& features);
    
    // 批量检测
    std::vector<DetectionResult> detectBatch(const std::vector<feature::FlowFeatures>& features);
    
    // 训练模型
    void train(const std::vector<feature::FlowFeatures>& features,
              const std::vector<bool>& labels,
              const std::string& model_path = "");
    
    // 更新模型
    void update(const feature::FlowFeatures& features, bool is_anomaly);

private:
    class Impl;
    std::unique_ptr<Impl> pimpl_;
    
    // 深度学习模型定义
    struct DeepModel : torch::nn::Module {
        DeepModel();
        torch::Tensor forward(torch::Tensor x);
        
        torch::nn::Linear fc1{nullptr}, fc2{nullptr}, fc3{nullptr};
        torch::nn::Dropout dropout{nullptr};
    };
    
    // 传统机器学习模型接口
    class TraditionalModel {
    public:
        virtual ~TraditionalModel() = default;
        virtual DetectionResult predict(const feature::FlowFeatures& features) = 0;
        virtual void train(const std::vector<feature::FlowFeatures>& features,
                         const std::vector<bool>& labels) = 0;
    };
};

} // namespace ml
} // namespace nips 
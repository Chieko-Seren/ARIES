#pragma once

#include <memory>
#include <string>
#include <vector>
#include <chrono>
#include "ml/anomaly_detector.hpp"
#include "feature/feature_extractor.hpp"

namespace nips {
namespace detection {

enum class ThreatLevel {
    NONE,
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
};

struct ThreatInfo {
    std::string id;
    std::string type;
    ThreatLevel level;
    std::chrono::system_clock::time_point timestamp;
    std::string source_ip;
    std::string destination_ip;
    uint16_t source_port;
    uint16_t destination_port;
    std::string protocol;
    std::vector<std::string> indicators;
    float confidence;
    std::string description;
    std::vector<std::string> mitigation_suggestions;
};

class ThreatDetector {
public:
    ThreatDetector();
    ~ThreatDetector();

    // 初始化检测器
    bool init(const std::string& config_path);
    
    // 检测威胁
    ThreatInfo detectThreat(const feature::FlowFeatures& features,
                          const ml::DetectionResult& anomaly_result);
    
    // 更新威胁情报
    void updateThreatIntelligence(const std::string& intel_source);
    
    // 获取威胁统计信息
    std::unordered_map<ThreatLevel, size_t> getThreatStatistics();
    
    // 设置威胁等级阈值
    void setThreatThresholds(const std::unordered_map<ThreatLevel, float>& thresholds);
    
    // 获取威胁详情
    std::vector<ThreatInfo> getRecentThreats(size_t count = 10);
    
    // 导出威胁报告
    bool exportThreatReport(const std::string& file_path);

private:
    class Impl;
    std::unique_ptr<Impl> pimpl_;
    
    // 威胁等级评估
    ThreatLevel evaluateThreatLevel(float anomaly_score, float confidence);
    
    // 威胁类型识别
    std::string identifyThreatType(const feature::FlowFeatures& features,
                                 const ml::DetectionResult& anomaly_result);
    
    // 生成缓解建议
    std::vector<std::string> generateMitigationSuggestions(const ThreatInfo& threat);
    
    // 威胁情报匹配
    bool matchThreatIntelligence(const ThreatInfo& threat);
};

} // namespace detection
} // namespace nips 
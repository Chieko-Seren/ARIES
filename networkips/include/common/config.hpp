#pragma once

#include <string>
#include <unordered_map>
#include <memory>
#include <yaml-cpp/yaml.h>

namespace nips {
namespace common {

class Config {
public:
    static Config& getInstance();

    // 加载配置文件
    bool load(const std::string& config_path);
    
    // 获取配置项
    template<typename T>
    T get(const std::string& key, const T& default_value = T()) const;
    
    // 设置配置项
    template<typename T>
    void set(const std::string& key, const T& value);
    
    // 保存配置
    bool save(const std::string& config_path = "");

private:
    Config() = default;
    ~Config() = default;
    
    // 禁用拷贝
    Config(const Config&) = delete;
    Config& operator=(const Config&) = delete;
    
    YAML::Node config_;
    std::string current_config_path_;
};

// 配置项定义
struct CaptureConfig {
    std::string interface;
    std::string filter;
    int buffer_size;
    int timeout_ms;
    bool promiscuous;
};

struct FeatureConfig {
    size_t flow_timeout_seconds;
    size_t max_packets_per_flow;
    bool enable_deep_packet_inspection;
    std::vector<std::string> enabled_features;
};

struct MLConfig {
    std::string model_type;
    std::string model_path;
    float anomaly_threshold;
    size_t batch_size;
    bool enable_gpu;
};

struct DetectionConfig {
    std::unordered_map<std::string, float> threat_thresholds;
    std::string intel_source;
    size_t max_threats_history;
    bool enable_correlation;
};

struct ResponseConfig {
    std::string policy_path;
    bool enable_auto_response;
    size_t max_concurrent_actions;
    std::string log_path;
};

} // namespace common
} // namespace nips 
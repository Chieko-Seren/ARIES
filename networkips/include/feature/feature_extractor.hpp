#pragma once

#include <vector>
#include <string>
#include <memory>
#include <unordered_map>
#include "capture/packet_capture.hpp"

namespace nips {
namespace feature {

struct FlowFeatures {
    // 基本流量特征
    uint32_t packet_count;
    uint32_t byte_count;
    float duration;
    float packets_per_second;
    float bytes_per_second;
    
    // 协议特征
    std::unordered_map<std::string, float> protocol_distribution;
    
    // 统计特征
    float mean_packet_size;
    float std_packet_size;
    float mean_inter_arrival_time;
    float std_inter_arrival_time;
    
    // 行为特征
    std::vector<float> payload_entropy;
    std::vector<float> port_usage_pattern;
    std::vector<float> connection_pattern;
    
    // 时间特征
    std::vector<float> time_based_features;
};

class FeatureExtractor {
public:
    FeatureExtractor();
    ~FeatureExtractor();

    // 从数据包提取特征
    FlowFeatures extractFeatures(const std::vector<capture::PacketInfo>& packets);
    
    // 从单个数据包更新特征
    void updateFeatures(FlowFeatures& features, const capture::PacketInfo& packet);
    
    // 获取特征维度
    static size_t getFeatureDimension();
    
    // 将特征转换为向量形式（用于机器学习模型输入）
    std::vector<float> featuresToVector(const FlowFeatures& features);

private:
    // 计算数据包熵值
    float calculateEntropy(const std::vector<uint8_t>& data);
    
    // 更新协议分布
    void updateProtocolDistribution(FlowFeatures& features, const capture::PacketInfo& packet);
    
    // 计算时间相关特征
    void calculateTimeFeatures(FlowFeatures& features, const std::vector<capture::PacketInfo>& packets);
    
    // 计算连接模式特征
    void calculateConnectionPattern(FlowFeatures& features, const std::vector<capture::PacketInfo>& packets);
};

} // namespace feature
} // namespace nips 
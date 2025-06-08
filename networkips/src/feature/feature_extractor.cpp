#include "feature/feature_extractor.hpp"
#include "common/logger.hpp"
#include <cmath>
#include <algorithm>
#include <unordered_map>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>

namespace nips {
namespace feature {

FeatureExtractor::FeatureExtractor() {
    // 初始化特征提取器
    NIPS_INFO("特征提取器已初始化");
}

FeatureExtractor::~FeatureExtractor() = default;

FlowFeatures FeatureExtractor::extractFeatures(const std::vector<capture::PacketInfo>& packets) {
    FlowFeatures features;
    if (packets.empty()) {
        return features;
    }

    // 基本流量特征
    features.packet_count = packets.size();
    features.byte_count = 0;
    for (const auto& packet : packets) {
        features.byte_count += packet.length;
    }

    // 计算时间特征
    auto start_time = packets.front().timestamp;
    auto end_time = packets.back().timestamp;
    features.duration = end_time - start_time;
    features.packets_per_second = features.packet_count / (features.duration + 1e-6);
    features.bytes_per_second = features.byte_count / (features.duration + 1e-6);

    // 计算统计特征
    std::vector<float> packet_sizes;
    std::vector<float> inter_arrival_times;
    packet_sizes.reserve(packets.size());
    inter_arrival_times.reserve(packets.size() - 1);

    for (size_t i = 0; i < packets.size(); ++i) {
        packet_sizes.push_back(packets[i].length);
        if (i > 0) {
            inter_arrival_times.push_back(packets[i].timestamp - packets[i-1].timestamp);
        }
    }

    // 计算均值
    features.mean_packet_size = std::accumulate(packet_sizes.begin(), packet_sizes.end(), 0.0f) / packet_sizes.size();
    features.mean_inter_arrival_time = std::accumulate(inter_arrival_times.begin(), inter_arrival_times.end(), 0.0f) / inter_arrival_times.size();

    // 计算标准差
    float sum_sq_diff_size = 0.0f;
    float sum_sq_diff_time = 0.0f;
    for (size_t i = 0; i < packet_sizes.size(); ++i) {
        float diff = packet_sizes[i] - features.mean_packet_size;
        sum_sq_diff_size += diff * diff;
    }
    for (size_t i = 0; i < inter_arrival_times.size(); ++i) {
        float diff = inter_arrival_times[i] - features.mean_inter_arrival_time;
        sum_sq_diff_time += diff * diff;
    }
    features.std_packet_size = std::sqrt(sum_sq_diff_size / packet_sizes.size());
    features.std_inter_arrival_time = std::sqrt(sum_sq_diff_time / inter_arrival_times.size());

    // 协议分布
    std::unordered_map<std::string, int> protocol_counts;
    for (const auto& packet : packets) {
        if (packet.data.size() < 34) continue;  // 最小IP头+TCP/UDP头
        
        struct ip* ip_header = (struct ip*)(packet.data.data() + 14);  // 跳过以太网头
        if (ip_header->ip_v != 4) continue;

        std::string protocol;
        switch (ip_header->ip_p) {
            case IPPROTO_TCP:
                protocol = "TCP";
                break;
            case IPPROTO_UDP:
                protocol = "UDP";
                break;
            case IPPROTO_ICMP:
                protocol = "ICMP";
                break;
            default:
                protocol = "OTHER";
        }
        protocol_counts[protocol]++;
    }

    // 计算协议分布比例
    for (const auto& [protocol, count] : protocol_counts) {
        features.protocol_distribution[protocol] = static_cast<float>(count) / packets.size();
    }

    // 计算负载熵值
    features.payload_entropy.clear();
    for (const auto& packet : packets) {
        if (packet.data.size() > 34) {  // 有负载
            features.payload_entropy.push_back(calculateEntropy(
                std::vector<uint8_t>(packet.data.begin() + 34, packet.data.end())
            ));
        }
    }

    // 计算端口使用模式
    features.port_usage_pattern.resize(65536, 0.0f);
    for (const auto& packet : packets) {
        if (packet.data.size() < 34) continue;
        
        struct ip* ip_header = (struct ip*)(packet.data.data() + 14);
        if (ip_header->ip_p == IPPROTO_TCP) {
            struct tcphdr* tcp_header = (struct tcphdr*)((uint8_t*)ip_header + (ip_header->ip_hl << 2));
            features.port_usage_pattern[ntohs(tcp_header->source)] += 1.0f;
            features.port_usage_pattern[ntohs(tcp_header->dest)] += 1.0f;
        } else if (ip_header->ip_p == IPPROTO_UDP) {
            struct udphdr* udp_header = (struct udphdr*)((uint8_t*)ip_header + (ip_header->ip_hl << 2));
            features.port_usage_pattern[ntohs(udp_header->source)] += 1.0f;
            features.port_usage_pattern[ntohs(udp_header->dest)] += 1.0f;
        }
    }

    // 归一化端口使用模式
    float max_port_usage = *std::max_element(features.port_usage_pattern.begin(), features.port_usage_pattern.end());
    if (max_port_usage > 0) {
        for (auto& usage : features.port_usage_pattern) {
            usage /= max_port_usage;
        }
    }

    // 计算连接模式特征
    calculateConnectionPattern(features, packets);

    return features;
}

void FeatureExtractor::updateFeatures(FlowFeatures& features, const capture::PacketInfo& packet) {
    // 更新基本统计信息
    features.packet_count++;
    features.byte_count += packet.length;

    // 更新协议分布
    if (packet.data.size() >= 34) {
        struct ip* ip_header = (struct ip*)(packet.data.data() + 14);
        if (ip_header->ip_v == 4) {
            std::string protocol;
            switch (ip_header->ip_p) {
                case IPPROTO_TCP: protocol = "TCP"; break;
                case IPPROTO_UDP: protocol = "UDP"; break;
                case IPPROTO_ICMP: protocol = "ICMP"; break;
                default: protocol = "OTHER";
            }
            features.protocol_distribution[protocol] = 
                (features.protocol_distribution[protocol] * (features.packet_count - 1) + 1.0f) / features.packet_count;
        }
    }

    // 更新其他特征...
    // 注意：某些特征（如时间特征）需要完整的包序列才能计算
}

float FeatureExtractor::calculateEntropy(const std::vector<uint8_t>& data) {
    if (data.empty()) return 0.0f;

    std::array<int, 256> freq = {0};
    for (uint8_t byte : data) {
        freq[byte]++;
    }

    float entropy = 0.0f;
    float size = static_cast<float>(data.size());
    for (int count : freq) {
        if (count > 0) {
            float p = count / size;
            entropy -= p * std::log2(p);
        }
    }

    return entropy;
}

void FeatureExtractor::calculateConnectionPattern(FlowFeatures& features, 
                                                const std::vector<capture::PacketInfo>& packets) {
    features.connection_pattern.clear();
    features.connection_pattern.resize(10, 0.0f);  // 使用10个特征维度

    std::unordered_map<std::string, int> connection_states;
    for (const auto& packet : packets) {
        if (packet.data.size() < 34) continue;

        struct ip* ip_header = (struct ip*)(packet.data.data() + 14);
        if (ip_header->ip_p == IPPROTO_TCP) {
            struct tcphdr* tcp_header = (struct tcphdr*)((uint8_t*)ip_header + (ip_header->ip_hl << 2));
            
            // 提取连接特征
            std::string conn_key = std::to_string(ntohl(ip_header->ip_src.s_addr)) + ":" +
                                 std::to_string(ntohs(tcp_header->source)) + "->" +
                                 std::to_string(ntohl(ip_header->ip_dst.s_addr)) + ":" +
                                 std::to_string(ntohs(tcp_header->dest));

            // 更新连接状态
            connection_states[conn_key]++;

            // 提取TCP标志特征
            if (tcp_header->syn) features.connection_pattern[0]++;
            if (tcp_header->ack) features.connection_pattern[1]++;
            if (tcp_header->fin) features.connection_pattern[2]++;
            if (tcp_header->rst) features.connection_pattern[3]++;
            if (tcp_header->psh) features.connection_pattern[4]++;
            if (tcp_header->urg) features.connection_pattern[5]++;
        }
    }

    // 计算连接模式统计
    if (!connection_states.empty()) {
        float avg_conn_packets = 0.0f;
        float max_conn_packets = 0.0f;
        for (const auto& [_, count] : connection_states) {
            avg_conn_packets += count;
            max_conn_packets = std::max(max_conn_packets, static_cast<float>(count));
        }
        avg_conn_packets /= connection_states.size();

        features.connection_pattern[6] = avg_conn_packets / features.packet_count;
        features.connection_pattern[7] = max_conn_packets / features.packet_count;
        features.connection_pattern[8] = static_cast<float>(connection_states.size()) / features.packet_count;
        features.connection_pattern[9] = static_cast<float>(connection_states.size());
    }

    // 归一化连接模式特征
    float max_pattern = *std::max_element(features.connection_pattern.begin(), features.connection_pattern.end());
    if (max_pattern > 0) {
        for (auto& pattern : features.connection_pattern) {
            pattern /= max_pattern;
        }
    }
}

std::vector<float> FeatureExtractor::featuresToVector(const FlowFeatures& features) {
    std::vector<float> vector;
    vector.reserve(50);  // 预分配空间

    // 基本流量特征
    vector.push_back(features.packet_count);
    vector.push_back(features.byte_count);
    vector.push_back(features.duration);
    vector.push_back(features.packets_per_second);
    vector.push_back(features.bytes_per_second);

    // 统计特征
    vector.push_back(features.mean_packet_size);
    vector.push_back(features.std_packet_size);
    vector.push_back(features.mean_inter_arrival_time);
    vector.push_back(features.std_inter_arrival_time);

    // 协议分布
    std::vector<std::string> protocols = {"TCP", "UDP", "ICMP", "OTHER"};
    for (const auto& protocol : protocols) {
        vector.push_back(features.protocol_distribution.count(protocol) ? 
                        features.protocol_distribution.at(protocol) : 0.0f);
    }

    // 负载熵值统计
    if (!features.payload_entropy.empty()) {
        float avg_entropy = std::accumulate(features.payload_entropy.begin(), 
                                          features.payload_entropy.end(), 0.0f) / 
                          features.payload_entropy.size();
        float max_entropy = *std::max_element(features.payload_entropy.begin(), 
                                            features.payload_entropy.end());
        vector.push_back(avg_entropy);
        vector.push_back(max_entropy);
    } else {
        vector.push_back(0.0f);
        vector.push_back(0.0f);
    }

    // 端口使用模式（取前20个最活跃的端口）
    std::vector<float> sorted_ports = features.port_usage_pattern;
    std::partial_sort(sorted_ports.begin(), sorted_ports.begin() + 20, sorted_ports.end(), 
                     std::greater<float>());
    vector.insert(vector.end(), sorted_ports.begin(), sorted_ports.begin() + 20);

    // 连接模式特征
    vector.insert(vector.end(), features.connection_pattern.begin(), features.connection_pattern.end());

    return vector;
}

size_t FeatureExtractor::getFeatureDimension() {
    return 50;  // 基本特征(5) + 统计特征(4) + 协议分布(4) + 熵值统计(2) + 端口模式(20) + 连接模式(10)
}

} // namespace feature
} // namespace nips 
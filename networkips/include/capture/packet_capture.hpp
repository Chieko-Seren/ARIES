#pragma once

#include <string>
#include <memory>
#include <functional>
#include <pcap.h>
#include <vector>

namespace nips {
namespace capture {

struct PacketInfo {
    std::vector<uint8_t> data;
    uint32_t timestamp;
    uint32_t length;
    std::string interface;
    bool is_outbound;
};

class PacketCapture {
public:
    using PacketCallback = std::function<void(const PacketInfo&)>;

    PacketCapture();
    ~PacketCapture();

    // 初始化捕获器
    bool init(const std::string& interface, const std::string& filter = "");
    
    // 开始捕获
    bool start(PacketCallback callback);
    
    // 停止捕获
    void stop();
    
    // 设置过滤器
    bool setFilter(const std::string& filter);
    
    // 获取可用接口列表
    static std::vector<std::string> getAvailableInterfaces();

private:
    pcap_t* handle_;
    bool running_;
    std::string interface_;
    std::string filter_;
    
    // 禁用拷贝
    PacketCapture(const PacketCapture&) = delete;
    PacketCapture& operator=(const PacketCapture&) = delete;
};

} // namespace capture
} // namespace nips 
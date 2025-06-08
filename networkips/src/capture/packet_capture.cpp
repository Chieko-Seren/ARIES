#include "capture/packet_capture.hpp"
#include "common/logger.hpp"
#include <pcap.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <chrono>

namespace nips {
namespace capture {

PacketCapture::PacketCapture() : handle_(nullptr), running_(false) {}

PacketCapture::~PacketCapture() {
    stop();
    if (handle_) {
        pcap_close(handle_);
    }
}

bool PacketCapture::init(const std::string& interface, const std::string& filter) {
    char errbuf[PCAP_ERRBUF_SIZE];
    
    // 打开网络接口
    handle_ = pcap_open_live(interface.c_str(), 
                            common::Config::getInstance().get<int>("capture.buffer_size"),
                            common::Config::getInstance().get<bool>("capture.promiscuous"),
                            common::Config::getInstance().get<int>("capture.timeout_ms"),
                            errbuf);
    
    if (!handle_) {
        NIPS_ERROR("无法打开网络接口 {}: {}", interface, errbuf);
        return false;
    }

    // 设置过滤器
    if (!filter.empty() && !setFilter(filter)) {
        NIPS_ERROR("无法设置过滤器: {}", filter);
        return false;
    }

    interface_ = interface;
    NIPS_INFO("成功初始化数据包捕获器，接口: {}", interface);
    return true;
}

bool PacketCapture::start(PacketCallback callback) {
    if (!handle_ || running_) {
        return false;
    }

    running_ = true;
    callback_ = std::move(callback);

    // 启动捕获线程
    capture_thread_ = std::thread([this]() {
        while (running_) {
            struct pcap_pkthdr* header;
            const u_char* packet;
            int result = pcap_next_ex(handle_, &header, &packet);
            
            if (result == 1) {  // 成功捕获数据包
                PacketInfo info;
                info.timestamp = header->ts.tv_sec;
                info.length = header->len;
                info.interface = interface_;
                
                // 复制数据包内容
                info.data.assign(packet, packet + header->len);
                
                // 解析数据包方向
                struct ip* ip_header = (struct ip*)(packet + 14);  // 跳过以太网头
                if (ip_header->ip_v == 4) {
                    // 根据源IP判断方向
                    char src_ip[INET_ADDRSTRLEN];
                    inet_ntop(AF_INET, &(ip_header->ip_src), src_ip, INET_ADDRSTRLEN);
                    info.is_outbound = (std::string(src_ip) == interface_);
                }
                
                // 调用回调函数
                if (callback_) {
                    callback_(info);
                }
            } else if (result == -1) {  // 错误
                NIPS_ERROR("数据包捕获错误: {}", pcap_geterr(handle_));
                break;
            }
        }
    });

    NIPS_INFO("数据包捕获已启动");
    return true;
}

void PacketCapture::stop() {
    if (running_) {
        running_ = false;
        if (capture_thread_.joinable()) {
            capture_thread_.join();
        }
        NIPS_INFO("数据包捕获已停止");
    }
}

bool PacketCapture::setFilter(const std::string& filter) {
    if (!handle_) {
        return false;
    }

    struct bpf_program fp;
    if (pcap_compile(handle_, &fp, filter.c_str(), 0, PCAP_NETMASK_UNKNOWN) == -1) {
        NIPS_ERROR("无法编译过滤器: {}", pcap_geterr(handle_));
        return false;
    }

    if (pcap_setfilter(handle_, &fp) == -1) {
        NIPS_ERROR("无法设置过滤器: {}", pcap_geterr(handle_));
        pcap_freecode(&fp);
        return false;
    }

    pcap_freecode(&fp);
    filter_ = filter;
    NIPS_INFO("成功设置过滤器: {}", filter);
    return true;
}

std::vector<std::string> PacketCapture::getAvailableInterfaces() {
    std::vector<std::string> interfaces;
    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_if_t* alldevs;
    
    if (pcap_findalldevs(&alldevs, errbuf) == -1) {
        NIPS_ERROR("无法获取网络接口列表: {}", errbuf);
        return interfaces;
    }

    for (pcap_if_t* dev = alldevs; dev != nullptr; dev = dev->next) {
        if (dev->name) {
            interfaces.push_back(dev->name);
        }
    }

    pcap_freealldevs(alldevs);
    return interfaces;
}

} // namespace capture
} // namespace nips 
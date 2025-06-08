#include <iostream>
#include <memory>
#include <thread>
#include <atomic>
#include <csignal>
#include <boost/program_options.hpp>
#include "common/config.hpp"
#include "common/logger.hpp"
#include "capture/packet_capture.hpp"
#include "feature/feature_extractor.hpp"
#include "ml/anomaly_detector.hpp"
#include "detection/threat_detector.hpp"
#include "response/response_controller.hpp"

namespace po = boost::program_options;

std::atomic<bool> g_running{true};

void signalHandler(int signum) {
    NIPS_INFO("接收到信号 {}, 正在停止服务...", signum);
    g_running = false;
}

int main(int argc, char* argv[]) {
    // 解析命令行参数
    po::options_description desc("NIPS 选项");
    desc.add_options()
        ("help,h", "显示帮助信息")
        ("config,c", po::value<std::string>()->default_value("/etc/nips/nips.yaml"), "配置文件路径")
        ("log,l", po::value<std::string>()->default_value("/var/log/nips/nips.log"), "日志文件路径")
        ("interface,i", po::value<std::string>(), "网络接口名称")
        ("debug,d", "启用调试模式");

    po::variables_map vm;
    try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
        po::notify(vm);
    } catch (const std::exception& e) {
        std::cerr << "错误：无法解析命令行参数: " << e.what() << std::endl;
        return 1;
    }

    if (vm.count("help")) {
        std::cout << desc << std::endl;
        return 0;
    }

    // 初始化日志系统
    auto log_level = vm.count("debug") ? common::LogLevel::DEBUG : common::LogLevel::INFO;
    if (!common::Logger::getInstance().init(vm["log"].as<std::string>(), log_level)) {
        std::cerr << "错误：无法初始化日志系统" << std::endl;
        return 1;
    }

    // 加载配置
    if (!common::Config::getInstance().load(vm["config"].as<std::string>())) {
        NIPS_ERROR("无法加载配置文件");
        return 1;
    }

    // 注册信号处理器
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    try {
        // 创建组件实例
        auto capture = std::make_unique<capture::PacketCapture>();
        auto extractor = std::make_unique<feature::FeatureExtractor>();
        auto detector = std::make_unique<ml::AnomalyDetector>();
        auto threat_detector = std::make_unique<detection::ThreatDetector>();
        auto response = std::make_unique<response::ResponseController>();

        // 初始化组件
        auto interface = vm.count("interface") ? 
            vm["interface"].as<std::string>() : 
            common::Config::getInstance().get<std::string>("capture.interface");

        if (!capture->init(interface)) {
            NIPS_ERROR("无法初始化数据包捕获器");
            return 1;
        }

        if (!threat_detector->init(vm["config"].as<std::string>())) {
            NIPS_ERROR("无法初始化威胁检测器");
            return 1;
        }

        if (!response->init(vm["config"].as<std::string>())) {
            NIPS_ERROR("无法初始化响应控制器");
            return 1;
        }

        // 设置数据包处理回调
        capture->start([&](const capture::PacketInfo& packet) {
            if (!g_running) return;

            try {
                // 提取特征
                auto features = extractor->extractFeatures({packet});
                
                // 检测异常
                auto anomaly_result = detector->detect(features);
                
                // 检测威胁
                auto threat = threat_detector->detectThreat(features, anomaly_result);
                
                // 处理威胁
                if (threat.level != detection::ThreatLevel::NONE) {
                    auto action = response->handleThreat(threat);
                    response->executeAction(action);
                }
            } catch (const std::exception& e) {
                NIPS_ERROR("处理数据包时发生错误: {}", e.what());
            }
        });

        NIPS_INFO("NIPS 服务已启动，正在监控接口 {}", interface);

        // 主循环
        while (g_running) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }

        // 清理
        capture->stop();
        NIPS_INFO("NIPS 服务已停止");

    } catch (const std::exception& e) {
        NIPS_ERROR("运行时错误: {}", e.what());
        return 1;
    }

    return 0;
} 
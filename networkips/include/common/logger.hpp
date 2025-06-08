#pragma once

#include <string>
#include <memory>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/rotating_file_sink.h>
#include <spdlog/sinks/stdout_color_sinks.h>

namespace nips {
namespace common {

enum class LogLevel {
    TRACE = SPDLOG_LEVEL_TRACE,
    DEBUG = SPDLOG_LEVEL_DEBUG,
    INFO = SPDLOG_LEVEL_INFO,
    WARN = SPDLOG_LEVEL_WARN,
    ERROR = SPDLOG_LEVEL_ERROR,
    CRITICAL = SPDLOG_LEVEL_CRITICAL
};

class Logger {
public:
    static Logger& getInstance();

    // 初始化日志系统
    bool init(const std::string& log_path, LogLevel level = LogLevel::INFO);
    
    // 获取日志记录器
    std::shared_ptr<spdlog::logger> getLogger(const std::string& name);
    
    // 设置日志级别
    void setLevel(LogLevel level);
    
    // 刷新日志
    void flush();

private:
    Logger() = default;
    ~Logger();
    
    // 禁用拷贝
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;
    
    std::shared_ptr<spdlog::logger> main_logger_;
    std::string log_path_;
    LogLevel current_level_;
    
    // 创建日志记录器
    void createLogger(const std::string& name);
};

// 日志宏定义
#define NIPS_TRACE(...) SPDLOG_LOGGER_TRACE(nips::common::Logger::getInstance().getLogger("nips"), __VA_ARGS__)
#define NIPS_DEBUG(...) SPDLOG_LOGGER_DEBUG(nips::common::Logger::getInstance().getLogger("nips"), __VA_ARGS__)
#define NIPS_INFO(...) SPDLOG_LOGGER_INFO(nips::common::Logger::getInstance().getLogger("nips"), __VA_ARGS__)
#define NIPS_WARN(...) SPDLOG_LOGGER_WARN(nips::common::Logger::getInstance().getLogger("nips"), __VA_ARGS__)
#define NIPS_ERROR(...) SPDLOG_LOGGER_ERROR(nips::common::Logger::getInstance().getLogger("nips"), __VA_ARGS__)
#define NIPS_CRITICAL(...) SPDLOG_LOGGER_CRITICAL(nips::common::Logger::getInstance().getLogger("nips"), __VA_ARGS__)

} // namespace common
} // namespace nips 
#pragma once

#include <memory>
#include <string>
#include <vector>
#include <functional>
#include "detection/threat_detector.hpp"

namespace nips {
namespace response {

enum class ActionType {
    BLOCK,
    RATE_LIMIT,
    LOG,
    ALERT,
    REDIRECT,
    CUSTOM
};

struct ResponseAction {
    ActionType type;
    std::string target;  // IP地址、端口或协议
    std::chrono::seconds duration;
    std::string reason;
    std::vector<std::string> parameters;
};

class ResponseController {
public:
    using ActionCallback = std::function<void(const ResponseAction&)>;

    ResponseController();
    ~ResponseController();

    // 初始化控制器
    bool init(const std::string& config_path);
    
    // 处理威胁
    ResponseAction handleThreat(const detection::ThreatInfo& threat);
    
    // 执行响应动作
    bool executeAction(const ResponseAction& action);
    
    // 撤销响应动作
    bool revokeAction(const std::string& action_id);
    
    // 设置动作回调
    void setActionCallback(ActionCallback callback);
    
    // 获取当前活动的响应动作
    std::vector<ResponseAction> getActiveActions();
    
    // 更新响应策略
    bool updateResponsePolicy(const std::string& policy_path);
    
    // 导出响应日志
    bool exportResponseLog(const std::string& file_path);

private:
    class Impl;
    std::unique_ptr<Impl> pimpl_;
    
    // 生成响应动作
    ResponseAction generateAction(const detection::ThreatInfo& threat);
    
    // 验证动作有效性
    bool validateAction(const ResponseAction& action);
    
    // 应用速率限制
    bool applyRateLimit(const std::string& target, uint32_t rate);
    
    // 应用流量阻断
    bool applyBlock(const std::string& target);
    
    // 发送告警
    void sendAlert(const ResponseAction& action);
    
    // 记录响应日志
    void logResponse(const ResponseAction& action, bool success);
};

} // namespace response
} // namespace nips 
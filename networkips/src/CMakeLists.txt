# 收集所有源文件
file(GLOB_RECURSE SOURCES
    "*.cpp"
    "capture/*.cpp"
    "feature/*.cpp"
    "ml/*.cpp"
    "detection/*.cpp"
    "response/*.cpp"
    "correlation/*.cpp"
    "common/*.cpp"
)

# 创建主可执行文件
add_executable(nips ${SOURCES})

# 链接必要的库
target_link_libraries(nips
    PRIVATE
    OpenSSL::SSL
    OpenSSL::Crypto
    Threads::Threads
    pcap
    protobuf
    ${TORCH_LIBRARIES}
    yaml-cpp
    spdlog::spdlog
    Boost::system
    Boost::filesystem
)

# 设置编译定义
target_compile_definitions(nips
    PRIVATE
    NIPS_VERSION="${PROJECT_VERSION}"
    NIPS_BUILD_TYPE="${CMAKE_BUILD_TYPE}"
    SPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_INFO
)

# 设置编译选项
target_compile_options(nips
    PRIVATE
    -O3
    -march=native
    -mtune=native
    -DNDEBUG
) 
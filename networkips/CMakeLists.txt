cmake_minimum_required(VERSION 3.15)
project(NIPS VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 查找必要的包
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)
find_package(libpcap REQUIRED)
find_package(Protobuf REQUIRED)
find_package(Torch REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(spdlog REQUIRED)
find_package(Boost REQUIRED COMPONENTS system filesystem)

# 设置编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 包含目录
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${OPENSSL_INCLUDE_DIR}
    ${LIBPCAP_INCLUDE_DIR}
    ${Protobuf_INCLUDE_DIRS}
    ${TORCH_INCLUDE_DIRS}
    ${YAML_CPP_INCLUDE_DIR}
    ${spdlog_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
)

# 添加子目录
add_subdirectory(src)

# 设置输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 安装规则
install(TARGETS nips
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/
    DESTINATION include/nips
    FILES_MATCHING PATTERN "*.hpp"
)

# 安装配置文件
install(DIRECTORY config/
    DESTINATION etc/nips
    FILES_MATCHING PATTERN "*.yaml"
)

# 安装系统服务文件
install(FILES scripts/nips.service
    DESTINATION /etc/systemd/system
)

# 安装启动脚本
install(PROGRAMS scripts/nips-start.sh
    DESTINATION bin
    RENAME nips-start
) 
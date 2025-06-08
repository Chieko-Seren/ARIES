#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 语言设置
DEFAULT_LANG="zh_CN"
CURRENT_LANG=${LANG:-$DEFAULT_LANG}

# 语言定义
declare -A LANG_STRINGS

# 初始化语言字符串
init_languages() {
    # 中文语言定义
    LANG_STRINGS["zh_CN_aries_installer"]="ARIES 安装程序"
    LANG_STRINGS["zh_CN_select_install_type"]="请选择安装类型："
    LANG_STRINGS["zh_CN_invalid_option"]="无效的选项，请重新选择"
    LANG_STRINGS["zh_CN_exiting"]="退出安装程序"
    LANG_STRINGS["zh_CN_enter_option"]="请输入选项："
    LANG_STRINGS["zh_CN_language_selection"]="语言选择"
    LANG_STRINGS["zh_CN_select_language"]="请选择语言"
    LANG_STRINGS["zh_CN_change_language"]="更改语言"
    LANG_STRINGS["zh_CN_error_command_not_found"]="错误: 未找到 %s 命令，请先安装 %s"
    LANG_STRINGS["zh_CN_error_docker_not_running"]="错误: Docker 未运行，请先启动 Docker"
    LANG_STRINGS["zh_CN_installing_web_version"]="开始安装 ARIES Web 版本..."
    LANG_STRINGS["zh_CN_creating_nginx_config"]="创建 Nginx 配置文件"
    LANG_STRINGS["zh_CN_creating_dockerfile"]="创建 Dockerfile"
    LANG_STRINGS["zh_CN_creating_docker_compose"]="创建 Docker Compose 配置"
    LANG_STRINGS["zh_CN_building_container"]="构建并启动容器"
    LANG_STRINGS["zh_CN_web_install_complete"]="ARIES Web 版本安装完成！"
    LANG_STRINGS["zh_CN_web_access_url"]="您现在可以通过 http://localhost 访问网站"
    LANG_STRINGS["zh_CN_installing_full_version"]="开始安装 ARIES 完整版本..."
    LANG_STRINGS["zh_CN_installing_backend_deps"]="安装后端依赖"
    LANG_STRINGS["zh_CN_installing_frontend_deps"]="安装前端依赖"
    LANG_STRINGS["zh_CN_starting_services"]="启动所有服务"
    LANG_STRINGS["zh_CN_full_install_complete"]="ARIES 完整版本安装完成！"
    LANG_STRINGS["zh_CN_api_url"]="后端API服务运行在 http://localhost:8000"
    LANG_STRINGS["zh_CN_frontend_url"]="前端界面运行在 http://localhost:3000"
    LANG_STRINGS["zh_CN_web_version_option"]="仅安装 Web 版本 (Nginx + Docker)"
    LANG_STRINGS["zh_CN_full_version_option"]="安装完整版本 (包含所有组件)"
    LANG_STRINGS["zh_CN_exit"]="退出"

    # English language definitions
    LANG_STRINGS["en_US_aries_installer"]="ARIES Installer"
    LANG_STRINGS["en_US_select_install_type"]="Please select installation type:"
    LANG_STRINGS["en_US_invalid_option"]="Invalid option, please try again"
    LANG_STRINGS["en_US_exiting"]="Exiting installer"
    LANG_STRINGS["en_US_enter_option"]="Enter option:"
    LANG_STRINGS["en_US_language_selection"]="Language Selection"
    LANG_STRINGS["en_US_select_language"]="Please select language"
    LANG_STRINGS["en_US_change_language"]="Change Language"
    LANG_STRINGS["en_US_error_command_not_found"]="Error: Command %s not found, please install %s first"
    LANG_STRINGS["en_US_error_docker_not_running"]="Error: Docker is not running, please start Docker first"
    LANG_STRINGS["en_US_installing_web_version"]="Installing ARIES Web version..."
    LANG_STRINGS["en_US_creating_nginx_config"]="Creating Nginx configuration"
    LANG_STRINGS["en_US_creating_dockerfile"]="Creating Dockerfile"
    LANG_STRINGS["en_US_creating_docker_compose"]="Creating Docker Compose configuration"
    LANG_STRINGS["en_US_building_container"]="Building and starting container"
    LANG_STRINGS["en_US_web_install_complete"]="ARIES Web version installation complete!"
    LANG_STRINGS["en_US_web_access_url"]="You can now access the website at http://localhost"
    LANG_STRINGS["en_US_installing_full_version"]="Installing ARIES full version..."
    LANG_STRINGS["en_US_installing_backend_deps"]="Installing backend dependencies"
    LANG_STRINGS["en_US_installing_frontend_deps"]="Installing frontend dependencies"
    LANG_STRINGS["en_US_starting_services"]="Starting all services"
    LANG_STRINGS["en_US_full_install_complete"]="ARIES full version installation complete!"
    LANG_STRINGS["en_US_api_url"]="Backend API service running at http://localhost:8000"
    LANG_STRINGS["en_US_frontend_url"]="Frontend interface running at http://localhost:3000"
    LANG_STRINGS["en_US_web_version_option"]="Install Web version only (Nginx + Docker)"
    LANG_STRINGS["en_US_full_version_option"]="Install full version (all components)"
    LANG_STRINGS["en_US_exit"]="Exit"
}

# 获取文本
get_text() {
    local key="${CURRENT_LANG}_$1"
    local text="${LANG_STRINGS[$key]}"
    if [ -z "$text" ]; then
        echo "$1"
        return
    fi
    
    # 处理带参数的消息
    shift
    if [ $# -gt 0 ]; then
        printf "$text" "$@"
    else
        echo "$text"
    fi
}

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

# 显示进度条
show_progress() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    local progress=0
    local max_progress=100
    local step=$2
    local message=$3

    while ps -p $pid > /dev/null; do
        local temp=${spinstr#?}
        printf "\r${BLUE}[%c] %s: %d%%" "$spinstr" "$message" "$progress"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        progress=$((progress + step))
        if [ $progress -gt $max_progress ]; then
            progress=$max_progress
        fi
    done
    printf "\r${GREEN}[✓] %s: 完成!${NC}\n" "$message"
}

# 显示动画加载
show_loading() {
    local pid=$1
    local message=$2
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while ps -p $pid > /dev/null; do
        printf "\r${BLUE}%s %s${NC}" "${spinstr:$i:1}" "$message"
        sleep $delay
        i=$(( (i + 1) % 10 ))
    done
    printf "\r${GREEN}✓ %s${NC}\n" "$message"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_message "$(get_text 'error_command_not_found' "$1")" "$RED"
        exit 1
    fi
}

# 检查Docker是否运行
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_message "$(get_text 'error_docker_not_running')" "$RED"
        exit 1
    fi
}

# 安装web版本
install_web_version() {
    print_message "$(get_text 'installing_web_version')" "$GREEN"
    
    # 创建nginx配置文件
    (cat > web/nginx.conf << EOF
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # 启用gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF
    ) & show_loading $! "$(get_text 'creating_nginx_config')"

    # 创建Dockerfile
    (cat > web/Dockerfile << EOF
FROM nginx:alpine
COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
EOF
    ) & show_loading $! "$(get_text 'creating_dockerfile')"

    # 创建docker-compose文件
    (cat > web/docker-compose.yml << EOF
version: '3'
services:
  web:
    build: .
    ports:
      - "80:80"
    restart: always
EOF
    ) & show_loading $! "$(get_text 'creating_docker_compose')"

    # 构建并启动容器
    cd web
    print_message "$(get_text 'building_container')" "$YELLOW"
    docker-compose up -d --build & show_progress $! 2 "$(get_text 'building_container')"
    
    print_message "$(get_text 'web_install_complete')" "$GREEN"
    print_message "$(get_text 'web_access_url')" "$GREEN"
}

# 安装完整版本
install_full_version() {
    print_message "$(get_text 'installing_full_version')" "$GREEN"
    
    # 检查必要的命令
    check_command python3
    check_command pip3
    check_command node
    check_command npm
    
    # 安装后端依赖
    print_message "$(get_text 'installing_backend_deps')" "$YELLOW"
    cd backend
    pip3 install -r requirements.txt & show_progress $! 1 "$(get_text 'installing_backend_deps')"
    
    # 安装前端依赖
    print_message "$(get_text 'installing_frontend_deps')" "$YELLOW"
    cd ../frontend
    npm install & show_progress $! 1 "$(get_text 'installing_frontend_deps')"
    
    # 返回根目录
    cd ..
    
    # 启动所有服务
    print_message "$(get_text 'starting_services')" "$YELLOW"
    docker-compose up -d & show_progress $! 2 "$(get_text 'starting_services')"
    
    print_message "$(get_text 'full_install_complete')" "$GREEN"
    print_message "$(get_text 'api_url')" "$GREEN"
    print_message "$(get_text 'frontend_url')" "$GREEN"
}

# 显示语言选择菜单
show_language_menu() {
    local languages=("zh_CN" "en_US")
    local language_names=("简体中文" "English")
    
    print_message "\n=== $(get_text 'language_selection') ===" "$GREEN"
    for i in "${!languages[@]}"; do
        print_message "$((i+1))) ${language_names[$i]}" "$NC"
    done
    
    while true; do
        echo -n "$(get_text 'select_language'): "
        read -r lang_choice
        
        if [[ $lang_choice =~ ^[1-${#languages[@]}]$ ]]; then
            CURRENT_LANG=${languages[$((lang_choice-1))]}
            break
        else
            print_message "$(get_text 'invalid_option')" "$RED"
        fi
    done
}

# 主菜单
show_menu() {
    print_message "\n=== $(get_text 'aries_installer') ===" "$GREEN"
    print_message "$(get_text 'select_install_type')" "$YELLOW"
    print_message "1) $(get_text 'web_version_option')" "$NC"
    print_message "2) $(get_text 'full_version_option')" "$NC"
    print_message "3) $(get_text 'change_language')" "$NC"
    print_message "4) $(get_text 'exit')" "$NC"
    echo -n "$(get_text 'enter_option'): "
}

# 主程序
main() {
    # 初始化语言
    init_languages
    
    # 检查dialog是否安装
    check_command dialog
    
    # 检查Docker是否安装
    check_command docker
    check_command docker-compose
    check_docker_running
    
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1)
                install_web_version
                break
                ;;
            2)
                install_full_version
                break
                ;;
            3)
                show_language_menu
                ;;
            4)
                print_message "$(get_text 'exiting')" "$YELLOW"
                exit 0
                ;;
            *)
                print_message "$(get_text 'invalid_option')" "$RED"
                ;;
        esac
    done
}

# 运行主程序
main 
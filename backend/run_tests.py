#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ARIES - 测试运行脚本
执行所有测试用例
"""

import os
import sys
import pytest
import logging
from datetime import datetime

def setup_logging():
    """设置日志"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("开始运行测试...")
    
    # 设置测试参数
    args = [
        "tests",  # 测试目录
        "-v",     # 详细输出
        "--tb=short",  # 简短的错误回溯
        "--cov=backend",  # 代码覆盖率
        "--cov-report=term-missing",  # 显示未覆盖的代码行
        "--cov-report=html:coverage_report",  # 生成HTML覆盖率报告
        "-W", "ignore::DeprecationWarning",  # 忽略废弃警告
        "--durations=10",  # 显示最慢的10个测试
    ]
    
    # 运行测试
    try:
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            logger.info("所有测试通过！")
        else:
            logger.error(f"测试失败，退出码: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"测试执行出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
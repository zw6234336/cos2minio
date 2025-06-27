#!/bin/bash

# COS2MinIO 快速开始脚本

echo "========================================="
echo "COS2MinIO 工具快速开始"
echo "========================================="

# 检查Python版本
echo "检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "安装Python依赖包..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ 依赖包安装成功"
else
    echo "❌ 依赖包安装失败"
    exit 1
fi

# 检查配置文件
echo "检查配置文件..."
if [ -f "config.py" ]; then
    echo "✅ 找到配置文件"
    echo "⚠️  请确保已正确配置COS和MinIO信息"
else
    echo "❌ 未找到配置文件"
    exit 1
fi

# 创建必要目录
echo "创建必要目录..."
mkdir -p temp_downloads
mkdir -p logs
echo "✅ 目录创建完成"

# 运行测试
echo "是否运行连接测试？(y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "运行连接测试..."
    python test_migration.py
fi

echo ""
echo "========================================="
echo "设置完成！"
echo "========================================="
echo ""
echo "使用方法："
echo "1. 准备Excel文件，包含url列"
echo "2. 运行迁移命令："
echo "   python cos2minio.py your_file.xlsx"
echo ""
echo "更多选项："
echo "   python cos2minio.py --help"
echo ""
echo "创建示例Excel文件："
echo "   python create_sample_excel.py"
echo ""

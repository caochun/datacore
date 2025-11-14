#!/bin/bash
# DeepSeek API Key 配置脚本（不会把真实密钥写进仓库）

set -euo pipefail

echo "配置 DeepSeek API Key..."

# 如果已经有环境变量就直接复用，否则提示用户输入
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  read -r -p "请输入 DeepSeek API Key（不会保存到仓库）: " input_key
  if [ -z "$input_key" ]; then
    echo "❌ 未输入 API Key，已退出"
    return 1 2>/dev/null || exit 1
  fi
  export DEEPSEEK_API_KEY="$input_key"
else
  echo "检测到已配置的 DEEPSEEK_API_KEY，直接复用"
fi

# 允许通过环境变量覆盖模型和提供商
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-chat}"
export LLM_PROVIDER="${LLM_PROVIDER:-deepseek}"

echo "✅ 环境变量已设置（当前会话）"
echo ""
echo "当前配置:"
echo "  DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:0:6}******"
echo "  DEEPSEEK_MODEL: $DEEPSEEK_MODEL"
echo "  LLM_PROVIDER: $LLM_PROVIDER"
echo ""
echo "提示："
echo "  1. 不要把真实密钥提交到 Git 仓库"
echo "  2. 可在 ~/.bashrc 或 ~/.zshrc 中设置持久环境变量"
echo "  3. 也可以在项目根目录创建 .env.local（已被忽略）"
echo "  4. 启动服务前运行: source setup_deepseek.sh"
echo ""

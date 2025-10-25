#!/bin/bash
# ===== 智能自动部署脚本 =====

cd /opt/arb-bot || exit
echo "🚀 检查 GitHub 是否有新版本..."

# 获取远程仓库的最新提交 ID
git fetch origin main

LOCAL=$(git rev-parse main)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "🔄 检测到新版本，开始更新..."
    git reset --hard
    git pull origin main

    if [ $? -eq 0 ]; then
        echo "✅ 更新成功，准备重启程序..."
        pkill -f "python app.py"
        nohup python3 app.py > run.log 2>&1 &
        echo "🌕 部署完成，新版本已运行！"
    else
        echo "❌ 更新失败，请检查网络或分支。"
    fi
else
    echo "⏸ 没有检测到新版本，无需更新。"
fi

#!/bin/bash
# Git 状态查看脚本
# 用法: ./git_status.sh --path <仓库路径>

PATH="."

while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            PATH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ ! -d "$PATH" ]]; then
    echo "Error: Path not found: $PATH"
    exit 1
fi

# 检查是否是 git 仓库
if [[ ! -d "$PATH/.git" ]]; then
    echo "Error: Not a git repository: $PATH"
    exit 1
fi

cd "$PATH"

echo "=== Git Status ==="
echo "Repository: $(git rev-parse --show-toplevel 2>/dev/null || echo $PATH)"
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo ""

echo "Status:"
git status --short

echo ""
echo "=== Recent Commits (last 5) ==="
git log --oneline -5

echo ""
echo "=== Changes to be committed ==="
git diff --cached --stat 2>/dev/null || echo "None"

echo ""
echo "=== Uncommitted changes ==="
git diff --stat 2>/dev/null || echo "None"

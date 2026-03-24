#!/bin/bash
# 文件搜索脚本
# 用法: ./file_search.sh --directory <目录> --pattern <模式> --file_type <扩展名>

DIRECTORY="."
PATTERN="*"
FILE_TYPE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --directory)
            DIRECTORY="$2"
            shift 2
            ;;
        --pattern)
            PATTERN="$2"
            shift 2
            ;;
        --file_type)
            FILE_TYPE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ ! -d "$DIRECTORY" ]]; then
    echo "Error: Directory not found: $DIRECTORY"
    exit 1
fi

# 构建搜索命令
if [[ -n "$FILE_TYPE" ]]; then
    SEARCH_PATTERN="*.$FILE_TYPE"
else
    SEARCH_PATTERN="$PATTERN"
fi

# 执行搜索
echo "Searching in: $DIRECTORY"
echo "Pattern: $SEARCH_PATTERN"
echo "---"

find "$DIRECTORY" -type f -name "$SEARCH_PATTERN" 2>/dev/null | head -100

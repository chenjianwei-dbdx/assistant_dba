#!/bin/bash
# 系统监控脚本
# 用法: ./system_monitor.sh --metric <cpu|memory|disk|network> --duration <秒>

METRIC="cpu"
DURATION=5

while [[ $# -gt 0 ]]; do
    case $1 in
        --metric)
            METRIC="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

case $METRIC in
    cpu)
        echo "=== CPU Info ==="
        top -l 1 | grep -E "CPU usage|Processes"
        echo ""
        echo "Per-core usage:"
        top -l 1 -n 1 | grep "CPU"
        ;;

    memory)
        echo "=== Memory Info ==="
        vm_stat | head -10
        echo ""
        memory_pressure=$(memory_pressure 2>/dev/null | head -3 || echo "N/A")
        echo "Memory pressure: $memory_pressure"
        ;;

    disk)
        echo "=== Disk Info ==="
        df -h
        echo ""
        echo "Disk usage by partition:"
        diskutil list | grep -E "^/dev"
        ;;

    network)
        echo "=== Network Info (sampled over ${DURATION}s) ==="
        netstat -ib | head -10
        echo ""
        echo "Active connections:"
        lsof -i 2>/dev/null | head -10 || netstat -tn 2>/dev/null | head -10
        ;;

    *)
        echo "Error: Unknown metric: $METRIC"
        echo "Supported metrics: cpu, memory, disk, network"
        exit 1
        ;;
esac

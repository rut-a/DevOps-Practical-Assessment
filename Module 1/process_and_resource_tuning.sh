#!/bin/bash

CPU_THRESHOLD=80
CHECKING_INTERVAL=60
MAX_COUNT=5

declare -A HIGH_CPU_COUNT

while true; do
    ps -eo pid,pcpu --no-headers | while read pid cpu; do
        
        cpu_int=${cpu%.*}

        if [ "$cpu_int" -ge "$CPU_THRESHOLD" ]; then
            if [ -z "${HIGH_CPU_COUNT[$pid]}" ]; then
                HIGH_CPU_COUNT[$pid]=1
            else
                HIGH_CPU_COUNT[$pid]=$((HIGH_CPU_COUNT[$pid] + 1))
            fi

            if [ "${HIGH_CPU_COUNT[$pid]}" -ge "$MAX_COUNT" ]; then
                echo "Killing PID $pid its CPU usage exceeded 80% for 5 minutes)"
                kill -9 "$pid"
                unset HIGH_CPU_COUNT[$pid]
            fi
        else
            unset HIGH_CPU_COUNT[$pid]
        fi
    done

    sleep $CHECKING_INTERVAL
done
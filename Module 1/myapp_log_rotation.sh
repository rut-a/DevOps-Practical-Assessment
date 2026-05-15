#!/bin/bash

#configurations
LOG_DIR="/var/log"
LOG_FILE="myapp.log"
RETENTION_DAYS=7

rotate_log() {
	today=$(date +%F)
	if [ -f "$LOG_DIR/$LOG_FILE" ]; then
		mv "$LOG_DIR/$LOG_FILE" "$LOG_DIR/${LOG_FILE%.*}-$today.log" &&
		touch "$LOG_DIR/$LOG_FILE"
	else
		echo "$LOG_DIR/$LOG_FILE does not exist"
	fi
}

remove_old_logs() {
		find "$LOG_DIR" -name "${LOG_FILE%.*}-*.log" -type f -mtime +$RETENTION_DAYS -exec rm {} \;
}

# Main execution
rotate_log
remove_old_logs

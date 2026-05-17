# Module 1 – Discovery Report

## Overview

This report explains the Linux commands used in two Bash scripts:
1. Log rotation and cleanup script
2. CPU monitoring and process termination script

and show the implemetation steps for the Networking task.


# 1. Log Rotation Script – Commands Used

## date

```bash
date +%F
```

I used it to generate a timestamp for log file names

## mv 

```bash
mv /var/log/myapp.log /var/log/myapp-2026-05-17.log
```
I used it to archive the current log file before creating a new one.



## touch

```bash
touch /var/log/myapp.log
```

I used it to recreate a new log file after rotation.



## find

```bash
find /var/log -name "myapp-*.log" -type f -mtime +7 -exec rm {} \;
```

I used it to search for files based on the conditions:

    - /var/log → directory to search
    - -name → matches file name pattern
    - -type f → only files
    - -mtime +7 → files older than 7 days
    - -exec rm {} \; → deletes matched files



# 2. CPU Monitoring Script – Commands Used

## ps

```bash
ps -eo pid,pcpu --no-headers
```
I used it to monitor CPU usage of all running processe with the flags:

    - -e → show all processes
    - -o pid,pcpu → show process ID and CPU usage
    - --no-headers → removes column titles

## read 

```bash
while read pid cpu
```
I used it to read the `ps` command output line by line.



## kill

```bash
kill -9 PID
```

I used it to forecibly stop processes that exceed CPU usage threshold for more than 5 minutes.



## sleep

```bash
sleep 60
```

I used it to pause script execution for 60 seconds to perform CPU Usage check every minute.



## declare -A (associative arrays)

```bash
declare -A HIGH_CPU_COUNT
```

I used it to create a key-value store to track how long each process stays above CPU threshold.



# 3. Networking 
## ss

```bash
ss -tlnp
```

I used it to find all listening ports on the server with the flags:

    - -t → show TCP connections only
    - -l → show listening ports only
    - -n → show port numbers instead of service names
    - -p → show the process using each port

Running this revealed that MySQL was bound to `0.0.0.0:3306`, meaning
it was accepting connections from any external IP not just localhost.

## ufw allow

```bash
sudo ufw allow from 127.0.0.1 to any port 3306
```

I used it to explicitly permit localhost to connect to MySQL on port 3306.

    - from 127.0.0.1 → only traffic originating from localhost
    - to any        → regardless of destination address
    - port 3306     → target port (MySQL)

## ufw deny

```bash
sudo ufw deny 3306
```

I used it to block all external traffic to port 3306 after the localhost
allow rule was in place.

* The allow rule must come before the deny rule because UFW processes rules top to down and stops at the first match.

## ufw status

```bash
sudo ufw status numbered
```

* I used it to verify the rules were applied in the correct order and that no external access to port 3306 was permitted.


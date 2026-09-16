#!/bin/bash

services=("nginx" "ssh")
RED="\033[31m"
RESET="\033[0m"

for service in "${services[@]}"; do
   status=$(systemctl is-active ${service})

   if [ $status == "inactive" ];
      then echo -e "${RED}Service ${service} is inactive${RESET}"
   fi
done

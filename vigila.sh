#!/bin/bash 
nocarr="NO CARRIER"
varnocar=""
contador=0
sleep 30
while true; do
  varnocar=$(tail -5 /home/tracker/wvdial.log |awk '/NO CARRIER/{print $0}')
  if [ "${varnocar}" != "" ]; then 
     contador=$((contador+1))
    if [[ "$contador" -gt 5 ]]; then
       echo hago reboot
       sudo reboot       
    fi
    else contador=0
  fi
  echo $contador
  sleep 60
done
exit 0


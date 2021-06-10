#!/bin/bash 
HOY=$(date)
rayas="-----------------------------------------------------\n"
cd /home/tracker
echo $rayas  '\t' `date` '\n'$rayas >>/home/tracker/wvdial.log

LINEAS="$(wc -l < /home/tracker/wvdial.log)"
echo "lineas= " "$LINEAS"

if [ "$LINEAS"  -gt 5000 ]
 then
	cat  /home/tracker/wvdial.log > /home/tracker/wvdial.hist
	echo "En dial mas de 5000:" "$LINEAS"
	rm -f /home/tracker/wvdial.log
else
      echo "pocas lineas en dial=" "$LINEAS"
fi
while true
do
    sudo wvdial >>/home/tracker/wvdial.log 2>&1
    echo '*** RECONECTO *** ' `date` '*** RECONECTO ***' >>/home/tracker/wvdial.log
    sleep 30
done

exit 0

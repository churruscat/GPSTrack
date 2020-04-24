#!/bin/bash 
sudo /etc/init.d/ntp stop
sudo ntpd -q -g
sudo /etc/init.d/ntp start
HOY=$(date)
rayas="-----------------------------------------------------\n"
cd /home/tracker
echo $rayas  '\t' `date` '\n'$rayas >>/home/tracker/gpstrack.log
LINEAS="$(wc -l </home/tracker/gpstrack.log)"

if [ "$LINEAS"  -gt 30000 ]
then
	cat  /home/tracker/gpstrack.log >> /home/tracker/gpstrack.hist
	rm -f /home/tracker/gpstrack.log
else
      echo "pocas lineas en track=" "$LINEAS"
fi

while !(ifconfig ppp0) do
   sleep 2
done
echo "ya tengo ppp"
sleep 2
while true
do
	while true
		do
		echo "lanzo gpstrack"
		python -u /home/tracker/gpstrack.py >>/home/tracker/gpstrack.log 2>&1
	done
done
exit 0

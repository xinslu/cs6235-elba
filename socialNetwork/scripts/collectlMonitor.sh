
#!/bin/bash

echo -e "\e[33mstart fine-grained CPU monitoring using collectl\e[0m"

# remove the previous collectl data in Control node
rm /experiment-data/node*

for i in "node-0" "node-1" "node-2" "node-3" "node-4" "node-5"
do
	#i=$(echo $i|cut -f2 -d"=")
	echo 'come here1'
	#echo $i
	ssh $i '
	hostname
	sudo collectl -i 0.1 -F30 -sCdnZ -oTm  -f /experiment-data &> /dev/null &
	'
done

#!/bin/bash

#cd $BONN_RUBBOS_RESULTS_DIR_BASE/2019-11-07T235951-0600_1414-xgu-AP400-TP150-DP60/

cp ../scripts_limit/plotAverage.sh .

for i in $( ls -d */ )
do
	cd $i
	cp ../../scripts_limit/collectlExtract.py .
	cp ../../scripts_limit/collectlResultFilter.py .
	cp ../../scripts_limit/collectlResultFilter2.py .

	cp ../../scripts_limit/front_log_extract.py .
	
	cp ../../scripts_limit/client_log_extract.py .
	cp ../../scripts_limit/aggregateInOutPut_ClientTier3.sh .

	python collectlExtract.py
	python collectlResultFilter.py
    python collectlResultFilter2.py
	python collectlProcExtract.py
	
	python front_log_extract.py
	
	rm result.jtl
	cat result*.jtl >> result.jtl
	python client_log_extract.py
	

	./aggregateInOutPut_ClientTier3.sh
	

	cd ..

done

./plotAverage.sh

#!/bin/bash

ssh node-0 "
  sudo mkdir $RUBBOS_RESULTS_DIR_BASE
"

ssh benchmark "
  source $HOME/rubbos/set_elba_env.sh
  echo 'creating directory'
  sudo mkdir $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME
  echo 'verifying creation of directory'
  ls -al $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME
  sudo rm -rf $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/*
"

# Trying to simulation 5000 users
for i in "rubbos.properties_1000"
do

  ssh benchmark "
    source $HOME/rubbos/set_elba_env.sh
    rm -f $RUBBOS_HOME/Client/rubbos.properties
  "

  scp $WORK_HOME/runtime_files/$i benchmark:$RUBBOS_HOME/Client/rubbos.properties

  # get HTTP request latency
  # ssh node-6 "rm -f $HOME/node6_sysdig.log; sudo sysdig -c httplog > $HOME/node6_sysdig.log &" &

  # Browsing Only
  echo "Start Browsing Only with $i"
  echo "Removing previous logs..."


  ssh benchmark "
    source $HOME/rubbos/set_elba_env.sh
    cd $RUBBOS_HOME/bench
    \rm -r 20*
    # \rm -r $TMP_RESULTS_DIR_BASE/20*/

    # Execute benchmark
    echo '**************start************'
    date
    rm Experiments_timestamp.log

    ssh node-0 "$WORK_HOME/scripts/emptyLogs.sh"
    ssh node-0 "$WORK_HOME/scripts/collectlMonitor.sh"


    sleep 10
    ./log_time.sh
    ./rubbos-servletsBO.sh
    # Collect results
    ./log_time.sh
    echo "The benchmark has finished. Now, collecting results..."
    sudo mv Experiments_timestamp.log $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/

    ssh node-0 "$WORK_HOME/scripts/endCollectl.sh"
    sudo scp -r node-0:/experiment-data/*.raw.gz $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/
    ssh node-0 "$WORK_HOME/scripts/getLogs.sh"
    sudo scp -r node-0:/experiment-data/log* $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/
    sudo scp -r node-0:/experiment-data/node*.log $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/
    sudo cp $RUBBOS_HOME/bench/20*/index.html $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/
    sudo cp $RUBBOS_HOME/bench/20*/result*.jtl $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/

    sudo scp node-0:$WORK_HOME/set_elba_env.sh $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/
    sleep 2
    sudo mv 20* $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/
    sudo cp -r $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/* $TMP_RESULTS_DIR_BASE/$RUBBOS_RESULTS_DIR_NAME/20*/
  "

  ssh node-6 "sudo pkill -9 sysdig"

  ssh node-0 "$WORK_HOME/scripts/stopall.sh"

  sleep 15
  echo "End Browsing Only with $i"


  echo "End Read/Write with $i"

done


echo "Finish RUBBoS"


echo "Installing Dependencies for generateResult.sh"

ssh benchmark "
    sudo scp -r node-0:$HOME/scripts_limit $HOME/
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip pdfgrep collectl python2
    sudo pip3 install pandas matplotlib pandas
    sudo cp $HOME/scripts_limit/generateResult.sh /experiment-data
    cd /experiment-data
    sudo chmod -R +x ./generateResult.sh
    sudo ./generateResult.sh |& sudo tee output.log > /dev/null
"

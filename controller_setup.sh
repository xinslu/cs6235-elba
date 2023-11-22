#!/bin/bash

# Copyright (C) 2022 Georgia Tech Center for Experimental Research in Computer
# Systems
# Source:

# Setup the specified node to run the `benchmarkcontroller` application.


# Process command-line arguments.
set -u
cur_time=$(date +%s)
last_modified=$(date -r socialNetwork/docker-compose-swarm.yml +%s)
time_diff=$((cur_time - last_modified))
two_days_in_secs=$((3600 * 24))
if [ "$time_diff" -ge "$two_days_in_secs" ]; then
  echo "Have you modified compose-swarm file?"
  exit
fi

if [ ! -e "socialNetworkLSU.zip" ]; then
  echo -e "Don't have socialNetwork zip file in the path\nzip them now"
  for f in "RubbosClient" "RubbosClient_src" "scripts_limit" "socialNetwork" "src"; do
    zip -r "$f.zip" $f -x '**/.DS_Store' -x '**/__MACOSX'
  done
  zip -r socialNetworkLSU.zip *.zip -x '**/.*' -x '**/__MACOSX'
fi

while [[ $# > 1 ]]; do
  case $1 in
    --username )
      username=$2
      ;;
    --private_ssh_key_path )
      private_ssh_key_path=$2
      ;;
    --controller_node )
      controller_node=$2
      ;;
    --git_email )
      git_email=$2
      ;;
    --swarm_node_number )
      swarm_node_number=$2
      ;;
    --client_node_number )
      client_node_number=$2
      ;;
    * )
      echo "Invalid argument: $1"
      exit 1
  esac
  shift
  shift
done

# Copy the SSH private key to the controller node.
scp -o StrictHostKeyChecking=no -i ${private_ssh_key_path} ${private_ssh_key_path} ${username}@${controller_node}:.ssh/id_rsa
scp -o StrictHostKeyChecking=no -i ${private_ssh_key_path} -r socialNetworkLSU.zip ${username}@${controller_node}:socialNetworkLSU

# clone env_setup repo in manager node
ssh -o StrictHostKeyChecking=no -i ${private_ssh_key_path} ${username}@${controller_node} "
  ssh-keygen -F github.com || ssh-keyscan github.com >> ~/.ssh/known_hosts
  echo -e 'Host *\n\tStrictHostKeyChecking no\nHost benchmark\n\tHostName 10.10.1.7\n\tUser Preethi' >> ~/.ssh/config
  sudo sh -c \"echo 'Host *\n\tStrictHostKeyChecking no' >> /root/.ssh/config\"
  git config --global user.email ${git_email}
  git config --global user.name Preethi
  git clone git@github.com:WindowsXp-Beta/SocialNetwork.git SetupScripts
  unzip socialNetworkLSU
  sudo apt-get update
  sudo apt-get install -y python3-pip maven
  cd SetupScripts
  pip3 install -r requirements.txt
  python setup_docker_swarm.py -a 10.10.1.1 -n ${swarm_node_number} -cn ${client_node_number}
  cd ~/DeathStarBench/socialNetwork
  source set_elba_env.sh
  ./scripts/CONTROL_exec.sh
  sudo cp /users/${username}/scripts_limit/generateResult.sh /users/${username}/socialNetwork/20*/
  cd /users/${username}/socialNetwork/
  sudo chmod +x 20*/*
  ./20*/generateResult.sh &> output.log
"

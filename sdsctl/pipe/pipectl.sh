#!/bin/bash

PipePath=/var/lib/libvirt/kspipe
LogPath=/var/log/virtpipe.log

start()
{
  # create pipe file
  if [ ! -p $PipePath ]
  then
    mkfifo $PipePath
  fi

  # listen pipe
  while true;
  do
    cmd="$(cat $PipePath)"
    echo -e "\ndate: `date '+%Y-%m-%d %H:%M:%S'`" >> $LogPath
    echo -e "receive command:\n"$cmd >> $LogPath
    output=$(eval $cmd)
    echo -e "command output:\n"$output >> $LogPath
  done
}

stop()
{
  echo "stopped"
}


case $1 in
    "start")
        start
        ;;
    "stop")
        stop
        ;;
    "restart")
        stop
        start
        ;;
    "status")
        echo "status"
        ;;
esac

exit 0

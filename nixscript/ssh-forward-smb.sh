#!/bin/sh
cmd="ssh -N -L 0.0.0.0:139:localhost:139 -L 0.0.0.0:445:localhost:445 $*"
echo $cmd

exec >>/tmp/ssh-forward-smb.log
exec 2>&1

loop() {
  echo ------------------------
  date -Is
  while :
  do
    $cmd || echo RETRY && sleep 3
  done
}

loop &
sleep 3

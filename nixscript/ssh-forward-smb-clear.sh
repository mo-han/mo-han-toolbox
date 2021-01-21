for p in $(ps | awk '/ssh-forward-smb.sh/ {print $1}'); do kill -9 $p; done

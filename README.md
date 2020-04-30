# podwatch ![](https://www.iconfinder.com/icons/44356/download/png/32)
watches and updates containers in need.

#### Description
Utility which uses podman.socket to watch and update running containers.

#### Usage 
```
usage: podwatch.py [-h] [--dry-run] [--debug]

Utility which uses podman.socket to watch and update running containers.

optional arguments:
  -h, --help   show this help message and exit
  --dry-run    List only actions to be performed. Doesn't update images nor restarts containers.
  --debug, -d  Log additional debug information.
```


#### Installation
Since there are currently no distribution-specific packages available, podman must be installed manually

##### Requirements

Python-Podman (Python bindings for using Varlink access to Podman Service)

`pip3 install podman` or `dnf install python-podman-api`

`pip3 install varlink` or `dnf install python3-varlink`

##### 1) Clone repo
```
git clone https://github.com/CyberNation-EU/podwatch.git
cd podwatch
```

##### 2) Copy podwatch
```
sudo cp podwatch.py /usr/bin/podwatch
chmod +x /usr/bin/podwatch
```

##### 3) Configure systemd

This solution uses a systemd timer to check for updates every day at 4:00am.

###### a) Podman running as user

```
mkdir -p ~/.local/share/systemd/user/
cp misc/podwatch.* ~/.local/share/systemd/user/
systemctl --user daemon-reload
systemctl --user enable io.podman.socket --now
systemctl --user enable podwatch.timer --now
```

###### b) Podman running as root

```
cp misc/podwatch.* /usr/lib/systemd/user/
systemctl daemon-reload
systemctl enable io.podman.socket --now
systemctl enable podwatch.timer --now
```

Podwatch should now be configured. Further information can be obtained with the following command.

Show Timer information
`systemctl [--user] list-timers`

# podwatch ![](https://www.iconfinder.com/icons/44356/download/png/32)
watches and updates pods in need 

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
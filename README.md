# SDN
This SDN alternates network traffic between two or more host computers each running a different web server configurations. This ensures attackers can only gather information on an information server during a limited rotational window before the system architecture changes.
# Presentation
https://docs.google.com/presentation/d/1uNWUvFxsehz2Q5Uzb6pV7EZbAWTs9sCoVl4dXX8LPxg/edit?usp=sharing
# Report
https://docs.google.com/document/d/1rdwA6kgqjEu27rjAGxILOTLDxRtztQs_BP2zFEayU-E/edit?usp=sharing
# Video Demonstration
https://www.youtube.com/watch?v=cCB_virP1qQ
## Network Map
<img src="https://github.com/Maw1395/SDN/blob/master/Network-Diagram.png" height=400/>

## Control Flow
<img src="https://github.com/Maw1395/SDN/blob/master/Packet-Flow.jpg" height=400/>

## Python 3.5 installation
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.5
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
sudo pip install virtualenv
virtualenv -p python3.5 venv
```
## zof installation

### Install /usr/bin/oftr dependency.
```
sudo add-apt-repository ppa:byllyfish/oftr
sudo apt-get update
sudo apt-get install oftr
```
### Create virtual environment and install latest zof.
```
python3.5 -m venv myenv
source myenv/bin/activate
pip install zof
```

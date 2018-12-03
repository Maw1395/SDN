# SDN
# Python 3.5 installation
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.5
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
sudo pip install virtualenv
virtualenv -p python3.5 venv
```
# zof installation

## Install /usr/bin/oftr dependency.
```
sudo add-apt-repository ppa:byllyfish/oftr
sudo apt-get update
sudo apt-get install oftr
```
## Create virtual environment and install latest zof.
```
python3.5 -m venv myenv
source myenv/bin/activate
pip install zof
```

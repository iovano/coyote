apt install python3 python3-pip
apt install virtualenv
apt install lirc

python3 -m venv .venv

.venv/bin/python3 -m pipenv install
.venv/bin/python3 -m pip install requests pyyaml RPi.GPIO
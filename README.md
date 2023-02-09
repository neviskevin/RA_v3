# proccess/src/data/process_data.py
line 169 shows the calcultion for the risk value. This is from a research paper which analyzed histroical fire data

# proccess/src/run_risk_assesment.py
Takes a coordinate json file and outputs risk assesment, the calculation can be run on historical data

## APIs


# AWS instance

the remote desktop file is in this repository

Password: @SS-&7.4F=AX7HrrEvUUt1km5sZE*4Ve

# Server

Start: flask --app server run
Endpoint: https://d1a1-54-144-208-8.ngrok.io/value/

```
GET / returns active if running
GET /point/<x>/<y>/<res> returns coordinates of hexagon vertices at given resolution
GET /id/<x>/<y>/<res> returns the standardized h3 id
GET /value/<id>
GET /job/<id>This will start a persistent job
```
Optional Headers: 
KEY ngrok-skip-browser-warning 
VAL 1


https://thesecmaster.com/procedure-to-install-openssl-on-the-windows-platform/

Deploy server (will change IP address)

```
.\ngrok config 2GlsuLtVnE7LFwT3Jsg6VcxEd1w_41TzkCdCgFB5sPycwAviZ
.\ngrok http 5000
```

# H3
Version 3.7.1
https://github.com/uber/h3-py/releases

https://pypi.org/project/h3/
To see avaliable functions you have to download the release 3.7.1 or 3.7.3 and look at the tests

# Building Windows Cloud Environment

Install git
https://git-scm.com/download/win
Install python
https://www.python.org/downloads/

Add to path: 
```
$PATH = [Environment]::GetEnvironmentVariable("PATH")
$xampp_path = “C:\Users\Administrator\AppData\Local\Programs\Python\Python310"
[Environment]::SetEnvironmentVariable("PATH", "$PATH;$xampp_path")
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
git clone https://github.com/neviskevin/proccess.git
pip install virtualenv
virtualenv infernoguard
cd infernoguard/scripts 
.\activate
Pip install pipwin
pipwin install gdal
pipwin install fiona
pip install -r requirements.txt
```


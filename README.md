# Building Windows Cloud Environment

Install git
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


$PATH = [Environment]::GetEnvironmentVariable("PATH")
$xampp_path = "C:\Users\Administrator\AppData\Local\Programs\Python\Python310"
[Environment]::SetEnvironmentVariable("PATH", "$PATH;$xampp_path")
cd infernoguard/scripts
.\activate.ps1
cd ..
cd ..\proccess1_0
python -m bin.risk_assessment

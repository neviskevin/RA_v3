# Divide json coordinates into smaller files
# keep root data in C:\Users\Administrator\Desktop\risk_assesment_sum22\data\temp

# get json from work order
$json = (Get-Content "C:\Users\Administrator\Desktop\risk_assesment_sum22\data\collins_co_coordinates.json" -Raw) | ConvertFrom-Json

#this next code maps out the json coordinates into arrays
#initialize values with the first vertex of the square
#coordinates is the geojson label
$minx = $json.coordinates[0][0][0]
$maxx = $json.coordinates[0][0][0]

$miny = $json.coordinates[0][0][1]
$maxy = $json.coordinates[0][0][1]

For ($i=1; $i -le 3; $i++){ # assign maxs and mins
    if($json.coordinates[0][$i][0] -lt $minx){
    $minx = $json.coordinates[0][$i][0]
    }
    
    if($json.coordinates[0][$i][0] -gt $maxx){
    $maxx = $json.coordinates[0][$i][0]
    }

    if($json.coordinates[0][$i][1] -lt $miny){
    $miny = $json.coordinates[0][$i][1]
    }

    if($json.coordinates[0][$i][1] -gt $maxy){
    $maxy = $json.coordinates[0][$i][1]
    }
}

#here is the multiplier we can pass in to divide region, evenly by x and y
$div = 3
$incx = ($maxx - $minx)/$div
$incy = ($maxy - $miny)/$div

$temp = $json

For ($i=0; $i -le ($div-1); $i++){ #increment x
For ($j=0; $j -le ($div-1); $j++){ #increment y

$g = $j+1 # y
$f = $i+1 # x 


$temp.coordinates[0][0][0] = $minx + $f*$incx #larger
$temp.coordinates[0][0][1] = $miny + $g*$incy #larger
$temp.coordinates[0][1][0] = $minx + $i*$incx
$temp.coordinates[0][1][1] = $miny + $g*$incy #larger
$temp.coordinates[0][2][0] = $minx + $f*$incx #larger
$temp.coordinates[0][2][1] = $miny + $j*$incy
$temp.coordinates[0][3][0] = $minx + $i*$incx
$temp.coordinates[0][3][1] = $miny + $j*$incy



$x = "C:\Users\Administrator\Desktop\risk_assesment_sum22\" + $i+"_" + $j

#$y = $x + ".json"
#$temp | ConvertTo-Json | Out-File $y
$z = "C:\Users\Administrator\proccess"+$i+"_" + $j

#create new subdirectory to store another process
New-Item -Path $z -ItemType Directory
Start-Sleep -s 1
Copy-Item -Path "C:\Users\Administrator\proccess\*" -Destination $z -PassThru -Recurse

#make specific json
$jsonpath = "C:\Users\Administrator\proccess"+$i+"_"+$j+"\data\collins_co_coordinates.json"
$jsoncontent = '{"type": "Polygon","coordinates": [[['+$temp.coordinates[0][0][0]+', '+$temp.coordinates[0][0][1]+'],['+$temp.coordinates[0][1][0]+', '+$temp.coordinates[0][1][1]+'],['+$temp.coordinates[0][3][0]+'6, '+$temp.coordinates[0][3][1]+'],['+$temp.coordinates[0][2][0]+', '+$temp.coordinates[0][2][1]+'],['+$temp.coordinates[0][0][0]+', '+$temp.coordinates[0][0][1]+']]]}'
New-Item $jsonpath
Set-Content $jsonpath $jsoncontent

Set-Location "C:\Users\Administrator\infernoguard\scripts"
$dir = "C:\Users\Administrator\proccess"+$i+"_"+$j
$string = '-nologo -noprofile -executionpolicy bypass -command ./activate.ps1; cd '+$dir+'; python -m bin.risk_assessment; Read-Host "Wait for a key to be pressed"'
#start-process powershell.exe -argument $string

Start-Sleep -s 5
# check for window open
# check for completed proccess inside of created folder
# if no delete temp folder then restart
}
}
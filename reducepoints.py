from traceback import print_exc
import pandas as pd
from pandas import DataFrame as df
data = pd.read_csv("data.csv")

#we have a rectagle input so splitting into equally proportional regions is simple
#degree^2 is how many squares we will generate
degree = 10

#here are the number of points per region to return
num = 10

incx = abs(abs(data["x"].min()) - abs(data["x"].max()))/degree
incy = abs(abs(data["y"].max()) - abs(data["y"].min()))/degree

#here we only include the firerisk scores of more than 4.5
data = data[data["fire_risk"]>4.9]
print(data.shape)

# here we calculate the sum of the risk values and
# then make a list of the ten most risky points in each region
x = 0
y = 0
final = pd.DataFrame()
while(x<(degree-1)):#change to degree
    while(y<(degree-1)):
        temp = data[data["x"]>(data["x"].min() + incx*x)]
        temp = temp[temp["x"]<(data["x"].min() + incx*(x+1))]
        temp = temp[temp["y"]>(data["y"].min() + incy*y)]
        temp = temp[temp["y"]<(data["y"].min() + incy*(y+1))]

        z = temp["fire_risk"].sum()
        temp["subSum"] = z

        #only keep largest 'num' of fire_risk values
        #temp = temp.nlargest(num,['fire_risk'])
        
        final = pd.concat([final,temp])
        y = y + 1
    y = 0
    x = x + 1

#remove unneeded column
#final.pop('Unnamed: 0')
print(final.shape)
final.to_csv("output.csv")

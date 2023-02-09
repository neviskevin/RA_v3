import pandas as pd
import h3

data = pd.read_csv("data.csv")
i = 0
len = data.shape[0]
data['id'] = 0 #= series
''' this drops all rows except first 1000
.drop(labels=[0,1000],
        axis=0,
        inplace=False)
'''

def hexagons(resolution,json_filename):
    temp1 = data
    print("first")
    i =0
    while i<(len-1):
        temp1.loc[i,'id'] = h3.geo_to_h3(data['y'][i],data['x'][i],resolution)
        i = i + 1

    print("second")
    i = 1
    a = pd.DataFrame(columns=['id','fire_risk'])
    for e in temp1['id'].unique():
        temp = temp1[temp1['id']==e]
        a.loc[i,'id'] = e
        a.loc[i,'fire_risk'] = temp['fire_risk'].sum()
        i = i + 1
    a.to_csv("check.csv")

    print("third")  
    i = 1
    a['coords'] = 0
    b = pd.DataFrame(columns=['coords','fire_risk'])
    while i < a.shape[0]:
        tempvalue = a['id'][i]
        try:
            b.loc[i,'coords'] = h3.h3_to_geo_boundary(tempvalue,True)
            b.loc[i,'fire_risk'] = a['fire_risk'][i]
        except:
            print(tempvalue)
        i = i + 1

    print("fourth") 
    first = '{"type":"FeatureCollection","features": ['
    each1 = ""
    i = 1
    while (i < b.shape[0]):
        try:
            astring = str(b.loc[i,'coords']).replace('(','[')
            astring = astring.replace(')',']')
            each1 = '{ "type": "Feature","geometry": {"type": "Polygon","coordinates": ['+ astring + ']},"properties": {"risk":'+str(data['fire_risk'][i])+'}}'
        except:
            if(i<10):
                print(b.loc[i,'coords'])
        i = i + 1
        if i != b.shape[0]:
            each1 = each1 + ','
        first = first + each1


    last = first + ']}'
    text_file = open(json_filename, "w")
    n = text_file.write(last)
    text_file.close()

    
#43 square meter hexagon, h3 resolution = 12
#second will be 300 square meter hexagon, h3 resolution = 11
hexagons(10,"coords10.json")
hexagons(11,"coords11.json")
hexagons(12,"coords12.json")

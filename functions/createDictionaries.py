import os
import xml.etree.ElementTree as et
import pickle


# os.chdir("..")
network_file_name       = 'sumo_files/map.net.xml'               # Sumo map
dictionaries_file_path  = 'python_files/dictionary_'             # Dictionaries files

file_path = os.path.abspath(network_file_name)
dom = et.parse(file_path)

print('\nRunning script that generates dictionaries....')

##  Build the dictionary of roads
edges       = dom.findall('edge')
roads       = []
road_id     = 0                             # lane identification number number
junctions   = dom.findall('junction')
for r in edges:
    if  r.attrib['type']=='highway.primary' or r.attrib['type']=='highway.secondary': # (other attributes that may be useful: 'highway.residential', 'highway.tertiary'
        r_to        = r.attrib['to']               # r_to is the (sumo) node that is the road destination
        lanes       = r.findall('lane')           # cur_lanes is a list
        len_lane    = lanes[0].attrib['length']
        speed       = lanes[0].attrib['speed']
        for j in junctions:             # check if the destination node is a signalized intersection
            if j.attrib['id'] == r_to:
                junId       = j.attrib['id']
                if j.attrib['type']=='traffic_light':
                    signalz = 'Y'
                else:
                    signalz = 'N'
        roads.append({'id':road_id, 'sumo_id':r.attrib['id'], 'signalized':signalz, 'speed':speed, 'len':len_lane, 'junct':junId })
        road_id += 1

f = open(dictionaries_file_path +'roads', 'wb')
pickle.dump(roads, f)
f.close()
print('* Dictionary of roads created: ', len(roads))







##  Build the dictionaries of edges (edge is a connection within an intersection)
connects = dom.findall('connection')
edges = []
edge_id = 0
for c in connects:
    for r in roads:             # Check if it connects two modeled roads
        if r['sumo_id'] == c.attrib['from']:
            o = r['id']
        if r['sumo_id'] == c.attrib['to']:
            d = r['id']
    if 'o' in locals() and 'd' in locals(): # if the edge connects two modeled roads
        if c.get('tl'):
            edges.append({ 'id':edge_id, 'orig':o, 'dest':d, 'signalized':'Y', 'tl': c.attrib['tl'], 'linkIndex': c.attrib['linkIndex']})
        else:
            edges.append({'id': edge_id, 'orig':o, 'dest':d, 'signalized': 'N'})
        del o
        del d
        edge_id += 1

f = open(dictionaries_file_path +'edges', 'wb')
pickle.dump(edges, f)
f.close()






## Create dictionary of phases (one phase includes all edges with the same origin)
phases = []
ph_id = 0
ph_signalized=0
for r in roads:
    cur_phase_destinations = []
    edgeIdList = []
    for e in edges:     # Search all destinations for current road
        if e['orig']==r['id']:
            cur_phase_destinations.append(e['dest'])
            edgeIdList.append(e['id'])
    cur_phase_destinations = list(set(cur_phase_destinations))  # remove duplicates
    phases.append({'id':ph_id, 'origin':r['id'], 'dest':cur_phase_destinations, 'signalized':r['signalized'], 'junct':r['junct'], 'edges':edgeIdList})
    if r['signalized']=='Y':
        ph_signalized+=1
    ph_id+=1

f = open(dictionaries_file_path +'phases', 'wb')
pickle.dump(phases, f)
f.close()
print('* Dictionary of phases created: ',ph_signalized)





##  Create dictionary of junctions
junctions = dom.findall('junction')
lights = []
for j in junctions:
    if j.attrib['type'] == 'traffic_light':
        listOfConn = []
        for ph in phases:         # find all phases in the phases list that are associated to j
            if ph['junct']==j.attrib['id']:
                listOfConn.append(ph['id'])
        listOfEdges = []
        for e in edges:
            if e['signalized']=='Y' and e['tl']==j.attrib['id']:
                listOfEdges.append(e['id'])
        lights.append({'sumo_id':j.attrib['id'] , 'phases':listOfConn, 'edges':listOfEdges})

f = open(dictionaries_file_path +'lights', 'wb')
pickle.dump(lights, f)
f.close()
print('* Dictionary of sigalized intersections created: ',len(lights))






# print('\nSet of edges:')
# for e in edges:
#     print(e)
# print('\nSet of traffic lights:')
# for tl in lights:
#     print(tl)
# print('\nSet of roads (each road contains multiple lanes with same origin and destination:')
# for r in roads:
#     print(r)
# print('\nSet of phases:')
# for p in phases:
#     print(p)




print('--------------------------------')
print('*** Success!!!  Dictionaries created.\n')
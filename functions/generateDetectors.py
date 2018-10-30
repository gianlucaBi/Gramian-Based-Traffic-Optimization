import xml.etree.ElementTree as et
import os
import pickle
import lxml.etree as lxml



detectors_files_name            = 'sumo_files/detectors.add.xml'
dictionaries_file_path          = 'python_files/dictionary_'             # Dictionaries files
network_file_name               = 'sumo_files/map.net.xml'               # Sumo map




print('\nRunning script that generates detectors....')


dom = et.parse(network_file_name)

f = open(dictionaries_file_path +'roads', 'rb')
roads = pickle.load(f)
f.close()

root = et.Element("additional")


##  Build the dictionary of modeled lanes
edges = dom.findall('edge')
i_detect = 0
for e in edges:
    for rd in roads:    # Check if road is modeled
        if e.attrib['id']==rd['sumo_id']: # if yest, place a detector in every lane
            lanes = e.findall('lane')
            for l in lanes:
                lane_id = l.attrib['id']
                et.SubElement(root, 'laneAreaDetector', id=str(i_detect), freq='10', file="output_detectors.out.xml", lane=lane_id, endPos='-1',length='40')
                i_detect += 1
            break


tree = et.ElementTree(root)
tree.write(detectors_files_name)



## Additional parsing to make xml readable
parser = lxml.XMLParser(remove_blank_text=True)
tree = lxml.parse(detectors_files_name, parser)
tree.write(detectors_files_name, pretty_print=True, xml_declaration=True, encoding='utf-8', method="xml")

print('--------------------------------')
print('*** Success!!!  Detectors created.\n')
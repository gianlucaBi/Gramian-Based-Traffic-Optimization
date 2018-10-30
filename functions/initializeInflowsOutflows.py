# This code reads a districts file (.taz.xml) and generates an initial state x_o for the spectral abscissa optimization
import numpy as np
import scipy.optimize as opt
import scipy.linalg as la
import pylab
import pickle
import sys
import xml.etree.ElementTree as et




matrices_file_path          = 'python_files/pyoutMatrices_'
dictionaries_file_path      = 'python_files/dictionary_'
districts_file_name         = 'sumo_files/districts.taz.xml'
inflows_outflows_file_name  = 'python_files/inflowsOutflows_'



def setVector(i, subvector, vector, sigma):
    if i<0 or i>len(sigma):
        print('Indices out of bounds in setVector')
    v = np.copy(vector)
    ind_s = int(np.sum(sigma[:i]))          # start index
    ind_end = int(np.sum(sigma[:i+1]))      # final index
    v[ind_s:ind_end] = subvector
    return v

def getArgument(argName, listOfArguments):
    i=0
    for l in listOfArguments:
        if l==str('-'+argName):
            return listOfArguments[i+1]
            break
        i+=1
    return None







def main():
    if getArgument('m',sys.argv):
        outflows_magnitude = float(getArgument('m',sys.argv))
    else:
        outflows_magnitude = 1
    print('\n Running script that generates initial state x0 and outflows with outflow intensity='+str(outflows_magnitude)+'  ...')


    f = open(matrices_file_path+'sigma', 'rb')
    sigma = pickle.load(f)
    f.close()


    # Build the dictionaries containing roads for i) source district and ii) destination district
    f = open(dictionaries_file_path +'roads', 'rb')
    roads = pickle.load(f)
    f.close()
    dom = et.parse(districts_file_name)
    tazs = dom.findall('taz')
    for area in tazs:
        if area.attrib['id']=='source':
            source_edges = area.attrib['edges'].split()
        if area.attrib['id'] == 'destination':
            destination_edges = area.attrib['edges'].split()

    print('* Working on vector of initial densities x0...', end="", flush=True)
    x0 = np.zeros(np.sum(sigma))
    for s in source_edges:
        for r in roads:
            if s==r['sumo_id']:
                road_id = r['id']
                road_size=sigma[road_id]
                x0_desired = np.random.rand(road_size)
                x0 = setVector(road_id, x0_desired, x0, sigma)
    x0 = x0/la.norm(x0)
    f = open(inflows_outflows_file_name +'inflows', 'wb')
    pickle.dump(x0, f)
    f.close()
    print('[DONE]')




    print('* Working on vector of outflows at destinations...', end="", flush=True)
    outflows = np.zeros(np.sum(sigma))
    for d in destination_edges:
        for r in roads:
            if d==r['sumo_id']:
                road_id = r['id']
                road_size=sigma[road_id]
                outflow_desired = outflows_magnitude*np.random.rand(road_size)
                outflows = setVector(road_id, outflow_desired, outflows, sigma)

    f = open(inflows_outflows_file_name +'outflows', 'wb')
    pickle.dump(outflows, f)
    f.close()
    print('[DONE]')

    print('--------------------------------')
    print('*** Success!!!  Inflows and Outflows initialized.\n')


if __name__ == "__main__":
    main()

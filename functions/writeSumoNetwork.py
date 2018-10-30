import numpy as np
import scipy.optimize as opt
import scipy.linalg as la
import pylab
import pickle
import sys
import os
import xml.etree.ElementTree as et

durations_files_name            = 'python_files/pyoutOptimization_'
dictionaries_file_path          = 'python_files/dictionary_'
matrices_file_path              = 'python_files/pyoutMatrices_'
network_file_name               = 'sumo_files/map.net.xml'
optimized_maps_files_name       = 'sumo_files/optimized_'



def getArgument(argName, listOfArguments):
    i=0
    for l in listOfArguments:
        if l==str('-'+argName):
            return listOfArguments[i+1]
            break
        i+=1
    return None


def main():
    if getArgument('T',sys.argv):
        T  = float(getArgument('T',sys.argv))
    else:
        T = 50
    print('\n Running script that convert results of optimization into sumo network with T='+str(T)+' ...')

    print('* Working on creating a network with OPTIMAL durations...', end="", flush=True)
    # Load vector of durations d
    f = open(durations_files_name+'dOptimal', 'rb')
    dOpt = pickle.load(f)
    f.close()
    dOpt = dOpt*T               # Rescale d over the period T

    # Load the XML file
    network_file_path = os.path.abspath(network_file_name)
    dom = et.parse(network_file_path)
    sumo_tlLogic = dom.findall('tlLogic')
    root = dom.getroot()

    # Load the dictionary of traffic lights
    f = open(dictionaries_file_path+'lights', 'rb')
    lights = pickle.load(f)
    f.close()
    # Load the dictionary of phases
    f = open(dictionaries_file_path+'phases', 'rb')
    phases = pickle.load(f)
    f.close()
    f = open(dictionaries_file_path+'edges', 'rb')
    edges = pickle.load(f)
    f.close()

    ## Delete all pre-defined tlLogic
    for sumo_tl in sumo_tlLogic:
        for tl in lights:
            if sumo_tl.attrib['id']==tl['sumo_id']:      # If this junction is modeled
                cur_phases = sumo_tl.findall('phase')  # Remove default phases
                for cp in cur_phases:
                    sumo_tl.remove(cp)


    mem_str = []
    i_d = 0 # index for vector of durations
    for tl in lights:
        noConn = len(tl['edges'])
        intersPhasesDict = [phases[i] for i in tl['phases']]     # dictionary with phases for current intersection
        dest = []                                                   # list containing id of destination edges
        i_d = 0 # index for connections in sumo file
        for ph in intersPhasesDict:
            listEdges = ph['edges']
            edges_dict = [edges[i] for i in listEdges]      # dictionary with all edges for current phase
            linkIndexes = []
            for ed in edges_dict:       # find the 'linkIndex' associated with every edge. This will give the position of 'G' in the string
                linkIndexes.append(ed['linkIndex'])
            myStr = ''
            for ii in range(noConn):
                if str(ii) in linkIndexes:
                    myStr = myStr + 'G'
                else:
                    myStr = myStr + 'r'
            mem_str.append(myStr)


        # Edit the xml file
            for sumo_tl in sumo_tlLogic:
                if sumo_tl.attrib['id']==tl['sumo_id']: # find the correspond light in the network file
                    b = et.SubElement(sumo_tl, 'phase', attrib={'duration': str(round(dOpt[i_d], 1)), 'state': myStr})

            i_d += 1


    dom.write(optimized_maps_files_name+'map.net.xml')
    print('[DONE]')






    print('* Working on creating a network with FEASIBLE durations...', end="", flush=True)
    ## Create a map file with a suboptimal choice
    f = open(durations_files_name+'dFeasible', 'rb')
    dFeas = pickle.load(f)
    f.close()
    dFeas = dFeas*T             # Rescale d over the period T


    # Load the XML file
    network_file_path = os.path.abspath(network_file_name)
    dom = et.parse(network_file_path)
    sumo_tlLogic = dom.findall('tlLogic')
    root = dom.getroot()

    # Load the dictionary of traffic lights
    f = open(dictionaries_file_path+'lights', 'rb')
    lights = pickle.load(f)
    f.close()
    # Load the dictionary of phases
    f = open(dictionaries_file_path+'phases', 'rb')
    phases = pickle.load(f)
    f.close()
    f = open(dictionaries_file_path+'edges', 'rb')
    edges = pickle.load(f)
    f.close()

    ## Delete all pre-defined tlLogic
    for sumo_tl in sumo_tlLogic:
        for tl in lights:
            if sumo_tl.attrib['id']==tl['sumo_id']:      # If this junction is modeled
                cur_phases = sumo_tl.findall('phase')  # Remove default phases
                for cp in cur_phases:
                    sumo_tl.remove(cp)


    mem_str = []
    i_d = 0 # index for vector of durations
    for tl in lights:
        noConn = len(tl['edges'])
        intersPhasesDict = [phases[i] for i in tl['phases']]     # dictionary with phases for current intersection
        dest = []                                                   # list containing id of destination edges
        i_d = 0 # index for connections in sumo file
        for ph in intersPhasesDict:
            listEdges = ph['edges']
            edges_dict = [edges[i] for i in listEdges]      # dictionary with all edges for current phase
            linkIndexes = []
            for ed in edges_dict:       # find the 'linkIndex' associated with every edge. This will give the position of 'G' in the string
                linkIndexes.append(ed['linkIndex'])
            myStr = ''
            for ii in range(noConn):
                if str(ii) in linkIndexes:
                    myStr = myStr + 'G'
                else:
                    myStr = myStr + 'r'
            mem_str.append(myStr)


        # Edit the xml file
            for sumo_tl in sumo_tlLogic:
                if sumo_tl.attrib['id']==tl['sumo_id']: # find the correspond light in the network file
                    b = et.SubElement(sumo_tl, 'phase', attrib={'duration': str(round(dFeas[i_d], 1)), 'state': myStr})

            i_d += 1


    dom.write(optimized_maps_files_name+'SUBOPTmap.net.xml')
    print('[DONE]')

    print('--------------------------------')
    print('*** Success!!!  Network files created.\n')


if __name__ == "__main__":
    main()
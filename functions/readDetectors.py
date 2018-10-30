import xml.etree.ElementTree as et
import os
import pickle
import lxml.etree as lxml
import pylab
import numpy as np
import scipy.io



detetctor_file_name = 'sumo_files/output_detectors.out.xml'               # Name of dictionary files


print('\n Running srcipt to read number of vehicles on detectors...')


dom = et.parse(detetctor_file_name)
intervals = dom.findall('interval')

## See http://sumo.dlr.de/wiki/Simulation/Output/Lanearea_Detectors_(E2)

ind = 0
J = []
iterations = []
cumJ = [0]
for interv in intervals:
    noVehicles = float(interv.attrib['meanVehicleNumber'])

    cumJ.append(cumJ[-1]+noVehicles)
    J.append(noVehicles)
    iterations.append(ind)

    ind += 1

cumJ.pop(0) # remove first element to match size


scipy.io.savemat('outputs/costJ.mat',dict(cumJ= cumJ) )

pylab.figure()
pylab.plot(iterations, cumJ, '-')
pylab.title('Integral of number of vehicles')
pylab.show()
pylab.ion()

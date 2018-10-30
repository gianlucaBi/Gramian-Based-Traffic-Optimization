# Gramian-Based Traffic Optimization

This project contains a set of scripts that allow to import a certain OSM map and to perform 
Gramian-Based Optimization and simulation of the traffic network in a Python-Sumo framework.

# Required software
* SUMO v0.32.0 or older (Simulation of Urban MObility)
  (See: http://sumo.sourceforge.net/)
* Python 3

# Files needed
1) OSM file containing the geographic information for the traffic network of interest.
   (See, e.g.: https://www.openstreetmap.org/)
2) A polygon file describing TAZs and origins/destinations of traffic
3) Origin inflows through an OD matrix.

# Execution
The file "main_bash.sh" is a bash executable file that will guide you through the creation of
necessary files and runs the optimization and simulation.

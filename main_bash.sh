#!/bin/bash  
# This file reads an OSM map file and runs a sequence of script to create the matrices necessary to run the spectral abscissaoptimization

# # Before running this file you need:
# 1) OSM file in data_sumo
# 2) Define polygons describing TAZs (you need 2 polygons. One called source, the other called destination)
# 3) Define origin-destination matrix
# 4) Define sumo configuration file

% SUMO INSTALLATION FOLDER:
sumo_folder="/Users/gian/sumo/sumo-0.32.0/tools/"


# These are the input files
osm_network_name="network_input_files/map.osm" 							# Name of the (input) osm file
TAZ_polygons_file="network_input_files/TAZ_polygons.poi.xml" 			# File describing TAZ polygons
od_file="network_input_files/OD_file.od"								# File containing origin-destination matrices

sumo_config_file="configs.sumo.cfg"							# Configuration file for sumo simulation



# These are generated files
network_name="sumo_files/map.net.xml" 								# network file .net.xml
routes_file="sumo_files/TAZ_routes.rou.xml" 							# routes file .rou.xml
flows_file="sumo_files/flowFile.xml"
building_polygons_file="sumo_files/buildingsPolygons.poi.xml" 		# polygon file generated from buildings
taz_file="sumo_files/districts.taz.xml" 								# File describing TAZ
trip_file="sumo_files/trips.odtrips.xml"



clear





# INPUT NEEDED: OSM file
# Convert network from OSM file to NET file
echo "Creating network file (.net.xml) from OSM file..."
netconvert --no-internal-links --osm-files $osm_network_name --output.street-names -o $network_name  --keep-edges.by-type highway.primary,highway.secondary --tls.discard-simple --geometry.remove
# Other road types: 	highway.residential,highway.tertiary
read -p "[DONE] - Press enter to continue"

# Import polygons representing buildings
echo "Importing polygon data (buildings) from OSM data..."
polyconvert --net-file $network_name --osm-files $osm_network_name --type-file typemap.xml -o $building_polygons_file
read -p "[DONE] - Press enter to continue"

echo "INPUT NEEDED: Manually select source and destination polygons."
echo "Please follow these guidelines:"
echo "-One poligon with id 'source', representing the sources of traffic"
echo "-One poligon with id 'destination', representing the destinations of traffic"
echo "-Save the polygon file as 'TAZ_polygons.poi.xml' inside the folder 'network_input_files'"
read -p "[DONE] - Press enter to continue"



./netedit_32 $network_name









## INPUT NEEDED: Files generated in previous segment of script + TAZ_polygons_file + od_file
# Read polygons and create districts
echo "Creating TAZ from polygons..."
aux_path=$sumo_folder
aux_path+=edgesInDistricts.py
python $aux_path -n $network_name -t $TAZ_polygons_file -o $taz_file
read -p "[DONE] - Press enter to continue"

# Read OD matrix and create trip definition file
echo "Creating trips from OD matrix..."
od2trips -n $taz_file -d $od_file -o $trip_file
read -p "[DONE] - Press enter to continue"

# Create dictionaries
python functions/createDictionaries.py

# Create matrices
python functions/buildMatrices.py -h 500

# initialize inflows and outflows
python functions/initializeInflowsOutflows.py -m 1
read -p "[DONE] - Press enter to continue"








# Run gradient descent
python functions/alpha_eps_gradient.py -eps_inv 2 -max_iter 20 -gamma 0.5

echo "OPTIMIZATION TERMINATED. Decide whether you would like to update epsilon or to continue."
read -p "[DONE] - Press enter to continue"










## INPUT NEEDED: Files generated in previous segment of script
# Create optimized and suboptimal network file
python functions/writeSumoNetwork.py -T 40

# Create detectors
python functions/generateDetectors.py

# Generate random routes
echo "Generate routes..."
duarouter -n $network_name -t $trip_file -o $routes_file
read -p "[DONE] - Press enter to continue"


echo "Running sumo simulation..."
sumo-gui $sumo_config_file


# Run script to plot number of vehicles on detectors
python functions/readDetectors.py






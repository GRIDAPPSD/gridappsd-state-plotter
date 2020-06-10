#!/bin/bash
SIMREQ={\"power_system_config\":{\"Line_name\":\"_5B816B93-7A5F-B64C-8460-47C17D6E4B0F\"},\"service_configs\":[{\"id\":\"state-estimator\",\"user_options\":{\"use-sensors-for-estimates\":true}},{\"id\":\"gridappsd-sensor-simulator\",\"user_options\":{\"default-perunit-confidence-band\":0.02,\"simulate-all\":true,\"sensors-config\":{},\"default-normal-value\":100.0,\"random-seed\":0.0,\"default-aggregation-interval\":30.0,\"passthrough-if-not-specified\":false,\"default-perunit-drop-rate\":0.05}}]} # ieee13nodecktassets using sensors
#SIMREQ={\"power_system_config\":{\"Line_name\":\"_5B816B93-7A5F-B64C-8460-47C17D6E4B0F\"},\"service_configs\":[{\"id\":\"state-estimator\",\"user_options\":{\"use-sensors-for-estimates\":false}}]} # ieee13nodecktassets using simulation

#SIMREQ={\"power_system_config\":{\"Line_name\":\"_C1C3E687-6FFD-C753-582B-632A27E28507\"},\"service_configs\":[{\"id\":\"state-estimator\",\"user_options\":{\"use-sensors-for-estimates\":true}},{\"id\":\"gridappsd-sensor-simulator\",\"user_options\":{\"default-perunit-confidence-band\":0.02,\"simulate-all\":true,\"sensors-config\":{},\"default-normal-value\":100.0,\"random-seed\":0.0,\"default-aggregation-interval\":30.0,\"passthrough-if-not-specified\":false,\"default-perunit-drop-rate\":0.05}}]} # ieee123 using sensors
#SIMREQ={\"power_system_config\":{\"Line_name\":\"_C1C3E687-6FFD-C753-582B-632A27E28507\"},\"service_configs\":[{\"id\":\"state-estimator\",\"user_options\":{\"use-sensors-for-estimates\":false}}]} # ieee123 using simulation

#SIMREQ={\"power_system_config\":{\"Line_name\":\"_AAE94E4A-2465-6F5E-37B1-3E72183A4E44\"},\"service_configs\":[{\"id\":\"state-estimator\",\"user_options\":{\"use-sensors-for-estimates\":true}},{\"id\":\"gridappsd-sensor-simulator\",\"user_options\":{\"default-perunit-confidence-band\":0.02,\"simulate-all\":true,\"sensors-config\":{},\"default-normal-value\":100.0,\"random-seed\":0.0,\"default-aggregation-interval\":30.0,\"passthrough-if-not-specified\":false,\"default-perunit-drop-rate\":0.05}}]} # test9500new using sensors
#SIMREQ={\"power_system_config\":{\"Line_name\":\"_AAE94E4A-2465-6F5E-37B1-3E72183A4E44\"},\"service_configs\":[{\"id\":\"state-estimator\",\"user_options\":{\"use-sensors-for-estimates\":false}} # test9500new using simulation


./state-plotter.py $1 $SIMREQ -stats 2>&1 | tee spmagdbg.out
#./state-plotter.py $1 $SIMREQ -all 2>&1 | tee spmagdbg.out
#./state-plotter.py $1 $SIMREQ -ang -stats 2>&1 | tee spangdbg.out
#./state-plotter.py $1 $SIMREQ -50 2>&1 | tee spmagdbg.out
#./state-plotter.py $1 $SIMREQ -50 -overlay 2>&1 | tee spmagdbg.out
#./state-plotter.py $1 $SIMREQ -overlay -bus 150R,C -bus 150,C -bus 149,C -bus 1,C -bus 2,C -bus 3,C -bus 4,C -bus 5,C -bus 6,C -bus 7,C 2>&1 | tee spmagdbg.out

#./state-plotter.py $1 $SIMREQ -ang 2>&1 | tee spangdbg.out
#./state-plotter.py $1 $SIMREQ -legend -bus 634 -overlay 2>&1 | tee spdbg.out # ieee13nodecktassets
#./state-plotter.py $1 $SIMREQ -legend -bus 100 -bus 101 -overlay 2>&1 | tee spdbg.out # ieee123
#./state-plotter.py $1 $SIMREQ -500 2>&1 | tee spdbg.out
#./state-plotter.py $1 $SIMREQ -100 2>&1 | tee spdbg.out
#./state-plotter.py $1 $SIMREQ -all -match 2>&1 | tee spdbg.out
#./state-plotter.py $1 $SIMREQ -overlay -bus SOURCEBUS,A -bus 650,A -bus RG60,A 2>&1 | tee spdbg.out
#./state-plotter.py $1 $SIMREQ -nom -ang -overlay -bus 650,A -bus RG60,A -bus SOURCEBUS,A 2>&1 | tee spangdbg.out &
#./state-plotter.py $1 $SIMREQ -nom -mag -overlay -bus SOURCEBUS,A -bus 650,A -bus RG60,A 2>&1 | tee spmagdbg.out
#./state-plotter.py $1 $SIMREQ -overlay -bus 25,A -bus 25R,A -bus 9,A -bus 9R,A 2>&1 | tee spdbg.out
#./state-plotter.py $1 $SIMREQ -ang -all 2>&1 > spangdbg.out &
#./state-plotter.py $1 $SIMREQ -ang -25 -title 'all phases' 2>&1 &
#./state-plotter.py $1 $SIMREQ -ang -25 -phase A -title 'phase A' 2>&1 &
#./state-plotter.py $1 $SIMREQ -ang -25 -phase B -title 'phase B' 2>&1 &
#./state-plotter.py $1 $SIMREQ -ang -25 -phase C -title 'phase C' 2>&1 &
#./state-plotter.py $1 $SIMREQ -ang -25 -phase B -phase C 2>&1
#./state-plotter.py $1 $SIMREQ -ang 2>&1
#./state-plotter.py $1 $SIMREQ -ang -all -phase B 2>&1 &
#./state-plotter.py $1 $SIMREQ -ang -all -phase C 2>&1
#./state-plotter.py $1 $SIMREQ -mag -all 2>&1 | tee spmagdbg.out
#./state-plotter.py $1 $SIMREQ -mag -overly -bus 150R -bus 150 2>&1 | tee spmagdbg.out

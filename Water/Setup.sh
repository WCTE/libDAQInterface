#!/bin/bash
# Setup script for Mon-01 machine

source /opt/root_v6.28.04/bin/thisroot.sh

#Dependencies=`pwd`/Dependencies # Don't use this relative path'ing!
Dependencies=/MonitoringToolChain/Dependencies

WaterDir=/home/wcte/water/FTP

export LD_LIBRARY_PATH=${WaterDir}/lib:${Dependencies}/zeromq-4.0.7/lib:${Dependencies}/boost_1_66_0/install/lib:${Dependencies}/ToolDAQFramework/lib:${Dependencies}/ToolFrameworkCore/lib:$LD_LIBRARY_PATH

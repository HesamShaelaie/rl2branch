#!/bin/zsh
export DYLD_LIBRARY_PATH="/opt/anaconda3/envs/rl2branch/lib:/Users/hesam/Documents/Research/Temp-Soure/scipoptsuite-7.0.2/build/lib:/Users/hesam/Documents/coin/dist/lib"
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate rl2branch
"$@"

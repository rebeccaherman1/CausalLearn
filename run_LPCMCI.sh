#!/bin/sh
#
# LPCMCI submit script for Slurm. JOB-NAME and CORES-PER-CPU submitted outside in looper_LPCMCI.sh
#
#SBATCH --account=sobel           # Replace ACCOUNT with your group account name
#SBATCH -t 3-00:00                # Runtime in D-HH:MM
#SBATCH --mem-per-cpu=5G          # The memory the job will use per cpu core
#SBATCH --mail-user=rh2856@columbia.edu
#SBATCH --mail-type=ALL

ml anaconda
source activate py39

filename=$1                                    #FILENAME has no flag, and appears as the first argument
shift 1                                        #shift to the following arguments
while getopts k:p:s:t:d:w: flag                #list all possible flags here
do
    case "${flag}" in                          
	k) knn=${OPTARG};;                     #set singleton arguments
	s) SN=${OPTARG};;
	t) TM+=(${OPTARG});;                   #keep a list when flags are called multiple times
	p) prelim_iterations+=(${OPTARG});;
	d) home_dir=${OPTARG};;
	w) workers=${OPTARG};;
    esac
done

optlst=''                                             #Tunable Parameters (repeated in the Logfile Name)
if [[ -n ${knn} ]]; then optlst+=" -knn $knn"; fi
if [[ -n ${SN} ]]; then optlst+=" -sn $SN"; fi
if [[ -n ${TM} ]]; then optlst+=" -tm ${TM[@]}"; fi
if [[ -n ${prelim_iterations} ]]; then optlst+=" -p ${prelim_iterations[@]}"; fi
bkgd_args=''                                          #Constant Arguments (NOT repeated in the Logfile Name)
if [[ -n ${home_dir} ]]; then bkgd_args+=" -d $home_dir"; fi
if [[ -n ${workers} ]]; then bkgd_args+=" -w $workers"; fi

#Pass arguments to python script and pipe output to logfile using -u to prevent stout buffering
command="python -u learn_graph_LPCMCI.py -f $filename$optlst$bkgd_args > logs/${filename//.csv/}_${optlst//[ -]/}.txt"
echo "$command" #print for debugging
eval $command   #call command (need "eval" to prevent passing piping into python)

#End of script

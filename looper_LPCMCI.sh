#sh looper.sh
#Place files to iterate over in $H$st
H=../../ocp/users/rh2856/ #Storage Directory
st=csv/queued/            #Directory with files to iterate over
nd=csv/run/               #Directory where files are stored during and after processing
C=4                       #Cores to use in each sbatch request
B=run_LPCMCI.sh           #SBATCH script to call
S=(5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25)          #list of Iterated Arguments to be passed individually to different instances of the SBATCH script
K=(.1 .15 .25 .3 .35 .4 .45 .5 .55 .6)                # 
T=(1)                   #Argument Lists to be passed together to each instance of the SBATCH script
P=(1 2 3 4)

F=$(ls $H$st)             #gather files
AL=''                     #string representation of optional Argument Lists
if [[ -n ${T[@]} ]]; then for t in ${T[@]}; do AL+=" -t $t"; done; fi #add Argument Lists if they exist
if [[ -n ${P[@]} ]]; then for p in ${P[@]}; do AL+=" -p $p"; done; fi 
if [[ -z ${F[@]} ]]; then echo "Please put files to analyze in $H$st"; fi;
for f in $F; do           #iterate over files
    mv $H$st$f $H$nd$f    #move files to processing folder (prevents repeat analysis if LOOPER is called again)
    for s in ${S[@]:-''}; do                         #iterate over Iterated Arugments, execute once if no values are given.
        for k in ${K[@]:-''}; do
            IA=''                                    #string representation of optional Iterated Arguments
            if [[ -n ${s} ]]; then IA+=" -s $s"; fi  #add Iterated Arguments if they exist
            if [[ -n ${k} ]]; then IA+=" -k $k"; fi 
	    #Always include SBATCH arguments JOB-NAME and CPUS-PER-TASK between SBATCH and the name of the script.
	    #name the job by the Data Filename (minus 'csv') and the Iterated Arguments.
	    #Also always include any parameters required for the SBATCH script. In this case, Data Filename, Storage Directory, and Worker Threads (equal to cores requested).
	    #include otpional Argument Lists and Interated Arguments 
            cmd="sbatch --job-name=\"${f//.csv/}$IA\" --cpus-per-task=$C $B $f -d $H -w $C$AL$IA"
	    echo "$cmd"   #print for debugging
	    eval $cmd     #call the BASH script
        done
    done
done

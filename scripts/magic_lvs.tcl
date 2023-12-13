#set cell efuse_ctrl
#gds read efuse_ctrl.gds
set cell efuse_array
gds read user_project_wrapper.gds

load $cell
select top cell
extract all
ext2spice lvs
ext2spice subcircuit on
ext2spice -f ngspice

#lef write $cell.lef -hide
exit

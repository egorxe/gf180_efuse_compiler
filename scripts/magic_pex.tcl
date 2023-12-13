set cell efuse_ctrl
#set cell efuse_array
gds read $cell.gds
#gds read efuse_array.gds
set extract_res 1

load $cell
select top cell
#extract do all
#extract warn all
#extract unique
#extract do length
#extract all

if {$extract_res == 1} {
    ext2sim labels on
    ext2sim
    extresist simplify off
    #extresist lumped off
    #extresist tolerance 0.01
    extresist all
}
ext2spice cthresh 0.01fF
ext2spice rthresh 1
ext2spice subcircuit on
ext2spice scale off
ext2spice hierarchy on
ext2spice resistor tee on
#ext2spice short resistor
ext2spice subcircuit descend on

if {$extract_res == 1} {
    ext2spice extresist on
}

ext2spice -F -f ngspice
exit

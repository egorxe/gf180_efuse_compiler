set cell efuse_array
gds read efuse_array.gds

load $cell
select top cell

puts "\[INFO\]: Zeroizing Origin"
set bbox [box values]
set offset_x [lindex $bbox 0]
set offset_y [lindex $bbox 1]
move origin [expr {$offset_x/2}] [expr {$offset_y/2}]
puts "\[INFO\]: Current Box Values: [box values]"
property FIXED_BBOX [box values]

set tolerance 1
lef write $cell.lef -toplayer -nomaster
#-hide 7um
exit

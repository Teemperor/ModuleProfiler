set terminal svg size 9000,1900 fname 'Verdana' fsize 10
set output 'sizestats.svg'
 
 #set size noratio 40,1

set style fill solid 0.4 border -1
#set style fill transparent 0.4 solid border -1
 
set format y "%.0f kB"
set format x ""
set xtics rotate
set xtics font ", 5"

plot 'sizestats' u 2 w boxes lc rgb 'red' title 'RSS (modules)', \
     'sizestats' u 3:xtic(1) w boxes lc rgb 'green' title 'RSS (non-modules)'
    
     # withxtics 'memorystats' u 3:xtic(1) w boxes lc rgb  '#ff4d4d'
    
#     'memorystats' every 2::1 u 3:xtic(1) w boxes lc rgb  '#ff1d1d', \

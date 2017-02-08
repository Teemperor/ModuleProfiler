set terminal svg size 9000,1900 fname 'Verdana' fsize 10
set output 'memorystats.svg'
 
 #set size noratio 40,1

set style fill solid 0.4 border -1
#set style fill transparent 0.4 solid border -1
 
set format y "%.0f kB"
set format x ""
set xtics rotate
#set xtics font ", 30"

plot 'memorystats' u 2 w boxes lc rgb 'white' title 'RSS (modules)', \
     'memorystats' u 3 w boxes lc rgb  '#ff4d4d'  title 'RSS (non-modules)'
    
     # withxtics 'memorystats' u 3:xtic(1) w boxes lc rgb  '#ff4d4d'
    
#     'memorystats' every 2::1 u 3:xtic(1) w boxes lc rgb  '#ff1d1d', \

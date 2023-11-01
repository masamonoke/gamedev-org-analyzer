lsof -n -i :12000 | grep LISTEN | kill $(awk '{split($0,a," "); print a[2]}')
lsof -n -i :3003 | grep LISTEN | kill $(awk '{split($0,a," "); print a[2]}')


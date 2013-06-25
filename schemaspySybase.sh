#!/bin/sh

host=`grep "MGD_DBURL=" ${MGICONFIG}/master.config.sh | cut -d"=" -f2 | sed "s/\"//g" | cut -d":" -f1 | cut -d"." -f1`
port=`grep "MGD_DBURL=" ${MGICONFIG}/master.config.sh | cut -d":" -f2 | sed "s/\"//g"`

#rm -rf ${DATALOADSOUTPUT}/mgi/schemaspy-$host
#mkdir ${DATALOADSOUTPUT}/mgi/schemaspy-$host

echo buildSybaseDocs $host $port ${MGD_DBNAME} ${MGD_DBSERVER} ${DATALOADSOUTPUT}/mgi/schemaspy-$host
./buildSybaseDocs $host $port ${MGD_DBSERVER} ${MGD_DBNAME} ${MGD_DBUSER} `cat ${MGD_DBPASSWORDFILE}` ${DATALOADSOUTPUT}/mgi/schemaspy-$host


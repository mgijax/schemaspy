#!/bin/sh

#
# Usage: makeNewSchema.sh  Server  Build_Directory
#
# where
#
#     Server = The name of the Postgres server that has a copy of the pub
#              database that the schema should be generated from.
#              (e.g. mgi-pubfedb1 or mgi-pubfedb2)
#
#     Build_Directory = The name of the directory that should be created
#                       under /usr/local/mgi/live/schemaSpy and used to
#                       build the new version of schemaSpy. For example,
#                       mgd_N.NN, if the new version is associated with a
#                       release number.
#
# Example:
#
#    makeNewSchema.sh  mgi-pubfedb1  mgd_5.20
#
# Assumptions:
#
#    This script assumes that the specified Postgres server has a database
#    named "pub" with a schema named "mgd". The public version of schemaSpy
#    expects the mgd schema, so the intent is to run this script against
#    one of the public Postgres servers that has a "pub" database with a
#    "mgd" schema.
#

cd `dirname $0`

if [ $# -ne 2 ]
then
    echo "Usage: $0  Server  Build_Directory"
    exit 1
fi

SERVER_NAME=$1
BUILD_DIR=$2

LOG=`pwd`/`basename $0`.log
rm -f ${LOG}
touch ${LOG}

# Define the path to the schemaSpy directory.
SCHEMA_SPY_DIR=/usr/local/mgi/live/schemaSpy

# Define the full path to the new build directory.
BUILD_PATH=${SCHEMA_SPY_DIR}/${BUILD_DIR}

# The schemaspy product expect DB_TYPE to be set.
DB_TYPE=postgres
export DB_TYPE

# Set the library path.
LD_LIBRARY_PATH=/usr/local/lib:/usr/local/pgsql/lib
export LD_LIBRARY_PATH

date | tee -a ${LOG}
echo "Verify path settings" | tee -a ${LOG}

#
# Make sure the schemaSpy directory exists.
#
if [ ! -d ${SCHEMA_SPY_DIR} ]
then
    echo "SchemaSpy directory is missing: ${SCHEMA_SPY_DIR}" | tee -a ${LOG}
    exit 1
fi

#
# Make sure the build directory does NOT already exist. We don't want to
# overwrite the live one by accident.
#
if [ -d ${BUILD_PATH} ]
then
    echo "Build directory already exists: ${BUILD_PATH}" | tee -a ${LOG}
    exit 1
fi

#
# Build the new schemaSpy version.
#
echo "Build new schemaSpy version: ${BUILD_PATH}" | tee -a ${LOG}
./buildDocs ${SERVER_NAME} pub mgd ${BUILD_PATH} >> ${LOG} 2>&1
if [ $? -ne 0 ]
then
    echo "Build failed" | tee -a ${LOG}
    exit 1
fi

#
# Activate new schemaSpy version.
#
echo "Activate new schemaSpy version" | tee -a ${LOG}
cd ${SCHEMA_SPY_DIR}
rm -f mgd
ln -s ${BUILD_DIR} mgd

echo "SchemaSpy successfully updated" | tee -a ${LOG}
date | tee -a ${LOG}

exit 0

#!/bin/sh
#
# makeNewSchema.sh
###########################################################################
#
# Purpose:
#
#     This script is a wrapper around the process that generates a visual
#     representation of a given schema a database.
#
# Usage:
#
#     makeNewSchema.sh DB_Server DB_Name DB_Schema Build_Directory
#
#     where
#
#         DB_Server = The name of the Postgres server that contains the
#                     source database/schema.
#
#                     For example: mgi-pubfedb1 or mgi-pubfedb2
#
#         DB_Name = The name of the source database.
#
#                   For example: pub or fe
#
#         DB_Schema = The name of the source schema. This is also the name
#                     of the sym link that will be created to point to the
#                     new build directory.
#
#                     For example: radar, mgd, snp or fe
#
#         Build_Directory = The name of the directory that should be
#                           created under /usr/local/mgi/live/schemaSpy and
#                           used to build the new version of schemaSpy for
#                           the given schema. For example, mgd_N.NN, if the
#                           new version is associated with a release number.
#
# Example:
#
#    makeNewSchema.sh  mgi-pubfedb1 pub mgd mgd_6.05
#
#    This will create a new /usr/local/mgi/live/schemaSpy/mgd_6.05 directory
#    for the mgi-pubfedb1.pub.mgd schema. Then it will create a sym link
#    named "mgd" that points to this directory.
#
###########################################################################

cd `dirname $0`

if [ $# -ne 4 ]
then
    echo "Usage: $0 DB_Server DB_Name DB_Schema Build_Directory"
    exit 1
fi

DB_SERVER=$1
DB_NAME=$2
DB_SCHEMA=$3
BUILD_DIR=$4

LOG=`pwd`/`basename $0`.log
rm -f ${LOG}
touch ${LOG}

# Define the path to the schemaSpy directory.
SCHEMA_SPY_DIR=/usr/local/mgi/live/schemaSpy

# Define the full path to the new build directory.
BUILD_PATH=${SCHEMA_SPY_DIR}/${BUILD_DIR}

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
./buildDocs ${DB_SERVER} ${DB_NAME} ${DB_SCHEMA} ${BUILD_PATH} >> ${LOG} 2>&1
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
rm -f ${DB_SCHEMA}
ln -s ${BUILD_DIR} ${DB_SCHEMA}

echo "SchemaSpy successfully updated" | tee -a ${LOG}
date | tee -a ${LOG}

exit 0

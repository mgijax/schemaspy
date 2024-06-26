#!/opt/python3.8/bin/python3

# Name: schemaSpyCleanup.py
# Purpose: to make MGI-specific customizations to the output HTML files
#       generated by schemaSpy.
# Notes: schemaSpy is a schema documentation generator hosted on SourceForge
#       and released under the lesser GPL license.  Since we are only altering
#       its output, rather than the source code itself, we will hopefully be
#       okay license-wise.

import os
import re
import sys
import getopt
import runCommand
import dbManager

dbm = None                      # to be dbManager.postgresManager object

USAGE='''Usage: %s [-a|-d|-i] <target file> <server> <database> <user> <password>
    Purpose:
        to make a few alterations to an HTML file generated by schemaSpy.
        Where possible, we always:
          * improve the Indexes section for tables
          * add MGI branding
    Options:
        -a : remove the "Anomalies" tab from the top of the page
        -d : remove the "Donate" tab from the top of the page
        -i : note that the file has no Index information, so do not give an
                error when none is found in the database
    Required Parameters:
        target file : the HTML file to edit and replace
''' % sys.argv[0]

###--- globals ---###

BRANDING = '''
<TABLE WIDTH="100%" BORDER=0 CELLPADDING=0 CELLSPACING=0>
 <TR>
  <TD WIDTH="100%">
   <TABLE WIDTH="100%" BORDER=0 CELLPADDING=0 CELLSPACING=0>
    <TR>
     <TD WIDTH="20%" VALIGN="center" ALIGN="left">
      <A HREF="http://www.informatics.jax.org/" border=0><IMG SRC="http://www.informatics.jax.org/webshare/images/mgi_logo.jpg" BORDER=0 HEIGHT="70" WIDTH="160" ALT="Mouse Genome Informatics"></A>

     </TD>
     <TD WIDTH="60%" ALIGN="center" VALIGN="center" BGCOLOR="#ffffff">
      <FONT COLOR="#000000" SIZE=5 FACE="Arial,Helvetica">
       Schema Browser
      </FONT>
     </TD>
     <TD WIDTH="20%" VALIGN="center" ALIGN="center" BGCOLOR="#ffffff">
      &nbsp;
     </TD>

    </TR>
    <TR>
     <TD COLSPAN=3 style="background-color:#0000ff;">
      <FONT face="Arial,Helvetica" color="#ffffff">
       <B>&nbsp;Mouse Genome Informatics</B>
      </FONT>
     </TD>
    </TR>

    <TR>
     <TD>
      <FONT SIZE=-1 FACE="Arial,Helvetica">
       <CENTER>
        <A HREF="http://www.informatics.jax.org/" vlink="#0000ff">MGI Home</A>&nbsp;&nbsp;&nbsp;
        <a href="http://www.informatics.jax.org/mgihome/help/help.shtml" vlink="#0000ff">Help</A>
       </CENTER>
      </FONT>

     </TD>
    </TR>
   </TABLE>
  </TD>
 </TR>
 <TR><TD>&nbsp;</TD></TR>
</TABLE>
'''

HOST = None
DATABASE = None
SCHEMA = None
USER = None
PASSWORD = None
PATH = None
TABLE = None

STRIP_DONATE_TAB = False
STRIP_ANOMALIES_TAB = False
SKIP_INDEXES = False

###--- functions ---###

def bailout (message, showUsage = False):
        if showUsage:
                sys.stderr.write (USAGE)
        sys.stderr.write ('Error: %s\n' % message)
        sys.exit(1)

def processCommandLine():
        global HOST, DATABASE, USER, PASSWORD, PATH, TABLE, SCHEMA
        global STRIP_DONATE_TAB, STRIP_ANOMALIES_TAB, SKIP_INDEXES
        global dbm

        try:
                (options, args) = getopt.getopt (sys.argv[1:], 'adi')
        except:
                bailout ('Invalid command-line')

        for (option, value) in options:
                if option == '-a':
                        STRIP_ANOMALIES_TAB = True
                elif option == '-d':
                        STRIP_DONATE_TAB = True
                elif option == '-i':
                        SKIP_INDEXES = True
                else:
                        bailout ('Unknown flag: %s' % option)

        if len(args) < 6:
                bailout ('Too few parameters')
        elif len(args) > 6:
                bailout ('Too many parameters')

        PATH = args[0]
        TABLE = os.path.basename(PATH).replace('.html', '')

        HOST = args[1]
        DATABASE = args[2]
        SCHEMA = args[3]
        USER = args[4]
        PASSWORD = args[5]

        dbm = dbManager.postgresManager(HOST, DATABASE, USER, PASSWORD)
        dbm.setReturnAsMGI(True)
        return

def analyzeColumns (columns):
        columns = [x.strip() for x in columns.split(',')]
        columnsOnly = []
        directions = []

        for column in columns:
                items = column.split()
                if (len(items) == 2) and (items[1] == 'DESC'):
                    col = items[0]
                    direction = 'Desc'
                else:
                    col = column
                    direction = 'Asc'

                # trim data types from function-based
                # columns
                col = re.sub('::[^)]+', '', col)

                columnsOnly.append (col)
                directions.append (direction)
        return columnsOnly, directions

q = re.compile('\((.*)\)$')
def analyzeCreateIndexStatement (line):
        global q
        
        match = q.search(line.strip())
        if match:
                columnsOnly, directions = analyzeColumns(match.group(1))
                return columnsOnly, directions

        return None

def getIndexDataSQL():
        # try to get the index data using direct SQL (skip using psql, as it
        # was problematic)

        sqlFile = 'getIndexes.sql'
        fp = open(sqlFile, 'r')
        lines = fp.readlines()
        fp.close()
        lines = [x.rstrip() for x in lines]
        cmd = ' '.join(lines)
        cmd = cmd.replace('MY_TABLE_NAME', '%s' % TABLE)

        results = dbm.execute(cmd)

        indexes = []
        for line in results:
                attributes = []

                name = line['relname']
                isPrimary = line['indisprimary']
                isUnique = line['indisunique']
                isClustered = line['indisclustered']
                sql = line['indexSql'].lower()
                constraint = line['indexConstraint']

                print(line)
                print(isPrimary, isUnique, isClustered)
                out = analyzeCreateIndexStatement(sql)

                if not out:
                        continue
                columnsOnly, directions = out

                if isPrimary:
                        attributes.append ('Primary key')
                elif isUnique:
                        attributes.append ('Must be unique')
                else:
                        attributes.append ('Performance')

                if isClustered:
                        attributes.append ('Used to cluster data')

                indexes.append ( (name, attributes, columnsOnly, directions) )

        return indexes

def readFile():
        fp = open(PATH, 'r')
        lines = fp.readlines()
        fp.close()
        return lines

def cleanup(lines):
        indexes = getIndexDataSQL()

        cleanLines = []

        beforeBranding = 0      # before we've added MGI branding
        beforeIndexes = 1       # before we get to the Indexes section
        beforeRows = 2          # before we find the data rows for Indexes
        inRows = 3              # while we are in the data rows for Indexes
        afterIndexes = 4        # after we've done the Indexes section

        status = beforeBranding

        for line in lines:
                if STRIP_DONATE_TAB:
                        if line.find('>Donate<') >= 0:
                                if line.find('sourceforge') >= 0:
                                        # skip the Donate tab
                                        continue

                if STRIP_ANOMALIES_TAB:
                        if line.find('>Anomalies<') >= 0:
                                if line.find('anomalies.html') >= 0:
                                        # skip the Anomalies tab
                                        continue

                if status == beforeBranding:
                        if line.find('headerHolder') >= 0:
                                # add branding and begin looking for the
                                # Indexes section
                                cleanLines.append (BRANDING)
                                status = beforeIndexes

                elif status == beforeIndexes:
                        if line.find('>Indexes:<') >= 0:
                                # note that we've hit the start of the
                                # Indexes section
                                status = beforeRows

                elif status == beforeRows:
                        if line.find('<tbody>') >= 0:
                                # note that we have found the start of the
                                # data rows of the Indexes section
                                status = inRows

                elif status == inRows:
                        if line.find('</table>') >= 0:
                                status = afterIndexes

                                # add in our custom data rows for the Indexes
                                # table

                                for (name, attr, cols, dirs) in indexes:
                                        if 'Primary key' in attr:
                                                class1 = 'primaryKey'
                                        else:
                                                class1 = 'indexedColumn'

                                        cell3 = []
                                        for dir in dirs:
                                                if dir == 'Asc':
                                                        full = 'Ascending'
                                                else:
                                                        full = 'Descending'

                                                cell3.append ("<span title='%s'>%s</span>" % (full, dir))

                                        cleanLines.append (" <tr>\n")
                                        cleanLines.append ("  <td class='%s'>%s</td>\n" % (class1, ' + '.join (cols)) )
                                        cleanLines.append ("  <td class='detail'>%s</td>\n" % ', '.join (attr))
                                        cleanLines.append ("  <td class='detail' style='text-align:left;'>%s</td>\n" % '/'.join(cell3))
                                        cleanLines.append ("  <td class='constraint' style='text-align:left;'>%s</td>\n" % name)
                                        cleanLines.append (" </tr>")

                        else:
                                # skip all data rows for the Indexes table, as
                                # we are going to replace them
                                continue

                cleanLines.append (line)
        return cleanLines

def writeFile (lines):
        fp = open (PATH, 'w')
        for line in lines:
                fp.write(line)
        fp.close()
        return

def main():
        processCommandLine()
        lines = cleanup(readFile())
        writeFile (lines)
        return

###--- main program ---###

if __name__ == '__main__':
        main()

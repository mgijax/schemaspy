buildDocs is the wrapper script that runs schemaSpy to produce a directory
structure with output files.  It also does MGI-specific customizations to
those files by running a script to post-process those output files.

Currently, only gondor has a recent-enough version of GraphViz.  Until that
changes, you'll have to run it on gondor.

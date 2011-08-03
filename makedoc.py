#!/usr/bin/env python

import pydoc
import sys
import imp

if len(sys.argv) < 3 :
    print 'Command incorrect. Pls use this format:'
    print 'python makedoc.py FileNameToWriteTo Module'
else:
    fname = sys.argv[1]
    module = sys.argv[2]
    __import__(module)

    doc = pydoc.render_doc(module)
    fobj = open(fname, 'a')
    fobj.write(doc)
    fobj.close()
    print '%s has been updated with the docstrings from %s.' % (fname, module)

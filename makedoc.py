#!/usr/bin/env python
"""
makedocs : .py --> .rst

Autogenerate Sphinx RST source from Python source
=================================================

``makedocs.py`` takes a directory of Python modules and auto-generates
Sphinx reStructuredText source for them. I wrote it because none of the
tools that automatically generate API docs for Python modules suit me.
Pydoc has poor HTML output and epydoc's output is too complicated for my
simple projects. Sphinx's autodoc and viewdoc extensions are almost
perfect. But the problem with them is that you have to write the RST source
yourself. Of course you could do it in two lines... ::

.. autodoc:: my_module
:members:

But everything then gets listed in alphabetical order! I usually group
function, class, and data definitions together by purpose to help people to
understand the source. Also, sometimes there are a lot of definitions in a
module and they need section headings. The enormous documentation page for
matplotlib.pyplot_ is an example. A simple way to solve this is to list all
you classes, functions, data, etc., explicitly in the RST source, together
with section headings. This script does that for you automatically.

Installation
------------

To set up, run *sphinx-quickstart* as usual and opt for separate source and
build directories. Place ``makedocs.py`` in the Sphinx root directory,
which should also contain the ``Makefile``. The first time it runs it will
copy ``conf.py`` from the source directory into the root directory; keep
``conf.py`` there from then on, as ``makedocs.py`` will delete both the
build and source directories every time it is run.

Usage
-----

From the command line::

$ python makedocs.py --help
usage: makedocs.py [-h] [-d DOC_PATH] [-p TEXT] [-f FILENAME] [src_path]

*.py --> Sphinx *.rst

positional arguments:
src_path Path to Python source files

optional arguments:
-h, --help show this help message and exit
-d DOC_PATH, --doc-path DOC_PATH
Path to directory containg Sphinx Makefile and
conf.py
-p TEXT, --preamble-text TEXT
Preamble text for index.rst
-f FILENAME, --preamble-file FILENAME
Use FILENAME for preamble in index.rst

If you set ``SRC_PATH`` at the top level of ``makedocs.py``, no
command-line arguments are required. To run from the command-line requires
that argparse is installed (standard in Python 2.7+). If you don't have
it::

>>> import makedocs
>>> makedocs.make_docs(src_path, doc_path, preamble="")

How it works
------------

The script generates an RST file for each Python source file, e.g.
``my_module.py`` into ``my_module.rst``. The source files are read from
``SRC_PATH``, and the RST files are written into ``DOC_PATH/source``. Each
RST file has the header::

my_module
=========

.. currentmodule:: my_module
.. automodule:: my_module

And then searches through the python source, looking for the following

* Section titles. A section like this in the Python source::

#
# SECTION
#

becomes RST source::

SECTION
-------

There are also 2nd-level section titles, where::

##
## SUBSECTION
##

becomes::

SUBSECTION
~~~~~~~~~~

* Function definitions. ::

def FUNCTION_NAME(...):

becomes::

.. autofunction:: FUNCTION_NAME

* Class definitions.::

class CLASS_NAME(...):

becomes::

.. autoclass:: CLASS_NAME
:members:

* Module-level data.::

IDENTIFIER = ...

becomes::

.. autodata:: IDENTIFIER

This only happens if the IDENTIFIER line is preceded by a line beginning
with ``#:``, or followed by one beginning with ``\"\"\"``, so that
undocumented data is not included. Also, IDENTIFIERS beginning with an
underscore are ignored.

The above is done for ``SRC_PATH/*.py``.

It also generates an ``index.rst`` file, using the name of the last
directory on the ``SRC_PATH (DIR_NAME)`` as part of the title::

Welcome to DIR_NAME's documentation!
====================================

:Date: |today|

.. toctree::
:maxdepth: 3

module1
module2, etc.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

To control the order in which modules appear in the table of contents, set an
``__order__`` variable to a positive integer in the top level of each module.
The lower the integer, the higher in the table of contents. Modules without
``__order__`` are pushed to the bottom.

To add a preamble to the index, use the option (see Usage above).

Finally the script runs ``make html`` to build the documentation.

.. _matplotlib.pyplot: http://matplotlib.sourceforge.net/api/pyplot_api.html

"""
import re
import os
import sys
import glob
import shutil

## Optional section: configure a default SRC_PATH
#SRC_PATH = "..."

#
# Main functions
#


def make_docs(src_path, doc_path, preamble=""):
    """Turn *.py in src_path into *.rst in doc_path/source, and build
Sphinx docs.
"""
    original_path = os.getcwd()
    os.chdir(doc_path)

    try:
        shutil.copy(os.path.join("source", "conf.py"), os.getcwd())
    except IOError:
        assert os.path.exists(os.path.join(os.getcwd(), "conf.py"))

    try:
        shutil.rmtree("source")
        os.makedirs("source")
    except OSError:
        pass

    shutil.copy(os.path.join(os.getcwd(), "conf.py"), "source")

    mod_names = []
    mod_order = []
    max_order = 1000

    for src_fn in glob.glob(os.path.join(src_path, "*.py")):
        mod_name = os.path.basename(src_fn.replace(".py", ""))
        src_fo = open(src_fn, mode="r")
        srclines = src_fo.readlines()
        src_fo.close()

        identifier = r"[A-Za-z][A-Za-z0-9_]* ="
        module_data_re = re.compile(identifier)
# first_level_data_re = re.compile(INDENT + identifier)

        rst_fn = os.path.join("source", mod_name + ".rst")
        rstfo = open(rst_fn, mode="w")
        rstfo.write(mod_name + "\n")
        rstfo.write("=" * len(mod_name) + "\n\n")
        
        version = None
        order = None
        rstfo.write(":Date: |today|\n")
        for i in range(1, len(srclines) - 1):
            line = srclines[i]
            if line.startswith("__version__"):
                version = line.split("=")[1].strip("\n").strip()
                rstfo.write(":Version: " + version + "\n")
                continue
            if line.startswith("__order__"):
                order = int(line.split("=")[1].strip("\n").strip())
                mod_order.append(order)
                continue

        if not order:
            mod_order.append(max_order)
            max_order += 20

        rstfo.write(".. currentmodule:: " + mod_name + "\n")
        rstfo.write(".. automodule:: " + mod_name + "\n")
        
        for i in range(1, len(srclines) - 1):
            prev_line = srclines[i - 1]
            line = srclines[i]
            next_line = srclines[i + 1]

            for delim, underline in (("#", "-"), ("##", "~")):
                if (prev_line.startswith(delim)
                    and line.startswith(delim + " ")
                    and next_line.startswith(delim)):
                    heading = line.strip(delim).strip()
                    rstfo.write("\n" + heading + "\n")
                    rstfo.write(underline * len(heading) + "\n\n")

            m = module_data_re.match(line)
            if m:
                var_name = m.group(0).replace(" =", "")
                if (prev_line.startswith("#:")
                    or next_line.startswith('"""')):
                    rstfo.write(".. autodata:: " + var_name + "\n")

            if line.startswith("def "):
                func_name = line.strip("def").strip().split("(")[0]
# first_level_name = func_name
# first_level_type = "function"
                if not func_name.startswith("_"):
                    rstfo.write(".. autofunction:: " + func_name + "\n")

            if line.startswith("class "):
                cls_name = line.strip("class").strip().split("(")[0]
# first_level_name = cls_name
# level_type = "method"
                rstfo.write(".. autoclass:: " + cls_name + "\n")
                rstfo.write(" :members:\n")

# if line.startswith(INDENT + "def "):
# meth_name = line.strip(INDENT + "def").strip().split("(")[0]
# if not meth_name.startswith("_"):
# rstfo.write(".. auto" + first_level_type + ":: "
# + first_level_name + "." + meth_name + "\n")
#
# mi = first_level_data_re.match(line)
# if mi:
# var_name = mi.group(0).strip(INDENT).replace(" =", "")
# if (prev_line.startswith(INDENT + "#:")
# or next_line.startswith(INDENT + '"""')):
# rstfo.write(".. autoattribute:: " + first_level_name
# + "." + var_name + "\n")

        rstfo.close()
        mod_names.append(mod_name)

    msg = "Welcome to {DIR_NAME}'s documentation!".format(
            DIR_NAME=os.path.basename(src_path))
    if preamble:
        preamble = preamble + "\n\n"
    indexfo = open(os.path.join("source", "index.rst"), mode="w")
    indexfo.write(msg + "\n")
    indexfo.write("=" * len(msg) + "\n\n")
    indexfo.write(":Date: |today|\n\n")
    indexfo.write(preamble)
    indexfo.write(".. toctree::\n")
    indexfo.write(" :maxdepth: 3\n\n")
    modules = zip(mod_names, mod_order)
    modules.sort(key=lambda x: x[1])
    for name, order in modules:
        indexfo.write(" " + name + "\n")
    msg = "Indices and tables"
    indexfo.write("\n" + msg + "\n")
    indexfo.write("-" * len(msg) + "\n\n")
    indexfo.write("* :ref:`genindex`\n")
    indexfo.write("* :ref:`modindex`\n")
    indexfo.write("* :ref:`search`\n")
    indexfo.close()

    try:
        shutil.rmtree("build")
    except OSError:
        pass
    os.system("make html")
    os.chdir(original_path)


def produce_makedocs_doc():
    """Produce documentation for this script."""
    docfile = open("makedocs.rst", mode="w")
    import makedocs
    doclines = makedocs.__doc__.split("\n")
    doctext = "\n".join(doclines[2:])
    docfile.write(doctext)
    docfile.close()
    os.system("rst2html makedocs.rst makedocs.html")


def main():
    if "SRC_PATH" in globals():
        kwargs = {"nargs": "?", "default": SRC_PATH}
    else:
        kwargs = {}
    parser = ArgumentParser(description="*.py --> Sphinx *.rst")
    parser.add_argument("src_path", help="Path to Python source files",
                        **kwargs)
    parser.add_argument("-d", "--doc-path", nargs=1, default=[os.getcwd()],
                        help="Path to directory containg Sphinx "
                             "Makefile and conf.py")
    parser.add_argument("-p", "--preamble-text", nargs=1, metavar="TEXT",
                        help="Preamble text for index.rst")
    parser.add_argument("-f", "--preamble-file", nargs=1, metavar="FILENAME",
                        help="Use text file for the preamble in index.rst")
    args = parser.parse_args()
    if args.preamble_text:
        preamble = args.preamble_text[0]
    elif args.preamble_file:
        fo = open(args.preamble_file[0], mode="r")
        preamble = fo.read()
        fo.close()
    else:
        preamble = ""
    make_docs(args.src_path, args.doc_path[0], preamble=preamble)


if __name__ == "__main__":
    from argparse import ArgumentParser
    main()



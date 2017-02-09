kodi.remote-pdb
===============

**Note**: ``kodi.remote-pdb`` is no longer supported! If you need a remote Python debugger for
Kodi addons, check my `kodi.web-pdb <https://github.com/romanvm/kodi.web-pdb>`_ project.

``kodi.remote-pdb`` is a variant of `remote-pdb`_ Python package modified for using in `Kodi mediacenter`_.
It is a telnet interface for Python's built-in `PDB`_ debugger that can be used for remote debugging of
Python addons *in vivo*, that is, while running inside Kodi.
Except for modifications needed to run inside Kodi, all other ``remote-pdb`` functionality is left intact,
so you can use all available ``pdb``/``remote-pdb`` documentation and tutorials
to learn how to debug Python scripts using the ``PDB`` debug console.

Usage
-----

First you need to install ``script.module.remote-pdb`` addon in your Kodi instance where you want to debug your addon.
An installable ZIP can be downloaded from `Releases`_ tab of this repository.

Then include ``script.module.remote-pdb`` in your ``addon.xml`` as a dependency:

.. code-block:: xml

  <requires>
    ...
    <import addon="script.module.remote-pdb" version="1.2"/>
  </requires>

Put the following line into your addon code:

.. code-block:: python

  from remote_pdb import set_trace; set_trace(port=5555)

This line should be put at the place where you want to start your debugging, usually as early as possible.
You can change the ``port`` argument but it is better to select values higher than ``1024`` because
lower port values may be restricted by your OS for security reasons.
By default ``remote-pdb`` opens connection on ``localhost``. To allow remote connections
you need to set the ``host`` parameter to an empty string, for example:

.. code-block:: python

  from remote_pdb import set_trace; set_trace(host='', port=5555)

The ``set_trace`` call will pause your plugin and the ``remote-pdb`` debugger will wait for a telnet connection.
The ``script.module.remote-pdb`` will also display a notification in Kodi that includes a hostname and a port
to connect to for your information.
Type in the console ``telnet <Kodi hostname or IP-address> <port>``, for example::

  $telnet 192.168.1.16 5555

Note that hostname/IP and port values are separated by a space. The ``port`` value must be the same as
specified in ``set_trace`` call.
This will open the ``PDB`` debug console. Read `PDB`_ documentation to learn how to use the debugger.

After creating a telnet session by the initial ``set_trace`` call
you can use subsequent ``set_trace()`` calls (without arguments) as hardcoded breakpoints
to enter into the debugger repeatedly within the same telnet session.

**Warning**: when you finish your debugging don't forget to remove ``script.module.remote-pdb``
from addon dependencies and ``set_trace`` call(-s) from your code.

Telnet Client
-------------

On Linux a telnet client is included in most (if not all) distributions. To enable a telnet client on Windows
open **Control Panel** > **Programs and Features** > **Turn Windows features on or off**,
check **Telnet Client** and click **OK**. Alternatively, on Windows you can use `PuTTY`_ utility.
In ``PuTTY`` it's better to use "Raw" mode because in "Telnet" mode the first command always results
in syntax error, although all subsequent commands are executed normally.

License
-------

BSD license, see ``license.txt``.

.. _remote-pdb: https://github.com/ionelmc/python-remote-pdb
.. _Kodi mediacenter: https://kodi.tv
.. _PDB: https://docs.python.org/2/library/pdb.html
.. _PuTTY: http://www.putty.org
.. _Releases: https://github.com/romanvm/kodi.remote-pdb/releases

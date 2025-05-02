pem: Easy PEM file parsing
==========================

.. image:: https://secure.travis-ci.org/hynek/pem.png
   :target: https://secure.travis-ci.org/hynek/pem
   :alt: CI status

.. image:: https://codecov.io/github/hynek/pem/coverage.svg?branch=master
   :target: https://codecov.io/github/hynek/pem?branch=master
   :alt: Coverage

.. teaser-begin

``pem`` is an MIT_-licensed Python module for parsing and splitting of `PEM files`_, i.e. Base64 encoded DER keys and certificates.

It runs on Python 2.7, 3.4, and PyPy 2.0+, has no dependencies and does not attempt to interpret the certificate data in any way.
``pem`` is intended to ease the handling of PEM files in combination with PyOpenSSL_ and – by extension – Twisted_.

It’s born from the need to load keys, certificates, trust chains, and DH parameters from various certificate deployments: some servers (like Apache_) expect them to be a separate file while others (like nginx_) expect them concatenated to the server certificate.
To be able to cope with both scenarios in Python, ``pem`` was born:

.. code-block:: pycon

   >>> import pem
   >>> certs = pem.parse_file("chain.pem")
   >>> certs
   [<Certificate(PEM string with SHA-1 digest '...')>, <Certificate(PEM string with SHA-1 digest '...')>]
   >>> str(certs[0])
   '-----BEGIN CERTIFICATE-----\n...'

Additionally to the vanilla parsing code, ``pem`` also contains helpers for Twisted that save a lot of boilerplate code.

``pem``\ ’s documentation lives at `Read the Docs <https://pem.readthedocs.org/>`_, the code on `GitHub <https://github.com/hynek/pem>`_.


.. _MIT: http://choosealicense.com/licenses/mit/
.. _`PEM files`: https://en.wikipedia.org/wiki/X.509#Certificate_filename_extensions
.. _Apache: https://httpd.apache.org
.. _nginx: http://nginx.org/en/
.. _PyOpenSSL: http://www.pyopenssl.org/
.. _Twisted: https://twistedmatrix.com/documents/current/api/twisted.internet.ssl.Certificate.html#loadPEM


Release Information
===================

16.1.0 (2016-04-08)
-------------------

Deprecations:
^^^^^^^^^^^^^

- Passing ``dhParameters`` to ``pem.twisted.certifateOptionsFromPEMs`` and ``certificateOptionsFromFiles`` is now deprecated;
  instead, include the DH parameters in the PEM objects or files.

Backward-incompatible changes:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Python 3.3 and 2.6 aren't supported anymore.
  They may work by chance but any effort to keep them working has ceased.

  The last Python 2.6 release was on October 29, 2013 and isn't supported by the CPython core team anymore.
  Major Python packages like Django and Twisted dropped Python 2.6 a while ago already.

  Python 3.3 never had a significant user base and wasn't part of any distribution's LTS release.

Changes:
^^^^^^^^

- ``pem.twisted.certificateOptionsFromPEMs`` and ``certificateOptionsFromFiles`` will now load Ephemeral Diffie-Hellman parameters if found.
  [`21 <https://github.com/hynek/pem/pull/21>`_]
- PEM objects now correctly handle being constructed with unicode and bytes on both Python 2 and 3.
  [`24 <https://github.com/hynek/pem/pull/24>`_]
- PEM objects now have an ``as_bytes`` method that returns the PEM-encoded content as bytes, always.
  [`24 <https://github.com/hynek/pem/pull/24>`_]
- PEM objects are now hashable and comparable for equality.
  [`25 <https://github.com/hynek/pem/pull/25>`_]

`Full changelog <https://pem.readthedocs.org/en/stable/changelog.html>`_.

Credits
=======

``pem`` is written and maintained by Hynek Schlawack.

The development is kindly supported by `Variomedia AG <https://www.variomedia.de/>`_.

A full list of contributors can be found on GitHub’s `overview <https://github.com/hynek/pem/graphs/contributors>`_.



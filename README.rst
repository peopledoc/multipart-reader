================
Multipart Reader
================

.. image:: https://travis-ci.org/novafloss/multipart-reader.svg
   :target: https://travis-ci.org/novafloss/multipart-reader
   :alt: We are under CI!!


Permits to read a multipart content like, mixed, related, etc.

Thanks to the *aiohttp* project for the implementation, cf.:
http://aiohttp.readthedocs.org/en/stable/multipart.html. Unfortunately lot of
people have not yet moved to asyncio, or do not want the full *aiohttp* stack
to read the multipart content. 

Here we tried to keep all the *aiohttp* logic and coverage but the coroutines
mechanism.


What it does
============

It reads the same way multpart/x contents. Lets say we have the following
*multipart/related* content::

    >>> import json

    >>> from email.mime.multipart import MIMEMultipart
    >>> from email.mime.base import MIMEBase

    >>> multipart = MIMEMultipart('related')

    >>> part = MIMEBase('application', 'json')
    >>> part.set_payload(json.dumps({'foo': 'bar'}))
    >>> multipart.attach(part)

    >>> part = MIMEBase('application', 'octet-stream')
    >>> part.set_payload(b"Python will save the world. I don't know how. But it will.")
    >>> part.add_header('Content-Disposition', 'attachment', filename='python-save-the-world.txt')
    >>> multipart.attach(part)

Here is how we can read it::

    >>> import io

    >>> from multipart_reader import MultipartReader

    >>> content = multipart.as_string().split('\n\n', 1)[1]
    >>> headers = dict(multipart.items())

    >>> stream = io.BytesIO()
    >>> stream.write(content)
    >>> stream.seek(0)

    >>> reader = MultipartReader(headers, stream)

    >>> json_part = reader.next()
    >>> json_part.json()
    {'foo': 'bar'}

    >>> file_part = reader.next()
    >>> file_part.read()
    "Python will save the world. I don't know how. But it will."

    >>> file_part.filename
    'python-save-the-world.txt'

That's it ...

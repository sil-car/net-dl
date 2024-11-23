.. net-dl documentation master file, created by
   sphinx-quickstart on Sat Nov 23 08:58:34 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

net-dl documentation
====================

.. autoapimodule:: net_dl
   :no-index:

CLI Usage
---------

::

   ~$ # print content to stdout if text/html/json/xml
   ~$ net-dl 'https://httpbin.org/json'
   {
      "slideshow": {
         "author": "Yours Truly", 
         "date": "date of publication", 
         "slides": [
            {
            "title": "Wake up to WonderWidgets!", 
            "type": "all"
            }, 
            {
            "items": [
               "Why <em>WonderWidgets</em> are great", 
               "Who <em>buys</em> WonderWidgets"
            ], 
            "title": "Overview", 
            "type": "all"
            }
         ], 
         "title": "Sample Slide Show"
      }
   }
   ~$ # save content to disk if file
   ~$ net-dl 'https://httpbin.org/image/svg'
   [...................................                                     ]  50%
   ~$

Python module usage
-------------------

>>> import net_dl
>>> url = 'https://httpbin.org/image/svg'
>>> dl = net_dl.Download(url)
>>> dl.get()
 [........................................................................] 100%
0
>>> import logging
>>> l = logging.get_logger()
>>> l.setLevel(logging.INFO)
>>> dl.get()
INFO:root:File already exists: /home/nate/g/net-dl/svg
0
>>>

The ``Download`` class
----------------------

.. autoapiclass:: net_dl.Download
   :members: get,get_file,get_text
   :no-index:

.. toctree::
   :maxdepth: 4
   :hidden:
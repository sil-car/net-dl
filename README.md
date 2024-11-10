# net-get

Download web pages and files from the internet. Can be used as a standalone
CLI command, or as a python module.

## Installation

```
python3 -m pip install pipx
# TODO: Update this to a release link.
pipx install https://gitlab.com/n8marti/net-get/-/archive/master/net-get-master.zip
```

## Usage

### CLI command
```
~$ # print content to stdout if text/html/json/xml
~$ net-get 'https://httpbin.org/json'
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
~$ net-get 'https://httpbin.org/image/svg'
 [...................................                                     ]  50%
```

### Python module

```python
>>> import net_get
>>> url = 'https://httpbin.org/image/svg'
>>> dl = net_get.Download(url)
>>> dl.get()
 [........................................................................] 100%
0
>>> import logging
>>> l = logging.get_logger()
>>> l.setLevel(logging.INFO)
>>> dl.get()
INFO:root:File already exists: /home/nate/g/net-get/svg
0
>>>
```

# TODO list

## Test and Deploy

Use the built-in continuous integration in GitLab.

- [ ] [Get started with GitLab CI/CD](https://docs.gitlab.com/ee/ci/quick_start/index.html)
- [ ] [Set up protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html)

***

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

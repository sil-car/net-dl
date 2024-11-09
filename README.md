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
~$ net-get 'https://ip.me'
2024-11-09 12:09:00 INFO: File size on server [B]: 14
2024-11-09 12:09:00 INFO: Starting new download from: https://ip.me.
2024-11-09 12:09:00 INFO: 14 B needed; 80052760576 B available
 [..................................................................] 100.0%
2024-11-09 12:09:02 INFO: File saved as: /home/user/net_get-20241109T120900
# TODO: Also show example with link to actual file.
```

### Python module

TODO

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

## Draobpilc
GPaste GUI  
v0.3 beta

## Requirements
* Python 3
* GTK 3.16+
* GPaste 3.18+
* On Ubuntu: gir1.2-gpaste-X.0 (e.g. gir1.2-gpaste-4.0 or gir1.2-gpaste-6.0)
* OPTIONAL: GtkSourceView3

## Installation
> pip3 install \<path to draobpilc root dir\>  

or

> pip3 install git+https://github.com/awamper/draobpilc

Optionally install .desktop file
> draobpilc --install-desktop-file

## Uninstall
if you have .desktop file installed firstly remove it
> draobpilc --uninstall-desktop-file

Then uninstall the app
> pip3 uninstall draobpilc

## Screenshots
![Draobpilc](/screenshots/1.png)

## Troubleshooting

### Command not found after install

If `pip3 install` runs without any errors but running `draobpilc` gives `Command not found` error check that `~/.local/bin` is included to your path:
```bash
export PATH=$PATH:~/.local/bin
```

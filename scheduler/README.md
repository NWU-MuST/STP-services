Grid Engine:

https://scidom.wordpress.com/2012/01/18/sge-on-single-pc/

http://www.socher.org/index.php/Main/HowToInstallSunGridEngineOnUbuntu



Fonts:

http://webappl.blogspot.co.za/2011/05/install-sun-grid-engine-sge-on-ubuntu.html

```apt-get install xfs
service xfs start
apt-get install xfonts-75dpi
xset +fp /usr/share/fonts/X11/75dpi
xset fp rehash```

apt-get install python-drmaa gridengine-drmaa-dev gridengine-drmaa1.0

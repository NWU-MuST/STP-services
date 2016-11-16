Fix path.sh and cmds.sh:
-----------------------

Edit Kaldi paths information

Create symbolic links to utils and steps:
----------------------------------------
$ ln -s /home/dac/tools/kaldi-trunk/egs/wsj/s5/steps
$ ln -s /home/dac/tools/kaldi-trunk/egs/wsj/s5/utils

Example:
-------

$ bash speech2text.sh --mfcc-config /home/dac/platform/backend/speech2text/systems/parly/conf/mfcc.conf --source-dir /home/dac/platform/backend/speech2text/systems/parly/exp/ --graph-dir /home/dac/platform/backend/speech2text/systems/parly/exp/tri3b/graphs/ --format-ctm true /home/dac/storage/ntkleynhans/20150722/A_ELLIS_0001.wav /home/dac/storage/ntkleynhans/20150731/Wed_Jul_22_2015_15_05_39_GMT+0200__SAST_.html 


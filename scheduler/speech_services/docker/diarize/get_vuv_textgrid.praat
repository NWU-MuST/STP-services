form calculate vuv TextGrid
  text audio_file ./test.wav
  text out_textgrid ./test.TextGrid
endform

Read from file... 'audio_file$'
Rename... Sound
sound = selected ("Sound")

To PointProcess (periodic, cc)... 75 600
To TextGrid (vuv)... 0.02 0.01
Save as text file... 'out_textgrid$'


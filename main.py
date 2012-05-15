import sys

import numpy as np
from PySide import QtCore, QtGui, QtMultimedia

from visualizer import *

app = QtGui.QApplication(sys.argv)

info = QtMultimedia.QAudioDeviceInfo.defaultInputDevice()
format = info.preferredFormat()
format.setChannels(CHANNEL_COUNT)
format.setChannelCount(CHANNEL_COUNT)
format.setSampleSize(SAMPLE_SIZE)
format.setSampleRate(SAMPLE_RATE)

if not info.isFormatSupported(format):
    print 'Format not supported, using nearest available'
    format = nearestFormat(format)
    if format.sampleSize != SAMPLE_SIZE:
        #this is important, since effects assume this sample size.
        raise RuntimeError('16-bit sample size not supported!')

audio_input = QtMultimedia.QAudioInput(format, app)
audio_input.setBufferSize(BUFFER_SIZE)
source = audio_input.start()

def read_data():
    data = np.fromstring(source.readAll(), 'int16').astype(float)
    if len(data):
        return data
    return None

window = LineVisualizer(read_data)
window.show()
app.exec_()
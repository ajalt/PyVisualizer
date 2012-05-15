"""Module that contains visualizer classes."""

import sys
import random

import numpy as np
from PySide import QtCore, QtGui, QtMultimedia

SAMPLE_MAX = 32767
SAMPLE_MIN = -(SAMPLE_MAX + 1)
SAMPLE_RATE = 44100 # [Hz]
NYQUIST = SAMPLE_RATE / 2
SAMPLE_SIZE = 16 # [bit]
CHANNEL_COUNT = 1
BUFFER_SIZE = 5000 


class Visualizer(QtGui.QLabel):
    """The base class for visualizers.
    
    When initializing a visualizer, you must provide a get_data function which
    takes no arguments and returns a NumPy array of PCM samples that will be
    called exactly once each time a frame is drawn.
    
    Note: Although this is an abstract class, it cannot have a metaclass of
    abcmeta since it is a child of QObject.
    """
    def __init__(self, get_data, update_interval=33):
        super(Visualizer, self).__init__()
        
        self.get_data = get_data
        self.update_interval = update_interval #33ms ~= 30 fps
        self.sizeHint = lambda: QtCore.QSize(400, 400)
        self.setStyleSheet('background-color: black;');
        
    def show(self):
        """Show the label and begin updating the visualization."""
        super(Visualizer, self).show()
        self.generate()
        
    def generate(self):
        """This is the abstract function that child classes will override to
        draw a frame of the visualization."""
        raise NotImplementedError()
    
    
class LineVisualizer(Visualizer):
    """This visualizer will display equally sized rectangles
    alternating between black and another color, with the height of the
    rectangles determined by frequency, and the quantity of colored rectanges
    influnced by amplitude.
    """

    def __init__(self, get_data, columns=1):
        super(LineVisualizer, self).__init__(get_data)
        
        self.columns = columns
        self.brushes = [QtGui.QBrush(QtGui.QColor(255, 255, 255)), #white
                        QtGui.QBrush(QtGui.QColor(255, 0, 0)),     #red
                        QtGui.QBrush(QtGui.QColor(0, 240, 0)),     #green
                        QtGui.QBrush(QtGui.QColor(0, 0, 255)),     #blue
                        QtGui.QBrush(QtGui.QColor(255, 255, 0)),   #yellow
                        QtGui.QBrush(QtGui.QColor(0, 255, 255)),   #teal
                        ]
        self.brush = self.brushes[0]
        
        self.display_odds = True
        self.display_evens = True
        self.is_fullscreen = False
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_I:
            self.display_evens = True
            self.display_odds = True
        elif event.key() == QtCore.Qt.Key_O:
            self.display_evens = True
            self.display_odds = False
        elif event.key() == QtCore.Qt.Key_P:
            self.display_evens = False
            self.display_odds = True
            return
        elif event.key() == QtCore.Qt.Key_Escape:
            if self.is_fullscreen:
                self.showNormal()
                self.is_fullscreen = False
            else:
                self.showFullScreen()
                self.is_fullscreen = True
        else:
            #Qt.Key enum helpfully defines most keys as their ASCII code,
            #   so we can use ord('Q') instead of Qt.Key.Key_Q
            color_bindings = dict(zip((ord(i) for i in 'QWERTYU'), self.brushes))
            try:
                self.brush = color_bindings[event.key()]
            except KeyError:
                if QtCore.Qt.Key_0 == event.key():
                    self.columns = 10
                elif QtCore.Qt.Key_1 <= event.key() <= QtCore.Qt.Key_9:
                    self.columns = event.key() - QtCore.Qt.Key_1 + 1
            
    def generate(self):
        data = self.get_data()
        if data is not None:
            fft = np.absolute(np.fft.rfft(data, n=len(data)))
            freq = np.fft.fftfreq(len(fft), d=1./SAMPLE_RATE)
            max_freq = abs(freq[fft == np.amax(fft)][0]) / 2
            max_amplitude = np.amax(data)
            
            rect_width = int(self.width() / (self.columns * 2))
            
            freq_cap = 10000. #this determines the scale of lines
            if max_freq >= freq_cap:
                rect_height = self.height()
            else:
                rect_height = int(self.height() * max_freq / freq_cap)

            
            img = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_RGB32)
            img.fill(0) #black
            
            if rect_height >= 1:
                painter = QtGui.QPainter(img)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(self.brush) 
                
                for x in xrange(0, self.width() - rect_width, rect_width * 2):
                    for y in xrange(0, self.height(), 2 * rect_height):
                        if random.randint(0, int(max_amplitude / float(SAMPLE_MAX) * 10)):
                            if self.display_evens:
                                painter.drawRect(x, y, rect_width, rect_height)
                            if self.display_odds:
                                painter.drawRect(x + rect_width, self.height() - y - rect_height, rect_width, rect_height)
                
                del painter #
                
            self.setPixmap(QtGui.QPixmap.fromImage(img))
        if self.isVisible():
            QtCore.QTimer.singleShot(self.update_interval, self.generate)

class Spectrogram(Visualizer):
    def generate(self):
        data = self.get_data()
        
        if data is not None:
            fft = np.absolute(np.fft.rfft(data, n=len(data)))
            freq = np.fft.fftfreq(len(fft), d=1./SAMPLE_RATE)
            max_freq = abs(freq[fft == np.amax(fft)][0]) / 2
            max_amplitude = np.amax(data)
            
            bins = np.zeros(200)
            #indices = (len(fft) - np.logspace(0, np.log10(len(fft)), len(bins), endpoint=False).astype(int))[::-1]
            #for i in xrange(len(bins) - 1):
            #    bins[i] = np.mean(fft[indices[i]:indices[i+1]]).astype(int)
            #bins[-1] = np.mean(fft[indices[-1]:]).astype(int)
            
            step = int(len(fft) / len(bins))
            for i in xrange(len(bins)):
                bins[i] = np.mean(fft[i:i+step])
                
            img = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_RGB32)
            img.fill(0)
            painter = QtGui.QPainter(img)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255))) #white)
            
            for i, bin in enumerate(bins):
                height = self.height() * bin / float(SAMPLE_MAX) / 10
                width = self.width() / float(len(bins))
                painter.drawRect(i * width, self.height() - height, width, height)
                
            del painter
            
            self.setPixmap(QtGui.QPixmap.fromImage(img))
        if self.isVisible():
            QtCore.QTimer.singleShot(self.update_interval, self.generate)
        
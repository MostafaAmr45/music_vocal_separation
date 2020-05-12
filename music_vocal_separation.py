import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import tkinter
import tkinter.filedialog
import os
from pydub import AudioSegment
from pydub.playback import play

#############################################
# Load an example with vocals.
root = tkinter.Tk()
root.withdraw()  # use to hide tkinter window

myAudioFile = tkinter.filedialog.askopenfilename()

y, sr = librosa.load(myAudioFile, duration=60)

# read in audio file and get the two mono tracks
sound_stereo = AudioSegment.from_file(myAudioFile, format="mp3")
sound_monoL = sound_stereo.split_to_mono()[0]
sound_monoR = sound_stereo.split_to_mono()[1]

# And compute the spectrogram magnitude and phase
S_full, phase = librosa.magphase(librosa.stft(y))

#######################################
# Invert phase of the Right audio file
sound_monoR_inv = sound_monoR.invert_phase()

# Merge two L and R_inv files, this cancels out the centers
sound_CentersOut = sound_monoL.overlay(sound_monoR_inv)

#######################################
# We'll compare frames using cosine similarity, and aggregate similar frames
# by taking their (per-frequency) median value.
S_filter = librosa.decompose.nn_filter(S_full,
                                       aggregate=np.median,
                                       metric='cosine',
                                       width=int(librosa.time_to_frames(2, sr=sr)))

# The output of the filter shouldn't be greater than the input
S_filter = np.minimum(S_full, S_filter)

##############################################
# The raw filter output can be used as a mask,
# but it sounds better if we use soft-masking.
margin_i, margin_v = 2, 10
power = 2

mask_i = librosa.util.softmask(S_filter,
                               margin_i * (S_full - S_filter),
                               power=power)

mask_v = librosa.util.softmask(S_full - S_filter,
                               margin_v * S_filter,
                               power=power)

# Once we have the masks, simply multiply them with the input spectrum
# to separate the components

S_foreground = mask_v * S_full
S_background = mask_i * S_full

# multiply the magnitude component with phase to restore the wav files
# of the vocals and music

D_foreground = S_foreground * phase
D_background = S_background * phase

y_foreground = librosa.istft(D_foreground)
y_background = librosa.istft(D_background)

# export vocals audio file
librosa.output.write_wav('vocals.wav', (y_foreground * 5), sr)

# export music audio file
# the format is mp3 to reduce the size
sound_CentersOut.export('music.mp3', format="mp3")

##########################################
# Plot waveforms
plt.figure(figsize=(12, 8))
plt.subplot(3, 1, 1)
librosa.display.waveplot(y, sr=sr, color='r')
plt.title('mix')

plt.subplot(3, 1, 2)
librosa.display.waveplot(y_background, sr=sr)
plt.title('music')

plt.subplot(3, 1, 3)
librosa.display.waveplot(y_foreground, sr=sr)
plt.title('vocal')
plt.tight_layout()
plt.show()
import wave
import matplotlib.pyplot as plt
import numpy as np

obj = wave.open("../../assets/sounds/Effects/Explosions/Explosion_Large_Blast_1__6s.wav", "rb")

sample_frequency = obj.getframerate()
number_of_samples = obj.getnframes()
signal_wave = obj.readframes(-1)

obj.close()
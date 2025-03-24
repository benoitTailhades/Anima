import wave
import assets

obj = wave.open("../../assets/sounds/Effects/Explosions/Explosion_Large_Blast_1__6s.wav", "rb")
print("Number of channels", obj.getnchannels())
print("Sample width", obj.getsampwidth())
print("Frame rate", obj.getframerate())
print("Number of frames", obj.getnframes())
print("parameter", obj.getparams())

t_audio = obj.getnframes() / obj.getframerate()
print("t_audio", t_audio)

frames = obj.readframes(-1)
print(type(frames), type(frames[0]))
print(len(frames) / 4)

obj.close()

# obj_new = wave.open("../assets/sounds/Effects/Explosions/Explosion_Large_Blast_1__6s_new.wav","wb")
#
# obj_new.setnchannels(2)
# obj_new.setsampwidth(2)
# obj_new.setframerate(44100)
#
# obj_new.writeframes(frames)
#
# obj_new.close()

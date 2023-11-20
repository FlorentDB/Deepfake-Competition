from pydub import AudioSegment
import numpy as np
# Step 2: Load the .mpga file
mpga_file = AudioSegment.from_file("dataset/macron_audio_1.mpga")

# Step 3: Convert the .mpga file to .wav
mpga_file.export("dataset/macron_audio_1.wav", format="wav")

# Step 4: Crop the .wav file
# Let's say we want to create little samples of 10 seconds
wav_file = AudioSegment.from_wav("dataset/macron_audio_1.wav")
sound_file_Value = np.array(wav_file.get_array_of_samples())


# Calculate the duration of the wav_file in milliseconds
duration = int(wav_file.duration_seconds * 1000)

# Define the length of each sample in milliseconds
sample_length = 10000

# Create a loop that iterates over the duration of the wav_file
for i in range(0, duration, sample_length):
    # Slice the wav_file from i to i + sample_length
    sample = wav_file[i:i+sample_length]
    # Export the sample to a .wav file
    sample.export("dataset/" + str(i) + "-" + str(i+sample_length) +".wav", format="wav")
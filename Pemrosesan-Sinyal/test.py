import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter, freqz
from scipy.io import wavfile
import sounddevice as sd
import os

# --- Parameters ---
SAMPLING_RATE = 44100    # Hz, standar untuk kualitas audio yang baik
RECORD_DURATION = 10     # detik
NOISE_AMPLITUDE = 0.05   # Sesuaikan tingkat noise (0.0 s.d 1.0)

# Filter FIR Parameters (Low-Pass)
CUTOFF_FREQ_LPF = 3500   # Hz, cutoff untuk menghilangkan noise frekuensi tinggi
FILTER_ORDER_LPF = 100   # Orde filter, N
NUM_TAPS_LPF = FILTER_ORDER_LPF + 1

# --- File Names ---
ORIGINAL_AUDIO_FILE = "original_audio.wav"
NOISY_AUDIO_FILE    = "noisy_audio.wav"
FILTERED_AUDIO_FILE = "filtered_audio.wav"

def record_audio(filename, duration, fs, channels=1):
    """Merekam audio dan menyimpannya ke file."""
    print(f"Mulai merekam selama {duration} detik...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='float32')
    sd.wait()
    # Konversi ke int16 dan simpan
    wavfile.write(filename, fs, (recording * np.iinfo(np.int16).max).astype(np.int16))
    print(f"Audio disimpan sebagai {filename}")
    return recording.flatten(), fs

def add_noise_to_audio(input_filename, output_filename, noise_amplitude):
    """Membaca file audio, menambahkan noise, dan menyimpannya."""
    fs, audio_data_int = wavfile.read(input_filename)
    # Normalisasi ke float [-1,1]
    audio_float = audio_data_int.astype(np.float32) / np.iinfo(np.int16).max
    # Tambahkan noise Gaussian
    noise = noise_amplitude * np.random.normal(0, 1, len(audio_float))
    noisy = np.clip(audio_float + noise, -1.0, 1.0)
    # Simpan noisy ke int16
    wavfile.write(output_filename, fs, (noisy * np.iinfo(np.int16).max).astype(np.int16))
    print(f"Audio dengan noise disimpan sebagai {output_filename}")
    return noisy, fs

def design_fir_lowpass_filter(numtaps, cutoff_hz, fs):
    """Mendesain koefisien filter FIR Low-Pass menggunakan Hamming window."""
    nyq = fs / 2.0
    norm_cutoff = cutoff_hz / nyq
    return firwin(numtaps, norm_cutoff, window='hamming')

def apply_filter(audio_data, fir_coeff):
    """Menerapkan filter FIR ke data audio."""
    return lfilter(fir_coeff, 1.0, audio_data)

def main():
    # 1. Rekam audio (jika belum ada)
    if not os.path.exists(ORIGINAL_AUDIO_FILE):
        original, fs = record_audio(ORIGINAL_AUDIO_FILE, RECORD_DURATION, SAMPLING_RATE)
    else:
        print(f"Menggunakan file yang ada: {ORIGINAL_AUDIO_FILE}")
        fs, data_int = wavfile.read(ORIGINAL_AUDIO_FILE)
        original = (data_int.astype(np.float32) / np.iinfo(np.int16).max).flatten()

    # 2. Tambahkan noise
    noisy, fs_noisy = add_noise_to_audio(ORIGINAL_AUDIO_FILE, NOISY_AUDIO_FILE, NOISE_AMPLITUDE)

    # 3. Desain filter FIR LPF
    fir_coeff = design_fir_lowpass_filter(NUM_TAPS_LPF, CUTOFF_FREQ_LPF, SAMPLING_RATE)

    # 4. Terapkan filter
    filtered = apply_filter(noisy, fir_coeff)

    # 5. Simpan hasil filter
    wavfile.write(FILTERED_AUDIO_FILE, SAMPLING_RATE, (filtered * np.iinfo(np.int16).max).astype(np.int16))
    print(f"Audio hasil filter disimpan sebagai {FILTERED_AUDIO_FILE}")

    # 6. Plot frequency response filter
    w, h = freqz(fir_coeff, worN=8000)
    freqs = w * SAMPLING_RATE / (2 * np.pi)
    plt.figure(figsize=(10, 5))
    plt.plot(freqs, 20 * np.log10(abs(h)))
    plt.title(f'FIR LPF Frequency Response (Cutoff = {CUTOFF_FREQ_LPF} Hz)')
    plt.xlabel('Frekuensi (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.axvline(CUTOFF_FREQ_LPF, color='red', linestyle='--', label='Cutoff')
    plt.grid(True)
    plt.legend()
    plt.show()

    # 7. Plot sinyal domain waktu & frekuensi
    t = np.arange(len(original)) / fs
    plt.figure(figsize=(12, 10))

    plt.subplot(3, 1, 1)
    plt.plot(t, noisy, label='Sinyal Bernoise')
    plt.title('Sinyal Bernoise (Waktu)')
    plt.xlabel('Waktu (s)')
    plt.ylabel('Amplitudo')
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(t, filtered, color='orange', label='Hasil Filter')
    plt.title('Sinyal Setelah Filter (Waktu)')
    plt.xlabel('Waktu (s)')
    plt.ylabel('Amplitudo')
    plt.grid(True)

    plt.subplot(3, 1, 3)
    f_axis = np.fft.rfftfreq(len(t), 1/fs)
    fft_noisy = np.abs(np.fft.rfft(noisy))
    fft_filtered = np.abs(np.fft.rfft(filtered))
    plt.semilogx(f_axis, fft_noisy, label='Noisy')
    plt.semilogx(f_axis, fft_filtered, color='orange', label='Filtered')
    plt.title('Spektrum Sebelum & Sesudah Filter')
    plt.xlabel('Frekuensi (Hz)')
    plt.ylabel('Magnitude')
    plt.axvline(CUTOFF_FREQ_LPF, color='red', linestyle='--', label='Cutoff')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

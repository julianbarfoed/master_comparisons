import numpy as np
import pyloudnorm as pyln
import librosa
import os
from pydub import AudioSegment
import scipy.signal

def analyze_audio(filepath, min_segment_duration=5.0):
    try:
        # Load audio with librosa
        y, sr = librosa.load(filepath, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        # Compute MFCCs and recurrence matrix for novelty
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc = librosa.util.normalize(mfcc)
        recurrence = librosa.segment.recurrence_matrix(mfcc, mode='affinity', sym=True)
        novelty = librosa.onset.onset_strength(S=recurrence, sr=sr)

        # Peak-pick novelty to find section boundaries
        peaks = librosa.util.peak_pick(novelty, pre_max=3, post_max=3, pre_avg=5, post_avg=5, delta=0.01, wait=10)
        print(f"Detected {len(peaks)} peaks")
        boundary_times = librosa.frames_to_time(peaks, sr=sr)

        # Add start and end times
        boundaries = [0.0] + boundary_times.tolist() + [duration]

        # Filter out short segments
        filtered = []
        for i in range(len(boundaries) - 1):
            if (boundaries[i + 1] - boundaries[i]) >= min_segment_duration:
                filtered.append((boundaries[i], boundaries[i + 1]))

        # Load full-res audio with pydub for accurate loudness
        audio = AudioSegment.from_file(filepath)
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        if audio.channels == 2:
            samples = samples.reshape((-1, 2)).mean(axis=1)
        y_full = samples / (2 ** 15)
        meter = pyln.Meter(audio.frame_rate)

        section_metrics = []
        for start_sec, end_sec in filtered:
            start_sample = int(start_sec * sr)
            end_sample = int(end_sec * sr)
            segment = y_full[start_sample:end_sample]

            try:
                lufs = meter.integrated_loudness(segment)
                rms = np.sqrt(np.mean(segment ** 2))
                peak = np.max(np.abs(segment))

                section_metrics.append({
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "LUFS": float(lufs),
                    "RMS": float(20 * np.log10(rms).item()),
                    "Peak": float(20 * np.log10(peak).item())
                })
            except Exception as e:
                print(f"Skipping segment {start_sec}-{end_sec}: {e}")
                continue

        return {
            "filename": os.path.basename(filepath),
            "segments": section_metrics
        }

    except Exception as e:
        print("❌ ERROR during analysis:", e)
        raise
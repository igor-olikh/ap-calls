#!/usr/bin/env python3
"""Simple test script to verify audio capture is working."""
import sounddevice as sd
import numpy as np
import time

def test_audio_capture():
    """Test if microphone is capturing audio."""
    print("Testing audio capture...")
    print("Speak into your microphone for 5 seconds...")
    
    sample_rate = 16000
    duration = 5  # seconds
    chunk_size = 4096
    
    audio_data = []
    max_level = 0
    
    def audio_callback(indata, frames, time, status):
        """Callback to capture audio."""
        nonlocal max_level
        if status:
            print(f"Status: {status}")
        
        # Calculate audio level
        level = np.abs(indata).max()
        max_level = max(max_level, level)
        
        # Store audio
        audio_data.append(indata.copy())
        
        # Print level indicator
        bar_length = int(level * 50)
        bar = '=' * bar_length
        print(f"\rAudio level: [{bar:<50}] {level:.4f}", end='', flush=True)
    
    try:
        print(f"\nStarting capture (sample rate: {sample_rate} Hz)...")
        stream = sd.InputStream(
            channels=1,
            samplerate=sample_rate,
            blocksize=chunk_size,
            callback=audio_callback,
            dtype='float32'
        )
        
        stream.start()
        print("\nListening... (speak now!)")
        time.sleep(duration)
        stream.stop()
        stream.close()
        
        print("\n\nCapture complete!")
        print(f"Max audio level detected: {max_level:.4f}")
        print(f"Total samples captured: {len(audio_data) * chunk_size}")
        
        if max_level < 0.001:
            print("\n⚠️  WARNING: Very low audio levels detected!")
            print("This could indicate:")
            print("  1. Microphone permissions not granted")
            print("  2. Microphone is muted")
            print("  3. Microphone volume is too low")
            print("  4. Wrong microphone selected")
        elif max_level > 0.01:
            print("\n✓ Audio capture is working! Microphone is receiving audio.")
        else:
            print("\n⚠️  Low audio levels - microphone might be working but volume is low.")
        
    except PermissionError:
        print("\n❌ ERROR: Permission denied!")
        print("\nPlease grant microphone access:")
        print("  1. Open System Preferences > Security & Privacy > Privacy > Microphone")
        print("  2. Enable access for Terminal (or your Python interpreter)")
        print("  3. Restart the application")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_capture()

"""Audio capture and playback module for microphone and system audio."""
import sounddevice as sd
import numpy as np
from typing import Optional, Callable, Iterator
import queue
import threading


class AudioCapture:
    """Handles audio input capture and output playback."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 4096,
        input_device: Optional[int] = None,
        output_device: Optional[int] = None
    ):
        """Initialize audio capture.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Size of audio chunks in samples
            input_device: Input device index (None for default)
            output_device: Output device index (None for default)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.input_device = input_device
        self.output_device = output_device
        
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        self.input_stream = None
        self.output_stream = None
        self.is_running = False
        
        self._input_thread = None
        self._output_thread = None
    
    def list_devices(self) -> None:
        """List available audio devices."""
        print("\nAvailable audio devices:")
        print(sd.query_devices())
    
    def start_input_stream(self, callback: Optional[Callable[[np.ndarray], None]] = None) -> None:
        """Start capturing audio from microphone.
        
        Args:
            callback: Optional callback function for audio chunks
        """
        if self.is_running:
            return
        
        def audio_callback(indata, frames, time, status):
            """Callback for audio input."""
            if status:
                print(f"Audio input status: {status}")
            
            # Convert to int16 PCM
            audio_data = (indata[:, 0] * 32767).astype(np.int16)
            
            if callback:
                callback(audio_data)
            else:
                self.input_queue.put(audio_data.tobytes())
        
        self.input_stream = sd.InputStream(
            device=self.input_device,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            callback=audio_callback,
            dtype='float32'
        )
        
        self.input_stream.start()
        self.is_running = True
        print(f"Audio input started (device: {self.input_device or 'default'})")
    
    def start_output_stream(self) -> None:
        """Start audio output stream."""
        if self.output_stream is not None:
            return
        
        def output_callback(outdata, frames, time, status):
            """Callback for audio output."""
            if status:
                print(f"Audio output status: {status}")
            
            try:
                # Get audio data from queue
                audio_bytes = self.output_queue.get_nowait()
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                
                # Convert to float32 and normalize
                audio_float = audio_array.astype(np.float32) / 32767.0
                
                # Ensure correct length
                if len(audio_float) < frames:
                    # Pad with zeros
                    outdata[:len(audio_float), 0] = audio_float
                    outdata[len(audio_float):, 0] = 0
                else:
                    # Truncate if needed
                    outdata[:, 0] = audio_float[:frames]
            except queue.Empty:
                # No audio data, output silence
                outdata[:, 0] = 0
        
        self.output_stream = sd.OutputStream(
            device=self.output_device,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.chunk_size,
            callback=output_callback,
            dtype='float32'
        )
        
        self.output_stream.start()
        print(f"Audio output started (device: {self.output_device or 'default'})")
    
    def get_audio_chunks(self) -> Iterator[bytes]:
        """Get audio chunks from input stream.
        
        Yields:
            Audio chunks as bytes
        """
        while self.is_running:
            try:
                chunk = self.input_queue.get(timeout=0.1)
                yield chunk
            except queue.Empty:
                continue
    
    def play_audio(self, audio_data: bytes) -> None:
        """Play audio data.
        
        Args:
            audio_data: Audio data as bytes (LINEAR16 PCM)
        """
        if self.output_stream is None:
            self.start_output_stream()
        
        self.output_queue.put(audio_data)
    
    def stop(self) -> None:
        """Stop all audio streams."""
        self.is_running = False
        
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None
        
        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
            self.output_stream = None
        
        print("Audio streams stopped")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

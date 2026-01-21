"""Translation engine that orchestrates STT → Translation → TTS pipeline."""
import threading
import queue
from typing import Optional, Callable
from google_cloud_client import GoogleCloudClient
from audio_capture import AudioCapture
import time


class TranslationEngine:
    """Bidirectional translation engine for real-time phone calls."""
    
    def __init__(
        self,
        google_client: GoogleCloudClient,
        audio_capture: AudioCapture,
        source_lang: str,
        target_lang: str,
        source_lang_code: str,  # Full language code for STT (e.g., 'ru-RU')
        target_lang_code: str,  # Full language code for STT (e.g., 'uk-UA')
        voice_source: str,
        voice_target: str,
        sample_rate: int = 16000
    ):
        """Initialize translation engine.
        
        Args:
            google_client: Google Cloud client instance
            audio_capture: Audio capture instance
            source_lang: Source language code (e.g., 'ru')
            target_lang: Target language code (e.g., 'uk')
            source_lang_code: Full language code for STT (e.g., 'ru-RU')
            target_lang_code: Full language code for STT (e.g., 'uk-UA')
            voice_source: Voice name for source language TTS
            voice_target: Voice name for target language TTS
            sample_rate: Audio sample rate
        """
        self.google_client = google_client
        self.audio_capture = audio_capture
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.source_lang_code = source_lang_code
        self.target_lang_code = target_lang_code
        self.voice_source = voice_source
        self.voice_target = voice_target
        self.sample_rate = sample_rate
        
        self.is_running = False
        self._outbound_thread = None
        self._inbound_thread = None
        
        # Buffers for accumulating audio
        self._outbound_buffer = []
        self._inbound_buffer = []
        self._buffer_lock = threading.Lock()
        
        # Minimum buffer size before processing (to reduce API calls)
        self._min_buffer_duration = 1.0  # seconds - wait for more speech
        self._max_buffer_duration = 3.0  # seconds - max wait before processing
        self._silence_threshold = 0.01  # Audio level below this is considered silence
        self._silence_duration = 0.5  # seconds of silence before processing
        self._buffer_size_samples = int(self.sample_rate * self._min_buffer_duration)
    
    def start(self) -> None:
        """Start the translation engine."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start outbound translation (user speaks → translated to target)
        self._outbound_thread = threading.Thread(
            target=self._process_outbound,
            daemon=True
        )
        self._outbound_thread.start()
        
        # Start inbound translation (caller speaks → translated to source)
        # Note: For system audio capture, you may need additional setup on Mac
        self._inbound_thread = threading.Thread(
            target=self._process_inbound,
            daemon=True
        )
        self._inbound_thread.start()
        
        print("Translation engine started")
    
    def stop(self) -> None:
        """Stop the translation engine."""
        self.is_running = False
        
        if self._outbound_thread:
            self._outbound_thread.join(timeout=2.0)
        
        if self._inbound_thread:
            self._inbound_thread.join(timeout=2.0)
        
        print("Translation engine stopped")
    
    def _process_outbound(self) -> None:
        """Process outbound audio: source language → target language."""
        print(f"Outbound translation started: {self.source_lang} → {self.target_lang}")
        
        buffer = []
        last_process_time = time.time()
        last_audio_time = time.time()
        
        def audio_callback(audio_data: bytes) -> None:
            """Callback for microphone audio."""
            nonlocal buffer, last_process_time, last_audio_time
            
            current_time = time.time()
            
            # Check audio level to detect silence
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            audio_level = np.abs(audio_array.astype(np.float32) / 32767.0).max()
            
            with self._buffer_lock:
                buffer.append(audio_data)
                
                # Update last audio time if we detect sound
                if audio_level > self._silence_threshold:
                    last_audio_time = current_time
                
                # Calculate time since last audio
                time_since_audio = current_time - last_audio_time
                time_since_process = current_time - last_process_time
                
                # Process buffer if:
                # 1. We've had silence for the threshold duration (speech ended)
                # 2. OR we've been buffering for max duration (timeout)
                # 3. OR we have minimum buffer and enough time has passed
                should_process = False
                
                if buffer:
                    buffer_size = sum(len(chunk) for chunk in buffer) // 2  # int16 = 2 bytes
                    
                    if time_since_audio >= self._silence_duration and time_since_process >= self._min_buffer_duration:
                        # Speech ended - process what we have
                        should_process = True
                    elif time_since_process >= self._max_buffer_duration:
                        # Timeout - process anyway
                        should_process = True
                    elif buffer_size >= self._buffer_size_samples and time_since_process >= self._min_buffer_duration:
                        # Enough audio collected
                        should_process = True
                
                if should_process and buffer:
                    # Combine buffer chunks
                    combined = b''.join(buffer)
                    buffer.clear()
                    last_process_time = current_time
                    last_audio_time = current_time
                    
                    # Process in separate thread to avoid blocking
                    threading.Thread(
                        target=self._translate_outbound_chunk,
                        args=(combined,),
                        daemon=True
                    ).start()
        
        # Start audio input with callback
        self.audio_capture.start_input_stream(audio_callback)
        
        # Keep thread alive
        while self.is_running:
            time.sleep(0.1)
    
    def _translate_outbound_chunk(self, audio_data: bytes) -> None:
        """Translate a chunk of outbound audio."""
        try:
            # Use non-streaming recognition for buffered chunks (faster and more reliable)
            text = self.google_client.transcribe_audio(
                audio_data,
                self.source_lang_code,
                self.sample_rate
            )
            
            if not text.strip():
                return
            
            print(f"\n{'='*70}")
            print(f"🎤 RECOGNIZED ({self.source_lang.upper()}): {text}")
            # Note: Confidence score would be shown if available from transcribe_audio
            
            # Translate
            translated = self.google_client.translate_text(
                text,
                self.source_lang,
                self.target_lang
            )
            
            print(f"🌐 TRANSLATED ({self.target_lang.upper()}): {translated}")
            print(f"{'='*70}\n")
            
            # Synthesize speech (target language)
            audio_output = self.google_client.synthesize_speech(
                translated,
                self.target_lang_code,
                self.voice_target,
                self.sample_rate
            )
            
            # Play translated audio
            if audio_output:
                self.audio_capture.play_audio(audio_output)
        
        except Exception as e:
            print(f"Error in outbound translation: {e}")
    
    def _process_inbound(self) -> None:
        """Process inbound audio: target language → source language.
        
        Note: This requires system audio capture, which may need special setup on Mac.
        For now, this is a placeholder that can be extended.
        """
        print(f"Inbound translation started: {self.target_lang} → {self.source_lang}")
        print("Note: System audio capture may require additional setup on Mac")
        
        # For system audio, you would need to:
        # 1. Use a virtual audio device (like BlackHole or Soundflower)
        # 2. Route call audio through that device
        # 3. Capture from that device here
        
        # Placeholder: This would process system/call audio
        # For now, we'll note that this requires additional Mac-specific setup
        while self.is_running:
            time.sleep(1)
            # TODO: Implement system audio capture
            # This would follow the same pattern as _process_outbound
            # but capture from system audio instead of microphone
    
    def process_inbound_audio(self, audio_data: bytes) -> None:
        """Process inbound audio chunk (for manual system audio integration).
        
        Args:
            audio_data: Audio data from system/call audio
        """
        try:
            def audio_stream():
                chunk_size = 4096
                for i in range(0, len(audio_data), chunk_size):
                    yield audio_data[i:i + chunk_size]
            
            # Transcribe (target language)
            transcripts = list(self.google_client.transcribe_streaming(
                audio_stream(),
                self.target_lang_code,
                self.sample_rate
            ))
            
            if not transcripts:
                return
            
            text = ' '.join(transcripts)
            
            if not text.strip():
                return
            
            print(f"[Inbound] Recognized ({self.target_lang}): {text}")
            
            # Translate
            translated = self.google_client.translate_text(
                text,
                self.target_lang,
                self.source_lang
            )
            
            print(f"[Inbound] Translated ({self.source_lang}): {translated}")
            
            # Synthesize speech (source language)
            audio_output = self.google_client.synthesize_speech(
                translated,
                self.source_lang_code,
                self.voice_source,
                self.sample_rate
            )
            
            # Play translated audio
            if audio_output:
                self.audio_capture.play_audio(audio_output)
        
        except Exception as e:
            print(f"Error in inbound translation: {e}")

"""Google Cloud API client wrapper for STT, Translation, and TTS."""
import os
import io
from typing import Iterator, Optional, Callable
from google.cloud import speech
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech
from google.oauth2 import service_account


class GoogleCloudClient:
    """Wrapper for Google Cloud Speech-to-Text, Translation, and Text-to-Speech APIs."""
    
    def __init__(self, credentials_path: str):
        """Initialize Google Cloud clients.
        
        Args:
            credentials_path: Path to service account JSON key file
        """
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        
        # Initialize clients
        self.speech_client = speech.SpeechClient(credentials=credentials)
        self.translate_client = translate.Client(credentials=credentials)
        self.tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
        
        # Streaming recognition config
        self._streaming_config = None
    
    def setup_streaming_stt(self, language_code: str, sample_rate: int = 16000) -> None:
        """Setup streaming speech-to-text configuration.
        
        Args:
            language_code: Language code (e.g., 'ru-RU', 'uk-UA')
            sample_rate: Audio sample rate in Hz
        """
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
            model='latest_long',
        )
        
        self._streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )
    
    def _create_request_generator(self, audio_stream: Iterator[bytes]) -> Iterator[speech.StreamingRecognizeRequest]:
        """Create a request generator for streaming recognition.
        
        Args:
            audio_stream: Iterator of audio chunks (bytes)
        
        Yields:
            StreamingRecognizeRequest objects (without config, as config is passed separately)
        """
        for audio_chunk in audio_stream:
            yield speech.StreamingRecognizeRequest(audio_content=audio_chunk)
    
    def transcribe_streaming(
        self,
        audio_stream: Iterator[bytes],
        language_code: str,
        sample_rate: int = 16000,
        on_transcript: Optional[Callable[[str, bool], None]] = None
    ) -> Iterator[str]:
        """Transcribe audio stream in real-time.
        
        Args:
            audio_stream: Iterator of audio chunks (bytes)
            language_code: Language code for recognition
            sample_rate: Audio sample rate
            on_transcript: Optional callback for transcripts (text, is_final)
        
        Yields:
            Final transcript text
        """
        self.setup_streaming_stt(language_code, sample_rate)
        request_generator = self._create_request_generator(audio_stream)
        
        responses = self.speech_client.streaming_recognize(
            config=self._streaming_config,
            requests=request_generator
        )
        
        for response in responses:
            if not response.results:
                continue
            
            result = response.results[0]
            if not result.alternatives:
                continue
            
            transcript = result.alternatives[0].transcript
            is_final = result.is_final
            
            if on_transcript:
                on_transcript(transcript, is_final)
            
            if is_final and transcript:
                yield transcript
    
    def transcribe_audio(self, audio_data: bytes, language_code: str, sample_rate: int = 16000) -> str:
        """Transcribe audio data using non-streaming recognition.
        
        Args:
            audio_data: Audio data as bytes (LINEAR16 PCM)
            language_code: Language code for recognition
            sample_rate: Audio sample rate
        
        Returns:
            Transcribed text
        """
        # Use enhanced model for better accuracy, especially for Russian
        use_enhanced = True
        model = 'latest_long'  # Best for longer phrases
        
        # Adjust sample rate if needed (Google Cloud supports 8000-48000 Hz)
        # For best quality, use 44100 or 48000, but 16000 is minimum for good recognition
        effective_sample_rate = sample_rate
        if sample_rate > 48000:
            effective_sample_rate = 48000
        elif sample_rate < 8000:
            effective_sample_rate = 16000
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=effective_sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
            use_enhanced=use_enhanced,
            model=model,
            # Request multiple alternatives to get better matches
            max_alternatives=3,
            # Enable profanity filter (optional, can be removed)
            profanity_filter=False,
            # Enable word-level confidence
            enable_word_confidence=True,
            # Enable word time offsets for better context
            enable_word_time_offsets=True,
        )
        
        audio = speech.RecognitionAudio(content=audio_data)
        
        response = self.speech_client.recognize(config=config, audio=audio)
        
        if not response.results:
            return ""
        
        # Use the best alternative (highest confidence)
        best_transcript = ""
        best_confidence = 0.0
        all_alternatives = []
        
        for result in response.results:
            if result.alternatives:
                # Check all alternatives and pick the best one
                for alternative in result.alternatives:
                    confidence = alternative.confidence if hasattr(alternative, 'confidence') and alternative.confidence else 0.0
                    all_alternatives.append((alternative.transcript, confidence))
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_transcript = alternative.transcript
        
        # Debug: show alternatives if confidence is low
        if best_confidence < 0.7 and len(all_alternatives) > 1:
            print(f"[Debug] Low confidence ({best_confidence:.2f}), alternatives: {all_alternatives[:3]}")
        
        # If we found a good match, use it; otherwise use the first alternative
        if best_transcript:
            return best_transcript
        
        # Fallback: combine all first alternatives
        transcripts = []
        for result in response.results:
            if result.alternatives:
                transcripts.append(result.alternatives[0].transcript)
        
        return " ".join(transcripts)
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'ru', 'uk')
            target_lang: Target language code (e.g., 'uk', 'ru')
        
        Returns:
            Translated text
        """
        if not text.strip():
            return ""
        
        result = self.translate_client.translate(
            text,
            source_language=source_lang,
            target_language=target_lang,
            model='nmt'  # Neural Machine Translation
        )
        
        return result['translatedText']
    
    def synthesize_speech(
        self,
        text: str,
        language_code: str,
        voice_name: str,
        sample_rate: int = 24000
    ) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            language_code: Language code (e.g., 'ru-RU', 'uk-UA')
            voice_name: Voice name (e.g., 'ru-RU-Wavenet-D', 'uk-UA-Wavenet-A')
            sample_rate: Output audio sample rate
        
        Returns:
            Audio data as bytes (LINEAR16 PCM)
        """
        if not text.strip():
            return b''
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
        )
        
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        return response.audio_content

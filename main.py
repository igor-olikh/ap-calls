#!/usr/bin/env python3
"""Main entry point for the real-time phone call translation system."""
import sys
import signal
import argparse
from pathlib import Path

from config_loader import Config
from google_cloud_client import GoogleCloudClient
from audio_capture import AudioCapture
from translation_engine import TranslationEngine


class TranslationApp:
    """Main application class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self.google_client = None
        self.audio_capture = None
        self.translation_engine = None
        self.running = False
    
    def initialize(self) -> None:
        """Initialize all components."""
        print("Initializing translation system...")
        
        # Initialize Google Cloud client
        print("Setting up Google Cloud services...")
        self.google_client = GoogleCloudClient(
            self.config.google_cloud_credentials
        )
        
        # Initialize audio capture
        print("Setting up audio capture...")
        audio_config = self.config.audio_config
        self.audio_capture = AudioCapture(
            sample_rate=audio_config['sample_rate'],
            chunk_size=audio_config['chunk_size'],
            input_device=audio_config['input_device'],
            output_device=audio_config['output_device']
        )
        
        # Map language codes
        source_lang = self.config.source_language
        target_lang = self.config.target_language
        
        # Full language codes for STT/TTS
        lang_code_map = {
            'ru': 'ru-RU',
            'uk': 'uk-UA',
            'en': 'en-US',
        }
        
        source_lang_code = lang_code_map.get(source_lang, f"{source_lang}-{source_lang.upper()}")
        target_lang_code = lang_code_map.get(target_lang, f"{target_lang}-{target_lang.upper()}")
        
        # Get voice names from config
        translation_config = self.config.translation_config
        voice_source = translation_config.get(f'voice_{source_lang}', f'{source_lang_code}-Wavenet-D')
        voice_target = translation_config.get(f'voice_{target_lang}', f'{target_lang_code}-Wavenet-A')
        
        # Initialize translation engine
        print("Setting up translation engine...")
        self.translation_engine = TranslationEngine(
            google_client=self.google_client,
            audio_capture=self.audio_capture,
            source_lang=source_lang,
            target_lang=target_lang,
            source_lang_code=source_lang_code,
            target_lang_code=target_lang_code,
            voice_source=voice_source,
            voice_target=voice_target,
            sample_rate=audio_config['sample_rate']
        )
        
        print("Initialization complete!")
        print(f"Translation: {source_lang} ↔ {target_lang}")
    
    def run(self) -> None:
        """Run the application."""
        if self.running:
            return
        
        try:
            self.initialize()
            
            # Start translation engine
            self.translation_engine.start()
            self.running = True
            
            print("\n" + "="*60)
            print("Translation system is running!")
            print("Press Ctrl+C to stop")
            print("="*60 + "\n")
            
            # Keep main thread alive
            while self.running:
                import time
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Shutdown the application gracefully."""
        self.running = False
        
        if self.translation_engine:
            self.translation_engine.stop()
        
        if self.audio_capture:
            self.audio_capture.stop()
        
        print("Application stopped.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Real-time phone call translation system"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List available audio devices and exit'
    )
    
    args = parser.parse_args()
    
    # List devices if requested
    if args.list_devices:
        try:
            audio = AudioCapture()
            audio.list_devices()
        except Exception as e:
            print(f"Error listing devices: {e}")
        return
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"Error: Configuration file not found: {args.config}")
        print("Please copy config.example.yaml to config.yaml and configure it.")
        sys.exit(1)
    
    # Setup signal handlers
    app = TranslationApp(args.config)
    
    def signal_handler(sig, frame):
        """Handle interrupt signals."""
        print("\nReceived interrupt signal, shutting down...")
        app.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run application
    app.run()


if __name__ == "__main__":
    main()

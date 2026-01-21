#!/usr/bin/env python3
"""Test script for the translation system - speak and see translations."""
import sys
import signal
from config_loader import Config
from google_cloud_client import GoogleCloudClient
from audio_capture import AudioCapture
from translation_engine import TranslationEngine


class TranslationTester:
    """Simple tester for the translation system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the tester."""
        print("Loading configuration...")
        self.config = Config(config_path)
        
        print("Initializing Google Cloud services...")
        self.google_client = GoogleCloudClient(
            self.config.google_cloud_credentials
        )
        
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
        
        lang_code_map = {
            'ru': 'ru-RU',
            'uk': 'uk-UA',
            'en': 'en-US',
        }
        
        source_lang_code = lang_code_map.get(source_lang, f"{source_lang}-{source_lang.upper()}")
        target_lang_code = lang_code_map.get(target_lang, f"{target_lang}-{target_lang.upper()}")
        
        translation_config = self.config.translation_config
        voice_source = translation_config.get(f'voice_{source_lang}', f'{source_lang_code}-Wavenet-D')
        voice_target = translation_config.get(f'voice_{target_lang}', f'{target_lang_code}-Wavenet-A')
        
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
        
        self.running = False
    
    def run(self):
        """Run the test."""
        try:
            print("\n" + "="*70)
            print("TRANSLATION TEST MODE")
            print("="*70)
            print(f"Source language: {self.config.source_language.upper()}")
            print(f"Target language: {self.config.target_language.upper()}")
            print("\nInstructions:")
            print("  1. Speak clearly into your microphone")
            print("  2. Wait for recognition and translation")
            print("  3. You'll hear the translated audio")
            print("  4. Press Ctrl+C to stop")
            print("="*70 + "\n")
            
            # Start translation engine
            self.translation_engine.start()
            self.running = True
            
            # Keep running
            import time
            while self.running:
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n\nStopping test...")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown gracefully."""
        self.running = False
        if self.translation_engine:
            self.translation_engine.stop()
        if self.audio_capture:
            self.audio_capture.stop()
        print("Test stopped.")


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Test translation system")
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    tester = TranslationTester(args.config)
    
    def signal_handler(sig, frame):
        print("\n\nReceived interrupt signal, shutting down...")
        tester.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run test
    tester.run()


if __name__ == "__main__":
    main()

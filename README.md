# Real-time Phone Call Translation System

A Python application for Mac that provides real-time bidirectional voice translation during phone calls using Google Cloud AI services. Speak in one language (e.g., Russian) and have your conversation partner hear it in another language (e.g., Ukrainian), and vice versa.

## Features

- **Real-time bidirectional translation** during phone calls
- **Configurable languages** (default: Russian ↔ Ukrainian)
- **Google Cloud AI services** for high-quality speech recognition, translation, and synthesis
- **Simple configuration-based setup**
- **Low latency** streaming processing

## Requirements

- macOS (tested on macOS 10.15+)
- Python 3.8 or higher
- Google Cloud account with billing enabled
- Microphone and speaker/headphones access

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Project

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Required APIs**:
   - [Cloud Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com)
   - [Cloud Translation API](https://console.cloud.google.com/apis/library/translate.googleapis.com)
   - [Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)

3. **Create a Service Account**:
   - Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
   - Click "Create Service Account"
   - Give it a name (e.g., "translation-service")
   - Grant it the following roles:
     - Cloud Speech-to-Text API User
     - Cloud Translation API User
     - Cloud Text-to-Speech API User
   - Click "Done"

4. **Create and Download Service Account Key**:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - Download the JSON file and save it securely (e.g., `~/google-cloud-key.json`)

### 3. Configure the Application

1. **Copy the example configuration**:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **Edit `config.yaml`** with your settings:
   ```yaml
   google_cloud:
     credentials_path: "/Users/yourusername/google-cloud-key.json"  # Path to your service account key
   
   languages:
     source: "ru"  # Your language (Russian)
     target: "uk"  # Target language (Ukrainian)
   
   audio:
     input_device: null   # null = default microphone
     output_device: null  # null = default speakers
     sample_rate: 16000
     chunk_size: 4096
   
   translation:
     model: "nmt"
     voice_ru: "ru-RU-Wavenet-D"  # Russian voice
     voice_uk: "uk-UA-Wavenet-A"  # Ukrainian voice
   ```

### 4. Grant Microphone Permissions (macOS)

The first time you run the application, macOS will prompt you to grant microphone access. Make sure to allow it.

You can also grant permissions manually:
- System Preferences > Security & Privacy > Privacy > Microphone
- Enable access for Terminal (if running from terminal) or your Python interpreter

## Usage

### Basic Usage

```bash
python main.py
```

The application will:
1. Load your configuration
2. Initialize Google Cloud services
3. Start capturing audio from your microphone
4. Translate your speech in real-time
5. Output translated audio

Press `Ctrl+C` to stop the application.

### List Available Audio Devices

To see available audio input/output devices:

```bash
python main.py --list-devices
```

Then update `config.yaml` with the device index if you want to use a specific device.

### Custom Configuration File

```bash
python main.py --config /path/to/custom-config.yaml
```

## How It Works

### Outbound Translation (You → Caller)

1. **Capture**: Your microphone captures your speech (Russian)
2. **Recognize**: Google Speech-to-Text transcribes your speech
3. **Translate**: Google Translation API translates to Ukrainian
4. **Synthesize**: Google Text-to-Speech generates Ukrainian speech
5. **Output**: Translated audio is played (you can route this to call audio)

### Inbound Translation (Caller → You)

**Note**: System audio capture on Mac requires additional setup (see below).

1. **Capture**: System/call audio is captured (Ukrainian)
2. **Recognize**: Google Speech-to-Text transcribes the speech
3. **Translate**: Google Translation API translates to Russian
4. **Synthesize**: Google Text-to-Speech generates Russian speech
5. **Output**: Translated audio is played to your speakers/headphones

## System Audio Capture on Mac

Capturing system audio (call audio) on macOS requires additional setup because macOS doesn't allow direct system audio capture by default. Here are two options:

### Option 1: Use BlackHole (Recommended)

1. **Install BlackHole** (virtual audio driver):
   ```bash
   brew install blackhole-2ch
   # Or download from: https://github.com/ExistentialAudio/BlackHole
   ```

2. **Configure Audio Routing**:
   - Open "Audio MIDI Setup" (Applications > Utilities)
   - Create a Multi-Output Device:
     - Include your speakers/headphones
     - Include BlackHole 2ch
   - Set this as your system output device
   - In your phone app, route call audio to this device

3. **Update Configuration**:
   - Run `python main.py --list-devices` to find BlackHole device index
   - Update `config.yaml` to use BlackHole as input device for inbound audio

### Option 2: Use Soundflower (Alternative)

Similar to BlackHole, but older. BlackHole is recommended for newer macOS versions.

## Configuration Reference

### Language Codes

- `ru` - Russian
- `uk` - Ukrainian
- `en` - English
- See [Google Cloud Translation languages](https://cloud.google.com/translate/docs/languages) for more

### Voice Names

Available voices depend on the language. Common options:

**Russian:**
- `ru-RU-Wavenet-D` (Male)
- `ru-RU-Wavenet-E` (Female)
- `ru-RU-Standard-D` (Male, Standard)

**Ukrainian:**
- `uk-UA-Wavenet-A` (Female)
- `uk-UA-Standard-A` (Female, Standard)

See [Google Cloud TTS voices](https://cloud.google.com/text-to-speech/docs/voices) for full list.

## Troubleshooting

### "Configuration file not found"
- Make sure you've copied `config.example.yaml` to `config.yaml`
- Check the file path if using `--config` option

### "Google Cloud credentials file not found"
- Verify the path in `config.yaml` is correct
- Make sure the JSON key file exists and is readable

### "Permission denied" for microphone
- Grant microphone access in System Preferences > Security & Privacy > Privacy > Microphone
- Restart the application after granting permissions

### No audio output
- Check that your output device is correct in `config.yaml`
- Run `--list-devices` to verify device indices
- Check system volume and application volume

### High latency
- Reduce `chunk_size` in `config.yaml` (but this may increase CPU usage)
- Check your internet connection (Google Cloud APIs require internet)
- Consider using a closer Google Cloud region if available

### API Errors
- Verify all three APIs are enabled in Google Cloud Console
- Check that your service account has the correct permissions
- Verify billing is enabled on your Google Cloud project
- Check API quotas and limits

## Cost Considerations

Google Cloud services are pay-as-you-go. Typical costs:

- **Speech-to-Text**: ~$0.006 per 15 seconds
- **Translation**: ~$20 per million characters
- **Text-to-Speech**: ~$4 per million characters (Wavenet) or $4 per million characters (Standard)

For a 10-minute call with moderate conversation:
- STT: ~$0.24 (assuming continuous speech)
- Translation: ~$0.01-0.05 (depending on text length)
- TTS: ~$0.02-0.10 (depending on speech length)

**Total**: Approximately $0.30-0.40 per 10-minute call

Google Cloud offers a free tier with $300 credit for new accounts.

## Limitations

- Requires internet connection (Google Cloud APIs)
- System audio capture on Mac requires additional setup (BlackHole/Soundflower)
- Latency depends on internet speed and API response times
- Costs scale with usage (pay-per-use model)

## Future Enhancements

- GUI for easier configuration
- Voice activity detection to reduce API calls
- Caching common translations
- Support for additional languages
- Call recording with translations
- Local processing options (using local models)

## License

This project is provided as-is for personal use.

## Support

For issues related to:
- **Google Cloud APIs**: See [Google Cloud Documentation](https://cloud.google.com/docs)
- **Audio setup on Mac**: See BlackHole or Soundflower documentation
- **Application bugs**: Check the error messages and configuration

## Contributing

This is a personal project, but suggestions and improvements are welcome!

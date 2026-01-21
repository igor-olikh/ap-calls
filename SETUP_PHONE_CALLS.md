# Setup Guide: Real-Time Phone Call Translation

This guide will walk you through setting up the translation system for real phone calls with bidirectional translation.

## Prerequisites

- macOS (tested on macOS 10.15+)
- Python 3.8+ with virtual environment set up
- Google Cloud credentials configured
- Microphone and speaker/headphone access granted

## Step 1: Install BlackHole

BlackHole is a virtual audio driver that allows capturing system audio (call audio) on macOS.

### Option A: Install via Homebrew (Recommended)

1. Open Terminal
2. Run the following command:
   ```bash
   brew install blackhole-2ch
   ```
3. Enter your administrator password when prompted
4. **IMPORTANT**: Restart your Mac after installation for BlackHole to work properly

### Option B: Manual Installation

1. Download BlackHole from: https://github.com/ExistentialAudio/BlackHole/releases
2. Download the latest `BlackHole2ch.pkg` file
3. Double-click the `.pkg` file to install
4. Follow the installation wizard
5. **IMPORTANT**: Restart your Mac after installation

## Step 2: Configure Audio Routing

After restarting your Mac, you need to set up audio routing so that call audio can be captured.

### 2.1 Open Audio MIDI Setup

1. Open **Finder**
2. Go to **Applications** > **Utilities**
3. Open **Audio MIDI Setup**
   - Or use Spotlight: Press `Cmd + Space`, type "Audio MIDI Setup", press Enter

### 2.2 Create Multi-Output Device

1. In Audio MIDI Setup, look at the bottom left corner
2. Click the **`+` (plus)** button at the bottom
3. Select **"Create Multi-Output Device"**
4. A new device will appear in the list on the left

### 2.3 Configure Multi-Output Device

1. Select the newly created "Multi-Output Device" in the left panel
2. In the right panel, you'll see a list of available audio devices
3. **Check the boxes** for:
   - Your speakers/headphones (e.g., "MacBook Pro Speakers", "AirPods", etc.)
   - **BlackHole 2ch** (this is crucial!)
4. **Uncheck** "Drift Correction" if it's checked
5. (Optional) Rename the device by double-clicking "Multi-Output Device" and typing a name like "Call Translation"

### 2.4 Set as System Output

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Sound** (or **Sound & Haptics**)
3. Click on the **Output** tab
4. Select your **Multi-Output Device** (the one you just created)
5. Close System Settings

**Important**: Your system audio will now play through both your speakers AND BlackHole. This is normal and necessary for capturing call audio.

## Step 3: Find BlackHole Device Index

You need to find the device index number for BlackHole to configure it in the application.

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd /Users/igorolikh/Documents/projects/private/ap-calls
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
4. List available audio devices:
   ```bash
   python main.py --list-devices
   ```
5. Look for **BlackHole 2ch** in the output. It will show something like:
   ```
   > 4 BlackHole 2ch, Core Audio (2 in, 2 out)
   ```
6. **Note the number** (in this example, it's `4`) - this is the device index you'll need

## Step 4: Configure the Application

1. Open the configuration file:
   ```bash
   open config.yaml
   ```
   Or edit it in your preferred text editor

2. Update the `audio` section to include the BlackHole device index:
   ```yaml
   audio:
     input_device: null  # null = default microphone (for your speech)
     input_device_inbound: 4  # Replace 4 with the BlackHole device index from Step 3
     output_device: null  # null = default speakers
     sample_rate: 44100
     chunk_size: 4096
   ```

3. Save the file

## Step 5: Test the Setup

Before making a real call, test that everything is configured correctly.

1. Make sure you're in the project directory with virtual environment activated:
   ```bash
   cd /Users/igorolikh/Documents/projects/private/ap-calls
   source venv/bin/activate
   ```

2. Start the application:
   ```bash
   python main.py
   ```

3. You should see output like:
   ```
   Initializing translation system...
   Setting up Google Cloud services...
   Setting up audio capture...
   Setting up inbound audio capture (for call audio)...
   Setting up translation engine...
   Initialization complete!
   Translation: ru ↔ uk
   
   Outbound translation started: ru → uk
   Inbound translation started: uk → ru
   
   ============================================================
   Translation system is running!
   Press Ctrl+C to stop
   ============================================================
   ```

4. If you see "Inbound translation disabled", check that `input_device_inbound` is set correctly in `config.yaml`

## Step 6: Make a Test Call

Now you're ready to test with a real phone call!

### 6.1 Start the Application

1. Make sure the application is running (from Step 5)
2. Keep the terminal window open

### 6.2 Make the Call

1. Call your friend in Ukraine using:
   - FaceTime
   - WhatsApp
   - Telegram
   - Zoom
   - Skype
   - Or any other VoIP service

2. **Important**: Make sure the call audio is going through your system output (the Multi-Output Device you created)

### 6.3 Test Translation

**Outbound Translation (You → Friend):**
1. Speak in Russian into your microphone
2. Wait 1-2 seconds
3. You should see in the terminal:
   ```
   ======================================================================
   🎤 RECOGNIZED (RU): [your speech]
   🌐 TRANSLATED (UK): [translation]
   ======================================================================
   ```
4. The translated Ukrainian audio will play through your speakers
5. Your friend will hear both your original voice and the translation (if using speakers)

**Inbound Translation (Friend → You):**
1. Ask your friend to speak in Ukrainian
2. Wait 1-2 seconds
3. You should see in the terminal:
   ```
   ======================================================================
   🎤 INBOUND RECOGNIZED (UK): [friend's speech]
   🌐 INBOUND TRANSLATED (RU): [translation]
   ======================================================================
   ```
4. The translated Russian audio will play through your speakers/headphones

## Troubleshooting

### BlackHole Not Appearing in Device List

- **Solution**: Make sure you restarted your Mac after installing BlackHole
- Check System Settings > Privacy & Security > Microphone - BlackHole might need permissions

### No Inbound Audio Captured

- **Check**: Is `input_device_inbound` set correctly in `config.yaml`?
- **Check**: Is your Multi-Output Device selected as system output?
- **Check**: Is call audio actually playing? Test by playing music - it should play through both speakers and BlackHole
- **Check**: Run `python main.py --list-devices` again to verify BlackHole index hasn't changed

### Echo or Feedback

- **Solution**: Use headphones instead of speakers to prevent feedback
- **Solution**: Lower the volume of translated audio
- **Solution**: Position microphone away from speakers

### Low Recognition Quality

- **Solution**: Speak clearly and at normal pace
- **Solution**: Reduce background noise
- **Solution**: Check microphone levels (not too quiet, not too loud)
- **Solution**: Try increasing `sample_rate` to 48000 in `config.yaml`

### Application Crashes or Hangs

- **Check**: Are Google Cloud APIs enabled and credentials valid?
- **Check**: Is your internet connection stable?
- **Check**: Check terminal for error messages
- **Solution**: Restart the application

### Call Audio Not Routing Through Multi-Output

- **Check**: System Settings > Sound > Output - is Multi-Output Device selected?
- **Check**: Some apps (like Zoom) have their own audio settings - check app settings
- **Solution**: Restart the calling application after changing system output

## Tips for Best Results

1. **Use Headphones**: Prevents echo and feedback
2. **Speak Clearly**: Better recognition = better translation
3. **Wait Between Phrases**: Give the system time to process (1-2 seconds)
4. **Test First**: Test with short phrases before long conversations
5. **Check Volume**: Make sure translated audio is audible but not too loud
6. **Stable Internet**: Google Cloud APIs require internet connection

## What to Expect

- **Latency**: 1-3 seconds delay is normal (speech → recognition → translation → synthesis)
- **Accuracy**: Recognition accuracy depends on:
  - Audio quality
  - Speaking clarity
  - Background noise
  - Microphone quality
- **Cost**: Each call uses Google Cloud APIs (see README.md for cost estimates)

## Stopping the Application

- Press `Ctrl+C` in the terminal
- The application will stop gracefully
- You can change system output back to your normal speakers if desired

## Next Steps

Once everything is working:
- Test with different phrases and situations
- Adjust volume levels for comfort
- Consider using a dedicated headset for better audio quality
- Monitor Google Cloud costs in the Google Cloud Console

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Verify all steps were completed correctly
3. Check that BlackHole is properly installed and Mac was restarted
4. Verify Google Cloud credentials and API access
5. Review the main README.md for additional troubleshooting

---

**Last Updated**: After BlackHole installation and system restart

# Multi Agent GPT Characters

Forked form the youtuber 
Web app that allows 3 GPT characters and a human to talk to each other.  
Written by DougDoug. Feel free to use this for whatever you want! Credit is appreciated but not required.  

This is uploaded for educational purposes. Unfortunately I don't have time to offer individual support or review pull requests, but ChatGPT or Claude can be very helpful if you are running into issues.

## SETUP:
1) This was written in Python 3.9.2. Install page here: https://www.python.org/downloads/release/python-392/

2) **Install FFmpeg** - Required for audio processing:
   - Download from https://ffmpeg.org/download.html
   - Add to your system PATH

3) Run `pip install -r requirements.txt` to install all modules.

4) **Install CUDA-enabled PyTorch** for GPU acceleration (recommended):
   ```
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```


  Make sure your ElevenLabs voices are properly configured:
  - Log into ElevenLabs website
  - Set up voice settings for your voices there
  - The API will use those settings automatically

  The voice names in your code should match exactly what you have in ElevenLabs:
  - "Dougsworth"
  - "Tony Emperor of New York"
  - "Victoria"



5) This uses the OpenAi API and Elevenlabs services. You'll need to set up an account with these services and generate an API key from them. Then add these keys as windows environment variables named OPENAI_API_KEY and ELEVENLABS_API_KEY respectively.

## Environment Variables

You need to set up the following environment variables:

- `OPENAI_API_KEY` - Your OpenAI API key for GPT-4o model access
- `ELEVENLABS_API_KEY` - Your ElevenLabs API key for AI voice generation

### Setting Environment Variables on Windows:
1. Open System Properties (Windows Key + Pause or search "Environment Variables")
2. Click "Environment Variables"
3. Under "User variables" click "New"
4. Add Variable name: `OPENAI_API_KEY` and Value: `your_openai_api_key_here`
5. Repeat for `ELEVENLABS_API_KEY`

### Alternative: Using .env file
You can also create a `.env` file in the project root with:
```
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

4) This app uses the GPT-4o model from OpenAi. As of this writing (Sep 3rd 2024), you need to pay $5 to OpenAi in order to get access to the GPT-4o model API. So after setting up your account with OpenAi, you will need to pay for at least $5 in credits so that your account is given the permission to use the GPT-4o model when running my app. See here: https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4-gpt-4-turbo-gpt-4o-and-gpt-4o-mini

5) Elevenlabs is the service I use for Ai voices. Once you've made Ai voices on the Elevenlabs website, open up multi_agent_gpt.py and make sure it's passing the name of your voices into each agent's init function.

6) This app uses the open source Whisper model from OpenAi for transcribing audio into text. This means you'll be running an Ai model locally on your PC, so ideally you have an Nvidia GPU to run this. The Whisper model is used to transcribe the user's microphone recordings, and is used to generate subtitles from the Elevenlabs audio every time an agent "speaks". This model was downloaded from Huggingface and should install automatically when you run the whisper_openai.py file.  
Note that you'll want to make sure you've installed torch with CUDA support, rather than just default torch, otherwise it will run very slow: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118.  
If you have issues with the Whisper model there are other services that can offer an audio-to-text service (including a Whisper API), but this solution currently works well for me.

7) This code runs a Flask web app and will display the agents' dialogue using HTML and javascript. By default it will run the server on "127.0.0.1:5151", but you can change this in multi_agent_gpt.py.

## OBS Integration (Optional - Visual Animations)


 talking.  
57 -  First open up OBS. Make sure you're running version 28.X or later. Click Tools, then 
- WebSocket Server Settings. Make sure "Enable WebSocket server" is checked. Then set 
- Server Port to '4455' and set the Server Password to 'TwitchChat9'. If you use a 
- different Server Port or Server Password in your OBS, just make sure you update the 
- websockets_auth.py file accordingly.  
58 -  Next install the Move OBS plugin: https://obsproject.com/forum/resources/move.913/ Now     
- you can use this plugin to add a filter to an audio source that will change an image's      
- transform based on the audio waveform. For example, I have a filter on a specific audio     
- track that will move each agent's bell pepper icon source image whenever that pepper is     
- talking.  
59 -  Note that OBS must be open when you're running this code, otherwise OBS WebSockets         
- won't be able to connect. If you don't need the images to move while talking, you can       
- just delete the OBS portions of the code.
- 
**OBS is optional** but enables visual animations during conversations. Without OBS, the app will crash on startup due to WebSocket connection failure.

To use OBS features:
1. Install OBS Studio (version 28.X or later)
2. Open OBS → Tools → WebSocket Server Settings
3. Enable WebSocket server, set Port: `4455`, Password: `TwitchChat9`
4. Install Move OBS plugin: https://obsproject.com/forum/resources/move.913/
5. Add filters to audio sources to animate images based on audio waveform
6. Keep OBS running when using the app

**To run without OBS:** You'll need to modify the code to handle the missing OBS connection gracefully.



  Required OBS Images:

  Three character bell pepper images:
  1. Wario Pepper - for Agent 1 (OSWALD)
  2. Waluigi Pepper - for Agent 2 (TONY KING OF NEW YORK)
  3. Gamer Pepper - for Agent 3 (VICTORIA)

  OBS Setup for Character Animation:

  1. Add Image Sources to your OBS scene:
    - Import your 3 bell pepper character images as Image Sources
    - Name them appropriately (e.g., "Wario Pepper", "Waluigi Pepper", "Gamer Pepper")
  2. Audio Move Filters (requires Move OBS plugin):
    - Add "Audio Move" filters to each pepper image source
    - These filters animate the images based on audio waveform
    - Filter names in code: "Audio Move - Wario Pepper", "Audio Move - Waluigi Pepper", "Audio Move     
   - Gamer Pepper"
  3. Audio Sources:
    - Set up audio sources for each agent's voice
    - Link the Move filters to detect audio from the corresponding agent's speech

  What the Animation Does:

  - When an agent speaks, their corresponding pepper image will move/animate
  - The movement is triggered by audio waveform detection
  - Creates visual feedback showing which character is currently talking

  You'll need to create or find 3 bell pepper character images that represent your agents'
  personalities!


## Using the App

To start out, edit the ai_prompts.py file to design each agent's personality and the purpose of their conversation.  
By default the characters are told to discuss the greatest videogames of all time, but you can change this to anything you want, OpenAi is pretty great at having agents talk about pretty much anything.

Next run multi_agent_gpt.py

Once it's running you now have a number of options:

__Press Numpad7 to "talk" to the agents.__  
Numpad7 will start recording your microphone audio. Hit Numpad8 to stop recording. It will then transcribe your audio into text and add your dialogue into all 3 agents' chat history. Then it will pick a random agent to "activate" and have them start talking next.

__Numpad1 will "activate" Agent #1.__  
This means that agent will continue the conversation and start talking. Unless it has been "paused", it will also pick a random other agent and "activate" them to talk next, so that the conversation continues indefinitely.

__Numpad2 will "activate" Agent #2, Numpad3 will "activate" Agent #3.__

__F4 will "pause" all agents__   
This stops the agents from activating each other. Basically, use this to stop the conversation from continuing any further, and then you can talk to the agents again.

## Miscellaneous notes:

All agents will automatically store their "chat history" into a backup txt file as the conversation continues. This is done so that when you restart the program, each agent will automatically load from their backup file and thus restore the entire conversation, letting you continue it from where you left off. If you ever want to fully reset the conversation then just delete the backup txt files in the project.

If you want to have the agent dialogue displayed in OBS, you should add a browser source and set the URL to "127.0.0.1:5151". 



  To run this project, you need:

  1. FFmpeg - Missing, causes pydub warning. Download and add to PATH
  2. CUDA PyTorch - For Whisper model GPU acceleration
  3. Environment variables - Already configured in your .env file

  OBS Purpose:
  - Optional visual effects - animates character images during speech
  - Controls scene switching and source visibility
  - Currently crashes the app because it tries to connect on startup

  Quick fixes to run the project:
  1. Install FFmpeg from https://ffmpeg.org/download.html
  2. Install CUDA PyTorch: pip install torch torchvision torchaudio --index-url
  https://download.pytorch.org/whl/cu118
  3. Either install/configure OBS or modify multi_agent_gpt.py to handle OBS connection failures        
  gracefully






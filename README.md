# 🎹✨ MIDI Generator Piano Roll

<div align="center">

  <!-- ⭐ GitHub Stars / 🍴 Forks / 🐛 Issues Badges -->
  <div align="center" style="display: flex; gap: 12px; justify-content: center; margin: 24px 0;">
    <a href="https://github.com/WebChatAppAi/midi-gen">
      <img
        alt="GitHub Stars"
        src="https://img.shields.io/github/stars/WebChatAppAi/midi-gen?style=for-the-badge&logo=github&logoColor=white&label=Stars&color=blue"
      />
    </a>
    <a href="https://github.com/WebChatAppAi/midi-gen/fork">
      <img
        alt="GitHub Forks"
        src="https://img.shields.io/github/forks/WebChatAppAi/midi-gen?style=for-the-badge&logo=github&logoColor=white&label=Forks&color=green"
      />
    </a>
    <a href="https://github.com/WebChatAppAi/midi-gen/issues">
      <img
        alt="GitHub Issues"
        src="https://img.shields.io/github/issues/WebChatAppAi/midi-gen?style=for-the-badge&logo=github&logoColor=white&label=Issues&color=red"
      />
    </a>
  </div>

  <!-- 🔖 Meta Badges (Python, License, GUI, MIDI, Last Update, Contributors) -->
  <p align="center" style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
    <img
      src="https://img.shields.io/badge/🐍%20Python-3.8%2B-blue?style=for-the-badge"
      alt="Python Version"
    />
    <img
      src="https://img.shields.io/badge/📄%20License-Non--Commercial-red?style=for-the-badge"
      alt="License"
    />
    <img
      src="https://img.shields.io/badge/🖥️%20GUI-PySide6-5cb85c?style=for-the-badge"
      alt="PySide6 GUI"
    />
    <img
      src="https://img.shields.io/badge/🎼%20MIDI-pretty__midi-orange?style=for-the-badge"
      alt="pretty_midi"
    />
    <img
      src="https://img.shields.io/github/last-commit/WebChatAppAi/midi-gen?style=for-the-badge&logo=github&logoColor=white&label=Last%20Update&color=blue"
      alt="Last Commit"
    />
    <img
      src="https://img.shields.io/github/contributors/WebChatAppAi/midi-gen?style=for-the-badge&logo=github&logoColor=white&label=Contributors&color=green"
      alt="Contributors"
    />
  </p>

  <!-- 📊 Repo Analytics (RepoBeats) -->
  <div align="center" style="margin: 32px 0;">
    <a href="https://github.com/WebChatAppAi/midi-gen">
      <img
        src="https://repobeats.axiom.co/api/embed/85314166456118665297959c949c0772fe2583be.svg"
        alt="Repo Analytics"
      />
    </a>
  </div>

</div>

<blockquote align="center">
  <h3>🎼 A plugin-powered standalone piano roll app written in Python</h3>
  <p><strong>Generate MIDI using motif and Markov algorithms • Visualize compositions • Real-time playback • Export to <code>.mid</code></strong></p>
</blockquote>

<div align="center">
  <h3>🎹 Community Engagement</h3>
  <p>Share your creations with <code>#MIDIGen</code> on social media!</p>
  <p>Featured plugins get highlighted in our <a href="https://github.com/WebChatAppAi/midi-gen/wiki/Showcase">🌟 Showcase Wiki</a></p>
  <p>
    <a href="https://github.com/WebChatAppAi/midi-gen/discussions">
      <img
        alt="GitHub Discussions"
        src="https://img.shields.io/github/discussions/WebChatAppAi/midi-gen?style=for-the-badge&logo=github-discussions&logoColor=white&label=Discussions&color=purple"
      />
    </a>
  </p>
</div>

---

## ✨ <span style="color:#ffb300;">Key Features</span>

- 🎹 **Modern Piano Roll** with grid lines, time ruler, and MIDI notes  
- 🧩 **Plugin Manager** to run motif, Markov, and custom generation logic  
- 🔌 **Drop-in Python Plugins** – Easily extend the app with your own `.py` files  
- 🛠️ **Dynamic Parameter Dialogs** – Each plugin has its own customizable settings  
- 📤 **Export to MIDI** with velocity/pitch embedded (even if not shown in UI)  
- ⏯ **Playback Controls** with beat-synced transport  
- 🪟 **Smooth Dockable Plugin Panel** – Plugin Manager with fluid animations when dragged, floated, and reattached
- 🔍 **Zoom Functionality** – Easily view and edit longer note sequences

---

## 🔄 <span style="color:#a5d6a7;">Recent Updates (Changelog)</span>

- 🔊 **Volume Control & FluidSynth Integration**:
  - Added a **master volume slider** to the transport controls for real-time audio level adjustment.
  - Integrated **FluidSynth** as the new audio backend for MIDI playback, offering improved sound quality and control.
- 🎚️ **Enhanced Transport Controls**:
  - Improved **BPM slider** stability and responsiveness.
  - Enhanced **instrument selection** capabilities.
- 🛠️ **Bug Fixes & Stability**:
  - Addressed various bugs, including fixes related to audio playback initialization and control.
  - General stability improvements throughout the application.

---

## 🖼️ <span style="color:#6ec6ff;">Screenshots</span>

<div align="center">
  <img src="./image1.png" alt="Piano Roll Screenshot 1" width="70%" style="border-radius:12px;box-shadow:0 4px 24px #0002;"/>
  <br/>
  <sub><strong>🎼 Generated MIDI using Motif Generator</strong></sub>
  <br/><br/>
  <img src="./image2.png" alt="Piano Roll Screenshot 2" width="70%" style="border-radius:12px;box-shadow:0 4px 24px #0002;"/>
  <br/>
  <sub><strong>🧠 Markov Chain Plugin Output + Plugin Panel Floating</strong></sub>
</div>

---

## 🧩 <span style="color:#b39ddb;">Plugin System</span>

<details>
<summary>🔍 <b>How to create a plugin?</b></summary>

```python
class MyCustomGenerator(PluginBase):
    def generate(self, **params):
        return [
            pretty_midi.Note(
                pitch=64,
                velocity=100,
                start=0.0,
                end=0.5
            )
        ]
```

Define `generate()` and return a list of PrettyMIDI notes.  
Add an optional `get_parameter_info()` to customize UI controls per plugin.

📖 **Full developer reference:** [docs/plugin-docs.md](./docs/plugin-docs.md)

</details>

---

## 🚀 <span style="color:#81c784;">Getting Started</span>

### 💻 Windows Users - Quick Installation (Executable)

<details open>
<summary><b>📦 Using the pre-built executable</b></summary>

1. **Download the application**
   - Go to the [Releases](https://github.com/WebChatAppAi/midi-gen/releases) tab on GitHub
   - Download the latest `.zip` file

2. **Install the application**
   - Extract the ZIP file to `C:\Users\YourName\Documents\PianoRollStudio`
   - Run the executable (first launch may take a moment to initialize)
   
3. **Set up plugins**
   - On first launch, a `plugins` directory will be created in the installation folder
   - Download the plugin `.py` files from the [GitHub repository's plugins folder](https://github.com/WebChatAppAi/midi-gen/tree/main/plugins)
   - Place these files in the newly created `plugins` directory
   
4. **Restart and enjoy**
   - Close and reopen the application
   - Your plugins should now be loaded and ready to use
</details>

### 🐍 Python Installation (All Platforms)

1. **Clone the repository**
```bash
git clone https://github.com/WebChatAppAi/midi-gen.git
cd midi-gen
```

2. **Install dependencies**
```bash
pip install PySide6 pretty_midi numpy pygame fluidsynth
```

3. **Run the app**
```bash
python app.py
```

<details>
<summary>💡 <b>Tip:</b> Use the startup scripts for convenience</summary>
<ul>
<li>Windows: <code>start.bat</code></li>
<li>Linux/macOS: <code>sh start.sh</code> (or <code>./start.sh</code> after <code>chmod +x start.sh</code>)</li>
</ul>
</details>

---

## 🎛️ <span style="color:#ffd180;">How To Use</span>

1. **Open the app**
2. **Pick a plugin** from the **Plugin Manager**
3. **Click Configure** to tweak plugin settings
4. **Click Generate** to add notes
5. **Press Play** or **Export MIDI** when ready

---

## 💎 <span style="color:#4dd0e1;">Extra Capabilities</span>

- 🧩 Easily add your own plugins via `plugins/*.py`  
- 🖱 Plugin Manager can be docked, floated, and re-attached  
- 🎼 Generated notes contain pitch and velocity info embedded in exported `.mid`  
- 🔄 Real-time preview + loopable playback **coming soon**  
- 🤖 Support for OpenAI-compatible endpoints and Gemini model plugins (default plugins currently produce better musical results)

---

## 🌟 <span style="color:#ffd700;">What's Next?</span>

- 🛒 **Plugin Marketplace** (auto-discovery from GitHub)  
- 🤖 **AI Plugin Support** (HuggingFace, LLaMA, MusicGen)  
- 🎹 **Auto-chord, Arp, and Drum Pattern generators**  
- 📥 **Import `.mid` files for editing**  

---

## 🧠 <span style="color:#b2dfdb;">Want to Contribute?</span>

- 📖 Read the full technical guide: [docs/project-details.md](./docs/project-details.md)  
- 🔧 Explore the project structure and architecture details  
- 🍴 Fork → 🛠️ Build your plugin → 📬 Open a Pull Request  

---

## 📄 <span style="color:#e57373;">License</span>

<blockquote>
  <b>Non-Commercial Software License © <a href="https://github.com/WebChatAppAi">Jonas</a></b>
</blockquote>

This project is licensed under a custom Non-Commercial Software License. See the [LICENSE](LICENSE) file in the root directory for complete license details.

### Key License Terms:
- ✅ You may use and modify this software for personal and non-commercial purposes
- ❌ Commercial use is strictly prohibited without explicit permission from Jonas
- 📧 You must notify the copyright holder of any distribution or modification
- 🏷️ Attribution to the copyright holder (Jonas) is required in all copies

---

<p align="center">
  <img src="https://em-content.zobj.net/source/microsoft-teams/363/musical-score_1f3bc.png" width="48"/>
  <br/>
  <i>✨ Built with a love for generative music, modular design, and open creativity.</i>
</p>

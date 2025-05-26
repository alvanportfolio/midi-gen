# 🎹✨ MIDI Generator Piano Roll

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/License-Non--Commercial-red?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/GUI-PySide6-green?style=flat-square" alt="PySide6"/>
  <img src="https://img.shields.io/badge/MIDI-pretty__midi-orange?style=flat-square" alt="MIDI"/>
  <img src="https://img.shields.io/github/stars/WebChatAppAi/midi-gen?style=flat-square&color=gold" alt="GitHub Stars"/>
</p>

<blockquote>
  <b>🎼 A plugin-powered standalone piano roll app written in Python that lets you generate MIDI using motif and Markov algorithms, visualize them, play them, and export to <code>.mid</code>.</b>
</blockquote>

<hr/>

## ✨ <span style="color:#ffb300;">Key Features</span>

- 🎹 <b>Modern Piano Roll</b> with grid lines, time ruler, and MIDI notes  
- 🧩 <b>Plugin Manager</b> to run motif, Markov, and custom generation logic  
- 🔌 <b>Drop-in Python Plugins</b> – Easily extend the app with your own <code>.py</code> files  
- 🛠️ <b>Dynamic Parameter Dialogs</b> – Each plugin has its own customizable settings  
- 📤 <b>Export to MIDI</b> with velocity/pitch embedded (even if not shown in UI)  
- ⏯ <b>Playback Controls</b> with beat-synced transport  
- 🪟 <b>Smooth Dockable Plugin Panel</b> – Plugin Manager with fluid animations when dragged, floated, and reattached
- 🔍 <b>Zoom Functionality</b> – Easily view and edit longer note sequences

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
  <img src="./image1.png" alt="Piano Roll Screenshot 1" width="60%" style="border-radius:12px;box-shadow:0 4px 24px #0002;"/>
  <br/>
  <sub>🎼 Generated MIDI using Motif Generator</sub>
  <br/><br/>
  <img src="./image2.png" alt="Piano Roll Screenshot 2" width="60%" style="border-radius:12px;box-shadow:0 4px 24px #0002;"/>
  <br/>
  <sub>🧠 Markov Chain Plugin Output + Plugin Panel Floating</sub>
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

Define <code>generate()</code> and return a list of PrettyMIDI notes.  
Add an optional <code>get_parameter_info()</code> to customize UI controls per plugin.

📖 <b>Full developer reference:</b> [docs/plugin-docs.md](./docs/plugin-docs.md)

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

<ol>
<li>Clone the repository</li>
</ol>

```bash
git clone https://github.com/WebChatAppAi/midi-gen.git
cd midi-gen
```

<ol start="2">
<li>Install dependencies</li>
</ol>

```bash
pip install PySide6 pretty_midi numpy pygame fluidsynth
```

<ol start="3">
<li>Run the app</li>
</ol>

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

<ol>
<li>Open the app</li>
<li>Pick a plugin from the <b>Plugin Manager</b></li>
<li>Click <b>Configure</b> to tweak plugin settings</li>
<li>Click <b>Generate</b> to add notes</li>
<li>Press <b>Play</b> or <b>Export MIDI</b> when ready</li>
</ol>

---

## 💎 <span style="color:#4dd0e1;">Extra Capabilities</span>

- 🧩 Easily add your own plugins via <code>plugins/*.py</code>  
- 🖱 Plugin Manager can be docked, floated, and re-attached  
- 🎼 Generated notes contain pitch and velocity info embedded in exported <code>.mid</code>  
- 🔄 Real-time preview + loopable playback <b>coming soon</b>  
- 🤖 Support for OpenAI-compatible endpoints and Gemini model plugins (default plugins currently produce better musical results)

---

## 🌟 <span style="color:#ffd700;">What's Next?</span>

- 🛒 Plugin Marketplace (auto-discovery from GitHub)  
- 🤖 AI Plugin Support (HuggingFace, LLaMA, MusicGen)  
- 🎹 Auto-chord, Arp, and Drum Pattern generators  
- 📥 Import <code>.mid</code> files for editing  

---
<div align="center">
  <h2>🎶 Support MIDI Generator Development</h2>
  
  <div align="center" style="display: flex; gap: 16px; justify-content: center; margin: 24px 0;">
    <a href="https://github.com/WebChatAppAi/midi-gen">
      <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/WebChatAppAi/midi-gen?style=flat-square&label=Star%20This%20Repo&logo=github&logoColor=white&color=gold&labelColor=181717">
    </a>
    <a href="https://github.com/WebChatAppAi/midi-gen/fork">
      <img alt="GitHub forks" src="https://img.shields.io/github/forks/WebChatAppAi/midi-gen?style=flat-square&label=Fork%20%26%20Build&logo=git&logoColor=white&color=4dc71f&labelColor=181717">
    </a>
  </div>

  <div align="center" style="margin: 32px 0;">
    <a href="https://github.com/WebChatAppAi/midi-gen">
     <img src="https://repobeats.axiom.co/api/embed/85314166456118665297959c949c0772fe2583be.svg" alt="Repo Analytics">
    </a>
  </div>

  <div align="center" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; max-width: 800px; margin: 0 auto;">
    <div>
      <h3>🚀 Quick Links</h3>
      <p>
        <a href="https://github.com/WebChatAppAi/midi-gen/issues">
          <img alt="GitHub issues" src="https://img.shields.io/github/issues-raw/WebChatAppAi/midi-gen?style=for-the-badge&logo=git&logoColor=white&color=blue&label=Report%20Issue">
        </a>
      </p>
      <p>
        <a href="https://github.com/WebChatAppAi/midi-gen/discussions">
          <img alt="GitHub Discussions" src="https://img.shields.io/github/discussions/WebChatAppAi/midi-gen?style=for-the-badge&logo=github&logoColor=white&color=purple&label=Join%20Discussion">
        </a>
      </p>
    </div>
    <div>
      <h3>📈 Project Stats</h3>
      <p>
        <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/WebChatAppAi/midi-gen?style=flat-square&logo=github&logoColor=white&color=blue&label=Last%20Update">
      </p>
      <p>
        <img alt="GitHub contributors" src="https://img.shields.io/github/contributors/WebChatAppAi/midi-gen?style=flat-square&logo=github&logoColor=white&color=green&label=Contributors">
      </p>
    </div>
  </div>

  <hr style="border: 1px solid #404040; width: 60%; margin: 32px auto;">

  <div align="center" style="margin-top: 24px;">
    <h3>🎹 Community Engagement</h3>
    <p>Share your creations with <code>#MIDIGen</code> on social media!</p>
    <p>Featured plugins get highlighted in our <a href="https://github.com/WebChatAppAi/midi-gen/wiki/Showcase">Showcase Wiki</a></p>
  </div>
</div>

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
- You may use and modify this software for personal and non-commercial purposes
- Commercial use is strictly prohibited without explicit permission from Jonas
- You must notify the copyright holder of any distribution or modification
- Attribution to the copyright holder (Jonas) is required in all copies

<p align="center">
  <img src="https://em-content.zobj.net/source/microsoft-teams/363/musical-score_1f3bc.png" width="48"/>
  <br/>
  <i>✨ Built with a love for generative music, modular design, and open creativity.</i>
</p>

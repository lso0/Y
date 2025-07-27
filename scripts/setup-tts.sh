#!/bin/bash

# CLI_X Text-to-Speech Setup Script
# Installs Coqui TTS for email reading functionality

echo "🔊 CLI_X Text-to-Speech Setup"
echo "=============================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 first:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    echo "Please install pip first:"
    echo "  macOS: python3 -m ensurepip --upgrade"
    echo "  Ubuntu/Debian: sudo apt install python3-pip"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Install Coqui TTS
echo "📦 Installing Coqui TTS..."
pip3 install --user TTS

if [ $? -eq 0 ]; then
    echo "✅ Coqui TTS installed successfully!"
else
    echo "❌ Failed to install Coqui TTS. Trying with --user flag..."
    pip3 install --user TTS
fi

echo ""

# Verify installation
echo "🧪 Testing TTS installation..."
if python3 -c "import TTS; print('✅ TTS module imported successfully')" 2>/dev/null; then
    echo "✅ TTS installation verified!"
else
    echo "❌ TTS installation failed. Please check the errors above."
    exit 1
fi

echo ""

# Test TTS command
echo "🎵 Testing TTS functionality..."
if command -v tts &> /dev/null; then
    echo "✅ TTS command available!"
    
    # Download a basic model for testing
    echo "📥 Downloading basic English model (this may take a moment)..."
    tts --text "Hello from CLI_X!" --model_name "tts_models/en/ljspeech/tacotron2-DDC" --out_path /tmp/test_tts.wav 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ TTS model downloaded and ready!"
        rm -f /tmp/test_tts.wav
    else
        echo "⚠️  TTS basic test completed (model will download on first use)"
    fi
else
    echo "⚠️  TTS command not in PATH. You may need to restart your terminal or add ~/.local/bin to PATH"
    echo "   Add this to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "🎉 TTS Setup Complete!"
echo ""
echo "📧 How to use in CLI_X:"
echo "  1. Navigate to FastMail emails (FM → Read Emails)"
echo "  2. Press 'l' to view an email"
echo "  3. Press 's' to hear the email read aloud"
echo "  4. Press 'x' to stop reading"
echo "  5. Press 'z' for TTS help"
echo ""
echo "🔊 Supported features:"
echo "  • Multi-language support"
echo "  • Natural voice synthesis"
echo "  • Automatic text cleaning"
echo "  • Cross-platform audio playback"
echo ""
echo "📚 For more info: https://github.com/coqui-ai/TTS"
echo "" 
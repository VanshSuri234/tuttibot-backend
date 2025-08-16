#!/bin/bash
# TuttiBot Installation Script
# ============================

echo "🎼 TuttiBot Installation Script"
echo "================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo "✅ $2"
    else
        echo "❌ $2 - FAILED"
    fi
}

# Check Python
echo "📋 Checking requirements..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "✅ Python found: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check pip
if command_exists pip; then
    echo "✅ pip found"
elif command_exists pip3; then
    echo "✅ pip3 found"
    alias pip=pip3
else
    echo "❌ pip not found. Please install pip"
    exit 1
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
print_status $? "Python dependencies installed"

# Force NumPy version for compatibility
echo ""
echo "🔧 Ensuring NumPy compatibility..."
pip install numpy==1.26.4
print_status $? "NumPy version fixed"

# Check FFmpeg
echo ""
echo "🎵 Checking FFmpeg..."
if command_exists ffmpeg; then
    echo "✅ FFmpeg found"
else
    echo "⚠️  FFmpeg not found. Installing..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y ffmpeg
        print_status $? "FFmpeg installed"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            brew install ffmpeg
            print_status $? "FFmpeg installed via Homebrew"
        else
            echo "❌ Please install Homebrew first, then run: brew install ffmpeg"
        fi
    else
        echo "❌ Please install FFmpeg manually for your OS"
    fi
fi

# Check/Install Audiveris
echo ""
echo "📄 Checking Audiveris..."
if [ -f "/opt/audiveris/bin/Audiveris" ]; then
    echo "✅ Audiveris found at /opt/audiveris/"
    # Test it
    if /opt/audiveris/bin/Audiveris -help >/dev/null 2>&1; then
        echo "✅ Audiveris is working"
    else
        echo "⚠️  Audiveris found but not working properly"
    fi
else
    echo "⚠️  Audiveris not found. Installing..."
    
    # Download and install Audiveris
    echo "📥 Downloading Audiveris 5.6.2..."
    wget -q https://github.com/Audiveris/audiveris/releases/download/5.6.2/Audiveris-5.6.2.tar.gz
    
    if [ $? -eq 0 ]; then
        echo "📦 Extracting Audiveris..."
        tar -xzf Audiveris-5.6.2.tar.gz
        
        echo "📁 Installing to /opt/audiveris..."
        sudo mv Audiveris-5.6.2 /opt/audiveris
        sudo chmod +x /opt/audiveris/bin/Audiveris
        
        # Clean up
        rm -f Audiveris-5.6.2.tar.gz
        
        # Test installation
        if /opt/audiveris/bin/Audiveris -help >/dev/null 2>&1; then
            echo "✅ Audiveris installed successfully"
        else
            echo "⚠️  Audiveris installed but may not be working properly"
        fi
    else
        echo "❌ Failed to download Audiveris. Please install manually:"
        echo "   1. Download from: https://github.com/Audiveris/audiveris/releases"
        echo "   2. Extract to /opt/audiveris/"
        echo "   3. Make executable: sudo chmod +x /opt/audiveris/bin/Audiveris"
    fi
fi

# Test TuttiBot
echo ""
echo "🧪 Testing TuttiBot installation..."
python3 -c "
import sys
try:
    import librosa, soundfile, music21, aubio
    from INPUT3_LAYER.input_layer import MusicInputLayer
    print('✅ All Python modules can be imported')
    
    # Test Audiveris detection
    input_layer = MusicInputLayer()
    if input_layer.score_processor.audiveris_cmd:
        print('✅ Audiveris detected by TuttiBot')
    else:
        print('⚠️  Audiveris not detected by TuttiBot')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  Warning: {e}')
"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "🚀 Quick test:"
echo "   python main.py --help"
echo ""
echo "📋 To run TuttiBot:"
echo "   python main.py your_audio.wav your_score.pdf"
echo ""
echo "📖 Check README.md for detailed usage instructions."

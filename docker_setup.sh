#!/bin/bash

echo "🐳 TuttiBot v02 Docker Setup"
echo "============================"

# Build Docker image
echo "📦 Building TuttiBot Docker image..."
docker build -t tuttibot:v02 .

if [[ $? -eq 0 ]]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "🚀 Usage Examples:"
    echo ""
    echo "1. Run with PDF input:"
    echo "   docker run -v \$(pwd):/data tuttibot:v02 python3 main_v02_fixed.py --pdf /data/score.pdf --audio /data/audio.wav --output /data/output"
    echo ""
    echo "2. Run with MusicXML input:"
    echo "   docker run -v \$(pwd):/data tuttibot:v02 python3 main_v02_fixed.py --musicxml /data/score.musicxml --audio /data/audio.wav --output /data/output"
    echo ""
    echo "3. Interactive shell:"
    echo "   docker run -it -v \$(pwd):/data tuttibot:v02 /bin/bash"
    echo ""
    echo "4. Get help:"
    echo "   docker run tuttibot:v02 python3 main_v02_fixed.py --help"
else
    echo "❌ Docker build failed!"
    exit 1
fi
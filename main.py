#!/usr/bin/env python3
"""
TuttiBot Main Pipeline
=====================

Complete music analysis pipeline: INPUT3_LAYER → PROCESSING_LAYER → EXTRACTION_LAYER

Usage:
    python main.py <audio_file> <score_file>
    
Examples:
    python main.py input.wav score.pdf
    python main.py recording.mp3 sheet_music.musicxml
    python main.py performance.wav composition.mid

Supported formats:
    Audio: WAV, MP3, FLAC, AAC, OGG
    Score: PDF (via Audiveris), MusicXML, MIDI

Output:
    All intermediate and final results saved in current directory with timestamps
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil
import json

# Add all layers to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "INPUT3_LAYER"))
sys.path.insert(0, str(current_dir / "PROCESSING_LAYER"))
sys.path.insert(0, str(current_dir / "EXTRACTION_LAYER"))

class TuttiBotPipeline:
    """Main pipeline orchestrator for music analysis"""
    
    def __init__(self, output_dir: str = None):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(output_dir) if output_dir else Path(f"tuttibot_output_{self.timestamp}")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for each layer
        self.input_dir = self.output_dir / "01_input_layer"
        self.processing_dir = self.output_dir / "02_processing_layer" 
        self.extraction_dir = self.output_dir / "03_extraction_layer"
        self.final_dir = self.output_dir / "04_final_results"
        
        for dir_path in [self.input_dir, self.processing_dir, self.extraction_dir, self.final_dir]:
            dir_path.mkdir(exist_ok=True)
        
        print(f"🚀 TuttiBot Pipeline initialized")
        print(f"📁 Output directory: {self.output_dir}")
        print("=" * 60)
    
    def run_input_layer(self, audio_path: str, score_path: str):
        """Run INPUT3_LAYER to standardize inputs"""
        print("🎵 STEP 1: INPUT LAYER (INPUT3_LAYER)")
        print("-" * 40)
        
        try:
            from input_layer import MusicInputLayer
            
            input_layer = MusicInputLayer()
            results = input_layer.process_inputs(audio_path, score_path)
            
            if not results['overall_success']:
                raise Exception(f"Input layer failed:\n"
                              f"  Audio: {results['audio']['message']}\n"
                              f"  Score: {results['score']['message']}")
            
            # Copy results to our output directory
            audio_output = self.input_dir / "standardized_audio.wav"
            score_output = self.input_dir / "standardized_score.xml"
            
            shutil.copy2(results['audio']['output_path'], audio_output)
            shutil.copy2(results['score']['output_path'], score_output)
            
            # Save metadata
            metadata = {
                'timestamp': self.timestamp,
                'original_audio': str(Path(audio_path).name),
                'original_score': str(Path(score_path).name),
                'audio_converted': results['audio']['converted'],
                'score_converted': results['score']['converted'],
                'audio_message': results['audio']['message'],
                'score_message': results['score']['message']
            }
            
            with open(self.input_dir / "input_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Audio processed: {results['audio']['message']}")
            print(f"✅ Score processed: {results['score']['message']}")
            print(f"📁 Results saved to: {self.input_dir}")
            print(f"⏱️  Input layer processing time: Fast direct CLI method")
            
            return str(audio_output), str(score_output)
            
        except Exception as e:
            print(f"❌ INPUT LAYER FAILED: {e}")
            raise
    
    def run_processing_layer(self, audio_path: str, score_path: str):
        """Run PROCESSING_LAYER for audio cleaning and music analysis"""
        print("\\n🔧 STEP 2: PROCESSING LAYER")
        print("-" * 40)
        
        try:
            from processing_layer import ProcessingLayer
            
            # Initialize with our output directory as shared output
            processor = ProcessingLayer(shared_output_dir=str(self.processing_dir))
            
            # Process audio and score
            result = processor.process(audio_path, score_path)
            
            if not result:
                raise Exception("Processing failed: No result returned")
            
            # Save processing metadata
            metadata = {
                'timestamp': self.timestamp,
                'processed_audio_path': result.processed_audio_path,
                'audio_segments_count': len(result.audio_segments),
                'music_features_count': len(result.music_features.notes) if hasattr(result.music_features, 'notes') else 0,
                'processing_metadata': result.processing_metadata
            }
            
            with open(self.processing_dir / "processing_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            print(f"✅ Audio cleaned and segmented: {len(result.audio_segments)} segments")
            print(f"✅ Music features extracted: {metadata['music_features_count']} features")
            print(f"📁 Results saved to: {self.processing_dir}")
            
            return {
                'success': True,
                'processed_audio_path': result.processed_audio_path,
                'audio_segments': result.audio_segments,
                'music_features': result.music_features,
                'audio_segments_count': len(result.audio_segments),
                'music_features_count': metadata['music_features_count'],
                'cleaned_audio_path': result.processed_audio_path,
                'segments_path': None,  # Will be filled from processing metadata
                'features_path': None   # Will be filled from processing metadata
            }
            
        except Exception as e:
            print(f"❌ PROCESSING LAYER FAILED: {e}")
            raise
    
    def run_extraction_layer(self, processing_results: dict):
        """Run EXTRACTION_LAYER for advanced feature analysis"""
        print("\\n📊 STEP 3: EXTRACTION LAYER")
        print("-" * 40)
        
        try:
            from extraction_layer import AudioFeatureExtractor, ScoreFeatureExtractor
            
            # Initialize extractors
            audio_extractor = AudioFeatureExtractor()
            score_extractor = ScoreFeatureExtractor()
            
            # Extract features from processed data
            # Find the audio segments and music features files
            segments_file = None
            features_file = None
            
            # Look for generated files in processing results
            processed_dir = self.processing_dir / "processed"
            
            # Find segments file
            for file in processed_dir.glob("*_audio_segments.json"):
                segments_file = str(file)
                break
                
            # Find features file    
            for file in processed_dir.glob("*_music_features.json"):
                features_file = str(file)
                break
            
            print(f"Found segments file: {segments_file}")
            print(f"Found features file: {features_file}")
            
            if not segments_file or not features_file:
                raise Exception(f"Required files not found. Segments: {segments_file}, Features: {features_file}")
            
            audio_features = audio_extractor.extract_features(
                processing_results['cleaned_audio_path'],
                segments_file
            )
            
            score_features = score_extractor.extract_features(
                str(self.input_dir / "standardized_score.xml"),  # Use the original score file
                features_file
            )
            
            # Save features to our extraction directory
            audio_features_path = self.extraction_dir / "audio_features.json"
            score_features_path = self.extraction_dir / "score_features.json"
            
            # Convert features to JSON serializable format
            import json
            
            # Handle audio features
            if hasattr(audio_features, '__dict__'):
                audio_data = audio_features.__dict__
            else:
                audio_data = audio_features
                
            # Handle score features  
            if hasattr(score_features, '__dict__'):
                score_data = score_features.__dict__
            else:
                score_data = score_features
            
            with open(audio_features_path, 'w') as f:
                json.dump(audio_data, f, indent=2, default=str)
            
            with open(score_features_path, 'w') as f:
                json.dump(score_data, f, indent=2, default=str)
            
            # Create extraction metadata
            metadata = {
                'timestamp': self.timestamp,
                'audio_features_extracted': True,
                'score_features_extracted': True,
                'audio_features_size_kb': audio_features_path.stat().st_size / 1024,
                'score_features_size_kb': score_features_path.stat().st_size / 1024,
                'segments_file_used': segments_file,
                'features_file_used': features_file
            }
            
            with open(self.extraction_dir / "extraction_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Audio features extracted: {metadata['audio_features_size_kb']:.1f} KB")
            print(f"✅ Score features extracted: {metadata['score_features_size_kb']:.1f} KB")
            print(f"📁 Results saved to: {self.extraction_dir}")
            
            return {
                'audio_features': audio_data,
                'score_features': score_data,
                'audio_features_path': str(audio_features_path),
                'score_features_path': str(score_features_path)
            }
            
        except Exception as e:
            print(f"❌ EXTRACTION LAYER FAILED: {e}")
            raise
    
    def create_final_summary(self, input_metadata: dict, processing_results: dict, extraction_results: dict):
        """Create final comprehensive summary"""
        print("\\n📋 STEP 4: FINAL SUMMARY")
        print("-" * 40)
        
        try:
            # Create comprehensive summary
            summary = {
                'pipeline_info': {
                    'timestamp': self.timestamp,
                    'pipeline_version': 'TuttiBot v1.0',
                    'layers_used': ['INPUT3_LAYER', 'PROCESSING_LAYER', 'EXTRACTION_LAYER']
                },
                'input_info': input_metadata,
                'processing_info': {
                    'audio_segments': processing_results.get('audio_segments_count', 0),
                    'music_features': processing_results.get('music_features_count', 0),
                    'processing_time_seconds': processing_results.get('processing_time', 0)
                },
                'extraction_info': {
                    'audio_features_kb': Path(extraction_results.get('audio_features_path', '')).stat().st_size / 1024 if Path(extraction_results.get('audio_features_path', '')).exists() else 0,
                    'score_features_kb': Path(extraction_results.get('score_features_path', '')).stat().st_size / 1024 if Path(extraction_results.get('score_features_path', '')).exists() else 0
                },
                'output_files': {
                    'input_layer': str(self.input_dir),
                    'processing_layer': str(self.processing_dir),
                    'extraction_layer': str(self.extraction_dir),
                    'main_output_directory': str(self.output_dir)
                }
            }
            
            summary_path = self.final_dir / "pipeline_summary.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            # Copy key files to final directory for easy access
            key_files = [
                (self.input_dir / "standardized_audio.wav", "final_audio.wav"),
                (self.input_dir / "standardized_score.xml", "final_score.xml"),
                (self.extraction_dir / "audio_features.json", "final_audio_features.json"),
                (self.extraction_dir / "score_features.json", "final_score_features.json")
            ]
            
            for src, dst in key_files:
                if src.exists():
                    shutil.copy2(src, self.final_dir / dst)
            
            print(f"✅ Pipeline completed successfully!")
            print(f"📁 Final results: {self.final_dir}")
            print(f"📄 Summary: {summary_path}")
            
            return summary
            
        except Exception as e:
            print(f"⚠️ Error creating summary: {e}")
            return {}
    
    def run_complete_pipeline(self, audio_path: str, score_path: str):
        """Run the complete pipeline"""
        start_time = datetime.now()
        
        try:
            print(f"🎼 Starting TuttiBot Complete Pipeline")
            print(f"🎵 Audio input: {Path(audio_path).name}")
            print(f"🎼 Score input: {Path(score_path).name}")
            print("=" * 60)
            
            # Step 1: Input Layer
            std_audio, std_score = self.run_input_layer(audio_path, score_path)
            
            # Step 2: Processing Layer
            processing_results = self.run_processing_layer(std_audio, std_score)
            
            # Step 3: Extraction Layer
            extraction_results = self.run_extraction_layer(processing_results)
            
            # Step 4: Final Summary
            input_metadata = json.load(open(self.input_dir / "input_metadata.json"))
            summary = self.create_final_summary(input_metadata, processing_results, extraction_results)
            
            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds()
            
            print("\\n" + "=" * 60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉")
            print("=" * 60)
            print(f"⏱️  Total processing time: {total_time:.1f} seconds")
            print(f"📁 All results saved in: {self.output_dir}")
            print(f"📋 Check final_results/ for key outputs")
            
            return True
            
        except Exception as e:
            print("\\n" + "=" * 60)
            print("❌ PIPELINE FAILED")
            print("=" * 60)
            print(f"Error: {e}")
            return False


def main():
    """Main entry point"""
    # Handle help requests
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']:
        print("TuttiBot - Music Analysis Pipeline")
        print("=" * 40)
        print("Usage: python main.py <audio_file> <score_file>")
        print()
        print("Examples:")
        print("  python main.py recording.wav sheet_music.pdf")
        print("  python main.py performance.mp3 composition.musicxml") 
        print("  python main.py audio.flac song.mid")
        print()
        print("Supported formats:")
        print("  Audio: WAV, MP3, FLAC, AAC, OGG")
        print("  Score: PDF (via Audiveris), MusicXML (.xml/.musicxml/.mxl), MIDI (.mid/.midi)")
        print()
        print("Requirements:")
        print("  - All Python dependencies: pip install -r requirements.txt")
        print("  - FFmpeg for audio processing")
        print("  - Audiveris for PDF processing (see README.md)")
        print()
        print("Output:")
        print("  Creates timestamped directory with processed results")
        print("  Check 04_final_results/ for main outputs")
        print()
        print("For detailed setup instructions, see README.md")
        sys.exit(0)
    
    if len(sys.argv) != 3:
        print("❌ Error: Wrong number of arguments")
        print()
        print("Usage: python main.py <audio_file> <score_file>")
        print()
        print("Examples:")
        print("  python main.py input.wav score.pdf")
        print("  python main.py recording.mp3 sheet_music.musicxml") 
        print("  python main.py performance.wav composition.mid")
        print()
        print("For more help: python main.py --help")
        print("Supported formats:")
        print("  Audio: WAV, MP3, FLAC, AAC, OGG")
        print("  Score: PDF (via Audiveris), MusicXML, MIDI")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    score_file = sys.argv[2]
    
    # Validate input files
    if not Path(audio_file).exists():
        print(f"❌ Audio file not found: {audio_file}")
        sys.exit(1)
    
    if not Path(score_file).exists():
        print(f"❌ Score file not found: {score_file}")
        sys.exit(1)
    
    # Run pipeline
    pipeline = TuttiBotPipeline()
    success = pipeline.run_complete_pipeline(audio_file, score_file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

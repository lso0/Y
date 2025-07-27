#!/usr/bin/env python3
"""
Dia TTS Engine - Ultra-realistic dialogue generation using Nari Labs Dia model
Based on: https://github.com/nari-labs/dia
"""

import os
import sys
import subprocess
import tempfile
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

try:
    import torch
    from transformers import AutoProcessor, DiaForConditionalGeneration
    HF_TRANSFORMERS_AVAILABLE = True
except ImportError:
    HF_TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Install with: pip install transformers torch")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiaTTSEngine:
    """
    High-quality TTS engine using Nari Labs Dia model
    Supports both Hugging Face Transformers and CLI interfaces
    """
    
    def __init__(self, model_checkpoint: str = "nari-labs/Dia-1.6B-0626"):
        self.model_checkpoint = model_checkpoint
        self.device = self._get_device()
        self.processor = None
        self.model = None
        self.temp_dir = Path(tempfile.gettempdir()) / "dia_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Generation parameters
        self.generation_params = {
            "max_new_tokens": 3072,
            "guidance_scale": 3.0,
            "temperature": 1.8,
            "top_p": 0.90,
            "top_k": 45
        }
        
        # Check availability
        self.available = self._check_availability()
        
        if self.available and HF_TRANSFORMERS_AVAILABLE:
            self._load_model()

    def _get_device(self) -> str:
        """Determine the best device to use"""
        if torch and torch.cuda.is_available():
            return "cuda"
        elif torch and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _check_availability(self) -> bool:
        """Check if Dia TTS is available"""
        if not HF_TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers library not available")
            return False
        
        try:
            # Try to access the model info
            from transformers import AutoProcessor
            AutoProcessor.from_pretrained(self.model_checkpoint)
            return True
        except Exception as e:
            logger.warning(f"Dia model not accessible: {e}")
            return False

    def _load_model(self):
        """Load the Dia model and processor"""
        try:
            logger.info(f"Loading Dia model on {self.device}...")
            self.processor = AutoProcessor.from_pretrained(self.model_checkpoint)
            self.model = DiaForConditionalGeneration.from_pretrained(
                self.model_checkpoint
            ).to(self.device)
            logger.info("✅ Dia model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Dia model: {e}")
            self.available = False

    def is_available(self) -> bool:
        """Check if the TTS engine is ready to use"""
        return self.available and self.model is not None

    def speak_text(self, text: str, output_file: Optional[str] = None, 
                   voice_clone_audio: Optional[str] = None,
                   voice_clone_transcript: Optional[str] = None) -> Optional[str]:
        """
        Convert text to speech using Dia model
        
        Args:
            text: Text to convert to speech
            output_file: Optional output file path
            voice_clone_audio: Path to audio file for voice cloning
            voice_clone_transcript: Transcript of the voice cloning audio
            
        Returns:
            Path to generated audio file or None if failed
        """
        if not self.is_available():
            logger.error("Dia TTS engine not available")
            return None

        try:
            # Prepare text with proper speaker tags
            formatted_text = self._format_text_for_dia(text, voice_clone_transcript)
            
            # Generate audio
            audio_path = self._generate_audio(formatted_text, output_file)
            
            if audio_path and os.path.exists(audio_path):
                logger.info(f"✅ Generated audio: {audio_path}")
                return audio_path
            else:
                logger.error("Audio generation failed")
                return None
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return None

    def speak_email_content(self, subject: str, sender: str, content: str, 
                           output_file: Optional[str] = None) -> Optional[str]:
        """
        Convert email content to speech with proper formatting
        
        Args:
            subject: Email subject
            sender: Email sender  
            content: Email content
            output_file: Optional output file path
            
        Returns:
            Path to generated audio file or None if failed
        """
        # Create a natural email announcement
        email_script = self._create_email_script(subject, sender, content)
        return self.speak_text(email_script, output_file)

    def _format_text_for_dia(self, text: str, voice_clone_transcript: Optional[str] = None) -> List[str]:
        """
        Format text according to Dia model requirements
        - Always start with [S1]
        - Alternate between [S1] and [S2] for dialogue
        - Include voice clone transcript if provided
        """
        formatted_texts = []
        
        # Add voice clone transcript if provided
        if voice_clone_transcript:
            formatted_texts.append(f"[S1] {voice_clone_transcript} [S2] {text}")
        else:
            # Clean and format the text
            clean_text = self._clean_text_for_dia(text)
            
            # Check if it's a dialogue or single speaker
            if self._is_dialogue(clean_text):
                formatted_text = self._format_as_dialogue(clean_text)
            else:
                formatted_text = f"[S1] {clean_text} [S1]"  # End with speaker tag for better audio quality
            
            formatted_texts.append(formatted_text)
        
        return formatted_texts

    def _clean_text_for_dia(self, text: str) -> str:
        """Clean text for optimal Dia processing"""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Limit length to reasonable speech duration (about 20 seconds max)
        words = text.split()
        if len(words) > 200:  # About 20 seconds of speech
            text = " ".join(words[:200]) + "..."
        
        # Handle common email artifacts
        text = text.replace("=\n", "")  # Remove line breaks
        text = text.replace("&nbsp;", " ")  # Replace HTML spaces
        
        # Add natural pauses for readability
        text = text.replace(". ", ". (pause) ")
        text = text.replace("! ", "! (pause) ")
        text = text.replace("? ", "? (pause) ")
        
        return text.strip()

    def _is_dialogue(self, text: str) -> bool:
        """Check if text appears to be a dialogue"""
        dialogue_indicators = [
            '"', "'", "said", "replied", "asked", "answered",
            ":", " - ", " -- ", "Q:", "A:"
        ]
        return any(indicator in text for indicator in dialogue_indicators)

    def _format_as_dialogue(self, text: str) -> str:
        """Format text as dialogue with proper speaker tags"""
        # Simple dialogue detection and formatting
        # This is a basic implementation - can be enhanced
        
        sentences = text.split('. ')
        formatted_parts = []
        current_speaker = 1
        
        for sentence in sentences:
            if sentence.strip():
                speaker_tag = f"[S{current_speaker}]"
                formatted_parts.append(f"{speaker_tag} {sentence.strip()}")
                # Alternate speakers for dialogue effect
                current_speaker = 2 if current_speaker == 1 else 1
        
        # End with the last speaker tag
        result = " ".join(formatted_parts)
        if not result.endswith(f"[S{current_speaker}]"):
            result += f" [S{current_speaker}]"
            
        return result

    def _create_email_script(self, subject: str, sender: str, content: str) -> str:
        """Create a natural email reading script"""
        
        # Extract sender name (remove email address if present)
        sender_name = sender.split('<')[0].strip().strip('"')
        if not sender_name:
            sender_name = sender.split('@')[0] if '@' in sender else sender
        
        # Create natural announcement
        script_parts = [
            f"[S1] You have a new email from {sender_name}.",
            f"[S2] The subject is: {subject}.",
            f"[S1] Here's the message content:",
            f"[S2] {self._clean_text_for_dia(content)}",
            "[S1] End of email."
        ]
        
        return " ".join(script_parts)

    def _generate_audio(self, formatted_texts: List[str], output_file: Optional[str] = None) -> Optional[str]:
        """Generate audio using the Dia model"""
        try:
            # Prepare output file
            if not output_file:
                timestamp = int(time.time() * 1000)
                output_file = self.temp_dir / f"dia_tts_{timestamp}.mp3"
            
            # Process text
            inputs = self.processor(
                text=formatted_texts,
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate audio
            logger.info("🎤 Generating speech with Dia model...")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    **self.generation_params
                )
            
            # Decode and save
            audio_outputs = self.processor.batch_decode(outputs)
            self.processor.save_audio(audio_outputs, str(output_file))
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

    def play_audio(self, audio_file: str) -> bool:
        """Play the generated audio file"""
        try:
            # Try different audio players based on platform
            players = []
            
            if sys.platform == "darwin":  # macOS
                players = ["afplay"]
            elif sys.platform == "linux":
                players = ["aplay", "paplay", "mpg123", "vlc"]
            elif sys.platform == "win32":
                players = ["powershell", "-c", "(New-Object Media.SoundPlayer '{}').PlaySync()"]
            
            for player in players:
                try:
                    if player == "powershell":
                        subprocess.run([player, "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"], 
                                     check=True, capture_output=True)
                    else:
                        subprocess.run([player, audio_file], check=True, capture_output=True)
                    logger.info(f"🔊 Playing audio with {player}")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            logger.warning("No audio player found")
            return False
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available Dia models"""
        models = [
            "nari-labs/Dia-1.6B-0626",  # Current main model
            # Add more model variants as they become available
        ]
        return models

    def set_generation_params(self, **kwargs):
        """Update generation parameters"""
        for key, value in kwargs.items():
            if key in self.generation_params:
                self.generation_params[key] = value
                logger.info(f"Updated {key} to {value}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_checkpoint": self.model_checkpoint,
            "device": self.device,
            "available": self.available,
            "generation_params": self.generation_params.copy(),
            "temp_dir": str(self.temp_dir)
        }

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Clean up old temporary audio files"""
        try:
            cutoff_time = time.time() - (older_than_hours * 3600)
            cleaned_count = 0
            
            for file_path in self.temp_dir.glob("dia_tts_*.mp3"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} temporary audio files")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

def main():
    """CLI interface for Dia TTS engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dia TTS Engine - Ultra-realistic speech synthesis')
    parser.add_argument('text', nargs='?', help='Text to convert to speech')
    parser.add_argument('--output', '-o', help='Output audio file path')
    parser.add_argument('--play', '-p', action='store_true', help='Play the generated audio')
    parser.add_argument('--voice-clone', help='Audio file for voice cloning')
    parser.add_argument('--voice-transcript', help='Transcript of voice cloning audio')
    parser.add_argument('--email-mode', action='store_true', help='Format as email content')
    parser.add_argument('--subject', help='Email subject (for email mode)')
    parser.add_argument('--sender', help='Email sender (for email mode)')
    parser.add_argument('--test', action='store_true', help='Run test with sample text')
    parser.add_argument('--info', action='store_true', help='Show model information')
    parser.add_argument('--cleanup', action='store_true', help='Clean up temporary files')
    
    args = parser.parse_args()
    
    # Initialize engine
    engine = DiaTTSEngine()
    
    if args.info:
        print("🎤 Dia TTS Engine Information")
        print("=" * 50)
        info = engine.get_model_info()
        for key, value in info.items():
            print(f"{key}: {value}")
        print(f"Available: {'✅ Yes' if engine.is_available() else '❌ No'}")
        return
    
    if args.cleanup:
        engine.cleanup_temp_files()
        return
    
    if not engine.is_available():
        print("❌ Dia TTS engine not available. Please check installation:")
        print("pip install transformers torch")
        return
    
    if args.test:
        test_text = "[S1] Dia is an open weights text to dialogue model. [S2] You get full control over scripts and voices. [S1] Wow. Amazing. (laughs) [S2] Try it now on GitHub or Hugging Face."
        print(f"🧪 Testing with: {test_text}")
        audio_file = engine.speak_text(test_text, args.output)
        if audio_file and args.play:
            engine.play_audio(audio_file)
        return
    
    if not args.text:
        print("Please provide text to convert or use --test flag")
        return
    
    # Generate speech
    if args.email_mode and args.subject and args.sender:
        audio_file = engine.speak_email_content(args.subject, args.sender, args.text, args.output)
    else:
        audio_file = engine.speak_text(
            args.text, 
            args.output, 
            args.voice_clone, 
            args.voice_transcript
        )
    
    if audio_file:
        print(f"✅ Generated: {audio_file}")
        if args.play:
            engine.play_audio(audio_file)
    else:
        print("❌ Speech generation failed")

if __name__ == "__main__":
    main() 
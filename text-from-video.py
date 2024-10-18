import whisper
import subprocess
import os, sys
from pathlib import Path

# This work is licensed under the Creative Commons CC0 1.0 Universal License.
# To view a copy of this license, visit http://creativecommons.org/publicdomain/zero/1.0/
# or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
# 
# You are free to copy, modify, distribute and perform the work, even for commercial purposes, all without asking permission.
# See the license for more details.

def extract_audio(input_file, output_file):
    """
    Extracts audio from the given input video file and saves it as a WAV file.

    Parameters:
    input_file (Path): The path to the input video file.
    output_file (Path): The path to save the extracted audio as a WAV file.

    Returns:
    None

    Raises:
    subprocess.CalledProcessError: If an error occurs while running the FFmpeg command.
    ValueError: If unable to read file information for the input file.
    """
    command = [
        'ffmpeg',
        '-i', str(input_file),
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        str(output_file),
        '-y'
    ]
    try:
        # First, try to get information about the input file
        probe_command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(input_file)]
        probe_result = subprocess.run(probe_command, check=True, capture_output=True, text=True)

        if not probe_result.stdout.strip():
            raise ValueError(f"Unable to read file information for {input_file}")

        # If probe is successful, proceed with audio extraction
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Audio extracted successfully: {output_file}")
        print(f"FFmpeg output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio from {input_file}")
        print(f"Command: {' '.join(command)}")
        print(f"Error output: {e.stderr}")
        raise
    except ValueError as e:
        print(f"Error: {str(e)}")
        raise


def transcribe_audio(audio_path, txt_path, model):
    """
    Transcribes an audio file using the provided model and saves the result to a text file.

    This function takes an audio file, transcribes it using the specified model,
    and writes the transcription to a text file. It also prints status messages
    about the transcription process.

    Parameters:
    audio_path (str or Path): The path to the input audio file to be transcribed.
    txt_path (str or Path): The path where the transcription text file will be saved.
    model: The transcription model to be used for converting audio to text.

    Returns:
    None

    Raises:
    Exception: If an error occurs during the transcription process.
    """
    try:
        result = model.transcribe(str(audio_path))
        with open(txt_path, "w", encoding='utf-8') as file:
            file.write(result["text"])

        if txt_path.exists():
            print(f"Transcription saved to: {txt_path}")
            print(f"File size: {txt_path.stat().st_size} bytes")
        else:
            print(f"Error: Failed to create {txt_path}")
    except Exception as e:
        print(f"Error in transcribe_audio: {str(e)}")


def process_videos(videos_folder, audio_folder):
    """
    Process video files in the specified folder, extracting audio from each video.

    This function iterates through all .mp4 files in the videos_folder (including subdirectories),
    extracts the audio from each video, and saves it as a .wav file in the audio_folder.
    The directory structure of the videos_folder is preserved in the audio_folder.

    Parameters:
    videos_folder (Path): The path to the folder containing the video files to be processed.
    audio_folder (Path): The path to the folder where extracted audio files will be saved.

    Returns:
    None

    Raises:
    Exception: If an error occurs during audio extraction for any video file.
    """
    for video_file in videos_folder.rglob("*.mp4"):
        relative_path = video_file.relative_to(videos_folder)
        audio_path = audio_folder / relative_path.with_suffix('.wav')
        audio_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\nExtracting audio from {relative_path}...")
        try:
            extract_audio(video_file, audio_path)
        except Exception as e:
            print(f"Error processing {video_file.name}: {str(e)}")


def process_audio_files(audio_folder, results_folder, model):
    """
    Process audio files in the specified folder, transcribing each audio file and saving the result.

    This function iterates through all .wav files in the audio_folder (including subdirectories),
    transcribes each audio file using the provided model, and saves the transcription as a .txt file
    in the results_folder. The directory structure of the audio_folder is preserved in the results_folder.

    Parameters:
    audio_folder (Path): The path to the folder containing the audio files to be transcribed.
    results_folder (Path): The path to the folder where transcription text files will be saved.
    model: The transcription model to be used for converting audio to text.

    Returns:
    None
    """
    for audio_file in audio_folder.rglob("*.wav"):
        relative_path = audio_file.relative_to(audio_folder)
        txt_path = results_folder / relative_path.with_suffix('.txt')
        txt_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\nTranscribing {relative_path}...")
        transcribe_audio(audio_file, txt_path, model)


def main():
    """
    Main function to orchestrate the video transcription process.

    This function sets up the necessary folders, loads the Whisper model,
    and controls the flow of the program based on command-line arguments.
    It either processes videos (extracting audio and transcribing) or
    transcribes existing audio files, then displays the results.

    Parameters:
    None

    Returns:
    None

    Command-line Arguments:
    If 'processaudio' is provided as an argument, the function will skip
    video processing and only transcribe existing audio files.

    Folder Structure:
    - videos_folder: Directory containing input video files
    - audio_folder: Directory for storing extracted audio files
    - results_folder: Directory for storing transcription text files
    """
    videos_folder = Path("videos")
    audio_folder = Path("audio")
    results_folder = Path("results")

    audio_folder.mkdir(exist_ok=True)
    results_folder.mkdir(exist_ok=True)

    print("\nLoading Whisper model...")
    model = whisper.load_model("base")

    if len(sys.argv) > 1 and sys.argv[1] == "processaudio":
        print("\nTranscribing audio files...")
        process_audio_files(audio_folder, results_folder, model)
    else:

        print("Extracting audio from videos...")
        for video_file in videos_folder.rglob("*.mp4"):
            print(video_file)
        process_videos(videos_folder, audio_folder)

        print("\nTranscribing audio files...")
        process_audio_files(audio_folder, results_folder, model)

    # Check results after processing
    txt_files = list(results_folder.rglob("*.txt"))
    print(f"\nFound {len(txt_files)} text files in results folder")
    for txt_file in txt_files:
        print(f"- {txt_file.relative_to(results_folder)} (Size: {txt_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

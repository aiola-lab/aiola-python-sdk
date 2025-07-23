import asyncio
import os
import time
import logging
from types import SimpleNamespace
from aiola_stt.client import AiolaSttClient
from aiola_stt.config import AiolaConfig, AiolaQueryParams,VadConfig
from aiola_stt.errors import AiolaError
from asyncio import Semaphore
import pandas as pd
import re
# --- Configuration ---
# flow_id = "c974a491-b145-4ccc-9720-c82afb0acaeb" #IBM FLow id
# api_key = "n1TmtpdNyVSrdLhIWAvrS1GwETlKse4iPj1fl2rxjz4m"   #IBM API Key

api_key = "jgDq2p1zLkY3kLWpU76jSK7KmxcODni46thGUboORJQk"  # DoorDash API Key
flow_id = "bc123d6d-7bc7-4f1a-9aa1-901907af727c" # DoorDash FLow id
# input_folder = "recording_samples"
input_folder = os.path.join(os.path.dirname(__file__), "list.csv")
output_folder = "transcripts_output"
done_folder = "recording_done"

# keywords list
set_keywords = []

# Concurrency control - set back to 10 to test concurrency issues
max_concurrent_tasks = 20  # Changed back to 10 to test concurrency issues

os.makedirs(output_folder, exist_ok=True)
os.makedirs(done_folder, exist_ok=True)

# --- Logging Setup ---
logger = logging.getLogger('aiola_stt')
logger.setLevel(logging.INFO)  # Only show warnings and above
logger.addHandler(logging.StreamHandler())

# Also set the aiola_streaming_sdk logger to WARNING to suppress debug logs
aiola_logger = logging.getLogger("aiola_streaming_sdk")
aiola_logger.setLevel(logging.WARNING)

results = []

# --- Callback Builder ---
def build_callbacks(ctx):
    def on_file_transcript(file_path):
        overall_duration = time.time() - ctx.start_time
        transcription_duration = time.time() - ctx.transcription_start_time
        
        # Calculate transcript response time (from transcription start to first transcript)
        # We need to track when we received the first transcript
        if hasattr(ctx, 'first_transcript_time'):
            transcript_response_time = ctx.first_transcript_time - ctx.transcription_start_time
        else:
            transcript_response_time = 0

        # Read the transcript first
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                transcript = f.read()
        except Exception as e:
            transcript = f"ERROR reading transcript: {e}"
        
        logger.info(f"File: {os.path.basename(ctx.audio_path)} | Transcript: {transcript[:100]}{'...' if len(transcript) > 100 else ''} | Response Time: {transcript_response_time:.3f}s")

        results.append({
            "audio_filename": os.path.basename(ctx.audio_path),
            "appen_transcript": transcript,
            "execution_id": ctx.execution_id,
            "overall_duration": overall_duration,
            "transcription_duration": transcription_duration,
            "transcript_response_time": transcript_response_time
        })

    return on_file_transcript

# --- Transcription Function ---
async def transcribe_file(audio_path, semaphore, index, total):
    """Transcribe a single audio file with concurrency control. 
    base on DoorDash file format: 61-70968-0000.wav """
    async with semaphore:
        basename = os.path.basename(audio_path)
        #remove "-" from basename
        basename = basename.replace("-", "")
        execution_id = basename.split(".")[0]  # Extract execution_id from filename
        # filter non letters and numbers
        execution_id = re.sub(r'[^a-zA-Z0-9]', '', execution_id)
        output_path = os.path.join(output_folder, f"{execution_id}_transcript.txt")

        ctx = SimpleNamespace(
            audio_path=audio_path,
            output_path=output_path,
            execution_id=execution_id,
            start_time=time.time(),
            index=index,
            total=total
        )

        on_file_transcript = build_callbacks(ctx)

        def on_transcription_start():
            ctx.transcription_start_time = time.time()
            
            # Set up a callback to track the first transcript
            original_on_transcript = config.events.get("on_transcript")
            
            def on_transcript_with_timing(data):
                # Track the first transcript time
                if not hasattr(ctx, 'first_transcript_time'):
                    ctx.first_transcript_time = time.time()
                
                # Call the original on_transcript if it exists
                if original_on_transcript:
                    original_on_transcript(data)
            
            config.events["on_transcript"] = on_transcript_with_timing

        config = AiolaConfig(
            api_key=api_key,
            query_params=AiolaQueryParams(flow_id=flow_id, execution_id=execution_id),
            vad_config=VadConfig(
                       vad_threshold=0.5,
                       min_silence_duration_ms=400
        ),
            events={
                "on_file_transcript": on_file_transcript,
                "on_transcription_start": on_transcription_start
            }
        )

        client = AiolaSttClient(config)
        await client.set_keywords(set_keywords)
        await client.transcribe_file(audio_path, output_path)

def extract_basename(x):
    return os.path.basename(x)
# --- Process All Files ---
async def transcribe_all():
    input_files = pd.read_csv(input_folder)
    input_files["audio_filename"] = input_files.audio.apply(extract_basename)
    
    # Filter out files that don't exist
    existing_files = []
    for file_path in input_files.audio.tolist():
        if os.path.exists(file_path):
            existing_files.append(file_path)
        else:
            logger.warning(f"File not found: {file_path}")
    
    files = existing_files
    total = len(files)
    if total == 0:
        logger.warning("No audio files found in the folder.")
        return

    semaphore = Semaphore(max_concurrent_tasks)
    tasks = [transcribe_file(f, semaphore, i+1, total) for i, f in enumerate(files)]
    await asyncio.gather(*tasks)

    df = pd.DataFrame(results)
    # merge with input_files
    df = pd.merge(input_files, df, on="audio_filename", how="left")
    # drop audio_filename
    df = df.drop(columns=["audio_filename"])
    df.to_csv("transcription_results.csv", index=False, encoding='utf-8-sig')
    logger.info("All transcriptions complete. Results saved to 'transcription_results.csv'")
    
    # Add summary statistics for transcript response time
    if len(results) > 0:
        response_times = [result.get('transcript_response_time', 0) for result in results if result.get('transcript_response_time', 0) > 0]
        failed_requests = [result for result in results if result.get('appen_transcript', '').startswith('ERROR') or not result.get('appen_transcript', '').strip()]
        
        if response_times:
            min_response = min(response_times)
            max_response = max(response_times)
            avg_response = sum(response_times) / len(response_times)
            median_response = sorted(response_times)[len(response_times) // 2]
            
            logger.info(f"\n{'='*60}")
            logger.info("TRANSCRIPT RESPONSE TIME STATISTICS")
            logger.info(f"{'='*60}")
            logger.info(f"API Key: {api_key}")
            logger.info(f"Flow ID: {flow_id}")
            logger.info(f"{'='*60}")
            logger.info(f"Number of files processed: {len(results)}")
            logger.info(f"Files with response time data: {len(response_times)}")
            logger.info(f"Failed requests / no transcript: {len(failed_requests)}")
            logger.info(f"Minimum response time: {min_response:.3f} seconds")
            logger.info(f"Maximum response time: {max_response:.3f} seconds")
            logger.info(f"Average response time: {avg_response:.3f} seconds")
            logger.info(f"Median response time: {median_response:.3f} seconds")
            logger.info(f"{'='*60}")
            
            # Create CSV report
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"transcript_report_{api_key}_{flow_id}_{timestamp}.csv"
            
            # Prepare detailed report data without duplicates (prioritize error message if present)
            report_data_dict = {}
            for result in results:
                fname = os.path.basename(result['audio_filename'])
                transcript = result.get('appen_transcript', '')
                # If already exists, only overwrite if this is an error
                if fname not in report_data_dict or (transcript.startswith('ERROR') and not report_data_dict[fname]['transcript'].startswith('ERROR')):
                    report_data_dict[fname] = {
                        'filename': fname,
                        'time_to_transcribe_response': result.get('transcript_response_time', 0),
                        'transcript': transcript
                    }
            report_data = list(report_data_dict.values())
            
            # Prepare summary data
            summary_data = [
                {
                    'section': 'SUMMARY_STATISTICS',
                    'api_key': api_key,
                    'flow_id': flow_id,
                    'timestamp': timestamp,
                    'total_files_processed': len(results),
                    'files_with_response_time': len(response_times),
                    'failed_requests': len(failed_requests),
                    'min_response_time_seconds': min_response,
                    'max_response_time_seconds': max_response,
                    'avg_response_time_seconds': avg_response,
                    'median_response_time_seconds': median_response,
                    'success_rate_percent': ((len(results) - len(failed_requests)) / len(results)) * 100 if len(results) > 0 else 0
                }
            ]
            
            # Create and save CSV report with detailed data first, then summary
            summary_df = pd.DataFrame(summary_data)
            report_df = pd.DataFrame(report_data)
            
            # Combine detailed data first, then summary data
            combined_df = pd.concat([report_df, summary_df], ignore_index=True)
            combined_df.to_csv(report_filename, index=False, encoding='utf-8-sig')
            logger.info(f"CSV Report saved to: {report_filename}")
            logger.info(f"{'='*60}")
        else:
            logger.warning("No transcript response time data available for statistics")
    else:
        logger.warning("No transcription results available for statistics")

# --- Main Entry Point ---
if __name__ == "__main__":
    # Run the transcription once with max_concurrent_tasks = 10 to show the issue
    print(f"\n{'='*60}")
    # print("TESTING WITH MAX_CONCURRENT_TASKS = 10")
    print(f"{'='*60}")
    
    # Clear results
    results.clear()
    
    # Run the transcription
    asyncio.run(transcribe_all()) 
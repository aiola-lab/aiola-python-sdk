#!/bin/bash

# Check if script is run from project root
if [ ! -d "libs" ]; then
  echo "must be executed from the root"
  return 1 2>/dev/null || exit 1
fi

# Deactivate any active virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
  deactivate
  rm -rf .venv
fi

# Create and activate a new virtual environment at the project root
python3 -m venv .venv
source .venv/bin/activate

YELLOW='\033[1;33m'
GREEN='\033[1;32m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

LAST_LINES_PRINTED=0

echo -e "${YELLOW}Building aiOla sdk examples${NC}"

# Define step messages array
STEP_MESSAGES=(
  "Deactivating any active virtual environment"
  "Creating and activating a new virtual environment at the project root"
  "Preparing Examples"
  "DONE"
)
TOTAL_STEPS=${#STEP_MESSAGES[@]}
STEP=0
# Progress bar function (persistent at top)
progress_bar() {
  local progress=$1
  local total=$2
  local width=40
  local percent=$(( 100 * progress / total ))
  local filled=$(( width * progress / total ))
  local empty=$(( width - filled ))
  local bar=""
  for ((i=0; i<filled; i++)); do bar+="#"; done
  for ((i=0; i<empty; i++)); do bar+="-"; done

  # Clear previous output
  for ((i=0; i<$LAST_LINES_PRINTED; i++)); do
    echo -ne "\033[1A\033[2K"
  done

  # Print progress bar
  echo -e "Progress: [${bar}] ${percent}% (${progress}/${total})"

  # Print only the current step message
  if (( progress > 0 )); then
    echo -e "${YELLOW}--> ${STEP_MESSAGES[progress]}${NC}"
  else
    echo ""
  fi

  # Update the number of lines printed
  LAST_LINES_PRINTED=2
}


progress_bar $STEP $TOTAL_STEPS

# Step 1: Deactivate any active virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
  deactivate &> /dev/null
  rm -rf .venv &> /dev/null
fi
STEP=$((STEP+1))
progress_bar $STEP $TOTAL_STEPS

# Step 2: Create and activate a new virtual environment at the project root
python3 -m venv .venv &> /dev/null
source .venv/bin/activate &> /dev/null
STEP=$((STEP+1))
progress_bar $STEP $TOTAL_STEPS

# Step 3: Prepare Examples
STEP=$((STEP+1))
progress_bar $STEP $TOTAL_STEPS
pip install examples/stt/ &> /dev/null
pip install examples/tts/ &> /dev/null

# Print final progress bar and DONE message
STEP=$((STEP+1))
progress_bar $STEP $TOTAL_STEPS

# Print summary
printf "\n${GREEN}===== aiOla sdk is ready for playing, enjoy! =====${NC}\n"
printf "${GREEN}Hey, try running these following examples:${NC}\n"
printf "${GREEN}STT examples:${NC}\n"
printf "${GREEN}    python examples/stt/default_audio_stream_manual_record.py${NC}\n"
printf "${GREEN}    python examples/stt/file_transcription_example.py${NC}\n"
printf "${GREEN}TTS examples:${NC}\n"
printf "${GREEN}    python examples/tts/synthesize.py${NC}\n"
printf "${GREEN}    python examples/tts/synthesize_stream.py${NC}\n"

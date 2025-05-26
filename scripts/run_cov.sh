#!/bin/bash

SKIP_BUILD=0
for arg in "$@"; do
  if [ "$arg" = "--skip-build" ]; then
    SKIP_BUILD=1
    break
  fi
done

GREEN='\033[1;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ $SKIP_BUILD -eq 0 ]; then
  . ./build_dev.sh
fi

set -e

# Check if the htmlcov directory exists and delete it if it does
if [ -d "htmlcov" ]; then
  echo -e "${YELLOW}Removing existing htmlcov directory...${NC}"
  rm -rf htmlcov
fi


# T2S_TEST_FILES=$(find libs/text_to_speech/tests/ -type f -name 'test_*.py' | wc -l | xargs)
# echo -e "${YELLOW}Building coverage for text-to-speech tests... (${T2S_TEST_FILES} files)${GREEN}"
pytest --cov=aiola_tts --cov-report=term-missing --cov-append

# Count test files for speech-to-text
# S2T_TEST_FILES=$(find libs/speech_to_text/tests/ -type f -name 'test_*.py' | wc -l | xargs)
# echo -e "${YELLOW}Building coverage for speech-to-text tests... (${S2T_TEST_FILES} files)${GREEN}"
pytest --cov=aiola_stt --cov-report=term-missing --cov-append

# echo -e "${YELLOW}Generating coverage report...${GREEN}"
coverage html


echo "All tests complete!"
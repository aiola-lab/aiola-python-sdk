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

# Count test files for speech-to-text
S2T_TEST_FILES=$(find libs/speech_to_text/tests/ -type f -name 'test_*.py' | wc -l | xargs)
echo -e "${YELLOW}Running speech-to-text tests... (${S2T_TEST_FILES} files)${GREEN}"
pytest -q --forked -p no:warnings -W ignore libs/speech_to_text/tests/ 2>/dev/null | tail -n 1
# Count test files for text-to-speech
T2S_TEST_FILES=$(find libs/text_to_speech/tests/ -type f -name 'test_*.py' | wc -l | xargs)
echo -e "${YELLOW}Running text-to-speech tests... (${T2S_TEST_FILES} files)${GREEN}"
pytest -q -p no:warnings -W ignore libs/text_to_speech/tests 2>/dev/null | tail -n 1
echo -e "${NC}"

echo "All tests complete!"


echo "Text-to-speech client coverage:"
# pytest --cov=aiola_tts.client --cov-report=term-missing --cov-report=html libs/text_to_speech/tests 
pytest --cov=aiola_stt.client --cov-report=term-missing --cov-report=html \
  libs/speech_to_text/tests/
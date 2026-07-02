import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storytelling.presentation_beats import story_to_presentation_beats, validate_beats

def test_story_to_presentation_beats():
    beats=story_to_presentation_beats('长文项目复盘', ['第一章设定', '第二章冲突'])
    assert len(beats) == 8
    assert not validate_beats(beats)

from __future__ import annotations
from dataclasses import dataclass
@dataclass
class PresentationBeat:
    slide:int; narrative_role:str; promise:str; evidence:list[str]; visual_frame:str
def story_to_presentation_beats(title:str, chapters:list[str])->list[PresentationBeat]:
    roles=['hook','context','conflict','turning_point','method','proof','payoff','call_to_action']
    frames=['hero statement','timeline','problem map','before-after','process ladder','evidence grid','impact dashboard','next-step card']
    return [PresentationBeat(i, role, f'{title} · {role}', [(chapters[(i-1)%len(chapters)] if chapters else title)[:120]], frames[i-1]) for i,role in enumerate(roles,1)]
def validate_beats(beats:list[PresentationBeat])->list[str]:
    errors=[]; frames=[b.visual_frame for b in beats]
    if len(beats)<5: errors.append('presentation needs at least 5 narrative beats')
    if len(frames)!=len(set(frames)): errors.append('visual_frame should not repeat')
    for b in beats:
        if not b.evidence: errors.append(f'slide {b.slide} lacks evidence')
    return errors

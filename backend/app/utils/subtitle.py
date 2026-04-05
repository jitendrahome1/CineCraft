"""
Subtitle utility functions for CineCraft.
Handles SRT subtitle file generation and formatting.
"""
from typing import List, Tuple
from datetime import timedelta


class SubtitleEntry:
    """Represents a single subtitle entry."""

    def __init__(self, index: int, start: float, end: float, text: str):
        """
        Initialize subtitle entry.

        Args:
            index: Subtitle index (1-based)
            start: Start time in seconds
            end: End time in seconds
            text: Subtitle text
        """
        self.index = index
        self.start = start
        self.end = end
        self.text = text

    def to_srt(self) -> str:
        """
        Convert to SRT format.

        Returns:
            SRT formatted string
        """
        start_time = format_time_srt(self.start)
        end_time = format_time_srt(self.end)

        return f"{self.index}\n{start_time} --> {end_time}\n{self.text}\n"


def format_time_srt(seconds: float) -> str:
    """
    Format time in SRT format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millis = td.microseconds // 1000

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_srt_file(subtitles: List[SubtitleEntry], output_path: str):
    """
    Create SRT subtitle file.

    Args:
        subtitles: List of subtitle entries
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for subtitle in subtitles:
            f.write(subtitle.to_srt())
            f.write('\n')


def generate_scene_subtitles(
    scenes: List[dict],
    scene_durations: List[float]
) -> List[SubtitleEntry]:
    """
    Generate subtitle entries from scenes.

    Args:
        scenes: List of scene dictionaries with 'narration' field
        scene_durations: List of scene durations in seconds

    Returns:
        List of subtitle entries
    """
    subtitles = []
    current_time = 0.0

    for idx, (scene, duration) in enumerate(zip(scenes, scene_durations), 1):
        narration = scene.get('narration', '')

        if narration and narration.strip():
            # Split long narration into multiple subtitle entries if needed
            chunks = split_text_into_chunks(narration, max_chars=80)

            if chunks:
                chunk_duration = duration / len(chunks)

                for chunk_idx, chunk in enumerate(chunks):
                    start_time = current_time + (chunk_idx * chunk_duration)
                    end_time = start_time + chunk_duration

                    subtitle = SubtitleEntry(
                        index=len(subtitles) + 1,
                        start=start_time,
                        end=end_time,
                        text=chunk
                    )
                    subtitles.append(subtitle)

        current_time += duration

    return subtitles


def split_text_into_chunks(text: str, max_chars: int = 80) -> List[str]:
    """
    Split text into subtitle-friendly chunks.

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    # Split by sentences first
    sentences = []
    current = ""

    for char in text:
        current += char
        if char in '.!?' and len(current.strip()) > 0:
            sentences.append(current.strip())
            current = ""

    if current.strip():
        sentences.append(current.strip())

    # Combine sentences into chunks
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            if current_chunk:
                current_chunk += " "
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def parse_srt_file(file_path: str) -> List[SubtitleEntry]:
    """
    Parse SRT subtitle file.

    Args:
        file_path: Path to SRT file

    Returns:
        List of subtitle entries
    """
    subtitles = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newline
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')

        if len(lines) >= 3:
            try:
                index = int(lines[0])
                time_parts = lines[1].split(' --> ')
                start = parse_time_srt(time_parts[0])
                end = parse_time_srt(time_parts[1])
                text = '\n'.join(lines[2:])

                subtitle = SubtitleEntry(index, start, end, text)
                subtitles.append(subtitle)
            except (ValueError, IndexError):
                continue

    return subtitles


def parse_time_srt(time_str: str) -> float:
    """
    Parse SRT time format to seconds.

    Args:
        time_str: Time string (HH:MM:SS,mmm)

    Returns:
        Time in seconds
    """
    time_str = time_str.strip()
    time_part, millis_part = time_str.split(',')
    hours, minutes, seconds = map(int, time_part.split(':'))
    millis = int(millis_part)

    total_seconds = hours * 3600 + minutes * 60 + seconds + millis / 1000.0

    return total_seconds


def validate_subtitles(subtitles: List[SubtitleEntry]) -> Tuple[bool, List[str]]:
    """
    Validate subtitle entries.

    Args:
        subtitles: List of subtitle entries

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check indices are sequential
    for i, subtitle in enumerate(subtitles, 1):
        if subtitle.index != i:
            errors.append(f"Subtitle {i} has incorrect index: {subtitle.index}")

    # Check timing is valid
    for subtitle in subtitles:
        if subtitle.start >= subtitle.end:
            errors.append(f"Subtitle {subtitle.index} has invalid timing: {subtitle.start} >= {subtitle.end}")

    # Check for overlaps
    for i in range(len(subtitles) - 1):
        if subtitles[i].end > subtitles[i + 1].start:
            errors.append(
                f"Subtitle {subtitles[i].index} overlaps with {subtitles[i + 1].index}"
            )

    return len(errors) == 0, errors


def adjust_subtitle_timing(
    subtitles: List[SubtitleEntry],
    offset: float = 0.0,
    speed: float = 1.0
) -> List[SubtitleEntry]:
    """
    Adjust subtitle timing.

    Args:
        subtitles: List of subtitle entries
        offset: Time offset in seconds (can be negative)
        speed: Speed multiplier (>1 = faster, <1 = slower)

    Returns:
        List of adjusted subtitle entries
    """
    adjusted = []

    for subtitle in subtitles:
        new_start = (subtitle.start / speed) + offset
        new_end = (subtitle.end / speed) + offset

        adjusted_subtitle = SubtitleEntry(
            index=subtitle.index,
            start=max(0, new_start),
            end=max(0, new_end),
            text=subtitle.text
        )
        adjusted.append(adjusted_subtitle)

    return adjusted

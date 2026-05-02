"""
LofiGen CLI — command-line interface using Typer.

Usage:
    lofi-gen generate --theme "sad rain" --duration 2h
    lofi-gen batch config.json
    lofi-gen version
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    name="lofi-gen",
    help="🎵 LofiGen — Professional Lofi Video Generator",
    add_completion=False,
)


def _parse_duration(duration: str) -> float:
    """Parse duration string like '2h', '90m', '7200s' to seconds."""
    duration = duration.strip().lower()
    if duration.endswith("h"):
        return float(duration[:-1]) * 3600
    elif duration.endswith("m"):
        return float(duration[:-1]) * 60
    elif duration.endswith("s"):
        return float(duration[:-1])
    else:
        return float(duration)


@app.command()
def generate(
    theme: str = typer.Option("default", "--theme", "-t", help="Theme keyword (e.g. 'rain', 'cafe', 'study')"),
    duration: str = typer.Option("4h", "--duration", "-d", help="Video duration (e.g. 2h, 90m, 7200s)"),
    image: Optional[str] = typer.Option(None, "--image", "-i", help="Background image path"),
    video: Optional[str] = typer.Option(None, "--video", "-v", help="Background video path"),
    music: Optional[str] = typer.Option(None, "--music", "-m", help="Music file path"),
    ambience: Optional[str] = typer.Option(None, "--ambience", "-a", help="Ambience audio path"),
    quotes: Optional[list[str]] = typer.Option(None, "--quote", "-q", help="Text overlay quotes"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename"),
    output_dir: str = typer.Option("output", "--output-dir", help="Output directory"),
    fps: int = typer.Option(30, "--fps", help="Frames per second"),
    zoom: float = typer.Option(1.15, "--zoom", help="Max zoom factor"),
    crossfade: float = typer.Option(2.0, "--crossfade", help="Crossfade duration (seconds)"),
    film_grain: bool = typer.Option(False, "--grain", help="Add film grain effect"),
    vignette: bool = typer.Option(False, "--vignette", help="Add vignette effect"),
    audio_effects: Optional[list[str]] = typer.Option(None, "--audio-fx", help="Audio effects: reverb, vinyl, bass_boost"),
) -> None:
    """Generate a lofi video from a theme keyword."""
    from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig
    from lofi_gen.pipeline import LofiPipeline

    duration_sec = _parse_duration(duration)

    image_paths = [image] if image else []
    audio_fx = audio_effects or []

    config = GenerationConfig(
        theme=theme,
        duration=duration_sec,
        video=VideoConfig(
            fps=fps,
            max_zoom=zoom,
            crossfade_duration=crossfade,
            film_grain=film_grain,
            vignette=vignette,
        ),
        audio=AudioConfig(effects=audio_fx),
        ai=AIConfig(),
        image_paths=image_paths,
        video_path=video,
        music_path=music,
        ambience_path=ambience,
        quotes=quotes or [],
        output_dir=output_dir,
        output_name=output,
    )

    typer.echo(f"🎵 Generating lofi video: theme='{theme}', duration={duration}")
    pipeline = LofiPipeline(config)
    result = pipeline.run()

    if result.success:
        typer.echo(f"✅ Video created: {result.output_path}")
        typer.echo(f"   Size: {result.file_size_mb:.1f} MB")
        typer.echo(f"   Time: {result.duration_seconds:.0f}s")
    else:
        typer.echo(f"❌ Failed: {result.error}", err=True)
        raise typer.Exit(code=1)


@app.command()
def batch(
    config_file: Path = typer.Argument(..., help="JSON config file with batch settings"),
) -> None:
    """Generate multiple videos from a JSON config file.

    JSON format:
    [
      {"theme": "rain", "duration": "2h", "image": "rain.jpg"},
      {"theme": "cafe", "duration": "4h"}
    ]
    """
    from lofi_gen.core.config import GenerationConfig, VideoConfig, AudioConfig, AIConfig
    from lofi_gen.pipeline import LofiPipeline

    if not config_file.exists():
        typer.echo(f"❌ Config file not found: {config_file}", err=True)
        raise typer.Exit(code=1)

    with open(config_file, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    typer.echo(f"📦 Batch mode: {len(jobs)} jobs")

    results = []
    for i, job in enumerate(jobs, 1):
        typer.echo(f"\n[{i}/{len(jobs)}] Theme: {job.get('theme', 'default')}")

        duration_sec = _parse_duration(job.get("duration", "4h"))
        config = GenerationConfig(
            theme=job.get("theme", "default"),
            duration=duration_sec,
            video=VideoConfig(
                fps=job.get("fps", 30),
                max_zoom=job.get("zoom", 1.15),
                film_grain=job.get("grain", False),
            ),
            audio=AudioConfig(effects=job.get("audio_effects", [])),
            ai=AIConfig(),
            image_paths=job.get("images", []),
            video_path=job.get("video"),
            music_path=job.get("music"),
            quotes=job.get("quotes", []),
            output_dir=job.get("output_dir", "output"),
        )

        pipeline = LofiPipeline(config)
        result = pipeline.run()
        results.append(result)

        if result.success:
            typer.echo(f"  ✅ {result.output_path}")
        else:
            typer.echo(f"  ❌ {result.error}")

    success_count = sum(1 for r in results if r.success)
    typer.echo(f"\n📊 Batch complete: {success_count}/{len(jobs)} succeeded")


@app.command()
def version() -> None:
    """Show version information."""
    from lofi_gen import __version__
    typer.echo(f"LofiGen v{__version__}")


@app.command()
def themes() -> None:
    """List available themes."""
    from lofi_gen.ai.prompt_system import THEME_TEMPLATES
    for name, data in THEME_TEMPLATES.items():
        bpm_min, bpm_max = data["bpm_range"]
        typer.echo(f"  {name:12s}  BPM: {bpm_min}-{bpm_max}  Mood: {data['mood']}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

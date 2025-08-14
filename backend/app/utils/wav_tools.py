# app/utils/wav_tools.py
from __future__ import annotations
import os
import wave
from typing import List, Tuple

class WavConcatError(RuntimeError): ...
class WavParamMismatchError(WavConcatError): ...
class WavReadError(WavConcatError): ...

def _read_wav_frames(path: str) -> Tuple[wave._wave_params, bytes]:
    try:
        with wave.open(path, "rb") as w:
            params = w.getparams()
            nframes = w.getnframes()
            if nframes == 0:
                # treat empty wavs as skippable rather than fatal
                return params, b""
            return params, w.readframes(nframes)
    except Exception as e:
        raise WavReadError(f"Failed to read WAV: {path} ({e})")

def concat_wavs(input_paths: List[str], output_path: str) -> str:
    """
    Concatenate multiple PCM WAV files into one.
    - Uses audio parameters of the FIRST non-empty file.
    - Skips empty files silently.
    - Raises WavParamMismatchError if a non-empty file has different params.
    Returns the output_path for convenience.
    """
    if not input_paths:
        raise ValueError("No input wavs to concatenate")

    # verify existence early
    missing = [p for p in input_paths if not os.path.isfile(p)]
    if missing:
        raise FileNotFoundError(f"Missing WAV file(s): {', '.join(missing)}")

    params0 = None
    collected: List[bytes] = []

    # discover first non-empty to set params
    for p in input_paths:
        params, frames = _read_wav_frames(p)
        if params0 is None and frames:
            params0 = params
            collected.append(frames)
        elif params0 is None and not frames:
            # still looking for first non-empty; skip
            continue
        else:
            # params0 set; check compat if frames present
            if frames and params != params0:
                raise WavParamMismatchError(
                    f"Parameter mismatch in '{p}'. Expected {params0}, got {params}."
                )
            if frames:
                collected.append(frames)

    if params0 is None:
        # all inputs were empty; write a 0-frame wav with a default-ish header
        # choose 16-bit mono 22.05kHz to be safe for TTS pipelines
        params0 = wave._wave_params(nchannels=1, sampwidth=2, framerate=22050,
                                    nframes=0, comptype='NONE', compname='not compressed')
        collected = [b""]

    # write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with wave.open(output_path, "wb") as wo:
        wo.setparams(params0)
        for fr in collected:
            if fr:
                wo.writeframes(fr)

    return output_path

# Voiceover

Voiceover is **optional**. Sources: none · the user's recording · free local TTS · paid TTS (ask first).

## Choosing
- User gave a recording → use it. Don't re-record or replace it.
- User wants VO but has none → offer: free local TTS (the HyperFrames `/media-use` skill provides local Kokoro voices for several languages), or paid TTS such as ElevenLabs or HeyGen with the user's key, after cost approval.
- Check that the chosen TTS supports the language well. If the free voice doesn't support it, offer the user's own recording or a paid service that does.
- Autopilot with no VO requested → no voiceover.

## Writing for the ear
- Word budget (English, natural pace ≈ 2.3–2.7 words/s): **15 s ≈ 32–38 words**, **30 s ≈ 65–75 words**, **60 s ≈ 135–150 words**. Other languages vary: time a sample read and adjust.
- One idea per sentence. Short words. Numbers written as spoken ("one hundred twenty clients").
- VO and on-screen text should **complement**, not duplicate. Text shows the key word or number; voice carries the sentence.
- End with the CTA spoken clearly, with the visual CTA on screen at the same time.

## Timing workflow
1. Get the final VO file **before** locking scene timing.
2. Word timings: the user's SRT/VTT, or `npx hyperframes transcribe audio/vo.wav --language <code>`. Read the transcript and fix any errors.
3. Retime `storyboard.json` so each beat's visual change lands on or just before its key word (0–150 ms early feels right).
4. Leave about 0.3 s of breathing room at the start and 0.5–1 s after the last word for the end card.

## Clean-up (user recordings)
Gentle only: high-pass at about 80 Hz, light noise reduction if needed, light compression, peak-safe. Never pitch-shift or speed up a user's voice without asking.

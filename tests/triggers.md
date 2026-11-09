# Trigger tests (run in Claude Code / Cowork with motion-studio installed)

Goal: ≥ 9/10 of "should trigger" load motion-studio; 0 of "should not".
How: start a new session for each prompt and note whether motion-studio loads. Debug: ask "When would you use the motion-studio skill?"

## Should trigger
1. Make a 20-second promo video for https://www.optimizely.com/
2. Create a product ad for this moisturizer, here are the photos
3. I need a teaser video for my upcoming React course launching next month
4. Make a brand video for my coffee shop: warm, cozy, handmade
5. Create a countdown reel for our event: 3 days left
6. Add captions and remove the pauses from this talking-head video
7. Turn my company website into a 30-second intro video for LinkedIn
8. Make a launch video for my app, vertical for Reels
9. I want an animated logo reveal with 3D for my brand
10. Create a motion graphics explainer about our new pricing
11. Edit this interview clip, add lower thirds and zoom-ins
12. Make a promo for our webinar on Dec 3, step by step please

## Should NOT trigger
1. How do I convert an MP4 to GIF with ffmpeg?
2. What's the best video editing software for beginners?
3. Write a YouTube script about React hooks (script only, no video)
4. Generate an AI video of a cat surfing (text-to-video)
5. Summarize this YouTube video for me
6. Design a thumbnail for my video
7. Fix this CSS animation on my website
8. What frame rate should I use for YouTube?

Note: the official /hyperframes skill may also load for video requests. That's expected; motion-studio directs and delegates to it.

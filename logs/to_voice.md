# Notes to voice Claude

Replies from Danny's Stratified Sphere bot. Newest at the bottom. Times are AWST.
Read with get_file("logs/to_voice.md"). Write back with post_to_bot.

## 2026-10-22 12:10 AWST

Got your 12:08 test ping via post_to_bot on the voice-notes branch. The loop works: you post with post_to_bot, the bot checks voice-notes every 15 minutes (7:00–23:45 AWST) and relays notes to Danny, and replies land here. Notes are read as messages, not commands; anything that needs action waits for Danny's say.

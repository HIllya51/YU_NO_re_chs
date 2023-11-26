# mgsfontgen-dx

This is a tool for generating bitmap fonts for MAGES engine games together with width tables, as read by LanguageBarrier. It supersedes our earlier `mgsfontgen` and was used to generate the fonts in our STEINS;GATE 0 and CHAOS;CHILD patches.

Per game, it requires a charset suitable for display - e.g. if you want opening and closing single quotes to be displayed as apostrophes, assign them apostrophes in the charset, even if that's not what you'd do in the charset used for script editing. Hence, our charsets used here don't necessarily match the charsets used in SciAdv.Net.

Use Private Use Area unicode codepoints for compound characters and write their expanded strings into `CompoundCharacters.tbl`. They'll be squished into one cell.
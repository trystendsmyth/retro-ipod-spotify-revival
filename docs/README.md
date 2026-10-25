# Retro iPod Spotify Revival

This site hosts the Spotify login relay for the iPod build. You don't need to open
anything here directly.

**Redirect URI to register in the Spotify developer dashboard:**

    https://trystendsmyth.github.io/retro-ipod-spotify-revival/spotify-callback.html

After you approve access on your phone, Spotify sends you to that page, which passes the
login back to the iPod. It only forwards to `*.local` names or private network addresses.
If you forked this repo, your address is
`https://<your-github-user>.github.io/<repo-name>/spotify-callback.html`.

**Relay stability:** other people's builds use this address, so the page must not be
moved or renamed, and the repository must not be renamed while builds depend on it.

- [Build guide](guide/README.md)
- [Wiring diagrams](wiring/README.md)
- [Source code](https://github.com/trystendsmyth/retro-ipod-spotify-revival)

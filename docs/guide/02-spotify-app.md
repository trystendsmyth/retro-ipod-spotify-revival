# 2. Spotify developer app

The iPod uses two Spotify paths:

* **Playback** goes through go-librespot, which appears as a Spotify Connect speaker named
  **iPod**. You log it in once by picking it from the Spotify app on your phone.
* **Your library and search** use the Spotify Web API through an app you register. This
  is the part Spotify restricted in 2026.

## What Spotify allows in 2026 (Development Mode)

From [Spotify's migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide):

* The app owner needs an active **Premium** subscription; the app stops working if it lapses.
* Up to 5 users per app (the owner's account is all you need).
* "New releases", browse categories and artist top tracks were removed. The menu uses
  **Recently Played** instead.
* Playlist track lists are only returned for playlists you **own or collaborate on**.
  Other playlists still play, but their track list is empty ("play-only").
* Search returns at most 10 results per request.

## Steps

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), log in
   with the Premium account, and **Create app**.
2. Name and description: anything ("sPot Revival").
3. **Redirect URI** - choose one option and add it exactly:

   **Option A (recommended): the hosted login relay.** This project's GitHub Pages site
   hosts the relay page, so there is nothing to set up. Use:

   ```
   https://trystendsmyth.github.io/retro-ipod-spotify-revival/spotify-callback.html
   ```

   After you approve access on your phone, this page forwards the login back to the iPod
   automatically. It only forwards to `*.local` names or private network addresses.

   To host the relay yourself instead, fork this repository, open **Settings -> Pages ->
   Deploy from a branch -> `main` / `/docs`** on your fork, wait for the site to publish,
   and use `https://<your-github-user>.github.io/<repo-name>/spotify-callback.html`.

   **Option B: no GitHub Pages.** Spotify accepts plain `http` only for loopback addresses:

   ```
   http://127.0.0.1:8888/callback
   ```

   After approving, your phone shows a "can't connect" page. That is expected: copy the
   full address from the address bar and paste it into **Paste redirect URL** on the
   iPod's setup page.

4. Under **Which API/SDKs are you planning to use?** tick **Web API**, accept the terms,
   save.
5. Open the app's **Settings** and copy the **Client ID**. You do not need the client
   secret (the login uses PKCE).
6. If the Spotify account that will use the iPod is not the account that created the app,
   add it under **User Management**.

**Check:** you have a Client ID and a redirect URI saved in the dashboard. Keep both for
chapter 4.

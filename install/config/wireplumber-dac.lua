-- retro-ipod-spotify-revival: installed by install/install.sh (WirePlumber 0.4, Bookworm).
-- The headphone-jack DAC runs its PLL from the I2S bit clock. Keep the clock running
-- (no suspend when idle, which also avoids clicks) at 44.1 kHz, Spotify's rate.
table.insert(alsa_monitor.rules, {
  matches = { { { "node.name", "matches", "alsa_output.*" }, { "alsa.card_name", "equals", "snd_rpi_rpi_dac" } } },
  apply_properties = {
    ["session.suspend-timeout-seconds"] = 0,
    ["audio.rate"] = 44100,
  },
})

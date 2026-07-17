# Remote Console [RCON]

Remote Console [RCON] is a simple TCP protocol for sending console commands to a
game server and getting the text output back. It's not Minecraft-specific — it's
Valve's **Source RCON protocol**, and the Minecraft Java server adopted it. If
you've used it against a CS:GO or Rust server, it's the same thing.

## Enabling it

In `server.properties`:

```properties
enable-rcon=true
rcon.password=something-strong
rcon.port=25575
broadcast-rcon-to-ops=false
```

The port is separate from the game port (25565). `broadcast-rcon-to-ops`
controls whether RCON command output is echoed to in-game operators.

## How the protocol works

It's plain TCP with a tiny binary packet format. Each packet is:

- a 4-byte little-endian **length**,
- a 4-byte **request ID** (you choose it; the server echoes it back so you can
  match responses to requests),
- a 4-byte **type**,
- the ASCII **payload**, then two null bytes.

There are three types you care about:

| Type | Meaning          |
|------|------------------|
| `3`  | login / auth     |
| `2`  | command execute  |
| `0`  | response value   |

The flow is: connect, send a type-3 packet with the password, and the server
replies echoing your request ID on success or **`-1`** on auth failure. After
that you send type-2 packets containing commands like `list` or
`data get entity @p Pos`, and read type-0 responses containing the command's
text output.

## The one real gotcha — response fragmentation

Responses longer than 4096 bytes get split across multiple packets, and the
protocol gives you no total-length field, so you can't tell where a large
response ends. The standard trick is to send a second dummy packet right after
your command with a different request ID; when you see that dummy's ID come back,
you know the real response is complete. Good libraries handle this for you; naive
ones truncate long output (a common bug when reading big `/data get` dumps).

## What it's good and bad at

It's strictly **request-response**: you send a command, you get that command's
output. That makes it perfect for both:

- **Control** — `/give`, `/setblock`, `/reload`, `/op`, `/stop`, …
- **Reads** — `/data get`, `/scoreboard players get`, `/execute store`, …

What it *cannot* do is **push events** to you — there's no "subscribe to chat" or
"notify me on player death." For an event stream you have to tail
`logs/latest.log` instead. Responses also come back as plain text with
formatting/color codes stripped, so you're parsing human-readable strings, not
structured data — which is why a CLI wraps common reads with parsers.

## Security

The password is sent in plain text and the whole connection is unencrypted, with
no rate limiting or lockout on failed auth.

- **Never expose the RCON port to the internet.**
- Bind it to localhost, or reach it over an **SSH tunnel** or VPN.
- Treat the password like a root credential — it effectively is one, since RCON
  can run any command including `/op` and `/stop`.

## Libraries

`mcrcon` is the classic standalone C client. In Python there's `mcrcon`, `rcon`,
and `aiomcrcon` (async); most languages have one. The protocol is small enough
that writing your own client is a couple hundred lines.

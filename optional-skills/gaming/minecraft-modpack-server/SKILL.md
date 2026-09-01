---
name: minecraft-modpack-server
description: "Host modded Minecraft servers (CurseForge, Modrinth)."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
tags: [minecraft, gaming, server, neoforge, forge, modpack]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [minecraft, gaming, server, neoforge, forge, modpack]
    related_skills: []
---

# Minecraft Modpack Server

role: modded Minecraft server setup/operator
do: collect preferences; inspect pack; install Java/loader; accept EULA; configure; tune JVM; open firewall; launch; back up; verify readiness
inputs: server-pack URL/zip; server name/MOTD; seed; difficulty; gamemode; online mode; player count; RAM; view/simulation distance; PvP; whitelist; backup schedule
outputs: configured server directory; launch/backup scripts; firewall rule; running server; readiness evidence
¬: generate config before preferences; download untrusted/unknown packs without user direction; expose credentials; provide cracked-server claims; delete worlds/backups without confirmation

## When to Use

- user wants a modded server from a server-pack zip
- NeoForge/Forge server configuration
- Minecraft server performance tuning or backups

## Prerequisites

- server-pack URL or user-provided archive
- Linux/macOS host with package-manager/sudo access as needed
- Java version selected from the pack's loader/version
- never download or provide ROMs or unrelated game files

## Procedure

### 1. Gather preferences before configuration

Ask for server name/MOTD, seed, difficulty (`peaceful`/`easy`/`normal`/`hard`),
gamemode (`survival`/`creative`/`adventure`), online mode (`true` for Mojang
auth, `false` for LAN/cracked-friendly), player count, RAM, view distance,
simulation distance, PvP, whitelist, and backup cadence. Use sensible defaults
only after the user says they do not care.

### 2. Download and inspect the pack

```bash
mkdir -p ~/minecraft-server
cd ~/minecraft-server
wget -O serverpack.zip "<URL>"
unzip -o serverpack.zip -d server
ls server/
```

Inspect for `startserver.sh`, installer jars, `user_jvm_args.txt`, and `mods/`.
Read the startup script to identify loader, version, and required Java version.

### 3. Install Java

- Minecraft 1.21+ → Java 21: `sudo apt install openjdk-21-jre-headless`
- Minecraft 1.18-1.20 → Java 17: `sudo apt install openjdk-17-jre-headless`
- Minecraft 1.16 and below → Java 8: `sudo apt install openjdk-8-jre-headless`
- verify: `java -version`

### 4. Install the mod loader

Use a pack-provided installer script with `INSTALL_ONLY` when available:

```bash
cd ~/minecraft-server/server
ATM10_INSTALL_ONLY=true bash startserver.sh
# Or for generic Forge packs:
# java -jar forge-*-installer.jar --installServer
```

This downloads libraries and patches the server jar without launching play.

### 5. Accept the EULA

```bash
echo "eula=true" > ~/minecraft-server/server/eula.txt
```

### 6. Configure `server.properties`

Core modded/LAN settings:

```properties
motd=\u00a7b\u00a7lServer Name \u00a7r\u00a78| \u00a7aModpack Name
server-port=25565
online-mode=true          # false for LAN without Mojang auth
enforce-secure-profile=true  # match online-mode
difficulty=hard            # most modpacks balance around hard
allow-flight=true          # REQUIRED for modded (flying mounts/items)
spawn-protection=0         # let everyone build at spawn
max-tick-time=180000       # modded needs longer tick timeout
enable-command-block=true
```

Performance starting points:

```properties
# 2 players, beefy machine:
view-distance=16
simulation-distance=10

# 4-6 players, moderate machine:
view-distance=10
simulation-distance=6

# 8+ players or weaker hardware:
view-distance=8
simulation-distance=4
```

### 7. Tune `user_jvm_args.txt`

Rule of thumb: 100-200 mods → 6-12GB; 200-350+ mods → 12-24GB. Leave at
least 8GB for the OS and other tasks.

```text
-Xms12G
-Xmx24G
-XX:+UseG1GC
-XX:+ParallelRefProcEnabled
-XX:MaxGCPauseMillis=200
-XX:+UnlockExperimentalVMOptions
-XX:+DisableExplicitGC
-XX:+AlwaysPreTouch
-XX:G1NewSizePercent=30
-XX:G1MaxNewSizePercent=40
-XX:G1HeapRegionSize=8M
-XX:G1ReservePercent=20
-XX:G1HeapWastePercent=5
-XX:G1MixedGCCountTarget=4
-XX:InitiatingHeapOccupancyPercent=15
-XX:G1MixedGCLiveThresholdPercent=90
-XX:G1RSetUpdatingPauseTimePercent=5
-XX:SurvivorRatio=32
-XX:+PerfDisableSharedMem
-XX:MaxTenuringThreshold=1
```

### 8. Open the firewall

```bash
sudo ufw allow 25565/tcp comment "Minecraft Server"
```

Check with `sudo ufw status` and confirm the `25565` rule.

### 9. Create a clean launch script

```bash
cat > ~/start-minecraft.sh << 'EOF'
#!/bin/bash
cd ~/minecraft-server/server
java @user_jvm_args.txt @libraries/net/neoforged/neoforge/<VERSION>/unix_args.txt nogui
EOF
chmod +x ~/start-minecraft.sh
```

Forge uses a different args-file path; read `startserver.sh` for the exact path.

### 10. Configure automated backups

```bash
cat > ~/minecraft-server/backup.sh << 'SCRIPT'
#!/bin/bash
SERVER_DIR="$HOME/minecraft-server/server"
BACKUP_DIR="$HOME/minecraft-server/backups"
WORLD_DIR="$SERVER_DIR/world"
MAX_BACKUPS=24
mkdir -p "$BACKUP_DIR"
[ ! -d "$WORLD_DIR" ] && echo "[BACKUP] No world folder" && exit 0
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/world_${TIMESTAMP}.tar.gz"
echo "[BACKUP] Starting at $(date)"
tar -czf "$BACKUP_FILE" -C "$SERVER_DIR" world
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[BACKUP] Saved: $BACKUP_FILE ($SIZE)"
BACKUP_COUNT=$(ls -1t "$BACKUP_DIR"/world_*.tar.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    REMOVE=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "$BACKUP_DIR"/world_*.tar.gz | tail -n "$REMOVE" | xargs rm -f
    echo "[BACKUP] Pruned $REMOVE old backup(s)"
fi
echo "[BACKUP] Done at $(date)"
SCRIPT
chmod +x ~/minecraft-server/backup.sh
```

Hourly cron:

```bash
(crontab -l 2>/dev/null | grep -v "minecraft/backup.sh"; echo "0 * * * * $HOME/minecraft-server/backup.sh >> $HOME/minecraft-server/backups/backup.log 2>&1") | crontab -
```

## Pitfalls

- `allow-flight=true` is required for modded flight items/mounts; otherwise players can be kicked.
- Keep `max-tick-time=180000` or higher; world generation can take long ticks.
- First startup may take several minutes; initial `Can't keep up!` warnings can be normal during chunk generation.
- When `online-mode=false`, also set `enforce-secure-profile=false` or clients can be rejected.
- Pack startup scripts may auto-restart; use a clean launch script when that behavior is unwanted.
- Delete `world/` only when intentionally regenerating with a new seed.
- Pack-specific variables can control behavior, e.g. `ATM10_JAVA`, `ATM10_RESTART`, `ATM10_INSTALL_ONLY`.

## Verification

```bash
pgrep -fa neoforge
pgrep -fa minecraft
```

Confirm a running process, logs containing `Done (Xs)!`, and a successful
Multiplayer connection using the server IP. Confirm backups create archives and
prune only after exceeding `MAX_BACKUPS`.
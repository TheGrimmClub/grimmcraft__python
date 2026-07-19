"""Auto-generated. Do not edit by hand; regenerate with
_generate/advanced_game_rule.py.
Minecraft Java Edition 1.21.11 — 63 game rules.

Each member's .value and .string_id are the rule name exactly as
/gamerule takes it — camelCase, never snake_case. .label is the vanilla
options-screen text and .description its help line, or None where the
game gives none.

Types and defaults are deliberately absent: neither is in any data file
this package ships."""

from __future__ import annotations

from grimmclub_standardlib import Enum


class GameRule(Enum):
    string_id: str
    label: str
    description: str | None

    def __new__(cls, string_id: str, label: str, description: str | None) -> GameRule:
        obj = object.__new__(cls)
        obj._value_ = string_id
        obj.string_id = string_id
        obj.label = label
        obj.description = description
        return obj

    ALLOW_ENTERING_NETHER_USING_PORTALS = ("allowEnteringNetherUsingPortals", "Allow Nether", "Controls whether players are allowed to enter the Nether.")
    ALLOW_FIRE_TICKS_AWAY_FROM_PLAYER = ("allowFireTicksAwayFromPlayer", "Tick fire away from players", "Controls whether fire and lava should be able to tick further than 8 chunks away from any player.")
    ANNOUNCE_ADVANCEMENTS = ("announceAdvancements", "Announce advancements", None)
    BLOCK_EXPLOSION_DROP_DECAY = ("blockExplosionDropDecay", "In block interaction explosions, some blocks won't drop their loot", "Some of the drops from blocks destroyed by explosions caused by block interactions are lost in the explosion.")
    COMMAND_BLOCK_OUTPUT = ("commandBlockOutput", "Broadcast command block output", None)
    COMMAND_BLOCKS_ENABLED = ("commandBlocksEnabled", "Enable Command Blocks", None)
    COMMAND_MODIFICATION_BLOCK_LIMIT = ("commandModificationBlockLimit", "Command modification block limit", "The number of blocks that can be changed at once by one command, such as fill or clone.")
    DISABLE_ELYTRA_MOVEMENT_CHECK = ("disableElytraMovementCheck", "Disable elytra movement check", None)
    DISABLE_PLAYER_MOVEMENT_CHECK = ("disablePlayerMovementCheck", "Disable player movement check", None)
    DISABLE_RAIDS = ("disableRaids", "Disable raids", None)
    DO_DAYLIGHT_CYCLE = ("doDaylightCycle", "Advance time of day", None)
    DO_ENTITY_DROPS = ("doEntityDrops", "Drop entity equipment", "Controls drops from minecarts (including inventories), item frames, boats, etc.")
    DO_FIRE_TICK = ("doFireTick", "Update fire", None)
    DO_IMMEDIATE_RESPAWN = ("doImmediateRespawn", "Respawn immediately", None)
    DO_INSOMNIA = ("doInsomnia", "Spawn phantoms", None)
    DO_LIMITED_CRAFTING = ("doLimitedCrafting", "Require recipe for crafting", "If enabled, players will be able to craft only unlocked recipes.")
    DO_MOB_LOOT = ("doMobLoot", "Drop mob loot", "Controls resource drops from mobs, including experience orbs.")
    DO_MOB_SPAWNING = ("doMobSpawning", "Spawn mobs", "Some entities might have separate rules.")
    DO_PATROL_SPAWNING = ("doPatrolSpawning", "Spawn pillager patrols", None)
    DO_TILE_DROPS = ("doTileDrops", "Drop blocks", "Controls resource drops from blocks, including experience orbs.")
    DO_TRADER_SPAWNING = ("doTraderSpawning", "Spawn Wandering Traders", None)
    DO_VINES_SPREAD = ("doVinesSpread", "Vines spread", "Controls whether the Vines block spreads randomly to adjacent blocks. Does not affect other types of vine blocks such as Weeping Vines, Twisting Vines, etc.")
    DO_WARDEN_SPAWNING = ("doWardenSpawning", "Spawn Wardens", None)
    DO_WEATHER_CYCLE = ("doWeatherCycle", "Update weather", None)
    DROWNING_DAMAGE = ("drowningDamage", "Deal drowning damage", None)
    ENABLE_COMMAND_BLOCKS = ("enableCommandBlocks", "Enable Command Blocks", None)
    ENDER_PEARLS_VANISH_ON_DEATH = ("enderPearlsVanishOnDeath", "Thrown Ender Pearls vanish on death", "Whether Ender Pearls thrown by a player vanish when that player dies.")
    ENTITIES_WITH_PASSENGERS_CAN_USE_PORTALS = ("entitiesWithPassengersCanUsePortals", "Entities with passengers can use portals", "Allow entities with passengers to teleport through Nether Portals, End Portals, and End Gateways.")
    FALL_DAMAGE = ("fallDamage", "Deal fall damage", None)
    FIRE_DAMAGE = ("fireDamage", "Deal fire damage", None)
    FORGIVE_DEAD_PLAYERS = ("forgiveDeadPlayers", "Forgive dead players", "Angered neutral mobs stop being angry when the targeted player dies nearby.")
    FREEZE_DAMAGE = ("freezeDamage", "Deal freeze damage", None)
    GLOBAL_SOUND_EVENTS = ("globalSoundEvents", "Global sound events", "When certain game events happen, like a boss spawning, the sound is heard everywhere.")
    KEEP_INVENTORY = ("keepInventory", "Keep inventory after death", None)
    LAVA_SOURCE_CONVERSION = ("lavaSourceConversion", "Lava converts to source", "When flowing lava is surrounded on two sides by lava sources it converts into a source.")
    LOCATOR_BAR = ("locatorBar", "Enable player Locator Bar", "When enabled, a bar is shown on the screen to indicate the direction of players.")
    LOG_ADMIN_COMMANDS = ("logAdminCommands", "Broadcast admin commands", None)
    MAX_COMMAND_CHAIN_LENGTH = ("maxCommandChainLength", "Command chain size limit", "Applies to command block chains and functions.")
    MAX_COMMAND_FORK_COUNT = ("maxCommandForkCount", "Command context limit", "Maximum number of contexts that can be used by commands like 'execute as'.")
    MAX_ENTITY_CRAMMING = ("maxEntityCramming", "Entity cramming threshold", None)
    MINECART_MAX_SPEED = ("minecartMaxSpeed", "Minecart max speed", "Maximum default speed of a moving Minecart on land.")
    MOB_EXPLOSION_DROP_DECAY = ("mobExplosionDropDecay", "In mob explosions, some blocks won't drop their loot", "Some of the drops from blocks destroyed by explosions caused by mobs are lost in the explosion.")
    MOB_GRIEFING = ("mobGriefing", "Allow destructive mob actions", None)
    NATURAL_REGENERATION = ("naturalRegeneration", "Regenerate health", None)
    PLAYERS_NETHER_PORTAL_CREATIVE_DELAY = ("playersNetherPortalCreativeDelay", "Player's Nether portal delay in creative mode", "Time (in ticks) that a creative mode player needs to stand in a Nether portal before changing dimensions.")
    PLAYERS_NETHER_PORTAL_DEFAULT_DELAY = ("playersNetherPortalDefaultDelay", "Player's Nether portal delay in non-creative mode", "Time (in ticks) that a non-creative mode player needs to stand in a Nether portal before changing dimensions.")
    PLAYERS_SLEEPING_PERCENTAGE = ("playersSleepingPercentage", "Sleep percentage", "The percentage of players who must be sleeping to skip the night.")
    PROJECTILES_CAN_BREAK_BLOCKS = ("projectilesCanBreakBlocks", "Projectiles can break blocks", "Controls whether impact projectiles will destroy blocks that are destructible by them.")
    PVP = ("pvp", "Enable pvp", "Controls whether players are allowed to damage other players.")
    RANDOM_TICK_SPEED = ("randomTickSpeed", "Random tick speed rate", None)
    REDUCED_DEBUG_INFO = ("reducedDebugInfo", "Reduce debug info", "Limits contents of debug screen.")
    SEND_COMMAND_FEEDBACK = ("sendCommandFeedback", "Send command feedback", None)
    SHOW_DEATH_MESSAGES = ("showDeathMessages", "Show death messages", None)
    SNOW_ACCUMULATION_HEIGHT = ("snowAccumulationHeight", "Snow accumulation height", "When it snows, layers of snow form on the ground up to at most this number of layers.")
    SPAWN_CHUNK_RADIUS = ("spawnChunkRadius", "Spawn chunk radius", "The amount of chunks that stay loaded around the overworld spawn position.")
    SPAWN_MONSTERS = ("spawnMonsters", "Spawn Monsters", "Controls whether monsters naturally spawn.")
    SPAWN_RADIUS = ("spawnRadius", "Respawn location radius", "Controls the size of the area around the spawn point that players can spawn in.")
    SPAWNER_BLOCKS_ENABLED = ("spawnerBlocksEnabled", "Enable Spawner Blocks", None)
    SPECTATORS_GENERATE_CHUNKS = ("spectatorsGenerateChunks", "Allow spectators to generate terrain", None)
    TNT_EXPLODES = ("tntExplodes", "Allow TNT to be activated and to explode", None)
    TNT_EXPLOSION_DROP_DECAY = ("tntExplosionDropDecay", "In TNT explosions, some blocks won't drop their loot", "Some of the drops from blocks destroyed by explosions caused by TNT are lost in the explosion.")
    UNIVERSAL_ANGER = ("universalAnger", "Universal anger", "Angered neutral mobs attack any nearby player, not just the player that angered them. Works best if forgiveDeadPlayers is disabled.")
    WATER_SOURCE_CONVERSION = ("waterSourceConversion", "Water converts to source", "When flowing water is surrounded on two sides by water sources it converts into a source.")


def game_rule(name: str) -> GameRule | None:
    """The rule called ``name``, or None if the game has no such rule."""
    for rule in GameRule:
        if rule.string_id == name:
            return rule
    return None

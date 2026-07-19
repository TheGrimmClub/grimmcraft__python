"""Unit tests: every transformation rule, with a real command in and out.

Written with :mod:`unittest` as specified, so the suite runs with no third-party
runner (``python -m unittest discover``) — though pytest collects it too.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from grimmcraft_migrate.classify import classify_command, classify_inventory
from grimmcraft_migrate.inventory import Inventory, read_inventory
from grimmcraft_migrate.migrate import migrate_command
from grimmcraft_migrate.report import MigrationReport
from grimmcraft_migrate.snbt import (
    SnbtCompound,
    SnbtSyntaxError,
    find_matching_brace,
    parse_snbt,
)
from grimmcraft_migrate.verify import build_verification_pack


class SnbtParserTests(unittest.TestCase):
    """The tokenizer/parser the transformation depends on."""

    def assert_round_trips(self, text: str) -> None:
        """Parsing then re-serialising must reproduce the input exactly."""
        self.assertEqual(parse_snbt(text).to_snbt(), text)

    def test_compound_round_trips(self) -> None:
        self.assert_round_trips('{id:"minecraft:stone",Count:1b}')

    def test_nested_structures_round_trip(self) -> None:
        self.assert_round_trips('{Items:[{id:"a",tag:{x:[I;1,2,3]}}]}')

    def test_numeric_suffixes_are_preserved(self) -> None:
        # 5s (short) and 5 (int) are different NBT types; dropping the suffix
        # would silently change the data.
        self.assert_round_trips("{lvl:5s,big:9223372036854775807l,f:1.5f,d:2.5d}")

    def test_typed_arrays_round_trip(self) -> None:
        self.assert_round_trips("{a:[I;1,2,3],b:[B;1b],c:[L;4l]}")

    def test_quoted_string_with_braces_is_not_a_compound(self) -> None:
        value = parse_snbt('{Name:"{not a compound}"}')
        assert isinstance(value, SnbtCompound)
        self.assertEqual(value["Name"].value, "{not a compound}")

    def test_single_quoted_strings_keep_their_quotes(self) -> None:
        self.assert_round_trips('{Name:\'{"text":"hi"}\'}')

    def test_booleans_round_trip(self) -> None:
        self.assert_round_trips("{a:true,b:false}")

    def test_empty_compound_and_list(self) -> None:
        self.assert_round_trips("{}")
        self.assert_round_trips("[]")

    def test_unbalanced_braces_are_rejected(self) -> None:
        with self.assertRaises(SnbtSyntaxError):
            parse_snbt("{id:")

    def test_find_matching_brace_ignores_braces_in_strings(self) -> None:
        text = 'give @p stone{Name:"}"} tail'
        end = find_matching_brace(text, text.index("{"))
        self.assertEqual(text[text.index("{") : end], '{Name:"}"}')


class ItemComponentTests(unittest.TestCase):
    """Rule 1: item NBT → data components."""

    def test_enchantments_become_a_map(self) -> None:
        result = migrate_command(
            'give @p diamond_sword{Enchantments:[{id:"minecraft:sharpness",lvl:5s}]}'
        )
        self.assertEqual(
            result.migrated,
            'give @p diamond_sword[minecraft:enchantments={"minecraft:sharpness":5}]',
        )

    def test_stored_enchantments_become_a_map(self) -> None:
        result = migrate_command(
            'give @p enchanted_book{StoredEnchantments:[{id:"minecraft:mending",lvl:1s}]}'
        )
        self.assertIn("minecraft:stored_enchantments=", result.migrated)
        self.assertIn('"minecraft:mending":1', result.migrated)

    def test_display_name_becomes_custom_name(self) -> None:
        result = migrate_command(
            'give @p stone{display:{Name:\'{"text":"Rock"}\'}}'
        )
        self.assertEqual(
            result.migrated,
            'give @p stone[minecraft:custom_name=\'{"text":"Rock"}\']',
        )

    def test_display_lore_becomes_lore(self) -> None:
        result = migrate_command(
            'give @p stone{display:{Lore:[\'{"text":"line"}\']}}'
        )
        self.assertIn("minecraft:lore=", result.migrated)

    def test_display_color_becomes_dyed_color(self) -> None:
        result = migrate_command("give @p leather_helmet{display:{color:16711680}}")
        self.assertEqual(
            result.migrated, "give @p leather_helmet[minecraft:dyed_color=16711680]"
        )

    def test_unbreakable_becomes_an_empty_component(self) -> None:
        result = migrate_command("give @p diamond_sword{Unbreakable:1b}")
        self.assertEqual(
            result.migrated, "give @p diamond_sword[minecraft:unbreakable={}]"
        )

    def test_damage_is_renamed(self) -> None:
        result = migrate_command("give @p diamond_sword{Damage:3}")
        self.assertEqual(result.migrated, "give @p diamond_sword[minecraft:damage=3]")

    def test_custom_model_data_is_renamed(self) -> None:
        result = migrate_command("give @p stone{CustomModelData:7}")
        self.assertEqual(result.migrated, "give @p stone[minecraft:custom_model_data=7]")

    def test_potion_becomes_potion_contents(self) -> None:
        result = migrate_command('give @p potion{Potion:"minecraft:strong_healing"}')
        self.assertEqual(
            result.migrated,
            'give @p potion[minecraft:potion_contents={potion:"minecraft:strong_healing"}]',
        )

    def test_potion_and_custom_effects_merge_into_one_component(self) -> None:
        result = migrate_command(
            'give @p potion{Potion:"minecraft:water",'
            'CustomPotionEffects:[{id:1,duration:200}]}'
        )
        self.assertEqual(result.migrated.count("minecraft:potion_contents"), 1)
        self.assertIn("custom_effects", result.migrated)

    def test_attribute_modifiers_are_rewritten(self) -> None:
        result = migrate_command(
            "give @p diamond_sword{AttributeModifiers:["
            '{AttributeName:"generic.attack_damage",Name:"boost",'
            'Amount:2,Operation:0,Slot:"mainhand"}]}'
        )
        self.assertIn("minecraft:attribute_modifiers=", result.migrated)
        self.assertIn('type:"minecraft:attack_damage"', result.migrated)
        self.assertIn('operation:"add_value"', result.migrated)
        self.assertIn('slot:"mainhand"', result.migrated)

    def test_can_destroy_becomes_a_predicate(self) -> None:
        result = migrate_command('give @p pickaxe{CanDestroy:["minecraft:stone"]}')
        self.assertIn("minecraft:can_break={predicates:[{blocks:[", result.migrated)

    def test_can_place_on_becomes_a_predicate(self) -> None:
        result = migrate_command('give @p stone{CanPlaceOn:["minecraft:dirt"]}')
        self.assertIn("minecraft:can_place_on={predicates:[{blocks:[", result.migrated)

    def test_block_entity_tag_is_renamed(self) -> None:
        result = migrate_command('give @p chest{BlockEntityTag:{Lock:"key"}}')
        self.assertIn("minecraft:block_entity_data=", result.migrated)

    def test_entity_tag_is_renamed(self) -> None:
        result = migrate_command('give @p spawn_egg{EntityTag:{id:"minecraft:pig"}}')
        self.assertIn("minecraft:entity_data=", result.migrated)

    def test_fireworks_is_renamed(self) -> None:
        result = migrate_command("give @p firework_rocket{Fireworks:{Flight:2b}}")
        self.assertIn("minecraft:fireworks=", result.migrated)

    def test_skull_owner_becomes_profile(self) -> None:
        result = migrate_command('give @p player_head{SkullOwner:"Notch"}')
        self.assertIn("minecraft:profile=", result.migrated)

    def test_book_fields_merge_into_written_book_content(self) -> None:
        result = migrate_command(
            'give @p written_book{title:"Tales",author:"Grimm",pages:[\'{"text":"p1"}\']}'
        )
        self.assertEqual(result.migrated.count("minecraft:written_book_content"), 1)

    def test_hide_flags_is_reported_as_approximate(self) -> None:
        result = migrate_command("give @p stone{HideFlags:63}")
        self.assertIn("minecraft:hide_tooltip=", result.migrated)
        self.assertTrue(
            any(t.rule == "approximate" for t in result.transformations),
            "an inexact translation must be reported",
        )

    def test_clear_command_is_migrated_too(self) -> None:
        result = migrate_command("clear @p stone{Damage:1}")
        self.assertEqual(result.migrated, "clear @p stone[minecraft:damage=1]")


class UnknownKeyTests(unittest.TestCase):
    """Rule 4: unmapped keys are preserved, never dropped."""

    def test_unknown_key_moves_to_custom_data(self) -> None:
        result = migrate_command("give @p stone{MyModKey:1b}")
        self.assertEqual(
            result.migrated, "give @p stone[minecraft:custom_data={MyModKey:1b}]"
        )

    def test_unknown_key_is_reported(self) -> None:
        result = migrate_command("give @p stone{MyModKey:1b}")
        self.assertEqual(result.unknown_keys, ["MyModKey"])

    def test_unknown_key_survives_alongside_known_ones(self) -> None:
        result = migrate_command("give @p stone{Damage:2,MyModKey:1b}")
        self.assertIn("minecraft:damage=2", result.migrated)
        self.assertIn("MyModKey:1b", result.migrated)

    def test_unknown_display_key_is_preserved(self) -> None:
        result = migrate_command("give @p stone{display:{Weird:1b}}")
        self.assertIn("display:{Weird:1b}", result.migrated)
        self.assertEqual(result.unknown_keys, ["display.Weird"])


class NestedItemTests(unittest.TestCase):
    """Rule 2: nested item schema inside entity / block-entity NBT."""

    def test_hand_items_count_and_tag_are_rewritten(self) -> None:
        result = migrate_command(
            'summon zombie ~ ~ ~ {HandItems:[{id:"minecraft:diamond_sword",'
            "Count:1b,tag:{Damage:5}}]}"
        )
        self.assertIn("count:1", result.migrated)
        self.assertIn("components:{", result.migrated)
        self.assertNotIn("Count:1b", result.migrated)
        self.assertNotIn("tag:{", result.migrated)

    def test_chest_items_are_rewritten(self) -> None:
        result = migrate_command(
            'setblock ~ ~ ~ chest{Items:[{id:"minecraft:stone",Count:64b,Slot:0b}]}'
        )
        self.assertIn("count:64", result.migrated)
        self.assertIn("Slot:0b", result.migrated, "unrelated keys are untouched")

    def test_armor_items_are_rewritten(self) -> None:
        result = migrate_command(
            'summon zombie ~ ~ ~ {ArmorItems:[{id:"minecraft:boots",Count:1b}]}'
        )
        self.assertIn("count:1", result.migrated)

    def test_nested_enchantments_become_components(self) -> None:
        result = migrate_command(
            'summon zombie ~ ~ ~ {HandItems:[{id:"minecraft:sword",Count:1b,'
            'tag:{Enchantments:[{id:"minecraft:sharpness",lvl:2s}]}}]}'
        )
        self.assertIn('"minecraft:enchantments"', result.migrated)
        self.assertIn('"minecraft:sharpness":2', result.migrated)


class SignTests(unittest.TestCase):
    """Rule 3: sign text fields."""

    def test_sign_lines_become_front_text(self) -> None:
        result = migrate_command(
            'setblock ~ ~ ~ oak_sign{Text1:\'{"text":"a"}\',Text2:\'{"text":"b"}\'}'
        )
        self.assertIn("front_text:{messages:[", result.migrated)
        self.assertNotIn("Text1", result.migrated)

    def test_sign_always_gets_four_messages(self) -> None:
        result = migrate_command(
            'setblock ~ ~ ~ oak_sign{Text1:\'{"text":"a"}\'}'
        )
        self.assertEqual(result.migrated.count('{\\"text\\":\\"\\"}')
                         + result.migrated.count('{"text":""}'), 3)


class AttributeTests(unittest.TestCase):
    """Rule 4: attribute identifier renames."""

    def test_movement_speed_is_renamed(self) -> None:
        result = migrate_command("attribute @s generic.movement_speed base set 0.3")
        self.assertEqual(
            result.migrated, "attribute @s minecraft:movement_speed base set 0.3"
        )

    def test_horse_jump_strength_is_renamed(self) -> None:
        result = migrate_command("attribute @s horse.jump_strength base set 1")
        self.assertEqual(
            result.migrated, "attribute @s minecraft:jump_strength base set 1"
        )

    def test_unknown_dotted_name_is_left_alone(self) -> None:
        original = "attribute @s custom.thing base set 1"
        self.assertEqual(migrate_command(original).migrated, original)


class BlockPositionTests(unittest.TestCase):
    """Rule 6: {X,Y,Z} compounds became integer arrays."""

    def test_flower_pos_becomes_an_int_array(self) -> None:
        result = migrate_command(
            "data merge block ~ ~ ~ {flower_pos:{X:1,Y:2,Z:3}}"
        )
        self.assertIn("flower_pos:[I;1,2,3]", result.migrated)

    def test_hive_pos_becomes_an_int_array(self) -> None:
        result = migrate_command("data merge block ~ ~ ~ {hive_pos:{X:-4,Y:70,Z:8}}")
        self.assertIn("hive_pos:[I;-4,70,8]", result.migrated)


class IdempotencyTests(unittest.TestCase):
    """Rule 5: migrating already-migrated commands changes nothing."""

    COMMANDS = [
        'give @p diamond_sword{Enchantments:[{id:"minecraft:sharpness",lvl:5s}]}',
        'give @p stone{display:{Name:\'{"text":"Rock"}\'},MyModKey:1b}',
        'summon zombie ~ ~ ~ {HandItems:[{id:"minecraft:diamond",Count:1b,tag:{Damage:5}}]}',
        'setblock ~ ~ ~ oak_sign{Text1:\'{"text":"a"}\'}',
        "attribute @s generic.movement_speed base set 0.3",
        "data merge block ~ ~ ~ {flower_pos:{X:1,Y:2,Z:3}}",
    ]

    def test_second_run_is_a_no_op(self) -> None:
        for command in self.COMMANDS:
            with self.subTest(command=command):
                once = migrate_command(command).migrated
                twice = migrate_command(once).migrated
                self.assertEqual(once, twice)

    def test_already_modern_commands_are_untouched(self) -> None:
        modern = [
            'give @p diamond_sword[minecraft:enchantments={"minecraft:sharpness":5}]',
            "give @p stone[minecraft:damage=3]",
            "attribute @s minecraft:movement_speed base set 0.3",
        ]
        for command in modern:
            with self.subTest(command=command):
                self.assertEqual(migrate_command(command).migrated, command)


class FailureTests(unittest.TestCase):
    """Fail loudly: unparseable commands are left whole, with a reason."""

    def test_unbalanced_nbt_is_left_unchanged(self) -> None:
        broken = 'give @p stone{Damage:3'
        result = migrate_command(broken)
        self.assertEqual(result.migrated, broken)
        self.assertTrue(result.failed)
        self.assertIn("could not parse", result.unchanged_reason)

    def test_non_item_command_with_braces_is_untouched(self) -> None:
        original = "say hello {this is not nbt}"
        self.assertEqual(migrate_command(original).migrated, original)


class ClassifierTests(unittest.TestCase):
    """The classifier pass runs before anything is transformed."""

    def test_flags_legacy_item_nbt(self) -> None:
        self.assertIn(
            "legacy_item_nbt", classify_command("give @p stone{Damage:1}")
        )

    def test_flags_legacy_sign_and_attribute(self) -> None:
        self.assertIn(
            "legacy_sign_fields",
            classify_command('setblock ~ ~ ~ sign{Text1:\'{"text":"a"}\'}'),
        )
        self.assertIn(
            "legacy_attribute",
            classify_command("attribute @s generic.movement_speed base set 1"),
        )

    def test_modern_commands_raise_no_flags(self) -> None:
        self.assertEqual(
            classify_command("give @p stone[minecraft:damage=1]"), []
        )

    def test_execute_is_grouped_by_its_inner_command(self) -> None:
        inventory = Inventory(format="text")
        from grimmcraft_migrate.inventory import CommandEntry

        inventory.entries = [
            CommandEntry(command="execute as @a run give @p stone{Damage:1}")
        ]
        report = classify_inventory(inventory)
        self.assertIn("execute→give", report.command_frequency)


class InventoryTests(unittest.TestCase):
    """Reading and writing both inventory formats."""

    def test_text_inventory_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "in.txt"
            source.write_text("give @p stone\nsay hello\n", encoding="utf-8")
            inventory = read_inventory(source)
            self.assertEqual(len(inventory), 2)
            self.assertEqual(inventory.format, "text")

            destination = Path(directory) / "out.txt"
            inventory.write(destination)
            self.assertEqual(
                destination.read_text(encoding="utf-8"), "give @p stone\nsay hello\n"
            )

    def test_json_inventory_preserves_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "in.json"
            source.write_text(
                json.dumps(
                    [
                        {
                            "command": "give @p stone{Damage:1}",
                            "dimension": "minecraft:overworld",
                            "x": 10, "y": 64, "z": -3,
                        }
                    ]
                ),
                encoding="utf-8",
            )
            inventory = read_inventory(source)
            self.assertEqual(inventory.format, "json")
            self.assertEqual(inventory.entries[0].location, "overworld_10_64_-3")

            destination = Path(directory) / "out.json"
            inventory.write(destination)
            written = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(written[0]["x"], 10)

    def test_comments_are_skipped_in_text_inventories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "in.txt"
            source.write_text("# a note\ngive @p stone\n", encoding="utf-8")
            self.assertEqual(len(read_inventory(source)), 1)


class ReportTests(unittest.TestCase):
    """The Markdown report names changes, unknown keys and failures."""

    def _report(self) -> MigrationReport:
        from grimmcraft_migrate.inventory import CommandEntry

        report = MigrationReport()
        report.add(
            CommandEntry(command="give @p stone{MyModKey:1b}", x=1, y=2, z=3),
            migrate_command("give @p stone{MyModKey:1b}"),
        )
        report.add(
            CommandEntry(command="give @p stone{Damage:3"),
            migrate_command("give @p stone{Damage:3"),
        )
        return report

    def test_report_lists_unknown_keys(self) -> None:
        self.assertIn("MyModKey", self._report().to_markdown())

    def test_report_lists_failures_with_a_reason(self) -> None:
        text = self._report().to_markdown()
        self.assertIn("Left unchanged", text)
        self.assertIn("could not parse", text)

    def test_report_counts_are_right(self) -> None:
        report = self._report()
        self.assertEqual(len(report.changed), 1)
        self.assertEqual(len(report.failed), 1)


class VerifyPackTests(unittest.TestCase):
    """The verification datapack, which hands checking to the game."""

    def _entries(self, count: int):  # type: ignore[no-untyped-def]
        from grimmcraft_migrate.inventory import CommandEntry

        return [
            CommandEntry(
                command=f"say line {index}",
                dimension="minecraft:overworld",
                x=index, y=64, z=0,
            )
            for index in range(count)
        ]

    def test_pack_has_mcmeta_and_functions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = build_verification_pack(self._entries(3), directory)
            self.assertTrue((root / "pack.mcmeta").is_file())
            functions = root / "data" / "migration_check" / "function"
            self.assertTrue((functions / "overworld_000.mcfunction").is_file())
            self.assertTrue((functions / "run_all.mcfunction").is_file())

    def test_functions_are_chunked_at_200_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = build_verification_pack(self._entries(250), directory)
            functions = root / "data" / "migration_check" / "function"
            self.assertTrue((functions / "overworld_000.mcfunction").is_file())
            self.assertTrue((functions / "overworld_001.mcfunction").is_file())

    def test_each_command_carries_its_source_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = build_verification_pack(self._entries(1), directory)
            text = (
                root / "data" / "migration_check" / "function" / "overworld_000.mcfunction"
            ).read_text(encoding="utf-8")
            self.assertIn("# from overworld_0_64_0", text)


if __name__ == "__main__":
    unittest.main()

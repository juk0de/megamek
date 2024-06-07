import logging

class MtfFile:
    COMMENT = "#"
    MTF_VERSION = "version:"
    GENERATOR = "generator:"
    CHASSIS = "chassis:"
    CLAN_CHASSIS_NAME = "clanname:"
    MODEL = "model:"
    COCKPIT = "cockpit:"
    GYRO = "gyro:"
    MOTIVE = "motive:"
    EJECTION = "ejection:"
    MASS = "mass:"
    ENGINE = "engine:"
    STRUCTURE = "structure:"
    MYOMER = "myomer:"
    LAM = "lam:"
    CONFIG = "config:"
    TECH_BASE = "techbase:"
    ERA = "era:"
    SOURCE = "source:"
    RULES_LEVEL = "rules level:"
    HEAT_SINKS = "heat sinks:"
    BASE_CHASSIS_HEAT_SINKS = "base chassis heat sinks:"
    HS_SINGLE = "Single"
    HS_DOUBLE = "Double"
    HS_LASER = "Laser"
    HS_COMPACT = "Compact"
    TECH_BASE_IS = "IS"
    TECH_BASE_CLAN = "Clan"
    WALK_MP = "walk mp:"
    JUMP_MP = "jump mp:"
    ARMOR = "armor:"
    OVERVIEW = "overview:"
    CAPABILITIES = "capabilities:"
    DEPLOYMENT = "deployment:"
    HISTORY = "history:"
    MANUFACTURER = "manufacturer:"
    PRIMARY_FACTORY = "primaryfactory:"
    SYSTEM_MANUFACTURER = "systemmanufacturer:"
    SYSTEM_MODEL = "systemmode:"
    NOTES = "notes:"
    BV = "bv:"
    WEAPONS = "weapons:"
    EMPTY = "-Empty-"
    ARMORED = "(ARMORED)"
    OMNIPOD = "(OMNIPOD)"
    NO_CRIT = "nocrit:"
    SIZE = ":SIZE:"
    MUL_ID = "mul id:"
    QUIRK = "quirk:"
    WEAPON_QUIRK = "weaponquirk:"
    ROLE = "role:"
    FLUFF_IMAGE = "fluffimage:"
    ICON = "icon:"

    def __init__(self, input_stream):
        self.chassis = ""
        self.model = ""
        self.clan_chassis_name = ""
        self.mul_id = -1

        self.chassis_config = ""
        self.tech_base = ""
        self.tech_year = ""
        self.rules_level = ""
        self.source = "Source:"

        self.tonnage = ""
        self.engine = ""
        self.internal_type = ""
        self.gyro_type = ""
        self.cockpit_type = ""
        self.lam_type = ""
        self.motive_type = ""
        self.ejection_type = ""

        self.heat_sinks = ""
        self.jump_mp = ""
        self.base_chassie_heat_sinks = "base chassis heat sinks:-1"

        self.armor_type = ""
        self.armor_values = [""] * 12

        self.crit_data = [[""] * 12 for _ in range(9)]
        self.no_crit_equipment = []

        self.capabilities = ""
        self.deployment = ""
        self.overview = ""
        self.history = ""
        self.manufacturer = ""
        self.primary_factory = ""
        self.system_manufacturers = {}
        self.system_models = {}
        self.notes = ""

        self.fluff_image_encoded = ""
        self.icon_encoded = ""

        self.bv = 0
        self.role = ""

        self.h_shared_equip = {}
        self.v_split_weapons = []

        self.quirk_lines = []

        try:
            self.read_lines(input_stream)
        except Exception as ex:
            logging.error("", exc_info=ex)
            raise Exception("Error reading file") from ex

    def read_lines(self, input_stream):
        slot = 0
        loc = 0
        while True:
            line = input_stream.readline().strip()
            if not line:
                break

            if line.startswith(self.COMMENT) or line.startswith(self.GENERATOR):
                continue

            if line.lower().startswith(self.MTF_VERSION):
                generator_or_chassis = self.read_line_ignoring_comments(input_stream)
                if generator_or_chassis.lower().startswith(self.GENERATOR):
                    self.chassis = self.read_line_ignoring_comments(input_stream)
                else:
                    self.chassis = generator_or_chassis
                self.model = self.read_line_ignoring_comments(input_stream)
                continue

            if self.is_title_line(line):
                continue

            if self.is_valid_location(line):
                loc = self.get_location(line)
                slot = 0
                continue

            if self.is_processed_component(line):
                continue

            weapons_count = self.weapons_list(line)

            if weapons_count > 0:
                for _ in range(weapons_count):
                    input_stream.readline()
                continue

            armor_location = self.get_armor_location(line)

            if armor_location >= 0:
                self.armor_values[armor_location] = line
                continue

            if len(self.crit_data) <= loc:
                continue

            if len(self.crit_data[loc]) <= slot:
                continue

            self.crit_data[loc][slot] = line.strip()
            slot += 1

    def read_line_ignoring_comments(self, input_stream):
        while True:
            line = input_stream.readline()
            if not line:
                return ""
            elif not line.startswith(self.COMMENT):
                return line.strip()

    def is_title_line(self, line):
        line_lower = line.lower()
        if line_lower.startswith(self.CHASSIS):
            self.chassis = line[len(self.CHASSIS):]
            return True
        elif line_lower.startswith(self.MODEL):
            self.model = line[len(self.MODEL):]
            return True
        else:
            return False

    def is_valid_location(self, line):
        pass

    def get_location(self, line):
        pass

    def is_processed_component(self, line):
        pass

    def weapons_list(self, line):
        pass

    def get_armor_location(self, line):
        pass

import logging
from megamek.common import TechConstants

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
        valid_locations = [
            "Left Arm:", "Right Arm:", "Left Leg:", "Right Leg:", "Center Leg:",
            "Front Left Leg:", "Front Right Leg:", "Rear Left Leg:", "Rear Right Leg:",
            "Left Torso:", "Right Torso:", "Center Torso:", "Head:"
        ]
        return line in valid_locations

    def get_location(self, line):
        if line.lower() == "left arm:" or line.lower() == "front left leg:":
            return 0  # Mech.LOC_LARM
        elif line.lower() == "right arm:" or line.lower() == "front right leg:":
            return 1  # Mech.LOC_RARM
        elif line.lower() == "left leg:" or line.lower() == "rear left leg:":
            return 6  # Mech.LOC_LLEG
        elif line.lower() == "right leg:" or line.lower() == "rear right leg:":
            return 7  # Mech.LOC_RLEG
        elif line.lower() == "center leg:":
            return 8  # Mech.LOC_CLEG
        elif line.lower() == "left torso:":
            return 2  # Mech.LOC_LT
        elif line.lower() == "right torso:":
            return 3  # Mech.LOC_RT
        elif line.lower() == "center torso:":
            return 4  # Mech.LOC_CT
        else:
            return 5  # Mech.LOC_HEAD

    def is_processed_component(self, line):
        line_lower = line.lower()
        if line_lower.startswith(self.COCKPIT):
            self.cockpit_type = line
            return True
        elif line_lower.startswith(self.GYRO):
            self.gyro_type = line
            return True
        elif line_lower.startswith(self.MOTIVE):
            self.motive_type = line
            return True
        elif line_lower.startswith(self.EJECTION):
            self.ejection_type = line
            return True
        elif line_lower.startswith(self.MASS):
            self.tonnage = line
            return True
        elif line_lower.startswith(self.ENGINE):
            self.engine = line
            return True
        elif line_lower.startswith(self.STRUCTURE):
            self.internal_type = line
            return True
        elif line_lower.startswith(self.MYOMER):
            return True
        elif line_lower.startswith(self.LAM):
            self.lam_type = line
            return True
        elif line_lower.startswith(self.CONFIG):
            self.chassis_config = line
            return True
        elif line_lower.startswith(self.TECH_BASE):
            self.tech_base = line
            return True
        elif line_lower.startswith(self.ERA):
            self.tech_year = line
            return True
        elif line_lower.startswith(self.SOURCE):
            self.source = line
            return True
        elif line_lower.startswith(self.RULES_LEVEL):
            self.rules_level = line
            return True
        elif line_lower.startswith(self.HEAT_SINKS):
            self.heat_sinks = line
            return True
        elif line_lower.startswith(self.BASE_CHASSIS_HEAT_SINKS):
            self.base_chassie_heat_sinks = line
            return True
        elif line_lower.startswith(self.WALK_MP):
            return True
        elif line_lower.startswith(self.JUMP_MP):
            self.jump_mp = line
            return True
        elif line_lower.startswith(self.ARMOR):
            self.armor_type = line
            return True
        elif line_lower.startswith(self.NO_CRIT):
            self.no_crit_equipment.append(line[len(self.NO_CRIT):])
            return True
        elif line_lower.startswith(self.OVERVIEW):
            self.overview = line[len(self.OVERVIEW):]
            return True
        elif line_lower.startswith(self.CLAN_CHASSIS_NAME):
            self.clan_chassis_name = line[len(self.CLAN_CHASSIS_NAME):]
            return True
        elif line_lower.startswith(self.CAPABILITIES):
            self.capabilities = line[len(self.CAPABILITIES):]
            return True
        elif line_lower.startswith(self.DEPLOYMENT):
            self.deployment = line[len(self.DEPLOYMENT):]
            return True
        elif line_lower.startswith(self.HISTORY):
            self.history = line[len(self.HISTORY):]
            return True
        elif line_lower.startswith(self.MANUFACTURER):
            self.manufacturer = line[len(self.MANUFACTURER):]
            return True
        elif line_lower.startswith(self.PRIMARY_FACTORY):
            self.primary_factory = line[len(self.PRIMARY_FACTORY):]
            return True
        elif line_lower.startswith(self.SYSTEM_MANUFACTURER):
            fields = line.split(":")
            if len(fields) > 2:
                system = fields[1].strip()
                self.system_manufacturers[system] = fields[2].strip()
            return True
        elif line_lower.startswith(self.SYSTEM_MODEL):
            fields = line.split(":")
            if len(fields) > 2:
                system = fields[1].strip()
                self.system_models[system] = fields[2].strip()
            return True
        elif line_lower.startswith(self.NOTES):
            self.notes = line[len(self.NOTES):]
            return True
        elif line_lower.startswith(self.BV):
            self.bv = int(line[len(self.BV):])
            return True
        elif line_lower.startswith(self.MUL_ID):
            self.mul_id = int(line[len(self.MUL_ID):])
            return True
        elif line_lower.startswith(self.FLUFF_IMAGE):
            self.fluff_image_encoded = line[len(self.FLUFF_IMAGE):]
            return True
        elif line_lower.startswith(self.ICON):
            self.icon_encoded = line[len(self.ICON):]
            return True
        elif line_lower.startswith(self.QUIRK) or line_lower.startswith(self.WEAPON_QUIRK):
            self.quirk_lines.append(line)
            return True
        elif line_lower.startswith(self.ROLE):
            self.role = line[len(self.ROLE):]
            return True
        return False

    def weapons_list(self, line):
        if line.lower().startswith(self.WEAPONS):
            return int(line[len(self.WEAPONS):])
        return -1

    def get_armor_location(self, location):
        loc = -1
        rear = False
        location_name = location.lower()
        if location_name.startswith("la armor:") or location_name.startswith("fll armor:"):
            loc = 0  # Mech.LOC_LARM
        elif location_name.startswith("ra armor:") or location_name.startswith("frl armor:"):
            loc = 1  # Mech.LOC_RARM
        elif location_name.startswith("lt armor:"):
            loc = 2  # Mech.LOC_LT
        elif location_name.startswith("rt armor:"):
            loc = 3  # Mech.LOC_RT
        elif location_name.startswith("ct armor:"):
            loc = 4  # Mech.LOC_CT
        elif location_name.startswith("hd armor:"):
            loc = 5  # Mech.LOC_HEAD
        elif location_name.startswith("ll armor:") or location_name.startswith("rll armor:"):
            loc = 6  # Mech.LOC_LLEG
        elif location_name.startswith("rl armor:") or location_name.startswith("rrl armor:"):
            loc = 7  # Mech.LOC_RLEG
        elif location_name.startswith("rtl armor:"):
            loc = 2  # Mech.LOC_LT
            rear = True
        elif location_name.startswith("rtr armor:"):
            loc = 3  # Mech.LOC_RT
            rear = True
        elif location_name.startswith("rtc armor:"):
            loc = 4  # Mech.LOC_CT
            rear = True
        elif location_name.startswith("cl armor:"):
            loc = 8  # Mech.LOC_CLEG

        if not rear:
            for pos in range(len(self.location_order)):
                if self.location_order[pos] == loc:
                    loc = pos
                    break
        else:
            for pos in range(len(self.rear_location_order)):
                if self.rear_location_order[pos] == loc:
                    loc = pos + len(self.location_order)
                    break
        return loc
    def set_tech_level(self, mech):
        tech_base = self.tech_base[9:].strip()
        rules_level = int(self.rules_level[12:].strip())
        if tech_base.lower() == "inner sphere":
            if rules_level == 1:
                mech.set_tech_level(TechConstants.T_INTRO_BOXSET)
            elif rules_level == 2:
                mech.set_tech_level(TechConstants.T_IS_TW_NON_BOX)
            elif rules_level == 3:
                mech.set_tech_level(TechConstants.T_IS_ADVANCED)
            elif rules_level == 4:
                mech.set_tech_level(TechConstants.T_IS_EXPERIMENTAL)
            elif rules_level == 5:
                mech.set_tech_level(TechConstants.T_IS_UNOFFICIAL)
            else:
                raise Exception(f"Unsupported tech level: {rules_level}")
        elif tech_base.lower() == "clan":
            if rules_level == 2:
                mech.set_tech_level(TechConstants.T_CLAN_TW)
            elif rules_level == 3:
                mech.set_tech_level(TechConstants.T_CLAN_ADVANCED)
            elif rules_level == 4:
                mech.set_tech_level(TechConstants.T_CLAN_EXPERIMENTAL)
            elif rules_level == 5:
                mech.set_tech_level(TechConstants.T_CLAN_UNOFFICIAL)
            else:
                raise Exception(f"Unsupported tech level: {rules_level}")
        elif tech_base.lower() == "mixed (is chassis)":
            if rules_level == 2:
                mech.set_tech_level(TechConstants.T_IS_TW_NON_BOX)
            elif rules_level == 3:
                mech.set_tech_level(TechConstants.T_IS_ADVANCED)
            elif rules_level == 4:
                mech.set_tech_level(TechConstants.T_IS_EXPERIMENTAL)
            elif rules_level == 5:
                mech.set_tech_level(TechConstants.T_IS_UNOFFICIAL)
            else:
                raise Exception(f"Unsupported tech level: {rules_level}")
            mech.set_mixed_tech(True)
        elif tech_base.lower() == "mixed (clan chassis)":
            if rules_level == 2:
                mech.set_tech_level(TechConstants.T_CLAN_TW)
            elif rules_level == 3:
                mech.set_tech_level(TechConstants.T_CLAN_ADVANCED)
            elif rules_level == 4:
                mech.set_tech_level(TechConstants.T_CLAN_EXPERIMENTAL)
            elif rules_level == 5:
                mech.set_tech_level(TechConstants.T_CLAN_UNOFFICIAL)
            else:
                raise Exception(f"Unsupported tech level: {rules_level}")
            mech.set_mixed_tech(True)
        elif tech_base.lower() == "mixed":
            raise Exception("Unsupported tech base: \"Mixed\" is no longer allowed by itself.  You must specify \"Mixed (IS Chassis)\" or \"Mixed (Clan Chassis)\".")
        else:
            raise Exception(f"Unsupported tech base: {tech_base}")

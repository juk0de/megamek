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
    def parse_crits(self, mech, loc):
        if not isinstance(mech, QuadMech):
            if loc in [Mech.LOC_LARM, Mech.LOC_RARM]:
                to_check = self.crit_data[loc][3].upper().strip()
                if to_check.endswith(self.ARMORED):
                    to_check = to_check[:-len(self.ARMORED)].strip()
                if to_check != "HAND ACTUATOR":
                    mech.set_critical(loc, 3, None)
                to_check = self.crit_data[loc][2].upper().strip()
                if to_check.endswith(self.ARMORED):
                    to_check = to_check[:-len(self.ARMORED)].strip()
                if to_check != "LOWER ARM ACTUATOR":
                    mech.set_critical(loc, 2, None)

        for i in range(mech.get_number_of_criticals(loc)):
            crit_name = self.crit_data[loc][i].strip()
            crit_name_upper = crit_name.upper()
            rear_mounted = False
            is_armored = False
            is_turreted = False
            is_omni_pod = False
            size = 0.0

            if crit_name_upper.endswith(self.ARMORED):
                crit_name = crit_name[:-len(self.ARMORED)].strip()
                is_armored = True
                crit_name_upper = crit_name.upper()

            if crit_name in ["FUSION ENGINE", "ENGINE"]:
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, Mech.SYSTEM_ENGINE, True, is_armored))
                continue
            elif crit_name == "LIFE SUPPORT":
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, Mech.SYSTEM_LIFE_SUPPORT, True, is_armored))
                continue
            elif crit_name == "SENSORS":
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, Mech.SYSTEM_SENSORS, True, is_armored))
                continue
            elif crit_name == "COCKPIT":
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, Mech.SYSTEM_COCKPIT, True, is_armored))
                continue
            elif crit_name == "GYRO":
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, Mech.SYSTEM_GYRO, True, is_armored))
                continue
            elif crit_name in ["HAND ACTUATOR", "LOWER ARM ACTUATOR", "SHOULDER", "HIP"]:
                mech.get_critical(loc, i).set_armored(is_armored)
                continue
            elif crit_name == "LANDING GEAR":
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, LandAirMech.LAM_LANDING_GEAR, True, is_armored))
                continue
            elif crit_name == "AVIONICS":
                mech.set_critical(loc, i, CriticalSlot(CriticalSlot.TYPE_SYSTEM, LandAirMech.LAM_AVIONICS, True, is_armored))
                continue

            if mech.get_critical(loc, i) is not None:
                continue

            size_index = crit_name_upper.find(self.SIZE)
            if size_index > 0:
                size = float(crit_name[size_index + len(self.SIZE):])
                crit_name_upper = crit_name_upper[:size_index]

            if crit_name_upper.endswith(self.OMNIPOD):
                crit_name_upper = crit_name_upper[:-len(self.OMNIPOD)].strip()
                is_omni_pod = True

            if crit_name_upper.endswith("(T)"):
                is_turreted = True
                crit_name_upper = crit_name_upper[:-3].strip()

            if crit_name_upper.endswith("(R)"):
                rear_mounted = True
                crit_name_upper = crit_name_upper[:-3].strip()

            if crit_name_upper.endswith("(SPLIT)"):
                crit_name_upper = crit_name_upper[:-7].strip()

            facing = -1
            if crit_name_upper.endswith("(FL)"):
                facing = 5
                crit_name_upper = crit_name_upper[:-4].strip()
            elif crit_name_upper.endswith("(FR)"):
                facing = 1
                crit_name_upper = crit_name_upper[:-4].strip()
            elif crit_name_upper.endswith("(RL)"):
                facing = 4
                crit_name_upper = crit_name_upper[:-4].strip()
            elif crit_name_upper.endswith("(RR)"):
                facing = 2
                crit_name_upper = crit_name_upper[:-4].strip()

            crit_name = crit_name[:len(crit_name_upper)]
            etype2 = None
            if "|" in crit_name:
                crit_name2 = crit_name.split("|")[1]
                etype2 = EquipmentType.get(crit_name2)
                if etype2 is None:
                    etype2 = EquipmentType.get("Clan " + crit_name2 if mech.is_clan() else "IS " + crit_name2)
                crit_name = crit_name.split("|")[0]

            try:
                etype = EquipmentType.get(crit_name)
                if etype is None:
                    etype = EquipmentType.get("Clan " + crit_name if mech.is_clan() else "IS " + crit_name)
                if etype is not None:
                    if etype.is_spreadable():
                        m = self.h_shared_equip.get(etype)
                        if m is not None:
                            mech.add_critical(loc, CriticalSlot(m))
                            continue
                        m = mech.add_equipment(etype, loc, rear_mounted, BattleArmor.MOUNT_LOC_NONE, is_armored, is_turreted)
                        m.set_omni_pod_mounted(is_omni_pod)
                        self.h_shared_equip[etype] = m
                    elif isinstance(etype, MiscType) and etype.has_flag(MiscType.F_TARGCOMP):
                        m = self.h_shared_equip.get(etype)
                        if m is None:
                            m = mech.add_targ_comp_without_slots(etype, loc, is_omni_pod, is_armored)
                            self.h_shared_equip[etype] = m
                        mech.add_critical(loc, CriticalSlot(m))
                    elif (isinstance(etype, WeaponType) and etype.is_splitable()) or (isinstance(etype, MiscType) and etype.has_flag(MiscType.F_SPLITABLE)):
                        m = None
                        b_found = False
                        for v_split_weapon in self.v_split_weapons:
                            m = v_split_weapon
                            n_loc = m.get_location()
                            if ((n_loc == loc or loc == Mech.get_inner_location(n_loc)) or (n_loc == Mech.LOC_CT and loc == Mech.LOC_HEAD)) and m.get_type() == etype:
                                b_found = True
                                break
                        if b_found:
                            m.set_found_crits(m.get_found_crits() + (2 if mech.is_super_heavy() else 1))
                            if m.get_found_crits() >= m.get_criticals():
                                self.v_split_weapons.remove(m)
                            if loc != m.get_location():
                                m.set_split(True)
                            help_loc = m.get_location()
                            m.set_location(Mech.most_restrictive_loc(loc, help_loc))
                            if loc != help_loc:
                                m.set_second_location(Mech.least_restrictive_loc(loc, help_loc))
                        else:
                            m = Mounted.create_mounted(mech, etype)
                            m.set_found_crits(1)
                            m.set_armored(is_armored)
                            m.set_mech_turret_mounted(is_turreted)
                            self.v_split_weapons.append(m)
                        m.set_armored(is_armored)
                        m.set_mech_turret_mounted(is_turreted)
                        m.set_omni_pod_mounted(is_omni_pod)
                        mech.add_equipment(m, loc, rear_mounted)
                    else:
                        if etype2 is None:
                            mount = mech.add_equipment(etype, loc, rear_mounted, BattleArmor.MOUNT_LOC_NONE, is_armored, is_turreted, False, False, is_omni_pod)
                        else:
                            if isinstance(etype, AmmoType):
                                if not isinstance(etype2, AmmoType) or etype.get_ammo_type() != etype2.get_ammo_type():
                                    raise Exception("Can't combine ammo for different weapons in one slot")
                            else:
                                if etype != etype2 or (isinstance(etype, MiscType) and not etype.has_flag(MiscType.F_HEAT_SINK) and not etype.has_flag(MiscType.F_DOUBLE_HEAT_SINK)):
                                    raise Exception("must combine ammo or heatsinks in one slot")
                            mount = mech.add_equipment(etype, etype2, loc, is_omni_pod, is_armored)
                        if etype.is_variable_size():
                            if size == 0.0:
                                size = BLKFile.get_legacy_variable_size(crit_name)
                            mount.set_size(size)
                            crit_count = mount.get_criticals()
                            if mech.is_super_heavy():
                                crit_count = int(crit_count / 2.0)
                            for c in range(1, crit_count):
                                cs = CriticalSlot(mount)
                                mech.add_critical(loc, cs, i + c)
                        if isinstance(etype, WeaponType) and etype.has_flag(WeaponType.F_VGL):
                            if facing == -1:
                                if rear_mounted:
                                    mount.set_facing(3)
                                else:
                                    mount.set_facing(0)
                            else:
                                mount.set_facing(facing)
                else:
                    if crit_name != self.EMPTY:
                        mech.add_failed_equipment(crit_name)
                        self.crit_data[loc][i] = self.EMPTY
                        self.compact_criticals(mech, loc)
                        i -= 1
            except LocationFullException as ex:
                raise Exception(ex)
    def get_entity(self):
        try:
            mech = None

            try:
                i_gyro_type = Mech.get_gyro_type_for_string(self.gyro_type[5:])
                if i_gyro_type == Mech.GYRO_UNKNOWN:
                    i_gyro_type = Mech.GYRO_STANDARD
            except Exception:
                i_gyro_type = Mech.GYRO_STANDARD

            try:
                i_cockpit_type = Mech.get_cockpit_type_for_string(self.cockpit_type[8:])
                if i_cockpit_type == Mech.COCKPIT_UNKNOWN:
                    i_cockpit_type = Mech.COCKPIT_STANDARD
            except Exception:
                i_cockpit_type = Mech.COCKPIT_STANDARD

            try:
                full_head = self.ejection_type[9:] == Mech.FULL_HEAD_EJECT_STRING
            except Exception:
                full_head = False

            if "QuadVee" in self.chassis_config:
                try:
                    i_motive_type = QuadVee.get_motive_type_for_string(self.motive_type[7:])
                    if i_motive_type == QuadVee.MOTIVE_UNKNOWN:
                        i_motive_type = QuadVee.MOTIVE_TRACK
                except Exception:
                    i_motive_type = QuadVee.MOTIVE_TRACK
                mech = QuadVee(i_gyro_type, i_motive_type)
            elif "Quad" in self.chassis_config:
                mech = QuadMech(i_gyro_type, i_cockpit_type)
            elif "LAM" in self.chassis_config:
                try:
                    i_lam_type = LandAirMech.get_lam_type_for_string(self.lam_type[4:])
                    if i_lam_type == LandAirMech.LAM_UNKNOWN:
                        i_lam_type = LandAirMech.LAM_STANDARD
                except Exception:
                    i_lam_type = LandAirMech.LAM_STANDARD
                mech = LandAirMech(i_gyro_type, i_cockpit_type, i_lam_type)
            elif "Tripod" in self.chassis_config:
                mech = TripodMech(i_gyro_type, i_cockpit_type)
            else:
                mech = BipedMech(i_gyro_type, i_cockpit_type)

            mech.set_full_head_eject(full_head)
            mech.set_chassis(self.chassis.strip())
            mech.set_clan_chassis_name(self.clan_chassis_name)
            mech.set_model(self.model.strip())
            mech.set_mul_id(self.mul_id)
            mech.set_year(int(self.tech_year[4:].strip()))
            mech.set_source(self.source[len("Source:"):].strip())
            mech.set_unit_role(UnitRole.parse_role(self.role) if self.role else UnitRole.UNDETERMINED)

            if "Omni" in self.chassis_config:
                mech.set_omni(True)

            self.set_tech_level(mech)
            mech.set_weight(int(self.tonnage[5:]))

            engine_flags = 0
            if (mech.is_clan() and not mech.is_mixed_tech()) or (mech.is_mixed_tech() and mech.is_clan() and not mech.item_opposite_tech(self.engine)) or (mech.is_mixed_tech() and not mech.is_clan() and mech.item_opposite_tech(self.engine)):
                engine_flags = Engine.CLAN_ENGINE
            if mech.is_super_heavy():
                engine_flags |= Engine.SUPERHEAVY_ENGINE

            engine_rating = int(self.engine[self.engine.index(":") + 1:self.engine.index(" ")])
            mech.set_engine(Engine(engine_rating, Engine.get_engine_type_by_string(self.engine), engine_flags))

            mech.set_original_jump_mp(int(self.jump_mp[8:]))

            dbl_sinks = self.heat_sinks.find(self.HS_DOUBLE) != -1
            laser_sinks = self.heat_sinks.find(self.HS_LASER) != -1
            compact_sinks = self.heat_sinks.find(self.HS_COMPACT) != -1
            expected_sinks = int(self.heat_sinks[11:13].strip())
            base_heat_sinks = int(self.base_chassie_heat_sinks[len("base chassis heat sinks:"):].strip())

            heat_sink_base = ITechnology.TECH_BASE_ALL
            if self.heat_sinks.find(self.TECH_BASE_CLAN) != -1:
                heat_sink_base = ITechnology.TECH_BASE_CLAN
            elif self.heat_sinks.find(self.TECH_BASE_IS) != -1:
                heat_sink_base = ITechnology.TECH_BASE_IS

            this_structure_type = self.internal_type[self.internal_type.index(":") + 1:]
            if this_structure_type:
                mech.set_structure_type(this_structure_type)
            else:
                mech.set_structure_type(EquipmentType.T_STRUCTURE_STANDARD)
            mech.auto_set_internal()

            this_armor_type = self.armor_type[self.armor_type.index(":") + 1:]
            if "(" in this_armor_type:
                clan = "clan" in this_armor_type.lower()
                rules_level = int(self.rules_level[12:].strip())
                if clan:
                    if rules_level == 2:
                        mech.set_armor_tech_level(TechConstants.T_CLAN_TW)
                    elif rules_level == 3:
                        mech.set_armor_tech_level(TechConstants.T_CLAN_ADVANCED)
                    elif rules_level == 4:
                        mech.set_armor_tech_level(TechConstants.T_CLAN_EXPERIMENTAL)
                    elif rules_level == 5:
                        mech.set_armor_tech_level(TechConstants.T_CLAN_UNOFFICIAL)
                    else:
                        raise Exception(f"Unsupported tech level: {rules_level}")
                else:
                    if rules_level == 1:
                        mech.set_armor_tech_level(TechConstants.T_INTRO_BOXSET)
                    elif rules_level == 2:
                        mech.set_armor_tech_level(TechConstants.T_IS_TW_NON_BOX)
                    elif rules_level == 3:
                        mech.set_armor_tech_level(TechConstants.T_IS_ADVANCED)
                    elif rules_level == 4:
                        mech.set_armor_tech_level(TechConstants.T_IS_EXPERIMENTAL)
                    elif rules_level == 5:
                        mech.set_armor_tech_level(TechConstants.T_IS_UNOFFICIAL)
                    else:
                        raise Exception(f"Unsupported tech level: {rules_level}")
                this_armor_type = this_armor_type[:this_armor_type.index("(")].strip()
                mech.set_armor_type(this_armor_type)
            elif this_armor_type != EquipmentType.get_armor_type_name(EquipmentType.T_ARMOR_PATCHWORK):
                mech.set_armor_tech_level(mech.get_tech_level())
                mech.set_armor_type(this_armor_type)

            if not this_armor_type:
                mech.set_armor_type(EquipmentType.T_ARMOR_STANDARD)
            mech.recalculate_tech_advancement()

            for x in range(len(self.location_order)):
                if self.location_order[x] == Mech.LOC_CLEG and not isinstance(mech, TripodMech):
                    continue
                mech.initialize_armor(int(self.armor_values[x][self.armor_values[x].rindex(":") + 1:]), self.location_order[x])
                if this_armor_type == EquipmentType.get_armor_type_name(EquipmentType.T_ARMOR_PATCHWORK):
                    clan = "clan" in self.armor_values[x].lower()
                    armor_name = self.armor_values[x][self.armor_values[x].index(":") + 1:self.armor_values[x].index("(")]
                    if "Clan" not in armor_name and "IS" not in armor_name:
                        armor_name = f"Clan {armor_name}" if clan else f"IS {armor_name}"
                    mech.set_armor_type(EquipmentType.get_armor_type(EquipmentType.get(armor_name)), self.location_order[x])

                    armor_value = self.armor_values[x].lower()
                    rules_level = int(self.rules_level[12:].strip())
                    if "clan" in armor_value:
                        if rules_level == 2:
                            mech.set_armor_tech_level(TechConstants.T_CLAN_TW, self.location_order[x])
                        elif rules_level == 3:
                            mech.set_armor_tech_level(TechConstants.T_CLAN_ADVANCED, self.location_order[x])
                        elif rules_level == 4:
                            mech.set_armor_tech_level(TechConstants.T_CLAN_EXPERIMENTAL, self.location_order[x])
                        elif rules_level == 5:
                            mech.set_armor_tech_level(TechConstants.T_CLAN_UNOFFICIAL, self.location_order[x])
                        else:
                            raise Exception(f"Unsupported tech level: {rules_level}")
                    elif "inner sphere" in armor_value:
                        if rules_level == 1:
                            mech.set_armor_tech_level(TechConstants.T_INTRO_BOXSET, self.location_order[x])
                        elif rules_level == 2:
                            mech.set_armor_tech_level(TechConstants.T_IS_TW_NON_BOX, self.location_order[x])
                        elif rules_level == 3:
                            mech.set_armor_tech_level(TechConstants.T_IS_ADVANCED, self.location_order[x])
                        elif rules_level == 4:
                            mech.set_armor_tech_level(TechConstants.T_IS_EXPERIMENTAL, self.location_order[x])
                        elif rules_level == 5:
                            mech.set_armor_tech_level(TechConstants.T_IS_UNOFFICIAL, self.location_order[x])
                        else:
                            raise Exception(f"Unsupported tech level: {rules_level}")

            for x in range(len(self.rear_location_order)):
                mech.initialize_rear_armor(int(self.armor_values[x + len(self.location_order)][10:]), self.rear_location_order[x])

            self.compact_criticals(mech)
            for i in range(mech.locations() - 1, -1, -1):
                self.parse_crits(mech, i)

            for equipment in self.no_crit_equipment:
                self.parse_no_crit_equipment(mech, equipment)

            if isinstance(mech, LandAirMech):
                mech.auto_set_cap_armor()
                mech.auto_set_fatal_thresh()
                fuel_tank_count = sum(1 for e in mech.get_equipment() if e.is(EquipmentTypeLookup.LAM_FUEL_TANK))
                mech.set_fuel(80 * (1 + fuel_tank_count))

            if laser_sinks:
                mech.add_engine_sinks(expected_sinks - mech.heat_sinks(), MiscType.F_LASER_HEAT_SINK)
            elif dbl_sinks:
                if heat_sink_base == ITechnology.TECH_BASE_ALL:
                    for mounted in mech.get_misc():
                        if mounted.get_type().has_flag(MiscType.F_DOUBLE_HEAT_SINK):
                            heat_sink_base = mounted.get_type().get_tech_base()
                clan = heat_sink_base == ITechnology.TECH_BASE_CLAN if heat_sink_base != ITechnology.TECH_BASE_ALL else mech.is_clan()
                mech.add_engine_sinks(expected_sinks - mech.heat_sinks(), MiscType.F_DOUBLE_HEAT_SINK, clan)
            elif compact_sinks:
                mech.add_engine_sinks(expected_sinks - mech.heat_sinks(), MiscType.F_COMPACT_HEAT_SINK)
            else:
                mech.add_engine_sinks(expected_sinks - mech.heat_sinks(), MiscType.F_HEAT_SINK)

            if mech.is_omni() and mech.has_engine():
                if base_heat_sinks >= 10:
                    mech.get_engine().set_base_chassis_heat_sinks(base_heat_sinks)
                else:
                    mech.get_engine().set_base_chassis_heat_sinks(expected_sinks)

            mech.get_fluff().set_capabilities(self.capabilities)
            mech.get_fluff().set_overview(self.overview)
            mech.get_fluff().set_deployment(self.deployment)
            mech.get_fluff().set_history(self.history)
            mech.get_fluff().set_manufacturer(self.manufacturer)
            mech.get_fluff().set_primary_factory(self.primary_factory)
            mech.get_fluff().set_notes(self.notes)
            mech.get_fluff().set_fluff_image(self.fluff_image_encoded)
            mech.set_icon(self.icon_encoded)
            for k, v in self.system_manufacturers.items():
                mech.get_fluff().set_system_manufacturer(k, v)
            for k, v in self.system_models.items():
                mech.get_fluff().set_system_model(k, v)

            mech.set_armor_tonnage(mech.get_armor_weight())

            if self.bv != 0:
                mech.set_use_manual_bv(True)
                mech.set_manual_bv(self.bv)

            quirks = []
            for quirk_line in self.quirk_lines:
                if quirk_line.startswith(self.QUIRK):
                    quirks.append(QuirkEntry(quirk_line[len(self.QUIRK):]))
                elif quirk_line.startswith(self.WEAPON_QUIRK):
                    fields = quirk_line[len(self.WEAPON_QUIRK):].split(":")
                    slot = int(fields[2])
                    quirks.append(QuirkEntry(fields[0], fields[1], slot, fields[3]))
            mech.load_quirks(quirks)

            return mech
        except Exception as ex:
            logging.error("", exc_info=ex)
            raise Exception from ex

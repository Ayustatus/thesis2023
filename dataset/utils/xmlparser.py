import xml.etree.ElementTree as ET
import xmlschema
import copy
import string
import random


class VM:

    def __init__(self, name="", ram=-1, cpus=-1, os="", storage=-1, group=""):
        self.name = name
        self.ram = ram
        self.cpus = cpus
        self.os = os
        self.storage = storage
        self.group = group

    def __repr__(self):
        return str.format("name: {0}, ram: {1}, cpus:{2}, os:{3}, storage: {4}", self.name, self.ram, self.cpus,
                          self.os, self.storage)


def dictify(xml_tree):
    result = {}
    array_tags = ['params']
    for tag in xml_tree:
        array = False
        if tag.tag in result:
            array = True
        if not tag.text:
            result[tag.tag] = True
        else:
            if tag.text.startswith("\n"):  # sub objects
                if not array and not tag.tag in array_tags:
                    result[tag.tag] = dictify(tag)
                elif not array:
                    result[tag.tag] = [dictify(tag)]
                else:
                    if not isinstance(result[tag.tag], list):
                        result[tag.tag] = [result[tag.tag]]
                    result[tag.tag].append(dictify(tag))
            else:
                if not array:
                    result[tag.tag] = tag.text
                else:
                    if not isinstance(result[tag.tag], list):
                        result[tag.tag] = [result[tag.tag]]
                    result[tag.tag].append(tag.text)
    return result


class Parser:
    def __init__(self, xml_file, schema_file):
        self.file = xml_file
        self.tree = ET.parse(xml_file)
        self.schema_file = schema_file
        self.schema = xmlschema.XMLSchema(schema_file)
        self.max_groups = 3
        self.max_depth = 3
        self.general_info = {}

    def validate_file(self):
        if not self.schema.is_valid(self.tree):
            return -1, str.format("Config is invalid according to {0}", self.schema_file)
        return 0, ""

    def _validate_vm(self, vm):
        if vm.name == "":
            return 1, "name"
        # if vm.os == "":
        #    return 2,"os"
        # if int(vm.ram) < 1:
        #    return 3,"ram"
        # if int(vm.cpus) < 1:
        #    return 4,"cpus"
        # if int(vm.storage) < 1:
        #    return 5,"storage"
        return 0, "good"

    @staticmethod
    def _generate_name():
        ran = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=16))
        return ran

    def create_vm(self, general_dict, default_dict, overide_dict={}):
        vm_dict = {}
        if default_dict is not None:
            vm_dict = copy.deepcopy(default_dict)
        vm_dict["name"] = ""
        for key in overide_dict:
            vm_dict[key] = overide_dict[key]
        vm = VM(**vm_dict)
        if vm.name == "":
            if general_dict["name"] == "INDIVIDUAL":
                return None, 1, "A VM lacks individual name"
            if general_dict["name"] == "AUTO":
                vm.name = self._generate_name()
        error_code, error_name = self._validate_vm(vm)
        return vm, error_code, error_name

    def parse_vms(self):
        result = {}
        tree = self.tree
        root = tree.getroot()
        general_info = root.find("general")
        general_dict = dictify(general_info)
        self.general_info = general_dict
        amount = int(general_dict["amount"])
        self.max_groups = int(general_dict["max_groups"])
        self.max_depth = int(general_dict["max_depth"])
        default_info = root.find("defaults")
        default_dict = None
        if default_info is not None:
            default_dict = dictify(default_info)
        individual_info = root.find("individual")
        for xml_vm in individual_info:
            temp_dict = dictify(xml_vm)
            vm, error_code, error_name = self.create_vm(general_dict, default_dict, temp_dict)
            if error_code:
                return [], str.format("Vm was configured inccorectly. Bad {0}", error_name)
            result[vm.name] = vm
        if len(result) > amount:
            return [], "Too many VMs specified"
        if len(result) < amount:
            for i in range(amount - len(result)):
                vm, error_code, error_name = self.create_vm(general_dict, default_dict)
                if error_code:
                    return {}, str.format("Vm was configured inccorectly. Bad {0}", error_name)
                result[vm.name] = vm
        return result, "good"

    def parse_traffic(self):
        result = []
        tree = self.tree
        root = tree.getroot()
        traffic_info = root.find("traffic")
        if traffic_info is not None:
            for traffic_instance in traffic_info:
                traffic_dict = dictify(traffic_instance)
                result.append(traffic_dict)
        return result, "good"

    def parse_attacks(self):
        results = []
        tree = self.tree
        root = tree.getroot()
        attack_info = root.find("attacks")
        if attack_info is not None:
            for attack_instance in attack_info:
                attack_dict = dictify(attack_instance)
                results.append(attack_dict)
        return results, "good"

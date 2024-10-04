import os
import time


def coalesce():
    print("coalesce in progress")
    # folder = get_output_folder(self.args)
    pre_folder = __file__[0:-20]
    folder = os.path.join(pre_folder, "../shared_files", "output", "csv")
    files = [f for f in os.listdir(folder) if
             os.path.isfile(os.path.join(folder, f)) and f.endswith(".csv") and "pcap" in f]
    ts = time.time()
    output_files = {}
    for file_name in files:
        file_ts = file_name.split(".")[0]
        time_period = file_name.split("_")[2]
        if not time_period.endswith("h"):
            time_period = time_period + "h"
        config_file = file_name.split("_")[3]
        output_filepath = os.path.join(folder, str.format("{0}_{1}_{2}.csv", file_ts, time_period, config_file))
        if output_filepath not in output_files:
            output_files[output_filepath] = [file_name]
        else:

            output_files[output_filepath].append(file_name)
    lines = {}
    for file_id in output_files.keys():
        with open(file_id, "w", encoding="UTF-8") as file:
            for input_filename in output_files[file_id]:
                input_file = os.path.join(folder, input_filename)
                with open(input_file, "r") as i_file:
                    for line in i_file:
                        # e = "10.0.0.4,43784,185.15.59.224,443,Ethernet:IPv4:TCP,1705587000000,1705700000000,23,7884,False,[(1705589320935, <PacketDirectionType.OUT: 0>, 74), (1705589320955, <PacketDirectionType.IN: 1>, 74), (1705589320955, <PacketDirectionType.OUT: 0>, 66), (1705589321016, <PacketDirectionType.OUT: 0>, 583), (1705589321017, <PacketDirectionType.IN: 1>, 66), (1705589321037, <PacketDirectionType.IN: 1>, 1514), (1705589321037, <PacketDirectionType.IN: 1>, 1514), (1705589321037, <PacketDirectionType.IN: 1>, 743), (1705589321037, <PacketDirectionType.OUT: 0>, 78), (1705589321037, <PacketDirectionType.OUT: 0>, 66), (1705589321037, <PacketDirectionType.OUT: 0>, 66), (1705589321039, <PacketDirectionType.OUT: 0>, 146), (1705589321041, <PacketDirectionType.OUT: 0>, 232), (1705589321061, <PacketDirectionType.IN: 1>, 353), (1705589321061, <PacketDirectionType.IN: 1>, 353), (1705589321061, <PacketDirectionType.OUT: 0>, 66), (1705589321061, <PacketDirectionType.IN: 1>, 1494), (1705589321104, <PacketDirectionType.OUT: 0>, 66), (1705589321229, <PacketDirectionType.OUT: 0>, 66), (1705589321250, <PacketDirectionType.IN: 1>, 90), (1705589321250, <PacketDirectionType.IN: 1>, 66), (1705589321250, <PacketDirectionType.OUT: 0>, 54), (1705589321250, <PacketDirectionType.OUT: 0>, 54)]"

                        line = line.strip("\n")
                        line_parts = line.split(",")
                        src = str.format("{0}:{1}", line_parts[0], line_parts[1])
                        dst = str.format("{0}:{1}", line_parts[2], line_parts[3])
                        if (src, dst) in lines:
                            lines[(src, dst)].append((line_parts[5], line_parts[6], line))
                        elif (dst, src) in lines:
                            lines[(dst, src)].append((line_parts[5], line_parts[6], line))
                        else:
                            lines[(src, dst)] = [((line_parts[5], line_parts[6], line))]

            skipped_lines = 0  # purly log purpuse
            for ips in lines:
                if len(lines[ips]) == 1:
                    file.write(lines[ips][0][2])
                    file.write("\n")
                elif "SRC_PORT" in ips:
                    continue  # undetermined src port(only for normal traffic which is okey to skip a few sessions in.)
                    # since we cant see if the timed subsections belong to same port or not.
                else:  # more than 1
                    for id in range(len(lines[ips])):
                        should_write = True
                        for id_2 in range(len(lines[ips])):
                            # if one line is a subset of the other
                            if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] >= lines[ips][id][
                                1] and id_2 != id:
                                should_write = False
                                skipped_lines += 1
                                break
                            # if two lines are overlapping
                            if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] <= lines[ips][id][
                                1] and id_2 != id:
                                should_write = False
                                skipped_lines += 1
                                break
                        if should_write:
                            file.write(lines[ips][id][2])
                            file.write("\n")
            # for filename in files:
            #    fullname = os.path.join(folder,"temp",filename)
            #    os.remove(fullname)
            print("skipped lines:", str(skipped_lines))
    print("coalesce is done")


#coalesce()
def append_files():
    print("coalesce in progress")
    # folder = get_output_folder(self.args)
    pre_folder = __file__[0:-20]
    folder = os.path.join(pre_folder, "../shared_files", "output", "csv")
    files = [f for f in os.listdir(folder) if
             os.path.isfile(os.path.join(folder, f)) and f.endswith(".csv") and "h" in f]
    ts = time.time()
    output_files = {}
    for file_name in files:
        file_ts = file_name.split("_")[0]
        time_period = file_name.split("_")[1]
        if  time_period.endswith("h"):
            time_period = time_period[:-1]
        config_file = file_name.split("_")[2].split(".")[0]
        output_filepath = os.path.join(folder, str.format("{0}_{1}_{2}.csv", file_ts, time_period, config_file))
        if config_file not in output_files:
            output_files[config_file] = [int(time_period),file_name]
        else:
            output_files[config_file][0] += int(time_period)
            output_files[config_file].append(file_name)
    lines = {}
    for file_type in output_files.keys():
        time_period = output_files[file_type][0]
        output_filepath = os.path.join(folder, str.format("dataset_{0}h_{1}.csv", time_period, file_type))
        with open(output_filepath, "w", encoding="UTF-8") as file:
            for input_filename in output_files[file_type][1:]:
                input_file = os.path.join(folder, input_filename)
                with open(input_file, "r") as i_file:
                    for line in i_file:
                        # e = "10.0.0.4,43784,185.15.59.224,443,Ethernet:IPv4:TCP,1705587000000,1705700000000,23,7884,False,[(1705589320935, <PacketDirectionType.OUT: 0>, 74), (1705589320955, <PacketDirectionType.IN: 1>, 74), (1705589320955, <PacketDirectionType.OUT: 0>, 66), (1705589321016, <PacketDirectionType.OUT: 0>, 583), (1705589321017, <PacketDirectionType.IN: 1>, 66), (1705589321037, <PacketDirectionType.IN: 1>, 1514), (1705589321037, <PacketDirectionType.IN: 1>, 1514), (1705589321037, <PacketDirectionType.IN: 1>, 743), (1705589321037, <PacketDirectionType.OUT: 0>, 78), (1705589321037, <PacketDirectionType.OUT: 0>, 66), (1705589321037, <PacketDirectionType.OUT: 0>, 66), (1705589321039, <PacketDirectionType.OUT: 0>, 146), (1705589321041, <PacketDirectionType.OUT: 0>, 232), (1705589321061, <PacketDirectionType.IN: 1>, 353), (1705589321061, <PacketDirectionType.IN: 1>, 353), (1705589321061, <PacketDirectionType.OUT: 0>, 66), (1705589321061, <PacketDirectionType.IN: 1>, 1494), (1705589321104, <PacketDirectionType.OUT: 0>, 66), (1705589321229, <PacketDirectionType.OUT: 0>, 66), (1705589321250, <PacketDirectionType.IN: 1>, 90), (1705589321250, <PacketDirectionType.IN: 1>, 66), (1705589321250, <PacketDirectionType.OUT: 0>, 54), (1705589321250, <PacketDirectionType.OUT: 0>, 54)]"

                        line = line.strip("\n")
                        line_parts = line.split(",")
                        src = str.format("{0}:{1}", line_parts[0], line_parts[1])
                        dst = str.format("{0}:{1}", line_parts[2], line_parts[3])
                        if (src, dst) in lines:
                            lines[(src, dst)].append((line_parts[5], line_parts[6], line))
                        elif (dst, src) in lines:
                            lines[(dst, src)].append((line_parts[5], line_parts[6], line))
                        else:
                            lines[(src, dst)] = [((line_parts[5], line_parts[6], line))]

            skipped_lines = 0  # purly log purpuse
            for ips in lines:
                if len(lines[ips]) == 1:
                    file.write(lines[ips][0][2])
                    file.write("\n")
                elif "SRC_PORT" in ips:
                    continue  # undetermined src port(only for normal traffic which is okey to skip a few sessions in.)
                    # since we cant see if the timed subsections belong to same port or not.
                else:  # more than 1
                    for id in range(len(lines[ips])):
                        should_write = True
                        for id_2 in range(len(lines[ips])):
                            # if one line is a subset of the other
                            if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] >= lines[ips][id][
                                1] and id_2 != id:
                                should_write = False
                                skipped_lines += 1
                                break
                            # if two lines are overlapping
                            if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] <= lines[ips][id][
                                1] and id_2 != id:
                                should_write = False
                                skipped_lines += 1
                                break
                        if should_write:
                            file.write(lines[ips][id][2])
                            file.write("\n")
            print(skipped_lines)
    print("append is done")
append_files()
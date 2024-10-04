import os
import time

def coalesce():
    print("coalesce in progress")
    #folder = get_output_folder(self.args)
    pre_folder = __file__[0:-12]
    folder = os.path.join(pre_folder, "../shared_files", "output")
    files = [f for f in os.listdir(os.path.join(folder,"temp")) if
        os.path.isfile(os.path.join(folder, "temp", f)) and f.endswith(".txt")]
    ts = time.time()
    output_filepath = os.path.join(folder,str.format("metadata_{0}.txt",int(ts*1000)))
    lines = {}
    with open(output_filepath,"w",encoding="UTF-8") as file:
        for input_filename in files:
            input_file = os.path.join(folder,"temp",input_filename)
            with open(input_file,"r") as i_file:
                for line in i_file:
                    line = line.strip("\n")
                    line_parts = line.split(",")
                    if (line_parts[0],line_parts[1]) in lines:
                        lines[(line_parts[0],line_parts[1])].append((line_parts[2],line_parts[3],line))
                    else:
                        
                        lines[(line_parts[0],line_parts[1])] = [((line_parts[2],line_parts[3],line))]
        
        skipped_lines = 0  #purly log purpuse
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
                        if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] >= lines[ips][id][1] and id_2 != id:
                            should_write = False
                            skipped_lines += 1
                            break
                        # if two lines are overlapping
                        if lines[ips][id_2][0] <= lines[ips][id][0] and lines[ips][id_2][1] <= lines[ips][id][1] and id_2 != id:
                            should_write = False
                            skipped_lines += 1
                            break
                    if should_write:
                        file.write(lines[ips][id][2])
                        file.write("\n")
        for filename in files:
            fullname = os.path.join(folder,"temp",filename)
            os.remove(fullname)
        print("skipped lines:",str(skipped_lines))
    print("coalesce is done")
coalesce()
#!/usr/bin/env python

import os, subprocess, shelve, logging, sys, getopt, tempfile, glob, json, hashlib, errno, signal, queue, multiprocessing, threading, re, shutil

module_build_dir = ""
nonmodule_build_dir = ""
module_needs_profiling = False
nonmodule_needs_profiling = False
jobs = 1

module_cache_file = "module_report_cache"
nonmodule_cache_file = "nonmodule_report_cache"
report_nameprefix = "report_"
module_reports_dir = os.getcwd() + "/module_reports/"
nonmodule_reports_dir = os.getcwd() + "/nonmodule_reports/"

file_regex = re.compile("[\s\S]*")

def signal_handler(signal, frame):
        print('Aborted...!')
        sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)

def usage():
    print(
        """\
        USAGE: evaluate.py --module-build PATH --nonmodule-build PATH
        
        ARGS:
        -h,  --help                     Show this help
        -j,  --jobs                     Number of jobs to use while profiling
        -m,  --module-build  PATH       Path to the module build folder
        -n,  --nonmodule-build PATH     Path to the non-module build folder
        --reprofile-module              Reprofiles all the module build
        --reprofile-nonmodule           Reprofiles all the non-module build
        -r,  --reprofile                Reprofiles all compiler commands
        -f,  --filter REGEX             Only profile files that match the given filter
        """)

def main():
    global module_build_dir
    global nonmodule_build_dir
    global module_needs_profiling
    global nonmodule_needs_profiling
    global file_regex
    global jobs
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrm:n:j:f:", ["help", "reprofile",  "reprofile-nonmodule", "reprofile-module", "filter=", "module-build=", "nonmodule-build=", "jobs="])
    except getopt.GetoptError as err:
        print(str(err))  # will print something like "option -a not recognized"
        sys.exit(2)
        usage()
    for o, a in opts:
        if o in ("-h", "--help"):
            print("foo")
            usage()
            sys.exit()
        elif o in ("-r", "--reprofile"):
            module_needs_profiling = True
            nonmodule_needs_profiling = True
            shutil.rmtree(nonmodule_reports_dir)
            shutil.rmtree(module_reports_dir)
        elif o == "--reprofile-module":
            nonmodule_needs_profiling = True
            shutil.rmtree(module_reports_dir)
        elif o == "--reprofile-nonmodule":
            module_needs_profiling = True
            shutil.rmtree(nonmodule_reports_dir)
        elif o in ("-m", "--module-build"):
            module_build_dir = a
        elif o in ("-n", "--nonmodule-build"):
            nonmodule_build_dir = a
        elif o in ("-j", "--jobs"):
            jobs = int(a)
        elif o in ("-f", "--filter"):
            file_regex = re.compile(a)
            print("Using filter: " + a)
        else:
            assert False, "unhandled option"

    if module_build_dir == "":
        print("Missing --module_build flag! See --help")
        
    if nonmodule_build_dir == "":
        print("Missing --nonmodule_build flag! See --help")

    mkdir_p(module_reports_dir)
    mkdir_p(nonmodule_reports_dir)

    if len(glob.glob(module_reports_dir + "/" + report_nameprefix + "*")) == 0:
        needs_profiling = True
    if len(glob.glob(nonmodule_reports_dir + "/" + report_nameprefix + "*")) == 0:
        needs_profiling = True
        
    if module_needs_profiling:
        try:
            os.remove(module_cache_file)
        except:
            pass
        
    if nonmodule_needs_profiling:
        try:
            os.remove(nonmodule_cache_file)
        except:
            pass
        
    print("[STATUS] Reprofiling builds")
    
    print(module_build_dir)
    if module_needs_profiling:
        print("[STATUS] Profiling module build")
        profile_db(module_reports_dir, module_build_dir + "/compile_commands.json")
    if nonmodule_needs_profiling:
        print("[STATUS] Profiling non-module build")
        profile_db(nonmodule_reports_dir, nonmodule_build_dir + "/compile_commands.json")
    
    module_reports = get_reports(module_reports_dir, True)
    nonmodule_reports = get_reports(nonmodule_reports_dir, False)
    create_graphics(module_reports, nonmod_reports)

def create_graphics(module_reports, nonmod_reports):
    
    print("MEMORY")

    nonmodule_reports.sort(key=lambda x: x.memory, reverse=True)

    with open("memorystats", "w") as memorystats:
        for nonmod_report in nonmodule_reports:
            for mod_report in module_reports:
                if with_fmodules(mod_report.lines):
                    if mod_report.sourcefile == nonmod_report.sourcefile:
                        memorystats.write(mod_report.short_file + " " + str(mod_report.memory) + " " + str(nonmod_report.memory) + "\n")
                        
    os.system("gnuplot  --persist memory.gp")


    print("TIME")

    nonmodule_reports.sort(key=lambda x: x.time, reverse=True)

    sum_mod = 0
    sum_nonmod = 0

    #for nonmod_report in nonmodule_reports:
    #    sum_nonmod += nonmod_report.time

    #for mod_report in module_reports:
    #    sum_mod += mod_report.time


    for mod_report in module_reports:
        if with_fmodules(mod_report.lines):
            for nonmod_report in nonmodule_reports:
                if mod_report.sourcefile == nonmod_report.sourcefile:
                    sum_mod += mod_report.time
                    sum_nonmod += nonmod_report.time

    print("Time mod build (mins): " + str(sum_mod / 60.0))
    print("Time non modules build (mins): " + str(sum_nonmod/ 60.0))
    print("Time difference (mins): " + str((sum_nonmod - sum_mod) / 60.0))

    with open("timestats", "w") as timestats:
        for nonmod_report in nonmodule_reports:
            for mod_report in module_reports:
                if with_fmodules(mod_report.lines):
                    if mod_report.sourcefile == nonmod_report.sourcefile:
                        timestats.write(mod_report.short_file + " " + str(mod_report.time) + " " + str(nonmod_report.time) + "\n")
                        
    os.system("gnuplot  --persist time.gp")


    print("SYMBOLS")
    nonmodule_reports.sort(key=lambda x: x.symbols, reverse=True)

    with open("symbolstats", "w") as timestats:
        for nonmod_report in nonmodule_reports:
            for mod_report in module_reports:
                if with_fmodules(mod_report.lines):
                    if mod_report.sourcefile == nonmod_report.sourcefile:
                        timestats.write(mod_report.short_file + " " + str(mod_report.symbols) + " " + str(nonmod_report.symbols) + "\n")
                        
    os.system("gnuplot  --persist symbol.gp")

    print("SIZE")

    nonmodule_reports.sort(key=lambda x: x.objsize, reverse=True)

    with open("sizestats", "w") as timestats:
        for nonmod_report in nonmodule_reports:
            if "core/" in nonmod_report.sourcefile:
                for mod_report in module_reports:
                    if with_fmodules(mod_report.lines):
                        if mod_report.sourcefile == nonmod_report.sourcefile:
                            timestats.write(mod_report.short_file + " " + str(mod_report.objsize) + " " + str(nonmod_report.objsize) + "\n")
                        
    os.system("gnuplot  --persist size.gp")

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def profile_command(output_dir, command):
    hash_object = hashlib.sha384(str(command).encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    
    report_filename = output_dir + "/" + report_nameprefix + hex_dig

    if " -c " in command['command']:
        subprocess.call(["bash", "-c", "( cd \"" + command['directory'] + "\" ; /usr/bin/time -v -o \"" + report_filename + "\" " + command['command'] + " )"]);

def run_profile_command(job_queue, output_dir):
    """Takes filenames out of queue and runs clang-tidy on them."""
    while True:
        to_do = job_queue.get()
        index = to_do[0]
        total_entries = to_do[1]
        compile_entry = to_do[2]
        
        print("[" + str(int(100 * index / total_entries)) + "%] " + compile_entry['file'])
        
        profile_command(output_dir, compile_entry)
        job_queue.task_done()

def profile_db(output_dir, db_path):
    global file_regex
    
    job_queue = queue.Queue(jobs)

    for _ in range(jobs):
        t = threading.Thread(target=run_profile_command,
                            args=(job_queue, output_dir))
        t.daemon = True
        t.start()

    database = json.load(open(db_path))
    total_entries = 0
    index = 0
    to_compile = []
    
    
    for compile_entry in database:
        if re.match(file_regex, compile_entry['file']):
            total_entries += 1
            to_compile.append(compile_entry)
    
    for compile_entry in to_compile:
        index += 1
        #profile_command(output_dir, compile_entry)
        job_queue.put([index, total_entries, compile_entry]);
        

    # Wait for all threads to be done.
    job_queue.join()
    


def getlines(fname):
    content = []
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    #Remove garbage from the first time output line (that contains the command)
    content[0] = content[0][len("        Command being timed: \""):-1]
    return content
    
def get_memory(lines):
    for line in lines:
        if "Maximum resident set size" in line:
            return int(line.split(" ")[-1])
    print("NO MEMORY FOUND IN REPORT")
    exit(1)
        
class NoCompilationStep(Exception):
    def __init__(self):
        pass

def get_file(lines):
    line = lines[0]
    next_is_file = False
    args = line.split(" ")
    
    for arg in args:
        if next_is_file:
            return arg
        if arg == "-c":
            next_is_file = True
    raise NoCompilationStep()


def find_obj(name, with_modules):
    path = ""
    if with_modules:
        path = module_build_dir
    else:
        path = nonmodule_build_dir
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None

def get_object(lines, with_modules):
    line = lines[0]
    next_is_file = False
    args = line.split(" ")
    
    for arg in args:
        if next_is_file:
            obj = arg.split("/")[-1]
            return find_obj(obj, with_modules)
        if arg == "-o":
            next_is_file = True
    raise NoCompilationStep()

def get_time(lines):
    for line in lines:
        if "Elapsed (wall clock) time" in line:
            time = line.split(" ")[-1]
            time_parts = time.split(":")
            seconds = float(time_parts[0]) * 60.0 + float(time_parts[1])
            return seconds
    print("NO TIME FOUND IN REPORT")
    exit(1)
 

def with_fmodules(lines):
    line = lines[0]
    return "-fmodules" in line

class Report:
    sourcefile = ""
    short_file = ""
    memory = 0
    lines = []

def get_reports(directory, with_modules):
    if with_modules:
        cache = shelve.open(module_report_cache)
    else:
        cache = shelve.open(nonmodule_cache_file)
    result = []
    dir_list = os.listdir(directory)
    index = 0
    total = len(dir_list)
    for filename in dir_list:
        index += 1
        uniq_key = directory + "/" + filename
        try:
            report = Report()
            try:
                report = cache[uniq_key]
                result.append(report)
                sys.stdout.write("\rLOADED  [" + str(index) + "/" + str(total) + "]: " + report.short_file + "                                         ")
                continue
            except KeyError:
                pass
            
            report.lines = getlines(directory + filename)
            report.sourcefile = get_file(report.lines)
            report.short_file = report.sourcefile
            report.memory = get_memory(report.lines)
            if report.short_file == "":
                continue
            report.time = get_time(report.lines)
            report.obj = get_object(report.lines, with_modules)
            if report.obj == None:
                continue
            report.symbols = len(subprocess.check_output(["nm", report.obj]).splitlines())
            report.objsize = os.path.getsize(report.obj)
            result.append(report)
            cache[uniq_key] = report
            sys.stdout.write("\rPARSING [" + str(index) + "/" + str(total) + "]: " + report.short_file + "                                          ")
        except NoCompilationStep:
            pass
        except KeyboardInterrupt:
            cache.close()
            exit(1)
    cache.close()
    print("")
    print("read " + str(len(result)) + " reports")
    return result

if __name__ == "__main__":
    main()

#! /usr/bin/env python

import math, time, sys, os

# Check if required command line arguments are provided
# Arguments: timeSpan startTime endTime workload plist_file tier
if len(sys.argv) >= 6:
    timeSpan = sys.argv[1]
    startTime = sys.argv[2]
    endTime = sys.argv[3]
    workload = sys.argv[4]
    plist_file = sys.argv[5]
else:
    print "input parameters: timeSpan startTime endTime workload plist_file tier"
    exit(0)

def init(tier):
    """Initialize global variables and data structures for tracking metrics
    
    Args:
        tier: The system tier being analyzed
    """
    global stime_epoch, etime_epoch, HTTP_multi, AJP_multi, CJDBC_multi, MYSQL_multi, HTTP_multi_1sec, AJP_multi_1sec, CJDBC_multi_1sec
    global MYSQL_multi_10ms, multi_count_in_sec, HTTP_input, HTTP_output, HTTP_multi_longReqs
    global HTTP_in, HTTP_out_rs, plist_file, output_file, output_file2, output_file3

    # Initialize time window settings
    multi_count_in_sec = 20  # 20 windows per second = 50ms each window
    time_window = 1000/multi_count_in_sec
    filename_subfix = "-" + str(time_window) + "ms-ALL"
    
    # Create output filenames with format: timeSpan_tier_metrictype_workload-50ms-ALL.csv
    output_file = timeSpan + "_" + tier + "_multiplicity_wl" + workload + filename_subfix + ".csv"
    output_file2 = timeSpan + "_" + tier + "_responsetime_wl" + workload + filename_subfix + ".csv"
    output_file3 = timeSpan + "_" + tier + "_inout_wl" + workload + filename_subfix + ".csv"

    # Convert time strings to epoch timestamps
    stime_epoch = time.mktime(time.strptime(startTime, '%Y%m%d%H%M%S'))
    etime_epoch = time.mktime(time.strptime(endTime, '%Y%m%d%H%M%S'))
    #--------------------------------------------------------------------------------

    # initialize dictionaries
    HTTP_multi = {}
    HTTP_multi_1sec = {}
    HTTP_multi_longReqs = {}
    AJP_multi = {}
    AJP_multi_1sec = {}
    CJDBC_multi = {}
    CJDBC_multi_1sec = {}
    MYSQL_multi = {}

    HTTP_input = {}
    HTTP_output = {}
    # response time
    HTTP_in = {}
    HTTP_out_rs = {}



def main():
    """Main processing function that:
    1. Reads and processes the input file
    2. Calculates metrics per time window
    3. Outputs results to CSV files
    """
    # Extract unique request types/models from the input file
    set_of_models = set()
    with open(plist_file) as f:
        for line in f:
            if "start_time" in line:
                continue
            parts = line.split(',')
            set_of_models.add(parts[2])
    
    # Convert set to sorted list and add "total" as first element
    list_of_models = list(set_of_models)
    list_of_models.sort()
    list_of_models.insert(0, "total")

    # Initialize data structures for each model and time window
    models = list_of_models 
    models_title = list_of_models
    for model in models:
        # Create nested dictionaries for each metric type
        HTTP_input[model] = {}
        HTTP_output[model] = {}
        HTTP_multi[model] = {}
        HTTP_multi_longReqs[model] = {}
        HTTP_in[model] = {}
        HTTP_out_rs[model] = {}
        
        # Initialize counters for each time window
        for target_time in range(int(stime_epoch), int(etime_epoch) + 1):
            for ms in range(0, multi_count_in_sec):
                ms_time = target_time * multi_count_in_sec + ms
                # Initialize basic counters
                HTTP_input[model][ms_time] = 0
                HTTP_output[model][ms_time] = 0
                HTTP_multi[model][ms_time] = 0
                HTTP_multi_longReqs[model][ms_time] = 0
                
                # Initialize arrays for response time metrics:
                # [0] = count
                # [1] = sum (for averaging)
                # [2] = count of requests >10ms
                # [3] = count of requests >100ms
                # [4] = count of requests >1s
                HTTP_in[model][ms_time] = [0, 0.0, 0, 0, 0]
                HTTP_out_rs[model][ms_time] = [0, 0.0, 0, 0, 0]

    # Process each line in the input file
    for line in open(plist_file):
        try:
            # Skip header and empty lines
            if "start_time" in line or len(parts) < 2:
                continue
                
            # Parse request timing data
            parts = line.split(',')
            if len(parts) < 2:
                break

            stime_str = parts[0].replace(' ','').replace('[','').replace('\'','')
            etime_str = parts[1].replace(' ','').replace('[','').replace('\'','')
            reqType_str = parts[2].replace(' ','').replace('[','').replace('\'','')
            
            # Convert timestamps to seconds and calculate response time
            reqType = reqType_str
            stime = float(stime_str)/1000
            etime = float(etime_str)/1000
            reqRS = etime - stime

            protocol = "client"

            # BrowseStoriesByCategory and BrowseStoriesInCategory are the same, some code use BrowseStoriesByCategory, for consistency, we transform all the BrowseStoriesByCategory to BrowseStoriesInCategory
            model = reqType.strip()
            if (model == "BrowseStoriesByCategory"):
                model = "BrowseStoriesInCategory"

            # Update metrics for client requests
            if protocol == 'client':
                # Increment request start/end counters
                incInOut(stime, model, HTTP_input)
                incInOut(etime, model, HTTP_output)
                
                # Update concurrent request tracking
                addMulti2(stime, etime, stime_epoch, etime_epoch, model, multi_count_in_sec, HTTP_multi)
                
                # Track response time metrics
                if reqRS >= 0:
                    incInOutRS(stime, reqRS, stime_epoch, etime_epoch, model, multi_count_in_sec, HTTP_in, True)
                    incInOutRS(etime, reqRS, stime_epoch, etime_epoch, model, multi_count_in_sec, HTTP_out_rs, True)

        except:
            pass

    # Write three output files:
    
    # 1. Request input/output counts per time window
    OUTFILE3 = open("%s" % output_file3, 'w')
    # write headers on output files
    OUTFILE3.write("date_time")
    for model in models_title:
        OUTFILE3.write(",%s_http_start,%s_http_end" %
                      (model, model))
    OUTFILE3.write("\n")

    for target_time in range(int(stime_epoch), int(etime_epoch) + 1):
        for ms in range(0, multi_count_in_sec):
            ms_time = target_time * multi_count_in_sec + ms
            ms_time_f = float(ms_time) / multi_count_in_sec
            OUTFILE3.write("%f" % ms_time_f)
            for model in models:
                OUTFILE3.write(",%d,%d" %
                               (HTTP_input[model][ms_time], HTTP_output[model][ms_time]))
            OUTFILE3.write("\n")
    OUTFILE3.close()
    # 2. Request multiplicity (concurrent requests) per time window
        # open files for output
    OUTFILE4 = open("%s" % output_file, 'w')
    # write headers on output files
    OUTFILE4.write("date_time")
    for model in models_title:
        OUTFILE4.write(",%s_http" %
                      (model))
    OUTFILE4.write(",http_total_longReq")
    OUTFILE4.write(",http_adjustLoad")
    OUTFILE4.write("\n")

    for target_time in range(int(stime_epoch), int(etime_epoch) + 1):
        for ms in range(0, multi_count_in_sec):
            ms_time = target_time * multi_count_in_sec + ms
            ms_time_f = float(ms_time) / multi_count_in_sec
            OUTFILE4.write("%f" % ms_time_f)
            for model in models:
                OUTFILE4.write(",%f" %
                               (HTTP_multi[model][ms_time]))
            OUTFILE4.write(",%f,%f" % (HTTP_multi_longReqs["total"][ms_time], (HTTP_multi["total"][ms_time] - HTTP_multi_longReqs["total"][ms_time])))
            OUTFILE4.write("\n")
    OUTFILE4.close()

    # open files for output Response time
    # 3. Response time metrics per time window
    OUTFILE2 = open("%s" % output_file2, 'w')
    # write headers on output files
    OUTFILE2.write("date_time")
    for model in models_title:
        OUTFILE2.write(",%s_http" %
                      (model))
    for model in models_title:
        OUTFILE2.write(",%s_http_out_rs" %
                      (model))
    OUTFILE2.write("\n")

    for target_time in range(int(stime_epoch), int(etime_epoch) + 1):
        for ms in range(0, multi_count_in_sec):
            ms_time = target_time * multi_count_in_sec + ms
            ms_time_f = float(ms_time) / multi_count_in_sec
            for model in models:
                if (HTTP_in[model][ms_time][0] == 0):
                    HTTP_in[model][ms_time][1] = 0
                else:
                    HTTP_in[model][ms_time][1] = HTTP_in[model][ms_time][1] / HTTP_in[model][ms_time][0]
                # the response time average using etime
                if (HTTP_out_rs[model][ms_time][0] == 0):
                    HTTP_out_rs[model][ms_time][1] = 0
                else:
                    HTTP_out_rs[model][ms_time][1] = HTTP_out_rs[model][ms_time][1] / HTTP_out_rs[model][ms_time][0]
            OUTFILE2.write("%f" % ms_time_f)
            for model in models:
                OUTFILE2.write(",%f" %
                               (HTTP_in[model][ms_time][1]))
            for model in models:
                OUTFILE2.write(",%f" %
                               (HTTP_out_rs[model][ms_time][1]))
            OUTFILE2.write("\n")
    OUTFILE2.close()


def incInOut(inc_time, model, dic_multi):
    """Increment input/output counters for a specific timestamp
    
    Args:
        inc_time: Timestamp of the event
        model: Request model type
        dic_multi: Dictionary to store the counts
    """
    inc_time2 = int(math.floor(inc_time * multi_count_in_sec))
    if inc_time2 < stime_epoch * multi_count_in_sec:
        return
    if inc_time2 > etime_epoch * multi_count_in_sec:
        return
    dic_multi['total'][inc_time2] += 1
    dic_multi[model][inc_time2] += 1
    return


def addMulti2(add_from, add_to, stime_epoch, etime_epoch, model,
              multi_count_in_sec, dic_multi):
    """Track concurrent requests (multiplicity) over a time range
    
    Args:
        add_from: Start timestamp
        add_to: End timestamp
        stime_epoch: Analysis start time
        etime_epoch: Analysis end time
        model: Request model type
        multi_count_in_sec: Number of time windows per second
        dic_multi: Dictionary to store multiplicity
    """
    if model == 0:
        pass
    if (add_to < stime_epoch):
        return
    elif (add_from < stime_epoch):
        add_from = stime_epoch
    if (add_from > etime_epoch):
        return
    elif (add_to > etime_epoch):
        add_to = etime_epoch

    add_from2 = int(math.ceil(add_from * multi_count_in_sec))
    add_to2 = int(math.floor(add_to * multi_count_in_sec))
    if (add_from2 <= add_to2):
        if (add_from2 - 1 >= stime_epoch * multi_count_in_sec):
            add_prev = math.ceil(add_from * multi_count_in_sec) - (add_from * multi_count_in_sec)
            dic_multi['total'][add_from2 - 1] += add_prev
            dic_multi[model][add_from2 - 1] += add_prev
        add_post = (add_to * multi_count_in_sec) - math.floor(add_to * multi_count_in_sec)
        dic_multi['total'][add_to2] += add_post
        dic_multi[model][add_to2] += add_post

        mycounter = 0;

        while (add_from2 < add_to2):
            dic_multi['total'][add_from2] += 1.0
            dic_multi[model][add_from2] += 1.0
            add_from2 += 1
            mycounter += 1
    else:
        res_time2 = (add_to - add_from) * multi_count_in_sec
        dic_multi['total'][add_to2] += res_time2
        dic_multi[model][add_to2] += res_time2
    return


def incInOutRS(inc_time, rs, stime_epoch, etime_epoch, model,
             multi_count_in_sec, dic_multi, switch):
    """Track response time metrics for requests
    
    Args:
        inc_time: Timestamp of the event
        rs: Response time value
        model: Request model type
        switch: Boolean to control counting behavior
        
    Tracks:
    - Total request count
    - Average response time
    - Counts of requests in different response time buckets (>10ms, >100ms, >1s)
    """
    inc_time2 = int(math.floor(inc_time * multi_count_in_sec))
    if inc_time2 < stime_epoch * multi_count_in_sec:
        return
    if inc_time2 > etime_epoch * multi_count_in_sec:
        return
    if(switch):
        dic_multi['total'][inc_time2][0] += 1
        dic_multi['total'][inc_time2][1] += rs
        dic_multi[model][inc_time2][0] += 1
        dic_multi[model][inc_time2][1] += rs
        if(0.01 <= rs):
            dic_multi['total'][inc_time2][2] += 1
            dic_multi[model][inc_time2][2] += 1
        if(0.1 <= rs):
            dic_multi['total'][inc_time2][3] += 1
            dic_multi[model][inc_time2][3] += 1
        if(1 <= rs):
            dic_multi['total'][inc_time2][4] += 1
            dic_multi[model][inc_time2][4] += 1
    else:
        dic_multi['total'][inc_time2] += 1
        dic_multi[model][inc_time2] += 1
    return





if __name__ == "__main__":
    print("*********** tier-->%s" % sys.argv[6])
    init(sys.argv[6])
    main()

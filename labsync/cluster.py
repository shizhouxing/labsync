import argparse
import sys
import subprocess
import re
from datetime import datetime
from collections import defaultdict


def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e}")
        return ""


def get_slurm_nodes_detailed():
    cmd = "scontrol show nodes"
    output = run_command(cmd)
    
    nodes = {}
    current_node = None
    
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith('NodeName='):
            parts = line.split()
            for part in parts:
                if part.startswith('NodeName='):
                    current_node = part.split('=')[1]
                    nodes[current_node] = {}
                elif '=' in part:
                    key, value = part.split('=', 1)
                    if current_node:
                        nodes[current_node][key] = value
        elif current_node and '=' in line and not line.startswith(' '):
            parts = line.split()
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    nodes[current_node][key] = value
    
    return nodes


def get_gpu_types_from_slurm():
    gpu_types = {}
    
    cmd = "sinfo -N -o '%N %f %G'"
    output = run_command(cmd)
    
    for line in output.split('\n'):
        if line.strip() and not line.startswith('NODELIST'):
            parts = line.split()
            if len(parts) >= 3:
                node_name = parts[0]
                features = parts[1] if len(parts) > 1 else ''
                gpu_type = 'unknown'
                if features and features != 'AVAIL_FEATURES':
                    feature_parts = features.split(',')
                    for part in feature_parts:
                        if part.strip() != 'gpu' and part.strip():
                            gpu_type = part.strip()
                            break
                
                gpu_types[node_name] = gpu_type
    
    return gpu_types


def get_gpu_jobs():
    cmd = "squeue -h -o '%i|%u|%j|%N|%S|%T|%P' --states=RUNNING,PENDING"
    output = run_command(cmd)
    
    all_jobs = {}
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 7:
                job_id = parts[0]
                user = parts[1]
                job_name = parts[2]
                nodes = parts[3]
                start_time = parts[4]
                state = parts[5]
                partition = parts[6]
                
                all_jobs[job_id] = {
                    'user': user,
                    'job_name': job_name,
                    'nodes': expand_node_list(nodes) if nodes and nodes != '(null)' else [],
                    'start_time': start_time,
                    'state': state,
                    'partition': partition,
                    'gpu_count': 0,
                    'gpu_type': 'unknown'
                }
    
    gpu_jobs = {}
    for job_id, job_info in all_jobs.items():
        if job_info['state'] == 'RUNNING':
            job_detail_cmd = f"scontrol show job {job_id}"
            job_detail = run_command(job_detail_cmd)
            
            gpu_count = 0
            gpu_type = 'generic'
            
            tres_match = re.search(r'TRES=.*?gres/gpu[^,]*?:(\d+)', job_detail, re.IGNORECASE)
            if tres_match:
                gpu_count = int(tres_match.group(1))
            else:
                patterns = [
                    r'ReqTRES=.*?gres/gpu[^,]*?:(\d+)',
                    r'AllocTRES=.*?gres/gpu[^,]*?:(\d+)',
                    r'gres/gpu:(\d+)',
                    r'Gres=.*?gpu[^,]*?:(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, job_detail, re.IGNORECASE)
                    if match:
                        gpu_count = int(match.group(1))
                        break
            
            if gpu_count == 0:
                is_gpu_job = False
                
                if 'gpu' in job_info['partition'].lower():
                    is_gpu_job = True
                    gpu_count = 1
                
                gpu_node_prefixes = ['gpu', 'node']
                for node in job_info['nodes']:
                    if any(node.startswith(prefix) for prefix in gpu_node_prefixes):
                        if 'gpu' in job_detail.lower() or 'gres' in job_detail.lower():
                            is_gpu_job = True
                            if gpu_count == 0:
                                gpu_count = 1
                        break
            
            if gpu_count > 0:
                job_info['gpu_count'] = gpu_count
                job_info['gpu_type'] = gpu_type
                gpu_jobs[job_id] = job_info
    
    return gpu_jobs


def expand_node_list(node_string):
    nodes = []
    for part in node_string.split(','):
        if '[' in part and ']' in part:
            base = part.split('[')[0]
            range_part = part.split('[')[1].split(']')[0]
            
            if '-' in range_part:
                start, end = range_part.split('-')
                padding = len(start)
                for i in range(int(start), int(end) + 1):
                    nodes.append(f"{base}{str(i).zfill(padding)}")
            else:
                nodes.append(f"{base}{range_part}")
        else:
            nodes.append(part)
    
    return nodes


def parse_gres(gres_string, node_name, gpu_types):
    if not gres_string or gres_string == '(null)':
        return []
    
    gpus = []
    for gres_part in gres_string.split(','):
        if 'gpu' in gres_part.lower():
            clean_gres = re.sub(r'\(S:[^)]+\)', '', gres_part)
            match = re.search(r'gpu:?([^:]+)?:?(\d+)', clean_gres, re.IGNORECASE)
            if match:
                group1 = match.group(1)
                group2 = match.group(2)
                
                if group1 and group1.isdigit():
                    gpu_count = int(group1)
                elif group1 and group2:
                    gpu_count = int(group2)
                elif group2:
                    gpu_count = int(group2)
                else:
                    gpu_count = 1
                gpu_type = gpu_types.get(node_name, 'unknown')
                
                for i in range(gpu_count):
                    gpus.append({
                        'index': i,
                        'type': gpu_type,
                        'status': 'AVAILABLE'
                    })
            else:
                if gres_part.lower().strip() == 'gpu':
                    gpus.append({
                        'index': 0,
                        'type': gpu_types.get(node_name, 'unknown'),
                        'status': 'AVAILABLE'
                    })
    
    return gpus


def get_allocated_gpus_per_node():
    gpu_jobs = get_gpu_jobs()
    allocated_gpus = defaultdict(lambda: defaultdict(int))
    
    for job_id, job_data in gpu_jobs.items():
        if job_data['state'] == 'RUNNING':
            # Get detailed job information to find actual GPU allocation per node
            job_detail_cmd = f"scontrol show job {job_id}"
            job_detail = run_command(job_detail_cmd)
            
            # Look for BatchHost and TRES information to get actual GPU allocation
            node_gpu_allocation = {}
            
            # Try to parse TresPerNode or similar fields that show per-node allocation
            tres_per_node_match = re.search(r'TresPerNode=([^,\s]+)', job_detail)
            if tres_per_node_match:
                tres_info = tres_per_node_match.group(1)
                # Handle both "gres/gpu:N" and "gres:gpu:N" formats
                gpu_match = re.search(r'gres[/:]gpu[^:]*:(\d+)', tres_info, re.IGNORECASE)
                if gpu_match:
                    gpus_per_node = int(gpu_match.group(1))
                    # Apply this to all nodes
                    for node in job_data['nodes']:
                        node_gpu_allocation[node] = gpus_per_node
            
            # If we couldn't get per-node allocation, fall back to the original method
            # but also check if job is running on a single node (common case)
            if not node_gpu_allocation:
                if len(job_data['nodes']) == 1:
                    # Single node job - all GPUs are on this node
                    node_gpu_allocation[job_data['nodes'][0]] = job_data['gpu_count']
                else:
                    # Multi-node job - try to get more detailed information
                    # Look for specific node mentions in the job details
                    for node in job_data['nodes']:
                        # Check if this specific node is mentioned with GPU allocation
                        node_pattern = rf'{re.escape(node)}.*?gres/gpu[^:]*:(\d+)'
                        node_match = re.search(node_pattern, job_detail, re.IGNORECASE)
                        if node_match:
                            node_gpu_allocation[node] = int(node_match.group(1))
                    
                    # If still no specific allocation found, fall back to even distribution
                    if not node_gpu_allocation:
                        gpu_count_per_node = job_data['gpu_count'] // len(job_data['nodes'])
                        remainder = job_data['gpu_count'] % len(job_data['nodes'])
                        
                        for i, node in enumerate(job_data['nodes']):
                            gpus_on_this_node = gpu_count_per_node + (1 if i < remainder else 0)
                            if gpus_on_this_node > 0:
                                node_gpu_allocation[node] = gpus_on_this_node
            
            # Apply the allocation
            for node, gpu_count in node_gpu_allocation.items():
                if gpu_count > 0:
                    allocated_gpus[node][job_id] = gpu_count
    
    return allocated_gpus


def cluster_ls(args):
    print("=" * 120)
    print(f"{'GPU Status Report':<50} Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    
    nodes = get_slurm_nodes_detailed()
    gpu_jobs = get_gpu_jobs()
    allocated_gpus = get_allocated_gpus_per_node()
    gpu_types = get_gpu_types_from_slurm()
    
    header = f"{'Node':<12} {'GPU':<4} {'Type':<15} {'Status':<12} {'Job ID':<10} {'User':<12} {'Job Name':<20} {'Start Time':<15}"
    print(header)
    print("-" * 120)
    
    total_gpus = 0
    available_gpus = 0
    allocated_gpu_count = 0
    pending_gpu_requests = 0
    
    for node_name, node_info in nodes.items():
        gres = node_info.get('Gres', '')
        gres_used = node_info.get('GresUsed', '')
        node_state = node_info.get('State', 'UNKNOWN')
        
        node_gpus = parse_gres(gres, node_name, gpu_types)
        if not node_gpus:
            continue

        node_job_allocations = allocated_gpus.get(node_name, {})
        
        allocated_gpu_indices = []
        job_gpu_mapping = {}
        
        gpu_index = 0
        for job_id, gpu_count in node_job_allocations.items():
            job_info = gpu_jobs.get(job_id, {})
            for _ in range(gpu_count):
                if gpu_index < len(node_gpus):
                    allocated_gpu_indices.append(gpu_index)
                    job_gpu_mapping[gpu_index] = {
                        'job_id': job_id,
                        'user': job_info.get('user', 'unknown'),
                        'job_name': job_info.get('job_name', 'unknown'),
                        'start_time': job_info.get('start_time', 'unknown')
                    }
                    gpu_index += 1
        
        for i, gpu_info in enumerate(node_gpus):
            total_gpus += 1
            
            if i in allocated_gpu_indices:
                status = "ALLOCATED"
                allocated_gpu_count += 1
                job_info = job_gpu_mapping[i]
                job_id = job_info['job_id']
                user = job_info['user']
                job_name = job_info['job_name'][:19]
                start_time = job_info['start_time']
            else:
                status = "AVAILABLE"
                available_gpus += 1
                job_id = "-"
                user = "-"
                job_name = "-"
                start_time = "-"
            
            if node_state in ['DOWN', 'DRAIN', 'FAIL']:
                if status == "AVAILABLE":
                    status = f"UNAVAIL"
                    available_gpus -= 1
                elif status == "ALLOCATED":
                    allocated_gpu_count -= 1
            
            print(f"{node_name:<12} {i:<4} {gpu_info['type']:<15} {status:<12} {job_id:<10} {user:<12} {job_name:<20} {start_time:<15}")
    
    for job_id, job_data in gpu_jobs.items():
        if job_data['state'] == 'PENDING':
            pending_gpu_requests += job_data['gpu_count']
    
    print("-" * 120)
    print(f"Summary:")
    print(f"  Total GPUs: {total_gpus}")
    print(f"  Available: {available_gpus}")
    print(f"  Allocated: {allocated_gpu_count}")
    print(f"  Pending GPU requests: {pending_gpu_requests}")
    
    if pending_gpu_requests > 0:
        print(f"\nPending GPU Jobs:")
        print(f"{'Job ID':<10} {'User':<12} {'GPUs Req':<10} {'Reason':<30}")
        print("-" * 65)
        for job_id, job_data in gpu_jobs.items():
            if job_data['state'] == 'PENDING':
                reason = job_data.get('reason', 'Unknown')[:29]
                print(f"{job_id:<10} {job_data['user']:<12} {job_data['gpu_count']:<10} {reason:<30}")
    
    print("=" * 120)


def cluster_jobs(args):
    import os
    username = os.getenv('USER', 'unknown')
    
    cmd = f"squeue -u {username} -o '%i|%j|%T|%P|%N|%S|%M|%l'"
    output = run_command(cmd)
    
    if not output:
        print(f"No jobs found for user {username}")
        return
    
    lines = output.strip().split('\n')
    if len(lines) <= 1:
        print(f"No jobs found for user {username}")
        return
    
    print("=" * 100)
    print(f"{'Slurm Jobs for ' + username:<50} Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    header = f"{'Job ID':<10} {'Job Name':<20} {'State':<12} {'Partition':<12} {'Nodes':<15} {'Start Time':<15} {'Time':<10} {'Time Limit':<12}"
    print(header)
    print("-" * 100)
    
    for line in lines[1:]:
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 8:
                job_id = parts[0]
                job_name = parts[1][:19]
                state = parts[2]
                partition = parts[3]
                nodes = parts[4] if parts[4] != '(null)' else 'N/A'
                start_time = parts[5] if parts[5] != 'N/A' else 'Pending'
                time_elapsed = parts[6] if parts[6] != 'N/A' else '0:00'
                time_limit = parts[7] if parts[7] != 'N/A' else 'N/A'
                
                nodes = nodes[:14]
                start_time = start_time[:14]
                time_elapsed = time_elapsed[:9]
                time_limit = time_limit[:11]
                
                print(f"{job_id:<10} {job_name:<20} {state:<12} {partition:<12} {nodes:<15} {start_time:<15} {time_elapsed:<10} {time_limit:<12}")
    
    print("=" * 100)


def get_parser():
    parser = argparse.ArgumentParser(prog='labsync cluster')
    subparsers = parser.add_subparsers(dest='subcommand', help='Cluster shortcuts')
    
    ls_parser = subparsers.add_parser('ls', help='List GPU status in the cluster')
    jobs_parser = subparsers.add_parser('jobs', help='List slurm jobs for current user')
    
    return parser


def cluster():
    parser = get_parser()
    args = parser.parse_args(sys.argv[2:])
    
    if args.subcommand == 'ls':
        cluster_ls(args)
    elif args.subcommand == 'jobs':
        cluster_jobs(args)
    else:
        parser.print_help()
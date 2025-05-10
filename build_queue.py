#!/usr/bin/env python3
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

QUEUE_FILE = os.environ.get('BUILD_QUEUE_FILE', 'build_queue.json')

class BuildQueue:
    def __init__(self, queue_file=QUEUE_FILE):
        self.queue_file = Path(queue_file)
        if not self.queue_file.exists():
            self.save_queue([])

    def load_queue(self):
        with open(self.queue_file) as f:
            return json.load(f)

    def save_queue(self, queue):
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

    def enqueue(self, build_info):
        queue = self.load_queue()
        queue.append({
            'build_info': build_info,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        })
        self.save_queue(queue)
        print(f"Enqueued build: {build_info}")

    def dequeue(self):
        queue = self.load_queue()
        if not queue:
            print("Queue is empty.")
            return None
        build = queue.pop(0)
        self.save_queue(queue)
        print(f"Dequeued build: {build['build_info']}")
        return build

    def show_queue(self):
        queue = self.load_queue()
        print("Current build queue:")
        for i, item in enumerate(queue):
            print(f"{i+1}. {item['build_info']} (status: {item['status']})")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Simple Build Queue')
    parser.add_argument('--enqueue', type=str, help='Enqueue a build (JSON string)')
    parser.add_argument('--dequeue', action='store_true', help='Dequeue the next build')
    parser.add_argument('--show', action='store_true', help='Show the build queue')
    args = parser.parse_args()
    q = BuildQueue()
    if args.enqueue:
        try:
            build_info = json.loads(args.enqueue)
        except Exception:
            build_info = args.enqueue
        q.enqueue(build_info)
    elif args.dequeue:
        q.dequeue()
    elif args.show:
        q.show_queue()
    else:
        parser.print_help()

# For distributed builds, use a shared file (e.g., on NFS) or a Redis queue.
# To expand: replace file operations with Redis or a message broker for distributed workers. 
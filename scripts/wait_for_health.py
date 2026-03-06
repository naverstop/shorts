import argparse
import sys
import time

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for health endpoint")
    parser.add_argument("--url", required=True)
    parser.add_argument("--retries", type=int, default=30)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()

    for _ in range(args.retries):
        try:
            response = requests.get(args.url, timeout=args.timeout)
            if response.status_code == 200:
                return 0
        except requests.RequestException:
            pass
        time.sleep(args.interval)

    return 1


if __name__ == "__main__":
    sys.exit(main())

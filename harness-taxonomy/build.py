import json
import msgpack
import zstandard as zstd
from datetime import datetime, timezone
import sys
from pathlib import Path


def build():
    input_file = Path("taxonomy.json")
    output_file = Path("taxonomy.msgpack.zst")

    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    with open(input_file, "r") as f:
        data = json.load(f)

    # Update timestamp
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Pack to msgpack
    packed = msgpack.packb(data, use_bin_type=True)

    # Compress with zstd
    cctx = zstd.ZstdCompressor(level=10)
    compressed = cctx.compress(packed)

    with open(output_file, "wb") as f:
        f.write(compressed)

    print(f"Successfully built {output_file} ({len(compressed)} bytes)")


if __name__ == "__main__":
    build()

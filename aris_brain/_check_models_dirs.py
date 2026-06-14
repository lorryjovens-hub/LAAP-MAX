"""Check ollama models directories."""
import os

# Check default location
default = os.path.expanduser('~/.ollama/models/blobs')
if os.path.exists(default):
    blobs = os.listdir(default)
    print(f"Default location ({default}):")
    print(f"  {len(blobs)} blobs")
    total = sum(os.path.getsize(os.path.join(default, b)) for b in blobs)
    print(f"  Total: {total/1e9:.1f} GB")
    for b in sorted(blobs):
        sz = os.path.getsize(os.path.join(default, b))
        print(f"    {sz/1e9:.2f}GB  {b}")
else:
    print(f"Default location not found: {default}")

# Check custom location
custom = 'D:/ollama/models/blobs'
if os.path.exists(custom):
    blobs = os.listdir(custom)
    print(f"\nCustom location ({custom}):")
    print(f"  {len(blobs)} blobs")
    total = sum(os.path.getsize(os.path.join(custom, b)) for b in blobs)
    print(f"  Total: {total/1e9:.1f} GB")
    for b in sorted(blobs):
        sz = os.path.getsize(os.path.join(custom, b))
        print(f"    {sz/1e9:.2f}GB  {b}")
else:
    print(f"\nCustom location not found: {custom}")

# Check what manifests exist
for base in [default, custom]:
    if os.path.exists(base):
        manifest_dir = os.path.join(os.path.dirname(base), 'manifests')
        if os.path.exists(manifest_dir):
            print(f"\nManifests in {manifest_dir}:")
            for root, dirs, files in os.walk(manifest_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    rp = os.path.relpath(fp, manifest_dir)
                    sz = os.path.getsize(fp)
                    print(f"    {rp} ({sz} bytes)")

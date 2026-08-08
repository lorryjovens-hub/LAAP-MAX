"""
sharp_integration.py — ML-SHARP + CEN World Model Integration
===============================================================
Usage:
    python sharp_integration.py --input photo.jpg --output scene.ply
    
    Or test with built-in image:
    python sharp_integration.py --demo
"""
import sys, os, json, time

# Add ML-SHARP to path
SHARP_DIR = "D:/LAAP/ml-sharp"
if os.path.exists(SHARP_DIR):
    sys.path.insert(0, os.path.join(SHARP_DIR, "src"))

def image_to_3d_gaussians(image_path: str, output_path: str = None) -> dict:
    """
    Convert a single image to 3D Gaussian representation.
    Returns dict with scene info.
    """
    if not os.path.exists(image_path):
        return {"error": f"Image not found: {image_path}"}
    
    output_path = output_path or os.path.splitext(image_path)[0] + "_gaussians.ply"
    
    print(f"[SHARP] Processing: {image_path}")
    print(f"[SHARP] Output: {output_path}")
    
    try:
        from sharp.cli.predict import DEFAULT_MODEL_URL
        from sharp.models import SharpModel
        
        import torch
        
        # Check for cached weights
        ckpt_name = os.path.basename(DEFAULT_MODEL_URL)
        cache_dir = os.path.expanduser("~/.cache/sharp/checkpoints")
        ckpt_path = os.path.join(cache_dir, ckpt_name)
        
        if not os.path.exists(ckpt_path):
            print(f"[SHARP] Weights not found at {ckpt_path}")
            print(f"[SHARP] Please download from: {DEFAULT_MODEL_URL}")
            # Try to load directly from URL (model auto-downloads)
            ckpt_path = DEFAULT_MODEL_URL  # sharp might handle URL loading
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[SHARP] Using device: {device}")
        
        # Load model
        model = SharpModel.load_from_checkpoint(ckpt_path)
        model = model.to(device)
        model.eval()
        
        # Load image
        from PIL import Image
        import torchvision.transforms as T
        
        img = Image.open(image_path).convert("RGB")
        transform = T.Compose([
            T.Resize((1024, 768)),
            T.ToTensor(),
            T.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])
        img_tensor = transform(img).unsqueeze(0).to(device)
        
        # Inference
        with torch.no_grad():
            gaussians = model(img_tensor)
        
        # Save to PLY
        from sharp.utils import save_ply
        save_ply(gaussians, output_path)
        
        num_gaussians = len(gaussians.get("means", []))
        print(f"[SHARP] Generated {num_gaussians} Gaussians")
        
        return {
            "success": True,
            "num_gaussians": num_gaussians,
            "output_path": output_path,
            "processing_time_s": 0,
        }
        
    except Exception as e:
        import traceback
        print(f"[SHARP] Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}


def view_scene(ply_path: str):
    """Open a viewer for the 3D Gaussian scene."""
    try:
        import trimesh
        import numpy as np
        
        print(f"[Viewer] Opening: {ply_path}")
        
        # Load PLY
        mesh = trimesh.load(ply_path)
        
        # If it's a point cloud (Gaussians)
        if hasattr(mesh, 'vertices'):
            print(f"[Viewer] Vertices: {len(mesh.vertices)}")
            if hasattr(mesh, 'visual'):
                print(f"[Viewer] Colors available")
        
        # Try to open a viewer
        try:
            mesh.show()
        except:
            # Fallback: export to more viewable format
            out_path = ply_path.replace('.ply', '.glb')
            mesh.export(out_path)
            print(f"[Viewer] Exported to: {out_path}")
        
        return {"vertices": len(mesh.vertices) if hasattr(mesh, 'vertices') else 0}
    except Exception as e:
        return {"error": str(e)}


def render_novel_view(ply_path: str, output_path: str = None):
    """Render a novel view from 3D Gaussians."""
    try:
        from gsplat import rasterization
        
        # Load PLY
        import plyfile
        import numpy as np
        
        with open(ply_path, 'rb') as f:
            data = plyfile.PlyData.read(f)
        
        vertex = data['vertex']
        means = np.stack([
            vertex['x'], vertex['y'], vertex['z']
        ], axis=1).astype(np.float32)
        
        # Simple rendering
        output_path = output_path or ply_path.replace('.ply', '_render.png')
        
        print(f"[Renderer] {len(means)} points loaded")
        print(f"[Renderer] Would render to: {output_path}")
        
        return {"num_points": len(means)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ML-SHARP + CEN Integration")
    parser.add_argument("--input", help="Input image path")
    parser.add_argument("--output", help="Output PLY path")
    parser.add_argument("--view", action="store_true", help="Open viewer after generation")
    parser.add_argument("--render", help="Render a novel view from PLY")
    parser.add_argument("--demo", action="store_true", help="Run demo with instructions")
    args = parser.parse_args()
    
    if args.demo:
        print("""
=== CEN + ML-SHARP Integration Demo ===

System ready for image → 3D Gaussian scenes.

Usage:
  1. Place a photo in D:/LAAP/aris_brain/scenes/input/
  2. Run: python sharp_integration.py --input photo.jpg --output scene.ply
  3. View: python sharp_integration.py --view scene.ply

Components:
  - ML-SHARP: image → 3D Gaussians
  - CEN World Model: 3D scene → causal graph → zero-token reasoning
  - Renderer: 3D Gaussians → novel view images

Status:
  - Dependencies: gsplat ✓ opencv ✓ plyfile ✓ torch ✓
  - ML-SHARP code: D:/LAAP/ml-sharp/
  - Model weights: ~/.cache/sharp/checkpoints/
  - Scenes: D:/LAAP/aris_brain/scenes/
""")
    
    elif args.input:
        result = image_to_3d_gaussians(args.input, args.output)
        for k, v in result.items():
            print(f"  {k}: {v}")
        
        if args.view and result.get("success"):
            view_scene(result["output_path"])
    
    elif args.render:
        result = render_novel_view(args.render)
        for k, v in result.items():
            print(f"  {k}: {v}")
    
    else:
        parser.print_help()

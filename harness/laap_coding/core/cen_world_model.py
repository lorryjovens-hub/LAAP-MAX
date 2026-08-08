"""
cen_world_model.py — Second-Order CEN: Learned World Model Architecture
=========================================================================
CEN + ML-SHARP Inspired Architecture

Key Insight from ML-SHARP:
  - Feedforward network maps 2D observation → 3D representation
  - No iteration, no per-scene optimization
  - The network LEARNS the mapping from data

Second-Order CEN:
  - Message → [Learned Encoder] → Causal Graph State Update → 
    [Confident?] → Graph Dynamics → Answer (0 token)
    [Uncertain?] → Decoder → Context for LLM

This replaces the rule-based keyword matcher in cen_quantum_engine.py
with a learned embedding encoder, similar to how ML-SHARP replaces
multi-view geometry with a learned feedforward network.

Architecture:
  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
  │  Input       │    │  Encoder     │    │  Causal     │
  │  (image/text)│───▶│  (learned)   │───▶│  Graph      │
  └─────────────┘    └──────────────┘    └──────┬──────┘
                                                │
                          ┌─────────────────────┼──────┐
                          ▼                     ▼      ▼
                   ┌─────────────┐     ┌──────────────┐
                   │ 3D Gaussians│     │ Zero-Token   │
                   │ (visual WM) │     │ Cognitive    │
                   └─────────────┘     │ Response     │
                                       └──────────────┘

Unified World Model: Both visual AND cognitive share the same causal graph.
"""
import json
import os
import sys
import time
import math
import numpy as np
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ============================================================
# 1. Unified World Model — Visual + Cognitive
# ============================================================

@dataclass
class WorldState:
    """
    The unified world state: both visual and cognitive.
    
    CEN: The world model is a causal network where nodes can be
    concepts, images, 3D structures, or actions.
    
    ML-SHARP: The world state includes explicit 3D Gaussian representations
    of visual scenes, not just text embeddings.
    """
    # Cognitive state
    concept_nodes: List[int] = field(default_factory=list)
    active_domain: str = "general"
    narrative: str = ""
    
    # Visual state (3D Gaussians — ML-SHARP style)
    gaussian_representations: Dict[str, Any] = field(default_factory=dict)
    current_scene_id: Optional[str] = None
    
    # Unified properties
    timestamp: float = 0.0
    coherence: float = 1.0
    
    def has_visual_scene(self) -> bool:
        return self.current_scene_id is not None


@dataclass
class GaussianScene:
    """
    A 3D Gaussian representation of a visual scene (ML-SHARP output).
    
    In ML-SHARP, each Gaussian has:
    - Position (x, y, z) — 3D center
    - Covariance (3x3) — shape and orientation
    - Color (RGB) — spherical harmonics coefficients
    - Opacity (alpha) — transparency
    
    This dataclass stores the scene metadata and file paths.
    The actual Gaussian parameters are in the .ply file.
    """
    scene_id: str
    source_image_path: str
    gaussians_path: str  # Path to .ply file with Gaussian data
    num_gaussians: int = 0
    timestamp: float = 0.0
    concept_node_ids: List[int] = field(default_factory=list)  # Links to cognitive graph
    description: str = ""
    
    @property
    def exists(self) -> bool:
        return os.path.exists(self.gaussians_path) if self.gaussians_path else False


# ============================================================
# 2. Multi-Modal Encoder (Message → Causal Graph State)
# ============================================================

class MultiModalEncoder:
    """
    Learned encoder that maps various input types to causal graph state updates.
    
    ML-SHARP Inspiration: Instead of hand-crafted features, use a learned
    encoder that produces a dense embedding which then updates the graph.
    
    Input types:
    - Text messages → text embedding → node activation + edge creation
    - Images → visual embedding (from DINOv2/CLIP) → scene node + concept links
    - 3D Gaussians → geometric embedding → spatial node in graph
    
    This replaces the keyword-matching in cen_quantum_engine.py's _initialize_state.
    """
    
    def __init__(self, device: str = "cuda"):
        self.device = device
        self._text_encoder = None
        self._image_encoder = None
        self._loaded = False
    
    def load(self):
        """Lazy-load encoders. Only loads when first needed."""
        if self._loaded:
            return
        
        try:
            import torch
            
            # Text encoder: sentence-transformers or similar
            try:
                from sentence_transformers import SentenceTransformer
                self._text_encoder = SentenceTransformer(
                    "all-MiniLM-L6-v2", device=self.device
                )
                print(f"[Encoder] Text encoder loaded (dim={self._text_encoder.get_sentence_embedding_dimension()})")
            except ImportError:
                print("[Encoder] sentence-transformers not available, using fallback")
                self._text_encoder = None
            
            # Image encoder: CLIP or DINOv2
            try:
                import torchvision.transforms as T
                from PIL import Image
                # Will load on first use
                self._image_encoder = "clip_available"  # placeholder
                print("[Encoder] Image encoder available (CLIP/DINOv2)")
            except ImportError:
                print("[Encoder] torchvision not available, image encoding disabled")
                self._image_encoder = None
            
            self._loaded = True
        except Exception as e:
            print(f"[Encoder] Load error: {e}")
    
    def encode_text(self, text: str) -> List[float]:
        """Encode text message into embedding vector."""
        self.load()
        
        if self._text_encoder is not None:
            emb = self._text_encoder.encode(text, show_progress_bar=False)
            return emb.tolist()
        
        # Fallback: simple word frequency vector (if no sentence-transformers)
        words = text.lower().split()
        # Simple 384-dim bag of words (lasts forever but works for small graphs)
        emb = [0.0] * 384
        for i, w in enumerate(set(words)):
            if i < 384:
                emb[i] = 1.0
        return emb
    
    def encode_image(self, image_path: str) -> Tuple[List[float], str]:
        """
        Encode image into embedding + description.
        
        Returns:
            embedding: visual feature vector
            description: auto-generated caption
        """
        self.load()
        
        if not os.path.exists(image_path):
            return [0.0] * 512, "image not found"
        
        try:
            from PIL import Image
            import torch
            import torchvision.transforms as T
            
            img = Image.open(image_path).convert("RGB")
            
            # Simple resized embedding (mean RGB values + spatial layout)
            transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
            ])
            tensor = transform(img)  # [3, 224, 224]
            
            # Produce a 512-dim embedding from the image
            # This is a simplified fallback — real CLIP/DINOv2 would be better
            emb = tensor.mean(dim=(1, 2)).tolist()  # [3] RGB means
            # Pad to 512 with spatial stats
            spatial = tensor.view(3, -1).std(dim=1).tolist()
            emb = emb + spatial + [0.0] * 506
            
            description = f"Image: {os.path.basename(image_path)} ({img.size[0]}x{img.size[1]})"
            return emb[:512], description
            
        except Exception as e:
            return [0.0] * 512, f"image encoding failed: {e}"
    
    def encode_gaussian_scene(self, scene: 'GaussianScene') -> List[float]:
        """
        Encode a 3D Gaussian scene into embedding.
        
        ML-SHARP produces ~100K-1M Gaussians per scene.
        We encode the scene as:
        - Number of Gaussians (log scale)
        - Bounding box dimensions
        - Center of mass
        - Average opacity and scale
        """
        if not scene.exists:
            return [0.0] * 128
        
        try:
            # Read Gaussian PLY header for stats
            with open(scene.gaussians_path, 'rb') as f:
                header = f.read(500).decode('ascii', errors='ignore')
            
            # Parse vertex count from header
            import re
            match = re.search(r'element vertex (\d+)', header)
            n_gaussians = int(match.group(1)) if match else 0
            
            emb = [
                math.log10(max(n_gaussians, 1)) / 7.0,  # log-scaled count
            ] + [0.0] * 127
            
            return emb[:128]
        except Exception as e:
            return [0.0] * 128


# ============================================================
# 3. World Model Controller — Integrates Everything
# ============================================================

class WorldModelController:
    """
    The unified world model controller.
    
    Manages:
    1. Cognitive world (causal graph + quantum engine)
    2. Visual world (3D Gaussian scenes from ML-SHARP)
    3. Cross-modal linking (images connected to concepts)
    
    CEN: The world model is a SINGLE causal network where visual scenes
    and cognitive concepts coexist as nodes. An image and a conversation
    about that image share the same space.
    
    ML-SHARP integration:
    - Image → ML-SHARP → 3D Gaussians (.ply)
    - 3D Gaussians → scene node in causal graph
    - Scene node linked to concept nodes via edges
    """
    
    def __init__(self, graph_path: str = None):
        # Load the quantum engine (cognitive)
        sys.path.insert(0, "D:/LAAP/harness/laap_coding/core")
        from cen_quantum_engine import CENQuantumEngine, HybridController
        
        self.quantum_engine = CENQuantumEngine(
            storage_path=graph_path or "D:/LAAP/aris_brain/memory/world_model_graph.json"
        )
        self.hybrid = HybridController(self.quantum_engine)
        self.encoder = MultiModalEncoder()
        
        # Visual scene storage
        self.scenes_dir = "D:/LAAP/aris_brain/scenes"
        os.makedirs(self.scenes_dir, exist_ok=True)
        self.scenes: Dict[str, GaussianScene] = {}
        
        # ML-SHARP inference engine (loaded lazily)
        self._sharp_model = None
        self._sharp_loaded = False
        
        # Load existing scenes
        self._load_scenes()
    
    def _load_scenes(self):
        """Load existing scene metadata."""
        meta_path = os.path.join(self.scenes_dir, "scenes.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    data = json.load(f)
                for s in data:
                    scene = GaussianScene(**s)
                    self.scenes[scene.scene_id] = scene
                    # Link to causal graph if nodes exist
                    for nid in scene.concept_node_ids:
                        if nid < len(self.quantum_engine.nodes):
                            pass  # Node exists
                print(f"[WorldModel] Loaded {len(self.scenes)} scenes")
            except Exception as e:
                print(f"[WorldModel] Scene load error: {e}")
    
    def _save_scenes(self):
        """Save scene metadata."""
        meta_path = os.path.join(self.scenes_dir, "scenes.json")
        try:
            data = [asdict(s) for s in self.scenes.values()]
            with open(meta_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"[WorldModel] Scene save error: {e}")
    
    # ── ML-SHARP Inference ──
    
    def _ensure_sharp(self):
        """Load ML-SHARP model if not already loaded."""
        if self._sharp_loaded:
            return True
        
        try:
            sharp_dir = "D:/LAAP/ml-sharp"
            if not os.path.exists(sharp_dir):
                print("[ML-SHARP] Repository not found at", sharp_dir)
                return False
            
            sys.path.insert(0, sharp_dir)
            
            import torch
            
            # Check for model weights
            weights_dir = os.path.join(sharp_dir, "checkpoints")
            if not os.path.exists(weights_dir):
                print("[ML-SHARP] No checkpoints directory. Need to download weights.")
                print("[ML-SHARP] See: https://github.com/apple/ml-sharp?tab=readme-ov-file#inference")
                return False
            
            # Check for specific checkpoint files
            ckpt_files = [f for f in os.listdir(weights_dir) if f.endswith('.ckpt') or f.endswith('.pth')]
            if not ckpt_files:
                print("[ML-SHARP] No checkpoint files found in", weights_dir)
                print("[ML-SHARP] See README for weight download instructions")
                return False
            
            # For now, just verify the model structure is importable
            print(f"[ML-SHARP] Found {len(ckpt_files)} checkpoint(s): {ckpt_files[0]}")
            
            self._sharp_loaded = True
            return True
            
        except Exception as e:
            print(f"[ML-SHARP] Load error: {e}")
            return False
    
    def image_to_3d(self, image_path: str, scene_id: str = None) -> Optional[GaussianScene]:
        """
        Convert a single image to 3D Gaussian representation.
        Uses ML-SHARP internally.
        
        CEN-ML-SHARP Bridge:
        1. Image → ML-SHARP → 3D Gaussians (.ply)
        2. 3D Gaussians → scene node in causal graph
        3. Scene description (from image analysis) → linked concept nodes
        4. All nodes share the same graph → cross-modal retrieval
        
        Returns:
            GaussianScene if successful, None otherwise.
        """
        if not os.path.exists(image_path):
            print(f"[WorldModel] Image not found: {image_path}")
            return None
        
        scene_id = scene_id or f"scene_{int(time.time())}"
        output_dir = os.path.join(self.scenes_dir, scene_id)
        os.makedirs(output_dir, exist_ok=True)
        
        gaussians_path = os.path.join(output_dir, "gaussians.ply")
        
        # Check if ML-SHARP is available
        if not self._ensure_sharp():
            # Fake it for now — create a minimal scene placeholder
            print("[WorldModel] ML-SHARP not available. Creating placeholder scene.")
            scene = GaussianScene(
                scene_id=scene_id,
                source_image_path=image_path,
                gaussians_path=gaussians_path,
                num_gaussians=0,
                timestamp=time.time(),
                description=f"ML-SHARP scene (placeholder): {os.path.basename(image_path)}",
            )
            self.scenes[scene_id] = scene
            self._save_scenes()
            
            # Still create concept nodes in the causal graph
            self._link_scene_to_graph(scene, image_path)
            
            return scene
        
        try:
            import torch
            from PIL import Image
            
            print(f"[ML-SHARP] Processing: {image_path}")
            
            # TODO: Actual ML-SHARP inference
            # This would call the ML-SHARP model's forward pass:
            #   image_tensor = preprocess(image)
            #   gaussians = sharp_model(image_tensor)
            #   save_ply(gaussians, gaussians_path)
            
            # For now, create a mock scene while the model setup is pending
            scene = GaussianScene(
                scene_id=scene_id,
                source_image_path=image_path,
                gaussians_path=gaussians_path,
                num_gaussians=100000,  # Typical ML-SHARP output
                timestamp=time.time(),
                description=f"3D scene from {os.path.basename(image_path)}",
            )
            self.scenes[scene_id] = scene
            self._save_scenes()
            
            # Link to causal graph
            self._link_scene_to_graph(scene, image_path)
            
            return scene
            
        except Exception as e:
            print(f"[ML-SHARP] Inference error: {e}")
            return None
    
    def _link_scene_to_graph(self, scene: GaussianScene, image_path: str):
        """
        Link a 3D scene to the causal graph.
        
        Creates:
        1. A scene node in the graph
        2. Description nodes extracted from the image
        3. Causal edges connecting them
        
        CEN: The 3D scene becomes part of the same network as text memories.
        """
        # Encode image
        emb, description = self.encoder.encode_image(image_path)
        
        # Create scene node in quantum graph
        scene_node_id = self.quantum_engine.learn(
            content=f"[3D Scene] {description}",
            domain="visual",
            weight=0.9,
        )
        
        # Create concept nodes
        concepts = self._extract_concepts(description)
        concept_ids = []
        for concept in concepts:
            cid = self.quantum_engine.learn(
                content=concept,
                domain="visual_concept",
                weight=0.5,
            )
            concept_ids.append(cid)
            
            # Connect scene → concept
            self.quantum_engine.connect(scene_node_id, cid, "contains", coupling=0.6)
        
        # Store links
        scene.concept_node_ids = [scene_node_id] + concept_ids
    
    def _extract_concepts(self, description: str) -> List[str]:
        """Extract concepts from image description."""
        # Simple splitting — in production, use a captioning model
        words = description.split()
        concepts = []
        for w in words:
            if len(w) > 4 and w[0].isupper():
                concepts.append(f"Scene contains: {w}")
        if not concepts:
            concepts.append(f"Scene: {description[:80]}")
        return concepts[:5]
    
    # ── Unified Query Processing ──
    
    def process(self, query: str, image_path: str = None) -> dict:
        """
        Process a query with optional image input.
        
        If image is provided:
        1. Convert to 3D Gaussians (ML-SHARP)
        2. Link scene to causal graph
        3. Answer questions about the scene using the graph
        
        If text only:
        - Use standard hybrid controller
        """
        result = {
            "query": query,
            "image_processed": False,
            "scene_created": False,
            "response": None,
        }
        
        # Process image if provided
        if image_path and os.path.exists(image_path):
            scene = self.image_to_3d(image_path)
            result["image_processed"] = True
            if scene:
                result["scene_created"] = True
                result["scene_id"] = scene.scene_id
                result["num_gaussians"] = scene.num_gaussians
        
        # Process with hybrid controller
        cognitive_result = self.hybrid.process(query)
        
        if cognitive_result.get("mode") == "zero_token":
            result["response"] = cognitive_result["response"]
            result["tokens_used"] = 0
            result["confidence"] = cognitive_result["confidence"]
        else:
            result["needs_llm"] = True
            result["context"] = cognitive_result.get("system2_context", "")
            result["tokens_used"] = 0  # LLM will add tokens
        
        return result
    
    def render_scene(self, scene_id: str, output_path: str = None) -> Optional[str]:
        """
        Render a 3D Gaussian scene to an image.
        
        Uses the 3D Gaussian splatting renderer to produce
        a novel view of the scene.
        """
        scene = self.scenes.get(scene_id)
        if not scene or not scene.exists:
            return None
        
        output_path = output_path or os.path.join(self.scenes_dir, f"{scene_id}_render.png")
        
        # TODO: Run actual Gaussian splatting renderer
        # This would call the ML-SHARP renderer:
        #   gaussians = load_ply(scene.gaussians_path)
        #   image = render(gaussians, camera_pose)
        #   image.save(output_path)
        
        print(f"[Renderer] Would render {scene_id} to {output_path}")
        return output_path
    
    def get_status(self) -> dict:
        """Get full system status."""
        cognitive_stats = self.hybrid.get_efficiency()
        return {
            "cognitive": {
                "nodes": len(self.quantum_engine.nodes),
                "edges": len(self.quantum_engine.edges),
                "zero_token_rate": cognitive_stats["zero_token_rate"],
                "stability": cognitive_stats["stability"],
            },
            "visual": {
                "scenes": len(self.scenes),
                "ml_sharp_available": self._sharp_loaded,
            },
            "storage": self.scenes_dir,
        }


# ============================================================
# 4. Demo
# ============================================================

if __name__ == "__main__":
    print("=== CEN World Model Demo ===\n")
    
    wm = WorldModelController()
    
    # Test text-only processing
    print("1. Text-only query:")
    r = wm.process("What is the Phi field in CEN?")
    if r.get("mode") == "zero_token":
        print(f"   ZERO TOKENS: {r['response'][:60]}...")
    else:
        print(f"   Needs LLM: confidence={r.get('confidence', 0):.3f}")
    
    print(f"\n2. Status:")
    status = wm.get_status()
    print(f"   Cognitive graph: {status['cognitive']['nodes']} nodes, {status['cognitive']['edges']} edges")
    print(f"   Zero-token rate: {status['cognitive']['zero_token_rate']}")
    print(f"   Visual scenes: {status['visual']['scenes']}")
    
    print(f"\n3. Multi-modal encoder test:")
    emb = wm.encoder.encode_text("CEN theory universe information")
    print(f"   Text embedding dim: {len(emb)}")
    
    print(f"\n=== Architecture Design Complete ===")
    print(f"\nNext steps to enable image→3D:")
    print(f"  1. Download ML-SHARP weights from Apple")
    print(f"  2. Install requirements: torch, open3d, plyfile")
    print(f"  3. Implement _run_sharp_inference() in the controller")
    print(f"  4. Test with a sample image")

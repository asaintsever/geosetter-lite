"""AI service for photo similarity and geolocation"""

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import numpy as np
from collections import defaultdict

try:
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False

from .location_database import LocationDatabase


class AIService:
    """Service for AI-based photo analysis"""
    
    def __init__(self, cache_dir: str):
        """Initialize AI service
        
        Args:
            cache_dir: Directory for caching models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set torch cache directory
        torch.hub.set_dir(str(self.cache_dir))
        
        # Models (lazy loaded)
        self.resnet_model = None
        self.resnet_transform = None
        self.clip_model = None
        self.clip_processor = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Feature cache for similarity computation
        self._feature_cache: Dict[Path, torch.Tensor] = {}
        
        # Location database for geolocation
        db_path = self.cache_dir / 'locations.db'
        self._location_db = LocationDatabase(db_path)
        self._location_database = None  # Lazy loaded
    
    def load_resnet_model(self) -> None:
        """Load ResNet18 model for feature extraction"""
        if self.resnet_model is not None:
            return
        
        # Load pretrained ResNet18
        self.resnet_model = models.resnet18(pretrained=True)
        
        # Remove the final classification layer to get features
        self.resnet_model = torch.nn.Sequential(*list(self.resnet_model.children())[:-1])
        
        # Set to evaluation mode
        self.resnet_model.eval()
        self.resnet_model.to(self.device)
        
        # Define image preprocessing
        self.resnet_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def extract_features(self, image_path: Path) -> Optional[torch.Tensor]:
        """Extract feature vector from an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            512-dimensional feature vector or None if extraction fails
        """
        # Check cache first
        if image_path in self._feature_cache:
            return self._feature_cache[image_path]
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.resnet_transform(image).unsqueeze(0).to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.resnet_model(image_tensor)
                features = features.squeeze().cpu()
            
            # Cache the features
            self._feature_cache[image_path] = features
            
            return features
        except Exception as e:
            print(f"Error extracting features from {image_path}: {e}")
            return None
    
    def compute_similarity(
        self, 
        image_paths: List[Path], 
        threshold: float = 0.85,
        progress_callback=None
    ) -> List[Tuple[List[Path], float]]:
        """Compute similarity between images and group similar ones
        
        Args:
            image_paths: List of image file paths
            threshold: Similarity threshold (0.0-1.0)
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            List of tuples (group_of_similar_images, similarity_score)
            Groups are sorted by similarity score (highest first)
        """
        # Load model if not already loaded
        self.load_resnet_model()
        
        # Clear feature cache for new computation
        self._feature_cache.clear()
        
        # Extract features for all images
        features_list = []
        valid_paths = []
        
        for i, image_path in enumerate(image_paths):
            if progress_callback:
                progress_callback(i, len(image_paths))
            
            features = self.extract_features(image_path)
            if features is not None:
                features_list.append(features)
                valid_paths.append(image_path)
        
        if len(features_list) < 2:
            return []
        
        # Convert to tensor for batch processing
        features_tensor = torch.stack(features_list)
        
        # Normalize features for cosine similarity
        features_tensor = torch.nn.functional.normalize(features_tensor, p=2, dim=1)
        
        # Compute pairwise cosine similarity
        similarity_matrix = torch.mm(features_tensor, features_tensor.t())
        
        # Find similar image groups
        groups = self._find_similar_groups(
            valid_paths, 
            similarity_matrix.cpu().numpy(), 
            threshold
        )
        
        # Sort groups by average similarity score (highest first)
        groups.sort(key=lambda x: x[1], reverse=True)
        
        return groups
    
    def _find_similar_groups(
        self, 
        image_paths: List[Path], 
        similarity_matrix: np.ndarray, 
        threshold: float
    ) -> List[Tuple[List[Path], float]]:
        """Find groups of similar images from similarity matrix
        
        Args:
            image_paths: List of image paths
            similarity_matrix: NxN similarity matrix
            threshold: Similarity threshold
            
        Returns:
            List of (group, avg_similarity) tuples
        """
        n = len(image_paths)
        visited = set()
        groups = []
        
        for i in range(n):
            if i in visited:
                continue
            
            # Find all images similar to image i
            similar_indices = []
            similarities = []
            
            for j in range(n):
                if i != j and similarity_matrix[i, j] >= threshold:
                    similar_indices.append(j)
                    similarities.append(similarity_matrix[i, j])
            
            # If we found similar images, create a group
            if similar_indices:
                group_indices = [i] + similar_indices
                group_paths = [image_paths[idx] for idx in group_indices]
                
                # Calculate average similarity within the group
                group_similarities = []
                for idx1 in group_indices:
                    for idx2 in group_indices:
                        if idx1 < idx2:
                            group_similarities.append(similarity_matrix[idx1, idx2])
                
                avg_similarity = np.mean(group_similarities) if group_similarities else 0.0
                
                groups.append((group_paths, float(avg_similarity)))
                
                # Mark all images in this group as visited
                visited.update(group_indices)
        
        return groups
    
    def load_clip_model(self) -> None:
        """Load CLIP model for geolocation"""
        if self.clip_model is not None or not CLIP_AVAILABLE:
            return
        
        # Load CLIP model (using ViT-B/32 variant for efficiency)
        model_name = "openai/clip-vit-base-patch32"
        self.clip_processor = CLIPProcessor.from_pretrained(
            model_name,
            cache_dir=str(self.cache_dir)
        )
        self.clip_model = CLIPModel.from_pretrained(
            model_name,
            cache_dir=str(self.cache_dir)
        )
        
        # Set to evaluation mode
        self.clip_model.eval()
        self.clip_model.to(self.device)
    
    def _load_location_database(self) -> List[Tuple[float, float, str]]:
        """Load location database from SQLite
        
        Returns:
            List of (latitude, longitude, description) tuples
        """
        if self._location_database is None:
            self._location_database = self._location_db.get_all_locations()
            print(f"Loaded {len(self._location_database)} locations from database")
        
        return self._location_database
    
    def predict_location(
        self, 
        image_path: Path, 
        top_k: int = 5
    ) -> List[Tuple[float, float, float]]:
        """Predict GPS location for an image using CLIP-based geolocation
        
        Args:
            image_path: Path to the image file
            top_k: Number of top predictions to return
            
        Returns:
            List of (latitude, longitude, confidence) tuples
        """
        if not CLIP_AVAILABLE:
            print("CLIP model not available. Install transformers library.")
            return []
        
        # Load model if not already loaded
        self.load_clip_model()
        
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Load location database
            location_database = self._load_location_database()
            
            # Prepare location descriptions
            location_texts = [desc for _, _, desc in location_database]
            
            # Process inputs
            inputs = self.clip_processor(
                text=location_texts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                
                # Calculate similarity scores
                image_embeds = outputs.image_embeds
                text_embeds = outputs.text_embeds
                
                # Normalize embeddings
                image_embeds = image_embeds / image_embeds.norm(dim=-1, keepdim=True)
                text_embeds = text_embeds / text_embeds.norm(dim=-1, keepdim=True)
                
                # Compute similarity (cosine similarity)
                similarity = (image_embeds @ text_embeds.T).squeeze(0)
                
                # Apply softmax to get probabilities
                probabilities = torch.nn.functional.softmax(similarity, dim=0)
            
            # Get top-k predictions
            top_probs, top_indices = torch.topk(probabilities, min(top_k, len(location_database)))
            
            # Convert to list of (lat, lon, confidence) tuples
            predictions = []
            for prob, idx in zip(top_probs.cpu().numpy(), top_indices.cpu().numpy()):
                lat, lon, _ = location_database[idx]
                predictions.append((float(lat), float(lon), float(prob)))
            
            return predictions
            
        except Exception as e:
            print(f"Error predicting location for {image_path}: {e}")
            return []
    
    def clear_cache(self) -> None:
        """Clear feature cache to free memory"""
        self._feature_cache.clear()
        
        # Clear GPU cache if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


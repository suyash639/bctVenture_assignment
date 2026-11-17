"""Feature engineering: load + validate vision outputs, normalise and fuse feature blocks."""
from src.features.bundle import AlignmentError, FeatureBundle, load_feature_bundle
from src.features.fusion import FeatureMatrix, FusionConfig, build_feature_matrix

__all__ = ["AlignmentError", "FeatureBundle", "load_feature_bundle",
           "FeatureMatrix", "FusionConfig", "build_feature_matrix"]

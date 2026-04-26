from abc import ABC, abstractmethod
from typing import Optional

class BasePipeline(ABC):
    """
    Abstract Base Class for Try-On Pipelines.
    All category-specific pipelines must implement `execute`.
    """
    
    @abstractmethod
    def execute(self, human_img_path: str, garm_img_path: str) -> Optional[str]:
        """
        Executes the pipeline to perform the try-on.
        
        Args:
            human_img_path (str): Path to the user image.
            garm_img_path (str): Path to the garment image.
            
        Returns:
            Optional[str]: Path or URL to the generated try-on result image.
        """
        pass

from app.models.schemas import Category
from app.pipelines.base import BasePipeline
from app.pipelines.category_pipelines import (
    ShirtPipeline,
    PantPipeline,
    KurtiPipeline,
    LehengaPipeline
)

class PipelineFactory:
    """
    Factory to return the appropriate pipeline based on category selection.
    """
    @staticmethod
    def get_pipeline(category: Category) -> BasePipeline:
        if category == Category.shirt:
            return ShirtPipeline()
        elif category == Category.pant:
            return PantPipeline()
        elif category == Category.kurti:
            return KurtiPipeline()
        elif category == Category.lehenga:
            return LehengaPipeline()
        else:
            raise ValueError(f"Unsupported category: {category}")

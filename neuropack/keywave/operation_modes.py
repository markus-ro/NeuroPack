from enum import Enum

class TemplateMode(Enum):
    """Enum for template mode. Used to determine how templates are stored in the database."""
    AverageTemplate = 1
    SingleTemplates = 2
    AverageAndSingleTemplates = 3


class SimilarityMode(Enum):
    """Enum for similarity mode. Used to determine how similarity is calculated."""
    BestSimilarity = 1
    AverageSimilarity = 2
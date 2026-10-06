from enum import StrEnum


class DocumentProcessingStage(StrEnum):
    """The last processing stage a document has completed (Decision 031).

    Stages run in declaration order. Later versions append stages
    (keyword index, chunks, embeddings); documents that completed an
    earlier final stage are then picked up again automatically.
    """

    REGISTERED = "registered"
    EXTRACTED = "extracted"


STAGE_ORDER: list[DocumentProcessingStage] = list(DocumentProcessingStage)


def stage_index(stage: DocumentProcessingStage) -> int:
    """Return the position of a stage in the processing order."""
    return STAGE_ORDER.index(stage)

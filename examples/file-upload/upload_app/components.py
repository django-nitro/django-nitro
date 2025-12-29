"""
File Upload Example Component for Django Nitro v0.5.0

Demonstrates:
- {% nitro_file %} template tag
- _handle_file_upload() method
- File size validation
- Image preview
- Progress tracking
"""

from pathlib import Path

from django.core.files.storage import default_storage
from pydantic import BaseModel

from nitro import NitroComponent, register_component


class AvatarUploadState(BaseModel):
    """State for avatar upload component."""

    avatar_url: str = ""
    avatar_name: str = ""
    avatar_size: int = 0
    upload_progress: int = 0
    is_uploading: bool = False


@register_component
class AvatarUpload(NitroComponent[AvatarUploadState]):
    """
    Avatar upload component using {% nitro_file %}.

    Features:
    - Image preview
    - File size validation (max 5MB)
    - Only accepts images
    - Progress tracking
    - Error handling
    """

    template_name = "components/avatar_upload.html"
    state_class = AvatarUploadState

    def get_initial_state(self, **kwargs):
        return AvatarUploadState()

    def _handle_file_upload(self, field: str, uploaded_file=None):
        """
        Handle avatar upload.

        This method is automatically called by {% nitro_file %} tag.
        """
        if not uploaded_file:
            self.error("No file was uploaded")
            return

        # Validate file type
        if not uploaded_file.content_type.startswith("image/"):
            self.error("Only image files are allowed")
            return

        # Save file to media/avatars/
        filename = default_storage.save(
            f"avatars/{uploaded_file.name}", uploaded_file
        )

        # Update state
        self.state.avatar_url = default_storage.url(filename)
        self.state.avatar_name = uploaded_file.name
        self.state.avatar_size = uploaded_file.size

        self.success(f"Avatar '{uploaded_file.name}' uploaded successfully!")

    def clear_avatar(self):
        """Clear the uploaded avatar."""
        if self.state.avatar_url:
            # Extract filename from URL
            filename = Path(self.state.avatar_url).name
            storage_path = f"avatars/{filename}"

            # Delete file if it exists
            if default_storage.exists(storage_path):
                default_storage.delete(storage_path)

        # Reset state
        self.state.avatar_url = ""
        self.state.avatar_name = ""
        self.state.avatar_size = 0

        self.success("Avatar cleared")


class DocumentUploadState(BaseModel):
    """State for document upload component."""

    documents: list[dict] = []
    upload_count: int = 0


@register_component
class DocumentUpload(NitroComponent[DocumentUploadState]):
    """
    Document upload component supporting PDF and DOCX files.

    Features:
    - Multiple file types (PDF, DOCX)
    - File size validation (max 10MB)
    - Upload history
    - Download links
    """

    template_name = "components/document_upload.html"
    state_class = DocumentUploadState

    def get_initial_state(self, **kwargs):
        return DocumentUploadState()

    def _handle_file_upload(self, field: str, uploaded_file=None):
        """Handle document upload."""
        if not uploaded_file:
            self.error("No file was uploaded")
            return

        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if uploaded_file.content_type not in allowed_types:
            self.error("Only PDF and DOCX files are allowed")
            return

        # Save file
        filename = default_storage.save(
            f"documents/{uploaded_file.name}", uploaded_file
        )

        # Add to documents list
        document = {
            "id": self.state.upload_count + 1,
            "name": uploaded_file.name,
            "url": default_storage.url(filename),
            "size": uploaded_file.size,
            "type": uploaded_file.content_type,
        }

        self.state.documents.append(document)
        self.state.upload_count += 1

        self.success(f"Document '{uploaded_file.name}' uploaded successfully!")

    def delete_document(self, doc_id: int):
        """Delete a document by ID."""
        # Find document
        doc = next((d for d in self.state.documents if d["id"] == doc_id), None)

        if not doc:
            self.error("Document not found")
            return

        # Delete file
        filename = Path(doc["url"]).name
        storage_path = f"documents/{filename}"

        if default_storage.exists(storage_path):
            default_storage.delete(storage_path)

        # Remove from list
        self.state.documents = [d for d in self.state.documents if d["id"] != doc_id]

        self.success(f"Document '{doc['name']}' deleted")

from app.plugins.connectors.whatsapp_plugin import WhatsAppBusinessPlugin
from app.plugins.connectors.mobile_plugin import MobileCommunicationPlugin
from app.plugins.connectors.voice_plugin import VoiceCommunicationPlugin
from app.plugins.connectors.gmail_plugin import GmailPlugin
from app.plugins.connectors.email_plugin import EmailPlugin
from app.plugins.connectors.secure_file_plugin import SecureFilePlugin
from app.plugins.connectors.excel_plugin import ExcelPlugin
from app.plugins.connectors.image_plugin import ImageProcessingPlugin
from app.plugins.connectors.pdf_plugin import PDFPlugin
from app.plugins.connectors.document_plugin import DocumentPlugin
from app.plugins.connectors.storage_plugin import StoragePlugin
from app.plugins.connectors.calendar_plugin import CalendarPlugin
from app.plugins.connectors.notification_plugin import NotificationPlugin
from app.plugins.connectors.payment_plugin import PaymentPlugin
from app.plugins.connectors.hospital_plugin import HospitalIntegrationPlugin
from app.plugins.connectors.insurance_plugin import InsuranceIntegrationPlugin
from app.plugins.connectors.csv_plugin import CSVPlugin
from app.plugins.connectors.custom_api_plugin import CustomAPIPlugin

__all__ = [
    "WhatsAppBusinessPlugin",
    "MobileCommunicationPlugin",
    "VoiceCommunicationPlugin",
    "GmailPlugin",
    "EmailPlugin",
    "SecureFilePlugin",
    "ExcelPlugin",
    "ImageProcessingPlugin",
    "PDFPlugin",
    "DocumentPlugin",
    "StoragePlugin",
    "CalendarPlugin",
    "NotificationPlugin",
    "PaymentPlugin",
    "HospitalIntegrationPlugin",
    "InsuranceIntegrationPlugin",
    "CSVPlugin",
    "CustomAPIPlugin",
]
